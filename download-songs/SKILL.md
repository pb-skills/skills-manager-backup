---
name:download-music-to-mp3
description:download music to mb3 from youtube using obscore browser and download-mp3 function
---
# Download Music to MP3
Search on youtube using obscura browser for the youtube song name (preferably studio version), fetch its URL then download it using the download-mp3 function.

## When to use it
- When the user wants to download the music from YouTube
- When the user asks download a song or play list
- When the user asks true download an album from an artist

## Workflow

### 1. Open Obscura browser
Run the /obscura skill to Search for the artist and song name the user have specified and then fetch its URL.

### 2. Decide Song or playlist
Make a decision if the user is trying to download a song or entire playlist and then use the correct function to download what the user specified.

### 3. Download music using download-mp3
Using /scripts/download-mp3.ps1 Download the songs or playlist using the correct flags and URL. If you are not sure how to use the script, there is a guide on /references/download-mp3-reference.md

#### 4. Fetch its Metadata 
After downloading this song, you can confirm if the fire exists in the folder, let's run the skill /etch-music-metadata to collect its metadata and move the file to the correct song.


