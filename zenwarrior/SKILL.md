# ZenWarriorSounds - Video Production Skill

## Trigger Phrases

This skill activates when you ask for any of:

- **"new youtube music video"** — full YouTube video (1920x1080), all songs in sequence
- **"new zen music instagram video"** — Instagram short (1080x1920), first song only, 45 seconds
- **"new zen music video"** — same as YouTube full-length (default behavior)
- **"new youtube music video 10 minutes"** — full video capped at the specified duration

## Workflow

When triggered, the skill runs the following sequence automatically:

### 1. Find next video number
- Scans existing `video*` folders in the project root
- Picks the next number (e.g., if video1–video5 exist → video6)

### 2. Initialize the project
- Runs `Initialize.ps1` to create `video<N>\` with `songs\`, `work\`, `final\` folders
- Copies `manifest.template.txt` → `video<N>\manifest.txt`
- Auto-fills manifest defaults: `title`, `background`, `background_instagram`

### 3. Copy assets from dropOff
- Copies all **MP3/WAV/M4A/AAC/OGG/FLAC/WMA** files from `dropOff\` → `video<N>\songs\`
- Copies the **image** from `dropOff\` → `_library\backgrounds\` (if any image file is present)
- Updates `manifest.txt` to reference the new background image

### 4. Build the video
- Runs `buildVideo.ps1 video<N>` (or with `-Instagram` for shorts)
- Uses ALL songs from `video<N>\songs\` in filename order
- Outputs to `video<N>\final\`

### 5. Move to finalVideos
- Copies the final MP4 to `finalVideos\Video<N>\`

### 6. Archive dropOff
- Moves all files from `dropOff\` → `archive\video<N>\`

## Usage Examples

```
"new youtube music video"
"new zen music instagram video"  
"new zen music video 10 minutes"
"new youtube music video"
```

## Project Structure

```
ZenWarriorSounds/
├── buildVideo.ps1          ← main video builder
├── Initialize.ps1          ← creates new videoN project
├── makeImage.ps1           ← AI image generator (OpenRouter)
├── dropOff/                ← drop songs + background image here
├── finalVideos/            ← completed videos land here
│   └── Video<N>/
├── archive/                ← processed dropOff files archived here
│   └── Video<N>/
├── _library/
│   ├── backgrounds/        ← bg<N>.png (YouTube), short<N>.png (Instagram)
│   ├── overlays/           ← looping overlay videos
│   ├── fonts/              ← EagleLake-Regular.ttf, cooper-black.TTF
│   └── songs/              ← master song library
├── video<N>/               ← per-project folders
│   ├── songs/              ← audio files for this video
│   ├── work/               ← temp/logs
│   ├── final/              ← output MP4s
│   └── manifest.txt        ← project options
└── _tools/
    ├── mergeMP4.bat        ← wrapper: calls buildVideo.ps1
    └── manifest.template.txt
```
