[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('cpu', 'cuda')]
    [string] $Device,
    [string] $Model,
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z]{2,3}$')]
    [string] $Language,
    [string] $ComputeType,
    [int] $BatchSize,
    [ValidateSet('vtt', 'srt', 'json', 'all')]
    [string] $OutputFormat = 'all'
)

$pipelineRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent $pipelineRoot
$audioRoot = Join-Path $repoRoot 'output\.audio'
$envFile = Join-Path $repoRoot '.env'
$outputRoot = Join-Path $repoRoot 'output'
$whisperxPath = Join-Path $pipelineRoot '.venv\Scripts\whisperx.exe'
$cacheRoot = Join-Path $pipelineRoot '.cache'
$ffmpegBin = Join-Path $pipelineRoot '.tools\ffmpeg\bin'

if (-not (Test-Path -LiteralPath $whisperxPath -PathType Leaf)) {
    throw "Repo-local WhisperX was not found: $whisperxPath. Run .\pipeline\bootstrap-local.ps1 first."
}

if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) {
    throw "Environment file not found: $envFile. Copy .env.example to .env and set HF_TOKEN."
}

if (-not (Test-Path -LiteralPath $audioRoot -PathType Container)) {
    throw "Prepared audio directory not found: $audioRoot. Run .\pipeline\convert-meetings.ps1 first."
}

function Get-EnvValue([string] $name, [string] $fallback) {
    $line = Get-Content -LiteralPath $envFile | Where-Object { $_ -match "^\s*$name\s*=" } | Select-Object -First 1
    if ($null -eq $line) {
        return $fallback
    }

    return (($line -split '=', 2)[1]).Trim().Trim('"').Trim("'")
}

$hfToken = Get-EnvValue 'HF_TOKEN' ''
if ([string]::IsNullOrWhiteSpace($hfToken) -or $hfToken -like 'hf_replace*') {
    throw 'HF_TOKEN is missing in .env.'
}

if ([string]::IsNullOrWhiteSpace($Device)) { $Device = Get-EnvValue 'WHISPERX_DEVICE' 'cpu' }
if ([string]::IsNullOrWhiteSpace($Model)) { $Model = Get-EnvValue 'WHISPERX_MODEL' 'large-v3' }
if ([string]::IsNullOrWhiteSpace($ComputeType)) { $ComputeType = Get-EnvValue 'WHISPERX_COMPUTE_TYPE' 'int8' }
if ($BatchSize -eq 0) { $BatchSize = [int](Get-EnvValue 'WHISPERX_BATCH_SIZE' '4') }
$modelRoot = Join-Path $cacheRoot "models\$Model"

$audioFiles = @(Get-ChildItem -LiteralPath $audioRoot -Recurse -File -Filter '*.wav')
if ($audioFiles.Count -eq 0) {
    Write-Host "No WAV files found under $audioRoot. Add media files to input\ and run pipeline\convert-meetings.ps1 first."
    exit 0
}

if (-not (Test-Path -LiteralPath $outputRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
}

$previousHfHome = $env:HF_HOME
$previousTorchHome = $env:TORCH_HOME
$previousNltkData = $env:NLTK_DATA
$previousHfHubOffline = $env:HF_HUB_OFFLINE
$previousPythonPath = $env:PYTHONPATH
$previousPath = $env:PATH
$env:HF_HOME = Join-Path $cacheRoot 'huggingface'
$env:TORCH_HOME = Join-Path $cacheRoot 'torch'
$env:NLTK_DATA = Join-Path $cacheRoot 'nltk'
$env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($previousPythonPath)) { $pipelineRoot } else { "$pipelineRoot;$previousPythonPath" }
$env:PATH = "$ffmpegBin;$previousPath"
if ((Get-EnvValue 'WHISPERX_OFFLINE' '0') -eq '1') {
    $env:HF_HUB_OFFLINE = '1'
}

try {
    foreach ($audioFile in $audioFiles) {
        $relativeDirectory = $audioFile.DirectoryName.Substring($audioRoot.Length).TrimStart('\')
        $transcriptDirectory = if ([string]::IsNullOrWhiteSpace($relativeDirectory)) {
            $outputRoot
        } else {
            Join-Path $outputRoot $relativeDirectory
        }
        if (-not (Test-Path -LiteralPath $transcriptDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $transcriptDirectory -Force | Out-Null
        }

        $arguments = @(
        $audioFile.FullName,
        '--model', $Model,
        '--language', $Language.ToLowerInvariant(),
        '--device', $Device,
        '--compute_type', $ComputeType,
        '--batch_size', $BatchSize,
        '--model_dir', $modelRoot,
        '--diarize',
        '--hf_token', $hfToken,
        '--output_dir', $transcriptDirectory,
        '--output_format', $OutputFormat)

        Write-Host "Diarizing $($audioFile.Name)"
        if ($PSCmdlet.ShouldProcess($audioFile.FullName, 'Run WhisperX transcription and diarization')) {
            & $whisperxPath @arguments
            if ($LASTEXITCODE -ne 0) {
                throw "WhisperX failed for '$($audioFile.FullName)' with exit code $LASTEXITCODE."
            }
        }
    }
}
finally {
    $env:HF_HOME = $previousHfHome
    $env:TORCH_HOME = $previousTorchHome
    $env:NLTK_DATA = $previousNltkData
    $env:HF_HUB_OFFLINE = $previousHfHubOffline
    $env:PYTHONPATH = $previousPythonPath
    $env:PATH = $previousPath
}

Write-Host "Transcribed $($audioFiles.Count) file(s). Output: $outputRoot"