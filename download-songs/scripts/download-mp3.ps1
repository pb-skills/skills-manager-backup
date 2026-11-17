function download-mp3 {
    param (
        [string]$url,
        [switch]$metadata,
	[switch]$playlist
    )
	
	if($playlist){
	yt-dlp.exe $url -f --yes-playlist 'ba[acodec^=mp3]/ba/b' -x --audio-format mp3
	}
	else{	
	yt-dlp.exe $url -f 'ba[acodec^=mp3]/ba/b' -x --audio-format mp3
	}
    if ($metadata) {
cd "C:\_web_apps_2025\audiobookshelf\dropOffZone"
        Write-Host "[INFO] - Fetching Audiobook metadata and uploading to audiobookshelf/audiobooks" -ForegroundColor Gray
	
        python3 "C:\_web_apps_2025\audiobookshelf\fetch_audiobook_metadata.py" --input "C:\_web_apps_2025\audiobookshelf\dropOffZone" --output "C:\_web_apps_2025\audiobookshelf\audiobooks"
    }
}