[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('cpu', 'cuda')]
    [string] $Device,
    [string] $Model,
    [ValidatePattern('^[a-z]{2,3}$')]
    [string] $Language,
    [string] $ComputeType,
    [int] $BatchSize,
    [ValidateSet('vtt', 'srt', 'json', 'all')]
    [string] $OutputFormat = 'all'
)

$converter = Join-Path $PSScriptRoot 'convert-meetings.ps1'
$transcriber = Join-Path $PSScriptRoot 'diarize-meetings.ps1'
$reviewer = Join-Path $PSScriptRoot 'review-transcripts.py'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$repoRoot = Split-Path -Parent $PSScriptRoot
$inputRoot = Join-Path $repoRoot 'input'
$outputRoot = Join-Path $repoRoot 'output'

if (-not $PSBoundParameters.ContainsKey('Language')) {
    do {
        $languageAnswer = (Read-Host 'Which language is spoken in the meeting or recording? Enter a language code (e.g. da = Danish, en = English, de = German)').Trim()
        if ($languageAnswer -notmatch '^[a-z]{2,3}$') {
            Write-Warning 'Enter a language code of two or three letters; there is no default language.'
        }
    } while ($languageAnswer -notmatch '^[a-z]{2,3}$')
    $Language = $languageAnswer
}
$PSBoundParameters['Language'] = $Language.ToLowerInvariant()

& $converter
& $transcriber @PSBoundParameters

if ($WhatIfPreference -or $OutputFormat -notin @('vtt', 'all')) {
    return
}

$mediaExtensions = @('.aac', '.avi', '.flac', '.m4a', '.mkv', '.mov', '.mp3', '.mp4', '.mpeg', '.mpg', '.ogg', '.wav', '.webm', '.wma', '.wmv')
foreach ($mediaFile in (Get-ChildItem -LiteralPath $inputRoot -Recurse -File | Where-Object { $mediaExtensions -contains $_.Extension.ToLowerInvariant() })) {
    $relativeDirectory = $mediaFile.DirectoryName.Substring($inputRoot.Length).TrimStart('\')
    $transcriptDirectory = if ($relativeDirectory) { Join-Path $outputRoot $relativeDirectory } else { $outputRoot }
    $transcript = Join-Path $transcriptDirectory "$($mediaFile.BaseName).vtt"
    if (-not (Test-Path -LiteralPath $transcript -PathType Leaf)) {
        throw "Transcript not found for '$($mediaFile.FullName)': $transcript"
    }
    $report = Join-Path $transcriptDirectory "$($mediaFile.BaseName).review.html"
    & $python $reviewer --transcript $transcript --media $mediaFile.FullName --output $report
    if ($LASTEXITCODE -ne 0) {
        throw "Review generation failed for '$($mediaFile.FullName)' with exit code $LASTEXITCODE."
    }
}
