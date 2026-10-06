param(
    [string]$EvidencePath = (Join-Path $PSScriptRoot 'evidence\2026-10-06.json')
)

$ErrorActionPreference = 'Stop'
python (Join-Path $PSScriptRoot 'cache_path.py') --evidence $EvidencePath
if ($LASTEXITCODE -ne 0) {
    throw "cache path experiment failed with exit code $LASTEXITCODE"
}
