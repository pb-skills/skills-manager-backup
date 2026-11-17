# Skill: Download MP3 Audio

## Description

Download audio from supported URLs using the existing PowerShell `download-mp3` function. Supports individual media downloads, playlists, MP3 conversion, and optional audiobook metadata processing.

## Requirements

- Windows PowerShell
- `yt-dlp.exe` installed and accessible through PATH
- FFmpeg installed for audio extraction and conversion
- Python 3 for audiobook metadata processing
- The `download-mp3` function loaded into the current PowerShell session

## Function Syntax

```powershell
download-mp3 -url <URL> [-playlist] [-metadata]
```

### Parameters

| Parameter | Description |
|---|---|
| `-url` | Source media URL |
| `-playlist` | Download all available items in a playlist |
| `-metadata` | Run the audiobook metadata processing script after downloading |

## Usage Examples

### Example 1 — Download a single MP3

**User intent:** "Download this video as an MP3."

```powershell
download-mp3 -url "https://www.youtube.com/watch?v=EXAMPLE"
```

Downloads the best available audio stream and converts it to MP3.

### Example 2 — Download an entire playlist

**User intent:** "Download all audio tracks from this playlist."

```powershell
download-mp3 -url "https://www.youtube.com/playlist?list=EXAMPLE" -playlist
```

Downloads the playlist's available tracks as MP3 files.

### Example 3 — Download and process audiobook metadata

**User intent:** "Download this audiobook and organise its metadata."

```powershell
download-mp3 -url "https://www.youtube.com/watch?v=EXAMPLE" -metadata
```

After downloading, invokes:

```powershell
python3 "C:\_web_apps_2025\audiobookshelf\fetch_audiobook_metadata.py" `
    --input "C:\_web_apps_2025\audiobookshelf\dropOffZone" `
    --output "C:\_web_apps_2025\audiobookshelf\audiobooks"
```

**Important:** The current function downloads to the working directory. The agent must ensure the intended MP3 files are in the `dropOffZone` before invoking metadata processing.

### Example 4 — Download an audiobook playlist with metadata

**User intent:** "Download this audiobook series and import it into Audiobookshelf."

```powershell
download-mp3 -url "https://www.youtube.com/playlist?list=EXAMPLE" -playlist -metadata
```

Downloads the playlist and invokes audiobook metadata processing.

### Example 5 — Download multiple individual URLs

**User intent:** "Download these three audio tracks."

```powershell
$urls = @(
    "https://www.youtube.com/watch?v=EXAMPLE1",
    "https://www.youtube.com/watch?v=EXAMPLE2",
    "https://www.youtube.com/watch?v=EXAMPLE3"
)

foreach ($url in $urls) {
    download-mp3 -url $url
}
```

### Example 6 — Download directly into the audiobook staging directory

**User intent:** "Download this audio and prepare it for my audiobook library."

```powershell
Push-Location "C:\_web_apps_2025\audiobookshelf\dropOffZone"

try {
    download-mp3 -url "https://www.youtube.com/watch?v=EXAMPLE" -metadata
}
finally {
    Pop-Location
}
```

## Agent Execution Rules

1. Confirm the URL is provided and is from a supported source.
2. Confirm that `download-mp3` is available using `Get-Command download-mp3`.
3. Use `-playlist` only when the user requests multiple playlist items.
4. Use `-metadata` only when audiobook metadata processing is requested.
5. Use the intended destination directory as the working directory before downloading.
6. Avoid duplicate downloads when existing files can be identified.
7. Do not report success unless the underlying download and processing commands succeeded.
8. Only download content the user is authorised to obtain.

## Known Implementation Limitations

- The function does not currently support a destination parameter.
- The metadata processing stage runs even if `yt-dlp.exe` fails.
- The `cd` inside the metadata branch changes the current PowerShell directory.
- The current `-f` placement should be corrected for reliable `yt-dlp` operation.
- The function does not capture a structured success/failure result.

## Recommended Agent Workflow

**Understand request → Validate URL → Select switches → Set destination → Execute download → Validate output → Report result**