---
name: youtube-upload
description: Uploads finished ZenWarriorSounds videos from finalVideos\ to the YouTube channel via the YouTube Data API (title, description, tags, privacy, schedule, playlist, thumbnail). Use when the user asks to upload, publish, post, or schedule a video to YouTube, or says "upload the latest video" / "upload Video5".
---

# ZenWarriorSounds - YouTube Upload Skill

Script: `.claude/skills/youtube-upload/scripts/upload.py` (run from the project root `Y:\13_YoutubeChannels\ZenWarriorSounds`).

Credentials are in `%USERPROFILE%\.zenwarrior\youtube\` (`client_secret.json`, `token.json`) - **never** copy them into the repo.

## Commands

```bash
python .claude/skills/youtube-upload/scripts/upload.py whoami                 # check auth + channel
python .claude/skills/youtube-upload/scripts/upload.py upload latest --dry-run
python .claude/skills/youtube-upload/scripts/upload.py upload latest [options]
python .claude/skills/youtube-upload/scripts/upload.py upload Video5 [options]
python .claude/skills/youtube-upload/scripts/upload.py upload "finalVideos/Video5/file.mp4" [options]
```

| Request | Options |
|---|---|
| default / "upload it" | *(none)* - **private** (from config) |
| "unlisted" / "public" | `--privacy unlisted` / `--privacy public` |
| "schedule for tomorrow 6pm" | `--publish-at 2026-11-21T18:00:00Z` (convert the user's local time to UTC; forces private until then) |
| "add to playlist X" | `--playlist "X"` (created if missing) |
| custom title | `--title "..."` (max 100 chars) |
| thumbnail | `--thumbnail path.jpg` (≤2 MB; channel must be phone-verified) |
| only the YouTube / only the Short | `--only youtube` / `--only instagram` |
| re-upload | `--force` |

A folder target uploads **every** mp4 in it. Portrait videos ≤3 min are uploaded as Shorts (`#Shorts` added).

## Steps

1. Run `whoami`. If it says "Not authorized" or refresh failed, re-authorize with the **copy-paste flow** (the local-listener `auth` command did not receive the browser callback on this machine):
   - `upload.py auth-url` → give the user the printed link. They sign in with the channel account, and the browser ends on a "This site can't be reached" page at `http://localhost:8765/?state=…&code=…` (expected).
   - The user pastes that full URL → `upload.py auth-finish "<url>"` (quote it). It saves the token and prints the channel.
   - The OAuth client is a **Web application** client with redirect URI `http://localhost:8765/`, and the channel account is a Test user. Never connect to port 8765 yourself while a sign-in is pending.
2. Always run `--dry-run` first and show the user the title, privacy and description. Publishing is outward-facing: get a yes before uploading anything **public** or **scheduled**. Private uploads after a dry run the user has seen are fine.
3. Upload. Use `run_in_background` for files over ~500 MB (1-hour videos are 1 GB+); otherwise a 600000 ms timeout.
4. Report the `https://youtu.be/<id>` link and the Studio edit link. The script writes `<file>.youtube.json` next to the mp4, which prevents duplicate uploads.

## Metadata rules (automatic)

- **Title**: filename with date/format suffix stripped, `_` → spaces, title-cased, plus ` | Relaxing Zen Meditation Music | Zen Warrior Sounds` (or ` | 1 Hour Meditation Music | ...` for ≥55 min).
- **Description**: `config/description.txt` with `{title}` and `{duration_text}` filled in. Edit that file to change the template.
- **Tags**: from `tags.txt` at the project root, trimmed to YouTube's 500-char limit.
- **Defaults** (`config/defaults.json`): category 10 (Music), not made for kids, `containsSyntheticMedia: true` (AI-generated music disclosure), language `en`, optional default `playlist`.

## Troubleshooting

- **Video locked as private / "unverified app"**: Google locks API uploads from unaudited projects to private. Fix = submit the YouTube API audit form (https://support.google.com/youtube/contact/yt_api_form) or publish manually in Studio.
- **Re-auth every 7 days**: the OAuth consent screen is in "Testing" mode. Set it to "In production" in Google Cloud Console → Google Auth Platform → Audience.
- **quotaExceeded**: default quota is 10,000 units/day; one upload ≈ 1,600 units (~6 uploads/day). Wait until midnight Pacific time.
- **access_denied / 403 on sign-in**: add the channel's Google account as a Test user under Audience.
