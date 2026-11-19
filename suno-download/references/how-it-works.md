# How suno-download works

## Why a plain download fails

`https://d2lwuy8qc234o3.cloudfront.net/1/clip/<clip-id>.m4a` is served by
CloudFront with `Content-Type: audio/mp4`, but the object stored at the origin is
**encrypted**: ~8 MB of uniformly random bytes (entropy 8.0 bits/byte), no `ftyp`
box anywhere in the file. The Suno web player decrypts it client-side before
handing it to `<audio>`. Saving it with `curl`, `wget`, `Invoke-WebRequest`,
`requests.get(...).content`, or a browser "Save link as" gives you an unplayable
blob.

## The pipeline (reproduced from Suno's bundle)

1. **License request** — `POST https://studio-api.prod.suno.com/api/mango/rights`

   ```json
   {"content_params": {"content_id": "<clip-id>", "content_type": "clip"}}
   ```

   Response: `{"key": "<b64>", "iv": "<b64>"}` and, for signed-out callers, also
   `"glt": "<JWT>"` (guest license token).

2. **Wrapping key** — `gcm_key = SHA-256(<seed>)`, where `<seed>` is
   - your Clerk session token (`__session` cookie value, sent as
     `Authorization: Bearer …`) when signed in, or
   - the `glt` string from the license response when signed out.

3. **Unwrap the AES-CTR parameters** — each blob is `iv(12) || ciphertext || tag(16)`
   under AES-GCM with additional data = the clip id string:

   ```text
   ctr_key = AES-GCM-decrypt(gcm_key, blob_key[0:12], blob_key[12:], aad=clip_id)
   ctr_iv  = AES-GCM-decrypt(gcm_key, blob_iv[0:12],  blob_iv[12:],  aad=clip_id)
   ```

4. **Decrypt the media** — AES-CTR with `ctr_key`/`ctr_iv`, 128-bit big-endian
   counter starting at `ctr_iv` and incrementing one per 16-byte block. The
   plaintext starts with `ftyp…` (an MP4 whose audio track is Opus, i.e.
   `m4a-opus`); a WebM/EBML alternative starts with `1a 45 df a3`.

5. **Transcode** — `ffmpeg -i plain.m4a -vn -c:a libmp3lame -q:a 2` with
   `title`/`artist` ID3 tags, giving `<song name>.mp3`.

The script verifies the decrypted magic (`ftyp` / EBML) and fails loudly rather
than writing a corrupt file.

## Media variants

`media_urls[]` may contain:

| `content_type` | `encoding` | Meaning |
|---|---|---|
| `m4a-opus` | set | encrypted MP4/Opus (the common v5 case) |
| `webm-opus` | set | encrypted WebM/Opus |
| `mp3` | absent | plain unencrypted MP3 (older clips) — no license/decrypt needed |

The script prefers an `m4a-opus` entry, then `webm-opus`, then `mp3`, and only
runs the license + decryption steps when the chosen entry has `encoding`.

## Cookies (optional)

Export cookies for `suno.com` from a signed-in browser in the EditThisCookie
JSON array format (a list of `{name, value, …}` objects) or Netscape
`cookies.txt`, and pass the path with `--cookies`. The script uses the
`__session` JWT; nothing is sent anywhere except Suno's API and CDN.

Treat that file like a password. Do not commit it, do not copy it into the skill
folder, delete it when done.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `error: unrecognised host` | Not a suno.com/CDN URL. Paste the song page link. |
| `error: no clip id (UUID) found` | The link contains no clip UUID. |
| `license request failed … 401/403` | Stale session. Re-export `cookies.json`, or retry without cookies (guest token). |
| `decryption failed` / `unknown container` | Stale license or session mismatch. Re-export cookies and retry; the raw bytes are kept as `*.encrypted.bin` for debugging. |
| `ffmpeg not found` | Install ffmpeg on PATH, or use `-f m4a`. |
| `Already exists: …` | Add `--force` or use `-o`. |
| `ModuleNotFoundError: cryptography` | `pip install cryptography`. |

## Limits

- One clip per run; no playlist/batch mode.
- Works against Suno's current `m4a-opus` delivery. If Suno changes the license
  endpoint or cipher scheme, the `fetch_license` / `decrypt_audio` functions in
  `scripts/suno_download.py` are what need updating.
- Only download songs you have the right to download; respect Suno's terms and
  the creators' rights.
