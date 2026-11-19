<#
.SYNOPSIS
    ZenWarriorSounds - automated video production orchestrator.

.DESCRIPTION
    Triggered by the "zenwarrior" skill. Reads songs and a background image
    from .\dropOff\, initializes a new video project, builds the video,
    copies the result to .\finalVideos\Video<N>\, and archives dropOff contents
    to .\archive\Video<N>\.

    Usage (from the project root):
        .\scripts\run.ps1                  # full YouTube video
        .\scripts\run.ps1 -Instagram       # 45s Instagram short
        .\scripts\run.ps1 -Minutes 10      # cap at 10 minutes
#>
param(
    [switch]$Instagram,
    [int]$Minutes = 0,
    [switch]$Fast,
    [string]$DropOff = ".\dropOff",
    [string]$FinalVideos = ".\finalVideos",
    [string]$Archive = ".\archive"
)

$root = if ($PSScriptRoot) { Split-Path $PSScriptRoot -Parent } else { (Get-Location).Path }
$date = Get-Date -Format ddMMyyyy

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ZenWarriorSounds - Video Production" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# --- 0. ensure directories exist ------------------------------------------------
foreach ($dir in @($DropOff, $FinalVideos, $Archive)) {
    $full = Join-Path $root $dir
    if (-not (Test-Path $full)) { New-Item -ItemType Directory -Force -Path $full | Out-Null }
}

# --- 1. find next video number --------------------------------------------------
$existing = Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^video(\d+)$' } |
    Sort-Object { [int]($_.Name -replace 'video', '') }
$nextNum = if ($existing.Count -eq 0) { 1 } else { [int]($existing[-1].Name -replace 'video', '') + 1 }
$videoFolder = "video{0}" -f $nextNum
$videoFolderPath = Join-Path $root $videoFolder
Write-Host "`n[1/6] Next video number: $videoFolder" -ForegroundColor Green

# --- 2. copy songs from dropOff -------------------------------------------------
$songsDir = Join-Path $videoFolderPath "songs"
New-Item -ItemType Directory -Force -Path $songsDir | Out-Null

$audioExt = @('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma')
$dropOffFull = Join-Path $root $DropOff
$songFiles = @()
if (Test-Path $dropOffFull) {
    $songFiles = Get-ChildItem $dropOffFull -File |
        Where-Object { $audioExt -contains $_.Extension.ToLower() }
    foreach ($sf in $songFiles) {
        Copy-Item $sf.FullName -Destination $songsDir -Force
        Write-Host "  Copied song: $($sf.Name)" -ForegroundColor Yellow
    }
}
if ($songFiles.Count -eq 0) {
    Write-Host "  WARNING: No audio files found in $DropOff" -ForegroundColor Red
    Write-Host "  Drop MP3/WAV/M4A files into $DropOff and re-run." -ForegroundColor Red
    exit 1
}
Write-Host "  Total songs: $($songFiles.Count)" -ForegroundColor Yellow

# --- 3. copy background image from dropOff (if any) ------------------------------
$bgName = ""
$imageFiles = Get-ChildItem $dropOffFull -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -match '\.(png|jpg|jpeg|webp|bmp|gif)$' }
if ($imageFiles.Count -gt 0) {
    $imgSrc = $imageFiles[0]
    $bgName = "bg{0}{1}" -f $nextNum, $imgSrc.Extension
    $bgDst = Join-Path $root "_library\backgrounds\$bgName"
    Copy-Item $imgSrc.FullName -Destination $bgDst -Force
    Write-Host "  Background image: $bgName (from $($imgSrc.Name))" -ForegroundColor Yellow
}

# --- 4. run Initialize.ps1 ------------------------------------------------------
Write-Host "`n[2/6] Running Initialize.ps1..." -ForegroundColor Green
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "Initialize.ps1") *>&1 |
    Select-String -Pattern 'Created|Error|error' | ForEach-Object { $_.Line }

if (-not (Test-Path $videoFolderPath)) {
    Write-Host "ERROR: Initialize.ps1 failed to create $videoFolder" -ForegroundColor Red
    exit 1
}

# --- 5. update manifest with background image if we have one ----------------------
$manifestFile = Join-Path $videoFolderPath "manifest.txt"
if ($bgName -and (Test-Path $manifestFile)) {
    $manifestContent = Get-Content $manifestFile
    $manifestContent = $manifestContent -replace '^background\s*=.*', "background = $bgName"
    $manifestContent = $manifestContent -replace '^#?\s*background_instagram\s*=.*', "background_instagram = $bgName"
    $manifestContent | Set-Content $manifestFile -Encoding UTF8
    Write-Host "  Manifest updated: background = $bgName" -ForegroundColor Yellow
}

# --- 6. build the video ---------------------------------------------------------
Write-Host "`n[3/6] Building video..." -ForegroundColor Green
$buildArgs = @($videoFolder)
if ($Instagram) { $buildArgs += "-Instagram" }
if ($Minutes -gt 0) { $buildArgs += "-Minutes", $Minutes }
if ($Fast) { $buildArgs += "-Fast" }

$buildScript = Join-Path $root "buildVideo.ps1"
$buildOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $buildScript @buildArgs 2>&1
$buildOutput | ForEach-Object {
    $line = $_.ToString()
    if ($line -match 'error|Error|throw|FAIL') { Write-Host $line -ForegroundColor Red }
    elseif ($line -match 'Done|Output|Songs|Duration|Format') { Write-Host $line -ForegroundColor Green }
    else { Write-Host $line }
}

# --- 7. find the final output and copy to finalVideos ----------------------------
Write-Host "`n[4/6] Copying final video to finalVideos..." -ForegroundColor Green
$finalDir = Join-Path $videoFolderPath "final"
$finalVideosDir = Join-Path $root $FinalVideos
$videoDestDir = Join-Path $finalVideosDir ("Video{0}" -f $nextNum)
New-Item -ItemType Directory -Force -Path $videoDestDir | Out-Null

$finalMp4s = Get-ChildItem $finalDir -Filter "*.mp4" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

$copied = @()
foreach ($mp4 in $finalMp4s) {
    $dest = Join-Path $videoDestDir $mp4.Name
    Copy-Item $mp4.FullName -Destination $dest -Force
    $copied += $dest
    Write-Host "  Copied: $mp4.Name -> Video$nextNum\" -ForegroundColor Yellow
}

if ($copied.Count -eq 0) {
    Write-Host "  WARNING: No MP4 found in $finalDir" -ForegroundColor Red
} else {
    Write-Host "  Final videos: $copied.Count file(s) in Video$nextNum" -ForegroundColor Green
}

# --- 8. archive dropOff contents ------------------------------------------------
Write-Host "`n[5/6] Archiving dropOff contents..." -ForegroundColor Green
$archiveDir = Join-Path $root $Archive
$archiveVideoDir = Join-Path $archiveDir ("Video{0}" -f $nextNum)
New-Item -ItemType Directory -Force -Path $archiveVideoDir | Out-Null

if (Test-Path $dropOffFull) {
    $archived = Get-ChildItem $dropOffFull -File -ErrorAction SilentlyContinue
    foreach ($af in $archived) {
        $dest = Join-Path $archiveVideoDir $af.Name
        # Move (not copy) so dropOff is cleared
        Move-Item $af.FullName -Destination $dest -Force
        Write-Host "  Archived: $af.Name" -ForegroundColor Yellow
    }
    Write-Host "  dropOff cleared." -ForegroundColor Green
}

# --- 9. summary -----------------------------------------------------------------
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  DONE - Video $nextNum" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Project:  $videoFolderPath" -ForegroundColor White
Write-Host "  Songs:    $($songFiles.Count) file(s)" -ForegroundColor White
Write-Host "  Final:    $videoDestDir" -ForegroundColor White
Write-Host "  Archive:  $archiveVideoDir" -ForegroundColor White
Write-Host "  Manifest: $manifestFile" -ForegroundColor White
Write-Host ""
Write-Host "  Next: review final video, then run:" -ForegroundColor Yellow
Write-Host "    _tools\mergeMP4 $videoFolder -Instagram   (if you want a short)" -ForegroundColor Yellow
Write-Host "    _tools\mergeMP4 $videoFolder -Full         (natural length)" -ForegroundColor Yellow
Write-Host "    _tools\mergeMP4 $videoFolder -Loop         (repeat to 1 hour)" -ForegroundColor Yellow
