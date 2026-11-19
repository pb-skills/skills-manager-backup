#!/usr/bin/env python3
"""
Download a Suno song and save it in the current directory as <song name>.mp3.

Usage
-----
    python suno_download.py https://suno.com/song/<clip-id>      # song page URL
    python suno_download.py <clip-id>                            # bare clip UUID
    python suno_download.py <url> -o "my song.mp3"
    python suno_download.py <url> -f m4a                         # skip MP3 conversion
    python suno_download.py <url> --cookies cookies.json         # optional sign-in export
    python suno_download.py <url> --force                        # overwrite existing file

Accepted targets
----------------
* a Suno song page, e.g. https://suno.com/song/ff366622-4d9b-4733-9a82-84cc51fc677f
* any shorter share link that contains the clip id
* a bare clip UUID
* a direct CDN URL (d2lwuy8qc234o3.cloudfront.net/1/clip/<id>.m4a)

The clip id is extracted from the URL and used to ask Suno's API for the
current media URL, so old/hard-coded CDN links are not required.

Why it is not a plain curl
--------------------------
Suno's CDN serves an AES-CTR *encrypted* MP4/Opus blob, so the raw bytes
are not playable. The web player decrypts them like this (verified against
Suno's bundle):

    1. POST https://studio-api.prod.suno.com/api/mango/rights
       {"content_params": {"content_id": <clip id>, "content_type": "clip"}}
       -> {"key": b64, "iv": b64}    (+ "glt" for signed-out visitors)

    2. gcm_key = SHA-256(<__session JWT>  , or "glt" when signed out)

    3. ctr_key = AES-GCM-decrypt(key[0:12], key[12:], aad=<clip id>, gcm_key)
       ctr_iv  = AES-GCM-decrypt(iv[0:12],  iv[12:],  aad=<clip id>, gcm_key)

    4. audio_plain = AES-CTR(ctr_key, ctr_iv) applied to the downloaded bytes

The result is a valid MP4 containing Opus audio ("m4a-opus"); ffmpeg then
turns it into an MP3.

Requires: Python 3.9+ and the `cryptography` package (pip install cryptography).
ffmpeg (in PATH) is optional: only needed to produce a real .mp3.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://studio-api.prod.suno.com"
RIGHTS_URL = API_BASE + "/api/mango/rights"
CLIP_URL_TMPL = "https://d2lwuy8qc234o3.cloudfront.net/1/clip/{id}.m4a"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,pt;q=0.7",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://suno.com/",
    "origin": "https://suno.com",
    "user-agent": UA,
}

UUID_RE = re.compile(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")
CHUNK = 256 * 1024
COVER_TYPES = ("m4a-opus", "webm-opus", "mp3")


# --------------------------------------------------------------------------- #
# target parsing
# --------------------------------------------------------------------------- #
def parse_clip_id(target: str) -> str:
    """Accept a song URL, a share link, a bare UUID or a direct CDN URL."""
    target = (target or "").strip().strip('"').strip("'")
    if not target:
        raise ValueError("empty target")
    if target.lower().startswith(("http://", "https://")):
        host = (urllib.parse.urlparse(target).hostname or "").lower()
        if host not in ("suno.com", "www.suno.com", "app.suno.ai", "suno.ai") \
                and ".suno." not in host and "cloudfront.net" not in host \
                and "suno.com" not in host:
            raise ValueError(f"unrecognised host {host!r} — paste a suno.com song link")
    match = UUID_RE.search(target)
    if not match:
        raise ValueError(
            "no clip id (UUID) found in that target.\n"
            "  Expected something like https://suno.com/song/ff366622-4d9b-4733-9a82-84cc51fc677f"
        )
    return match.group(1).lower()



# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def human(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GiB"


def safe_name(text: str, fallback: str = "clip") -> str:
    text = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', " ", text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:90] or fallback


def scrape_cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def session_token(cookies: dict[str, str]) -> str | None:
    for key in ("__session", "__session_Jnxw-muT"):
        if cookies.get(key):
            return cookies[key]
    for key, value in cookies.items():
        if key.startswith("__session"):
            return value
    return None


def load_cookies(path: str) -> dict[str, str]:
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read().strip()
    if raw.startswith("#") or "\t" in raw:  # Netscape cookies.txt
        out = {}
        for line in raw.splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                out[parts[5]] = parts[6]
        return out
    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]
    return {c["name"]: c["value"] for c in data if c.get("name")}


def http_json(url: str, payload: dict | None = None, cookies: dict[str, str] | None = None,
              authorized: bool = False, timeout: int = 60) -> dict:
    headers = dict(BROWSER_HEADERS)
    headers["accept"] = "application/json, text/plain, */*"
    if cookies:
        headers["cookie"] = scrape_cookie_header(cookies)
        if authorized:
            token = session_token(cookies)
            if token:
                headers["authorization"] = f"Bearer {token}"
    body = json.dumps(payload).encode() if payload is not None else None
    if body is not None:
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers,
                                 method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:200].decode("utf-8", "replace")
        raise RuntimeError(f"{url} -> HTTP {exc.code}: {detail}") from exc


# --------------------------------------------------------------------------- #
# crypto (AES-GCM unwrap + AES-CTR decrypt, matching WebCrypto)
# --------------------------------------------------------------------------- #
def _load_crypto():
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return Cipher, algorithms, modes, AESGCM
    except ImportError:
        pass
    try:  # fall back to pycryptodome if present
        from Crypto.Cipher import AES
        from Crypto.Protocol.KDF import HKDF  # noqa: F401  (import check only)

        class _AESGCM:
            def __init__(self, key: bytes):
                self.key = key

            def decrypt(self, iv: bytes, data: bytes, aad: bytes) -> bytes:
                ct, tag = data[:-16], data[-16:]
                c = AES.new(self.key, AES.MODE_GCM, nonce=iv)
                c.update(aad)
                return c.decrypt_and_verify(ct, tag)

        class _Cipher:
            def __init__(self, algo, mode):
                self.a, self.m = algo, mode

            def decryptor(self):
                return AES.new(self.a.key, AES.MODE_CTR,
                               nonce=b"", initial_value=int.from_bytes(self.m.iv, "big"))

        class _Algorithms:
            AES = lambda key: type("A", (), {"key": key})()  # noqa: E731

        class _Modes:
            CTR = lambda iv: type("M", (), {"iv": iv})()  # noqa: E731

        return _Cipher, _Algorithms, _Modes, _AESGCM
    except ImportError:
        pass
    print("ERROR: the 'cryptography' package is required to decrypt Suno audio.\n"
          "       Install it with:  pip install cryptography", file=sys.stderr)
    raise SystemExit(2)


def aes_gcm_decrypt(aesgcm, gcm_key: bytes, blob: bytes, aad: bytes) -> bytes:
    """WebCrypto layout: blob = iv(12) || ciphertext || tag(16)."""
    if len(blob) <= 12:
        raise ValueError("license blob too short")
    return aesgcm(gcm_key).decrypt(blob[:12], blob[12:], aad)


def decrypt_audio(encrypted: bytes, license_: dict, clip_id: str, cookies: dict[str, str] | None) -> tuple[bytes, str]:
    """Return (plaintext bytes, container kind: 'mp4' | 'webm' | 'unknown')."""
    Cipher, algorithms, modes, AESGCM = _load_crypto()

    seed = None
    if cookies:
        seed = session_token(cookies)
    if not seed:
        seed = license_.get("glt")
    if not seed:
        raise RuntimeError(
            "License response has no wrapping key: pass --cookies cookies.json "
            "with a fresh __session cookie."
        )

    gcm_key = hashlib.sha256(seed.encode()).digest()
    aad = clip_id.encode()

    key_blob = base64.b64decode(license_["key"])
    iv_blob = base64.b64decode(license_["iv"])
    ctr_key = aes_gcm_decrypt(AESGCM, gcm_key, key_blob, aad)
    ctr_iv = aes_gcm_decrypt(AESGCM, gcm_key, iv_blob, aad)
    if len(ctr_key) not in (16, 24, 32) or len(ctr_iv) != 16:
        raise RuntimeError(f"unexpected key material (key={len(ctr_key)}B iv={len(ctr_iv)}B)")

    decryptor = Cipher(algorithms.AES(ctr_key), modes.CTR(ctr_iv)).decryptor()
    plain = decryptor.update(encrypted) + decryptor.finalize()

    if plain[4:8] == b"ftyp":
        return plain, "mp4"
    if plain[:4] == b"\x1aE\xdf\xa3":
        return plain, "webm"
    return plain, "unknown"


# --------------------------------------------------------------------------- #
# network steps
# --------------------------------------------------------------------------- #
def fetch_clip_info(clip_id: str, cookies: dict[str, str] | None) -> dict:
    try:
        return http_json(f"{API_BASE}/api/clip/{clip_id}", cookies=cookies, authorized=True)
    except Exception:
        return {}


def fetch_license(clip_id: str, cookies: dict[str, str] | None) -> dict:
    payload = {"content_params": {"content_id": clip_id, "content_type": "clip"}}
    try:
        return http_json(RIGHTS_URL, payload=payload, cookies=cookies, authorized=True)
    except RuntimeError as exc:
        if cookies:
            print(f"  signed-in license request failed ({exc}); retrying signed-out...")
            return http_json(RIGHTS_URL, payload=payload)
        raise


def download_encrypted(url: str, cookies: dict[str, str] | None) -> bytes:
    headers = dict(BROWSER_HEADERS)
    if cookies:
        headers["cookie"] = scrape_cookie_header(cookies)
    req = urllib.request.Request(url, headers=headers, method="GET")
    buf = bytearray()
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            ctype = (resp.headers.get("content-type") or "?").lower()
            total = int(resp.headers.get("content-length") or 0)
            if "html" in ctype:
                raise RuntimeError("CDN returned HTML instead of audio (link expired or blocked)")
            print(f"  HTTP {resp.status} | {ctype} | {human(total) if total else 'unknown size'}")
            while True:
                chunk = resp.read(CHUNK)
                if not chunk:
                    break
                buf.extend(chunk)
                done = len(buf)
                if total:
                    pct = done * 100 / total
                    speed = done / max(time.time() - started, 1e-6)
                    sys.stdout.write(f"\r  {pct:5.1f}%  {human(done)} / {human(total)}  ({human(speed)}/s)   ")
                else:
                    sys.stdout.write(f"\r  {human(done)} ")
                sys.stdout.flush()
            sys.stdout.write("\n")
            if total and len(buf) != total:
                raise RuntimeError(f"incomplete download: {len(buf)} of {total} bytes")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GET {url} -> HTTP {exc.code} {exc.reason}") from exc
    return bytes(buf)


def pick_media(clip: dict) -> dict | None:
    items = clip.get("media_urls") or []
    if not items:
        return None
    for wanted in COVER_TYPES:
        for item in items:
            if item.get("content_type") == wanted:
                return item
    return items[0]


# --------------------------------------------------------------------------- #
# ffmpeg
# --------------------------------------------------------------------------- #
def find_ffmpeg() -> str | None:
    import shutil
    return shutil.which("ffmpeg")


def to_mp3(src: str, dst: str, meta: dict[str, str]) -> None:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found in PATH; write the .m4a instead (--format m4a)")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", src,
           "-vn", "-c:a", "libmp3lame", "-q:a", "2"]
    for key in ("title", "artist", "album"):
        if meta.get(key):
            cmd += ["-metadata", f"{key}={meta[key]}"]
    cmd.append(dst)
    print(f"  converting to MP3 ({os.path.basename(src)} -> {os.path.basename(dst)})")

    # Redirect ffmpeg's stdio to a real file rather than a pipe: pipe-backed
    # stdio is unavailable in some sandboxes (WinError 5 / EPERM) and is not
    # needed to report an error.
    log_path = dst + ".ffmpeg.log"
    try:
        with open(log_path, "wb") as log:
            proc = subprocess.run(cmd, stdout=log, stderr=log)
        if proc.returncode != 0:
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
                    detail = fh.read().strip()[:800]
            except OSError:
                detail = "(no log)"
            raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}):\n{detail}")
    finally:
        if os.path.exists(log_path):
            try:
                os.remove(log_path)
            except OSError:
                pass


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):  # keep titles with unicode readable on Windows
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="Download a Suno song page and save it as .mp3 / .m4a.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("target",
                    help="song page URL (https://suno.com/song/<id>), any link containing "
                         "the clip id, a bare UUID, or a direct CDN URL")
    ap.add_argument("-o", "--out", help="output file (default: '<song title>.mp3')")
    ap.add_argument("-f", "--format", choices=["mp3", "m4a", "webm"], default="mp3",
                    help="mp3 needs ffmpeg; m4a/webm save the decrypted container as-is")
    ap.add_argument("-c", "--cookies", help="cookies JSON export / Netscape cookie file (optional)")
    ap.add_argument("--force", action="store_true", help="overwrite existing output")
    ap.add_argument("--keep-source", action="store_true", help="keep the decrypted .m4a when making an .mp3")
    args = ap.parse_args(argv)

    try:
        clip_id = parse_clip_id(args.target)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cookies = None
    if args.cookies:
        if not os.path.exists(args.cookies):
            print(f"error: cookie file not found: {args.cookies}", file=sys.stderr)
            return 2
        cookies = load_cookies(args.cookies)

    print(f"Clip: {clip_id}")
    info = fetch_clip_info(clip_id, cookies)
    title = info.get("title") or "clip"
    artist = info.get("display_name") or info.get("handle") or ""
    if title and title != "clip":
        print(f"Title: {title}" + (f" — {artist}" if artist else ""))

    media = pick_media(info)
    url = (media or {}).get("url") or CLIP_URL_TMPL.format(id=clip_id)
    delivery = (media or {}).get("delivery") or "progressive"
    content_type = (media or {}).get("content_type") or "m4a-opus"
    encrypted = bool((media or {}).get("encoding"))
    print(f"Source: {url}")
    print(f"        {content_type} / {delivery} / encrypted={encrypted}")

    # Output is named after the song title only, e.g. "Celtic Wind LoTR.mp3".
    # The clip id is used only when the title is missing or unusable.
    base = safe_name(title, "")
    base = re.sub(r"\.(mp3|m4a|wav|flac|ogg|opus|webm)$", "", base, flags=re.I).strip()
    stem = base or clip_id
    fmt = args.format
    if args.out:  # let an explicit extension win over --format
        suffix = os.path.splitext(args.out)[1].lower()
        fmt = {".mp3": "mp3", ".m4a": "m4a", ".webm": "webm"}.get(suffix, fmt)
    out = args.out or f"{stem}.{fmt}"
    out = os.path.abspath(out)
    if os.path.exists(out) and not args.force:
        print(f"Already exists: {out}  (use --force to overwrite)")
        return 0

    print("1/3 license ...")
    try:
        lic = fetch_license(clip_id, cookies)
    except RuntimeError as exc:
        print(f"error: license request failed: {exc}\n"
              "       If the link needs a signed-in session, re-export cookies.json "
              "from a logged-in suno.com tab.", file=sys.stderr)
        return 1

    print("2/3 download + decrypt ...")
    raw = download_encrypted(url, cookies)
    if encrypted:
        try:
            plain, kind = decrypt_audio(raw, lic, clip_id, cookies)
        except Exception as exc:
            print(f"error: decryption failed: {exc}", file=sys.stderr)
            print("       Usually means the license/session went stale — re-export cookies "
                  "and retry, or add --cookies cookies.json.", file=sys.stderr)
            return 1
        if kind == "unknown":
            dump = os.path.splitext(out)[0] + ".encrypted.bin"
            open(dump, "wb").write(raw)
            print(f"error: decryption produced an unknown container; raw bytes kept at {dump}",
                  file=sys.stderr)
            return 1
        m4a_ext = ".webm" if kind == "webm" else ".m4a"
    else:
        plain, kind, m4a_ext = raw, "mp4", ".m4a"
    print(f"  decrypted {human(len(plain))} ({kind})")

    tmp_src = os.path.splitext(out)[0] + ".source" + m4a_ext
    with open(tmp_src, "wb") as fh:
        fh.write(plain)

    try:
        print(f"3/3 save -> {out}")
        if fmt == "mp3":
            if not find_ffmpeg():
                fallback = os.path.splitext(out)[0] + ".m4a"
                os.replace(tmp_src, fallback)
                print(f"  ffmpeg not found — saved {fallback} instead (still plays in VLC/browsers).")
                out = fallback
            else:
                to_mp3(tmp_src, out, {"title": title, "artist": artist})
                if args.keep_source:
                    kept = os.path.splitext(out)[0] + m4a_ext
                    if os.path.abspath(kept) != out:
                        os.replace(tmp_src, kept)
                        print(f"  kept decrypted source -> {kept}")
        else:
            os.replace(tmp_src, out)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        # remove the intermediate decrypted file unless the user asked to keep it
        keep_src = fmt == "mp3" and args.keep_source and os.path.exists(out)
        if os.path.exists(tmp_src) and not keep_src:
            try:
                os.remove(tmp_src)
            except OSError:
                pass

    if not os.path.exists(out):
        print("error: output file was not produced", file=sys.stderr)
        return 1
    print(f"Saved: {out}  ({human(os.path.getsize(out))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
