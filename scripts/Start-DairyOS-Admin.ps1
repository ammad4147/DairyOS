[CmdletBinding()]
param(
    [int]$Port = 18082
)

$ErrorActionPreference = "Stop"

# This launcher intentionally starts the standalone administrative surface.
# It does not start, import, or modify the nine-tab operational UI.
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (Get-Command dairyos-admin -ErrorAction SilentlyContinue) {
    & dairyos-admin --host 127.0.0.1 --port $Port
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python was not found. Install DairyOS or activate its Python environment before starting the Admin Tool."
}

& $python.Source -m dairyos.admin.app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
