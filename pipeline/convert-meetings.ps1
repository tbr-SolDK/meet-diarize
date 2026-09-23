[CmdletBinding(SupportsShouldProcess)]
param()

$repoRoot = Split-Path -Parent $PSScriptRoot
$inputRoot = Join-Path $repoRoot 'input'
$audioRoot = Join-Path $repoRoot 'output\.audio'
$ffmpegPath = Join-Path $PSScriptRoot '.tools\ffmpeg\bin\ffmpeg.exe'

if (-not (Test-Path -LiteralPath $ffmpegPath -PathType Leaf)) {
    throw "Repo-local FFmpeg was not found: $ffmpegPath. Run .\pipeline\bootstrap-local.ps1 first."
}

if (-not (Test-Path -LiteralPath $inputRoot -PathType Container)) {
    throw "Input directory not found: $inputRoot"
}

$mediaExtensions = @(
    '.aac', '.avi', '.flac', '.m4a', '.mkv', '.mov', '.mp3', '.mp4',
    '.mpeg', '.mpg', '.ogg', '.wav', '.webm', '.wma', '.wmv'
)
$mediaFiles = @(Get-ChildItem -LiteralPath $inputRoot -Recurse -File |
    Where-Object { $mediaExtensions -contains $_.Extension.ToLowerInvariant() })

if ($mediaFiles.Count -eq 0) {
    Write-Host "No supported audio or video files found under $inputRoot"
    exit 0
}

foreach ($mediaFile in $mediaFiles) {
    $relativeDirectory = $mediaFile.DirectoryName.Substring($inputRoot.Length).TrimStart('\')
    $outputDirectory = if ([string]::IsNullOrWhiteSpace($relativeDirectory)) {
        $audioRoot
    } else {
        Join-Path $audioRoot $relativeDirectory
    }
    $outputFile = Join-Path $outputDirectory "$($mediaFile.BaseName).wav"

    if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
        New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    }

    Write-Host "Preparing $($mediaFile.Name) -> $outputFile"

    if ($PSCmdlet.ShouldProcess($mediaFile.FullName, 'Convert audio with FFmpeg')) {
        & $ffmpegPath -y -i $mediaFile.FullName -map 0:a:0 -c:a pcm_s16le -vn $outputFile

        if ($LASTEXITCODE -ne 0) {
            throw "FFmpeg failed for '$($mediaFile.FullName)' with exit code $LASTEXITCODE."
        }
    }
}

Write-Host "Prepared $($mediaFiles.Count) audio/video file(s)."