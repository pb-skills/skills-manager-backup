---
name: fetch-music-metadata
description: 'Look up and embed online metadata (title, artist, album, year, genre, cover art) for MP3 files. Renames files to "Song name - Artist" format and organizes them into per-artist subfolders. Uses Deezer and iTunes APIs for metadata lookup.'
---

# Fetch Music Metadata

Look up and embed correct online metadata for MP3 files, rename them to "Song name - Artist" format, and reorganize into per-artist subfolders.

## When to Use

- You have a folder of MP3 files with inconsistent or missing filenames
- You need to embed ID3 tags (title, artist, album, year, genre, cover art)
- You want to organize music files into per-artist folders
- You need to rename files to a consistent "Song name - Artist.mp3" format

## Workflow

### 1. Inventory MP3 files

List all `.mp3` files in the target directory. Exclude `_work` and other non-MP3 files.

### 2. Parse filenames for artist/title hints

Existing filenames often contain "Artist - Title" patterns. Use this as a fallback but always verify against online lookup.

### 3. Look up metadata from Deezer (primary) and iTunes (fallback)

- **Deezer API** (`https://api.deezer.com/search`): Provides title, artist, album, cover_xl URL. Primary source for cover art.
- **iTunes API** (`https://itunes.apple.com/search`): Provides title, artist, album, releaseDate, primaryGenreName, artworkUrl100. Fallback for genre/year data.

For each file:
1. Extract the filename (without `.mp3`)
2. Split on separator (` - `, ` | `, ` / `, ` : `) to get candidate artist/title pairs
3. Query Deezer with the combined search term
4. Score results using similarity matching (SequenceMatcher on normalized strings)
5. If Deezer confidence < 1.5, fall back to iTunes
6. If both fail, use filename parsing as last resort

### 4. Download cover art

For files with cover URLs:
- Deezer covers: use URL as-is (already high-res, e.g., `1000x1000`)
- iTunes covers: replace `100x100` with `600x600` in the URL
- Save to `_work/_covers/<original_filename>.jpg`
- Skip if file already exists

### 5. Embed ID3 tags using Mutagen

Write the following ID3 frames to each MP3:
- `TIT2` — title
- `TPE1` — artist
- `TALB` — album
- `TDRC` — year (4-digit)
- `TCON` — genre
- `APIC` — cover art (JPEG, type=3 front cover)

Clear existing tags before writing to avoid duplicates.

### 6. Rename files to "Song name - Artist.mp3"

New filename format: `{title} - {artist}.mp3`

Sanitize filenames by replacing these characters with `_`: `< > : " / \ | ? *`
Strip trailing dots and spaces (Windows forbids these at end of filenames).
Limit filenames to 100 characters.

### 7. Organize into per-artist subfolders

Create a folder for each artist under the music directory.
Move (or copy, if rename is blocked) each renamed MP3 into its artist folder.
Artist folder names should be sanitized the same way as filenames.

### 8. Handle edge cases

- **No separator in filename**: Treat the whole name as title-only; artist comes from lookup
- **Multiple artists** (e.g., "Artist1, Artist2 & Artist3 - Song"): Keep all artists in the artist field
- **Duplicate filenames**: Append `(2)`, `(3)`, etc.
- **Special characters in artist names**: Remove leading/trailing quotes (fullwidth and ASCII)
- **Performance video / official video suffixes**: Strip these from title during lookup
- **Low confidence matches** (< 1.0): Flag for manual review

## Key Files

| File | Purpose |
|------|---------|
| `lookup3.json` | Deezer metadata results (title, artist, album, cover, confidence) |
| `lookup.json` | iTunes metadata results (title, artist, album, year, genre, artwork) |
| `_covers/` | Downloaded cover art images |
| `_staging/` | Temporary staging for processed files |
| `manifest.json` | Processing summary (counts, errors) |

## Requirements

- Python 3 with `mutagen`, `requests` packages
- Internet access for API lookups (Deezer + iTunes)
- Write permissions to the music directory

## API Rate Limits

- Deezer: ~50 requests/minute (be gentle, use 0.02-0.06s delays)
- iTunes: ~20 requests/minute (use 0.15-0.25s delays)
- Batch process with incremental saves every 10-25 files

## Confidence Thresholds

- **≥ 1.5**: High confidence — auto-accept
- **1.0 – 1.5**: Medium confidence — accept but flag for review
- **< 1.0**: Low confidence — use filename fallback, flag for manual review