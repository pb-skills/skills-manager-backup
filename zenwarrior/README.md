# ZenWarriorSounds Skill

Automated video production for the ZenWarriorSounds YouTube channel.

## Quick Start

1. Drop songs (MP3/WAV/M4A) and a background image into `./dropOff/`
2. Say **"new youtube music video"** or **"new zen music instagram video"**
3. The skill runs everything automatically

## What It Does

1. Finds the next available `video<N>` number
2. Runs `Initialize.ps1` to create the project folder
3. Copies songs + background image from `dropOff/` into the project
4. Runs `buildVideo.ps1` to produce the video
5. Copies the final MP4 to `finalVideos/Video<N>/`
6. Moves dropOff contents to `archive/Video<N>/`

## Commands

- **"new youtube music video"** — full YouTube video (all songs, natural length)
- **"new youtube music video 10 minutes"** — capped at 10 minutes
- **"new zen music instagram video"** — 45s Instagram short (first song only)
- **"new zen music video"** — same as YouTube full-length (default)

## Project Structure

```
ZenWarriorSounds/
├── .claude/skills/zenwarrior/   ← this skill
├── buildVideo.ps1               ← video builder
├── Initialize.ps1               ← project initializer
├── makeImage.ps1                ← AI image generator
├── dropOff/                     ← put songs + image here
├── finalVideos/Video<N>/        ← completed videos
├── archive/Video<N>/            ← archived dropOff contents
├── video<N>/                    ← per-project folders
│   ├── songs/                   ← audio files
│   ├── final/                   ← output MP4s
│   └── manifest.txt             ← project options
└── _library/                    ← shared assets
    ├── backgrounds/             ← bg<N>.png (YT), short<N>.png (IG)
    ├── overlays/                ← looping overlays
    └── fonts/                   ← EagleLake, Cooper Black
```

## Requirements

- PowerShell 5.1+
- ffmpeg 7+ (in PATH)
- `buildVideo.ps1` and `Initialize.ps1` in the project root
- `_tools\mergeMP4.bat` wrapper (optional)
