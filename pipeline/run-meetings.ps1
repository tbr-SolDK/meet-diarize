[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('cpu', 'cuda')]
    [string] $Device,
    [string] $Model,
    [string] $Language = 'da',
    [string] $ComputeType,
    [int] $BatchSize,
    [ValidateSet('vtt', 'srt', 'json', 'all')]
    [string] $OutputFormat = 'all'
)

$converter = Join-Path $PSScriptRoot 'convert-meetings.ps1'
$transcriber = Join-Path $PSScriptRoot 'diarize-meetings.ps1'

& $converter
& $transcriber @PSBoundParameters
