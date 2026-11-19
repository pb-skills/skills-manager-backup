---
name: suno-download
description: Download a song from Suno (suno.com) as a playable MP3 (or decrypted M4A) by pasting the song page URL. Handles Suno's encrypted m4a-opus CDN media (license + AES-GCM unwrap + AES-CTR decrypt) and converts to MP3 with ffmpeg. Use when the user pastes a https://suno.com/song/<id> link, asks to download/save/grab a Suno song or clip, or wants a Suno track as an mp3 file.
---

# Suno Download

Turn a Suno song page URL into a normal audio file on disk.

The bundled script `scripts/suno_download.py` (in this skill's base directory)
does the whole job: it resolves the clip, fetches Suno's license, downloads the
encrypted `.m4a`, decrypts it, and writes `<song name>.mp3` **into the current
working directory**.

## When to use

- The user pastes a link like `https://suno.com/song/ff366622-4d9b-4733-9a82-84cc51fc677f`.
- The user asks to download / save / grab a Suno song or clip to their machine.
- The user wants a Suno track as an `.mp3` (or the decrypted `.m4a`).

This is **not** a plain HTTP download: the CDN URL
(`d2lwuy8qc234o3.cloudfront.net/1/clip/<id>.m4a`) returns an AES-CTR encrypted
blob, so `curl`/`Invoke-WebRequest` produce an unplayable file. Use the script.

## Quick start

Substitute this skill's base directory for `<SKILL>` (the directory containing
this `SKILL.md`):

```bash
python "<SKILL>/scripts/suno_download.py" "https://suno.com/song/<clip-id>"
```

Windows PowerShell equivalent:

```powershell
python "<SKILL>\scripts\suno_download.py" "https://suno.com/song/<clip-id>"
```

The file lands in the directory you run it from. Run it from the folder where
the user wants the song — or pass `-o` explicitly.

## Options

| Flag | Meaning |
|---|---|
| `target` (required) | song page URL, any link containing the clip id, bare UUID, or direct CDN URL |
| `-o, --out` | output file (default: `<song title>.mp3`; clip id only if the title is missing) |
| `-f, --format` | `mp3` (default), `m4a`, or `webm` — `m4a`/`webm` skip ffmpeg and save the decrypted container |
| `-c, --cookies` | JSON cookie export (EditThisCookie array) or Netscape `cookies.txt`; optional |
| `--force` | overwrite an existing output file |
| `--keep-source` | with `-f mp3`, also keep the decrypted `.m4a` |

Useful invocations:

```bash
# normal download
python "<SKILL>/scripts/suno_download.py" https://suno.com/song/<id>

# no ffmpeg available / want the source container
python "<SKILL>/scripts/suno_download.py" https://suno.com/song/<id> -f m4a

# keep both the mp3 and the decrypted m4a
python "<SKILL>/scripts/suno_download.py" https://suno.com/song/<id> --keep-source

# overwrite
python "<SKILL>/scripts/suno_download.py" https://suno.com/song/<id> --force
```

## What the script prints

```
Clip: ff366622-4d9b-4733-9a82-84cc51fc677f
Title: Celtic Wind LoTR — Cyber Samurai
Source: https://d2lwuy8qc234o3.cloudfront.net/1/clip/<id>.m4a
        m4a-opus / progressive / encrypted=True
1/3 license ...
2/3 download + decrypt ...
  ...
3/3 save -> C:\path\to\Celtic Wind LoTR.mp3
Saved: C:\path\to\Celtic Wind LoTR.mp3  (10.1 MiB)
```

Exit codes: `0` success (or "already exists"), `1` license/decrypt/save failure,
`2` bad arguments (bad URL, cookie file not found).

## Requirements

- Python 3.9+
- Python package `cryptography` (`pip install cryptography`) — needed to decrypt.
  The script prints the exact install command if it is missing.
- `ffmpeg` on `PATH` — only for `.mp3`; without it the script writes the
  decrypted `.m4a` instead and says so.

## Notes

- Sign-in is usually **not** required: the license endpoint issues a guest token
  (`glt`) to signed-out callers. Pass `--cookies cookies.json` for clips that
  need your session (e.g. your own unpublished/private songs) or if anonymous
  access starts being refused. Never put cookie files inside the skill folder.
- Two different songs with the same title map to the same output filename — use
  `-o` to keep both.
- One song per run.
- Report the final absolute path back to the user.

Encryption details, cookie format and troubleshooting: `references/how-it-works.md`.
