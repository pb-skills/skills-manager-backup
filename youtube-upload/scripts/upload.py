"""ZenWarriorSounds - YouTube uploader.

Usage (from the project root):
  python .claude/skills/youtube-upload/scripts/upload.py auth
  python .claude/skills/youtube-upload/scripts/upload.py whoami
  python .claude/skills/youtube-upload/scripts/upload.py upload <file.mp4 | Video5 | latest> [options]

Credentials live in %USERPROFILE%\\.zenwarrior\\youtube (never in the repo):
  client_secret.json  - OAuth "Desktop app" client from console.cloud.google.com
  token.json          - created by `auth`, refreshed automatically
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SKILL_DIR.parent.parent.parent
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",  # playlists, thumbnails, channel info
]


def load_defaults():
    cfg = json.loads((SKILL_DIR / "config" / "defaults.json").read_text(encoding="utf-8"))
    cfg["credentialsDir"] = Path(os.path.expandvars(cfg["credentialsDir"]))
    return cfg


# ---------------------------------------------------------------- auth
def get_credentials(cfg, interactive=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    cdir = cfg["credentialsDir"]
    secret = cdir / "client_secret.json"
    token = cdir / "token.json"
    if not secret.exists():
        sys.exit(f"Missing {secret}. Download the OAuth Desktop client JSON there.")

    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if creds and creds.valid and not interactive:
        return creds
    if creds and creds.expired and creds.refresh_token and not interactive:
        try:
            creds.refresh(Request())
            token.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except Exception as e:  # refresh token revoked/expired (7-day limit in Testing mode)
            print(f"Token refresh failed ({e}); re-authorization needed.", file=sys.stderr)
    if not interactive:
        sys.exit("Not authorized. Run:  python .claude/skills/youtube-upload/scripts/upload.py auth")

    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    creds = flow.run_local_server(
        port=8765, prompt="select_account consent", access_type="offline",
        authorization_prompt_message="Opening browser for Google sign-in:\n{url}\n",
        success_message="ZenWarriorSounds uploader authorized. You can close this tab.",
    )
    cdir.mkdir(parents=True, exist_ok=True)
    token.write_text(creds.to_json(), encoding="utf-8")
    print(f"Saved token to {token}")
    return creds


MANUAL_REDIRECT = "http://localhost:8765/"


def manual_auth_start(cfg):
    """Step 1: print a sign-in URL; the browser ends on a 'can't connect' page whose URL holds the code."""
    from google_auth_oauthlib.flow import Flow
    cdir = cfg["credentialsDir"]
    flow = Flow.from_client_secrets_file(str(cdir / "client_secret.json"), SCOPES,
                                         redirect_uri=MANUAL_REDIRECT, autogenerate_code_verifier=True)
    url, state = flow.authorization_url(prompt="select_account consent", access_type="offline")
    (cdir / "pending_auth.json").write_text(json.dumps(
        {"state": state, "code_verifier": flow.code_verifier}), encoding="utf-8")
    print(url)


def manual_auth_finish(cfg, redirected_url):
    """Step 2: exchange the code from the pasted address-bar URL for a token."""
    from google_auth_oauthlib.flow import Flow
    cdir = cfg["credentialsDir"]
    pending = json.loads((cdir / "pending_auth.json").read_text(encoding="utf-8"))
    flow = Flow.from_client_secrets_file(str(cdir / "client_secret.json"), SCOPES,
                                         redirect_uri=MANUAL_REDIRECT, state=pending["state"])
    flow.code_verifier = pending["code_verifier"]
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # localhost http redirect
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    flow.fetch_token(authorization_response=redirected_url.strip())
    (cdir / "token.json").write_text(flow.credentials.to_json(), encoding="utf-8")
    (cdir / "pending_auth.json").unlink(missing_ok=True)
    print(f"Saved token to {cdir / 'token.json'}")


def youtube_client(cfg, interactive=False):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=get_credentials(cfg, interactive), cache_discovery=False)


def print_channel(yt):
    r = yt.channels().list(part="snippet,statistics", mine=True).execute()
    if not r.get("items"):
        print("Authorized, but this Google account has no YouTube channel.")
        return
    ch = r["items"][0]
    print(f"Channel: {ch['snippet']['title']}  (id {ch['id']})  "
          f"subscribers={ch['statistics'].get('subscriberCount', '?')} "
          f"videos={ch['statistics'].get('videoCount', '?')}")


# ---------------------------------------------------------------- resolve input
def resolve_videos(target):
    """Return list of mp4 paths for a file, a VideoN folder name, or 'latest'."""
    fv = PROJECT_ROOT / "finalVideos"
    p = Path(target)
    if p.suffix.lower() == ".mp4":
        p = p if p.is_absolute() else (PROJECT_ROOT / p)
        if not p.exists():
            sys.exit(f"File not found: {p}")
        return [p]
    if target.lower() == "latest":
        folders = [d for d in fv.glob("Video*") if d.is_dir()]
        if not folders:
            sys.exit("No finalVideos/Video* folders.")
        folder = max(folders, key=lambda d: int(re.sub(r"\D", "", d.name) or 0))
    else:
        num = re.sub(r"\D", "", target)
        folder = fv / f"Video{num}"
    if not folder.is_dir():
        sys.exit(f"Folder not found: {folder}")
    mp4s = sorted(folder.glob("*.mp4"))
    if not mp4s:
        sys.exit(f"No .mp4 in {folder}")
    return mp4s


# ---------------------------------------------------------------- metadata
def probe(path):
    ff = PROJECT_ROOT / "ffmpeg" / "bin" / "ffprobe.exe"
    exe = str(ff) if ff.exists() else "ffprobe"
    try:
        out = subprocess.run(
            [exe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height:format=duration", "-of", "json", str(path)],
            capture_output=True, text=True, check=True).stdout
        j = json.loads(out)
        s = j["streams"][0]
        return float(j["format"]["duration"]), int(s["width"]), int(s["height"])
    except Exception:
        return None, None, None


def duration_text(sec):
    if not sec:
        return "Pure"
    m = round(sec / 60)
    if m >= 55:
        h = round(sec / 3600)
        return f"{h} hour" + ("s" if h > 1 else "")
    return f"{m} minutes"


def title_from_filename(path, seconds, is_short):
    stem = path.stem
    one_hour = stem.lower().startswith("1_hour_")
    stem = re.sub(r"^1_hour_", "", stem, flags=re.I)
    stem = re.sub(r"_\d{8}_(youtube|instagram)(_\d+m)?$", "", stem, flags=re.I)
    words = stem.replace("_", " ").replace("-", " ").split()
    small = {"by", "the", "of", "and", "in", "on", "a", "an", "to", "for", "at"}
    words = [w if (i and w.lower() in small) else (w[:1].upper() + w[1:]) for i, w in enumerate(words)]
    base = " ".join(words) or "Zen Warrior Sounds"
    if is_short:
        title = f"{base} #Shorts"
    elif one_hour or (seconds and seconds >= 55 * 60):
        title = f"{base} | {duration_text(seconds).title()} Meditation Music | Zen Warrior Sounds"
    else:
        title = f"{base} | Relaxing Zen Meditation Music | Zen Warrior Sounds"
    return title[:100], base


def load_tags(cfg):
    f = PROJECT_ROOT / cfg["tagsFile"]
    if not f.exists():
        return []
    raw = [t.strip() for t in f.read_text(encoding="utf-8", errors="ignore").split(",") if t.strip()]
    tags, total = [], 0
    for t in raw:  # YouTube limit: 500 chars incl. separators (tags with spaces count +2 for quotes)
        cost = len(t) + (2 if " " in t else 0) + (1 if tags else 0)
        if total + cost > 490:
            break
        tags.append(t)
        total += cost
    return tags


def build_description(cfg, base_title, seconds, override_file=None):
    f = Path(override_file) if override_file else SKILL_DIR / "config" / cfg["descriptionTemplate"]
    text = f.read_text(encoding="utf-8")
    return text.replace("{title}", base_title).replace("{duration_text}", duration_text(seconds))[:5000]


# ---------------------------------------------------------------- upload
def find_or_create_playlist(yt, name, privacy):
    if re.fullmatch(r"PL[\w-]{10,}", name):
        return name
    req = yt.playlists().list(part="snippet", mine=True, maxResults=50)
    while req:
        r = req.execute()
        for p in r.get("items", []):
            if p["snippet"]["title"].strip().lower() == name.strip().lower():
                return p["id"]
        req = yt.playlists().list_next(req, r)
    r = yt.playlists().insert(part="snippet,status", body={
        "snippet": {"title": name}, "status": {"privacyStatus": privacy}}).execute()
    print(f"Created playlist '{name}' ({r['id']})")
    return r["id"]


def upload_one(yt, cfg, path, args):
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    log_file = path.with_suffix(".youtube.json")
    if log_file.exists() and not args.force:
        prev = json.loads(log_file.read_text(encoding="utf-8"))
        print(f"SKIP {path.name}: already uploaded -> {prev.get('url')} (use --force to re-upload)")
        return prev

    seconds, w, h = probe(path)
    is_short = bool(w and h and h > w and seconds and seconds <= 180)
    auto_title, base = title_from_filename(path, seconds, is_short)
    title = (args.title or auto_title)[:100]
    description = build_description(cfg, base, seconds, args.description_file)
    if is_short and "#Shorts" not in description:
        description = "#Shorts\n\n" + description
    privacy = args.privacy or cfg["privacy"]

    status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": cfg["madeForKids"],
        "containsSyntheticMedia": cfg["containsSyntheticMedia"],
        "embeddable": True,
    }
    if args.publish_at:
        status["privacyStatus"] = "private"  # required for scheduled publishing
        status["publishAt"] = args.publish_at
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": load_tags(cfg),
            "categoryId": cfg["categoryId"],
            "defaultLanguage": cfg["defaultLanguage"],
            "defaultAudioLanguage": cfg["defaultLanguage"],
        },
        "status": status,
    }

    size_mb = path.stat().st_size / 1e6
    print(f"\n=== {path.name}  ({size_mb:.0f} MB, {duration_text(seconds)}, {w}x{h}{', Short' if is_short else ''})")
    print(f"Title:   {title}")
    print(f"Privacy: {status['privacyStatus']}" + (f"  publishAt={args.publish_at}" if args.publish_at else ""))
    print(f"Tags:    {len(body['snippet']['tags'])}")
    if args.dry_run:
        print("--- description ---\n" + description + "\n--- (dry run, nothing uploaded)")
        return None

    media = MediaFileUpload(str(path), mimetype="video/mp4", chunksize=16 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=True)
    response, retries, t0 = None, 0, time.time()
    while response is None:
        try:
            st, response = req.next_chunk()
            if st:
                pct = st.progress() * 100
                el = time.time() - t0
                eta = el / st.progress() - el if st.progress() else 0
                print(f"  {pct:5.1f}%  elapsed {el/60:4.1f} min  eta {eta/60:4.1f} min", flush=True)
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and retries < 8:
                retries += 1
                time.sleep(min(2 ** retries, 60))
                continue
            raise
        except (ConnectionError, TimeoutError, OSError) as e:
            if retries < 8:
                retries += 1
                print(f"  network error ({e}), retry {retries}", flush=True)
                time.sleep(min(2 ** retries, 60))
                continue
            raise

    vid = response["id"]
    url = f"https://youtu.be/{vid}"
    print(f"UPLOADED: {url}  (studio: https://studio.youtube.com/video/{vid}/edit)")

    if args.thumbnail:
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(args.thumbnail)).execute()
            print(f"Thumbnail set: {args.thumbnail}")
        except HttpError as e:
            print(f"Thumbnail failed (channel may need phone verification): {e}")

    playlist = args.playlist or cfg.get("playlist")
    if playlist:
        try:
            pid = find_or_create_playlist(yt, playlist, "public")
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
            print(f"Added to playlist {playlist}")
        except HttpError as e:
            print(f"Playlist add failed: {e}")

    record = {"videoId": vid, "url": url, "title": title, "privacy": status["privacyStatus"],
              "publishAt": args.publish_at, "uploadedAt": dt.datetime.now().isoformat(timespec="seconds"),
              "file": path.name}
    log_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main():
    ap = argparse.ArgumentParser(description="ZenWarriorSounds YouTube uploader")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth", help="one-time browser sign-in (local listener)")
    sub.add_parser("auth-url", help="manual sign-in step 1: print URL")
    fin = sub.add_parser("auth-finish", help="manual sign-in step 2: paste redirected URL")
    fin.add_argument("redirected_url")
    sub.add_parser("whoami", help="show the authorized channel")
    up = sub.add_parser("upload")
    up.add_argument("target", help="path to .mp4, a VideoN folder name, or 'latest'")
    up.add_argument("--privacy", choices=["private", "unlisted", "public"])
    up.add_argument("--publish-at", help="schedule, ISO 8601 UTC e.g. 2026-11-21T18:00:00Z")
    up.add_argument("--title")
    up.add_argument("--description-file")
    up.add_argument("--thumbnail")
    up.add_argument("--playlist", help="playlist name (created if missing) or PL... id")
    up.add_argument("--only", choices=["youtube", "instagram"], help="filter files in a folder")
    up.add_argument("--dry-run", action="store_true")
    up.add_argument("--force", action="store_true", help="re-upload even if already uploaded")
    args = ap.parse_args()
    cfg = load_defaults()

    if args.cmd == "auth":
        print_channel(youtube_client(cfg, interactive=True))
        return
    if args.cmd == "auth-url":
        manual_auth_start(cfg)
        return
    if args.cmd == "auth-finish":
        manual_auth_finish(cfg, args.redirected_url)
        print_channel(youtube_client(cfg))
        return
    if args.cmd == "whoami":
        print_channel(youtube_client(cfg))
        return

    files = resolve_videos(args.target)
    if args.only:
        files = [f for f in files if f"_{args.only}" in f.stem.lower()]
    if not files:
        sys.exit("No matching videos.")
    yt = None if args.dry_run else youtube_client(cfg)
    for f in files:
        upload_one(yt, cfg, f, args)


if __name__ == "__main__":
    main()
