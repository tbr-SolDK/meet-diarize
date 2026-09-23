[CmdletBinding(SupportsShouldProcess)]
param()

$pipelineRoot = $PSScriptRoot
$toolsRoot = Join-Path $pipelineRoot '.tools'
$pythonRoot = Join-Path $toolsRoot 'python'
$ffmpegRoot = Join-Path $toolsRoot 'ffmpeg'
$ffmpegPath = Join-Path $ffmpegRoot 'bin\ffmpeg.exe'
$ffmpegArchive = Join-Path $toolsRoot 'ffmpeg-release-essentials.zip'
$ffmpegExtractRoot = Join-Path $toolsRoot '.ffmpeg-extract'
$ffmpegUrl = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'uv was not found on PATH. Install it from https://docs.astral.sh/uv/getting-started/installation/ and run this script again.'
}

if ($PSCmdlet.ShouldProcess($pipelineRoot, 'Create the repo-local Python 3.12 runtime and WhisperX environment')) {
    $env:UV_PYTHON_INSTALL_DIR = $pythonRoot
    & uv python install 3.12
    if ($LASTEXITCODE -ne 0) {
        throw "uv could not install Python 3.12 (exit code $LASTEXITCODE)."
    }

    & uv sync --directory $pipelineRoot
    if ($LASTEXITCODE -ne 0) {
        throw "uv could not create the WhisperX environment (exit code $LASTEXITCODE)."
    }
}

if (-not (Test-Path -LiteralPath $ffmpegPath -PathType Leaf)) {
    if ($PSCmdlet.ShouldProcess($ffmpegPath, 'Download and extract repo-local FFmpeg')) {
        New-Item -ItemType Directory -Path $toolsRoot -Force | Out-Null
        Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegArchive
        Remove-Item -LiteralPath $ffmpegExtractRoot -Recurse -Force -ErrorAction SilentlyContinue
        Expand-Archive -LiteralPath $ffmpegArchive -DestinationPath $ffmpegExtractRoot -Force
        $extractedFfmpeg = Get-ChildItem -LiteralPath $ffmpegExtractRoot -Recurse -File -Filter 'ffmpeg.exe' | Select-Object -First 1
        if ($null -eq $extractedFfmpeg) {
            throw 'FFmpeg archive did not contain ffmpeg.exe.'
        }

        New-Item -ItemType Directory -Path (Split-Path -Parent $ffmpegPath) -Force | Out-Null
        Copy-Item -LiteralPath $extractedFfmpeg.FullName -Destination $ffmpegPath -Force
        Remove-Item -LiteralPath $ffmpegExtractRoot -Recurse -Force
    }
}

Write-Host "Bootstrap complete. Verify with .\pipeline\.venv\Scripts\whisperx.exe --help and .\pipeline\.tools\ffmpeg\bin\ffmpeg.exe -version."