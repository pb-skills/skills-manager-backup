---
name: zenwarrior
description: ZenWarriorSounds video production - builds a YouTube (1920x1080) or Instagram (1080x1920) music video from the songs and background image in dropOff\. Use when the user asks for a new youtube/zen/music video, an Instagram short, or a video of N minutes / 1 hour.
---

# ZenWarriorSounds - Video Production Skill

## How to run (one command does everything)

From the project root `Y:\13_YoutubeChannels\ZenWarriorSounds`:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/skills/zenwarrior/scripts/run.ps1 [options]
```

Map the user's request to options:

| Request | Options |
|---|---|
| "new youtube music video" / "new zen music video" | *(none)* - all songs, natural length |
| "... 5 minutes" / "... 10 minutes" | `-Minutes 5` - capped, audio fades out at the end |
| "... 1 hour" / "long version" | `-Loop` - songs repeated in order to 60 min |
| "new zen music instagram video" / short / reel | `-Instagram` - 45 s portrait, first song |
| quick draft / test | add `-Fast` |
| "no crossfade" / hard cuts | `-Crossfade 0` (default is 3 s between songs) |

Run with a long timeout (up to 600000 ms). Long renders (`-Loop`) should use `run_in_background`.

## Before running - check

1. `ls dropOff` - there must be at least one audio file (mp3/wav/m4a/aac/ogg/flac/wma). If it is empty, stop and ask the user to drop songs in; the script exits without creating a project.
2. Optionally sum song durations with `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>`, and tell the user if a `-Minutes` cap will cut songs short, or if the songs are shorter than what they asked for (in that case suggest `-Loop` or adding a `target_duration` to the manifest).

## What the script does

1. **Picks the next video number.** It scans `video*` folders in the root, `archive\` and `finalVideos\`, so numbers are never reused (video1/video2 live only in `archive\`).
2. **Creates `video<N>\`** with `songs\ work\ final\` and `manifest.txt` copied from `_tools\manifest.template.txt`. It does this itself and does not call `Initialize.ps1`, which only scans the root and would pick a wrong number.
3. **Copies audio** from dropOff into `video<N>\songs\`.
4. **Copies the first image** from dropOff to `_library\backgrounds\bg<N>.<ext>`.
5. **Updates the manifest:** sets `title` to the image filename (sanitized, e.g. `Moonlit_Samurai_Meditation_by_the_Stream`), sets `background` and `background_instagram`, and sets `crossfade`.
6. **Runs `buildVideo.ps1 video<N>`** with the options. Output goes to `video<N>\final\`.
7. **Copies the MP4(s)** to `finalVideos\Video<N>\`.
8. **Moves everything** in dropOff to `archive\Video<N>\`, which clears dropOff.

## After running - verify and report

- `ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact <mp4>`: confirm the resolution and duration.
- Report the final path in `finalVideos\Video<N>\`, the duration, and the size.
- Tell the user the follow-ups: `_tools\mergeMP4 video<N> -Full | -Loop | -Instagram`.

## Output filenames

`<title>_<ddMMyyyy>_<youtube|instagram>[_<N>m].mp4`. A `-Minutes` cap adds `_<N>m`. A loop render is prefixed with `1_hour_`.

## Manifest options (video<N>\manifest.txt)

`title`, `background`, `background_instagram`, `overlay` (comma-separated, from `_library\overlays`), `crossfade` (s), `fade_out` (s, default 4, 0 = off; applies to any capped render), `target_duration` (s, loop to this length).

## Rebuilding an existing project

Don't re-run run.ps1 (it would make a new number). Call the builder directly:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File buildVideo.ps1 video<N> [-Minutes N] [-Full] [-Loop] [-Instagram] [-Fast]
```

Then copy the new MP4 to `finalVideos\Video<N>\` yourself.

## Project structure

```
ZenWarriorSounds/
├── buildVideo.ps1          ← video builder
├── Initialize.ps1          ← manual project init (NOT used by the skill)
├── dropOff/                ← songs + background image go here
├── finalVideos/Video<N>/   ← completed videos
├── archive/Video<N>/       ← processed dropOff files (+ old projects video1, video2)
├── _library/backgrounds|overlays|fonts|songs
├── video<N>/songs|work|final + manifest.txt
└── _tools/mergeMP4.bat, manifest.template.txt
```
