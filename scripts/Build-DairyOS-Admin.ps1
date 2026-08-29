[CmdletBinding()]
param(
    [string]$OutputRoot = "dist\DairyOS-Admin"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python was not found."
}

& $python.Source -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Unable to install PyInstaller." }

$spec = Join-Path $repoRoot "packaging\dairyos_admin.spec"
if (-not (Test-Path $spec)) {
    throw "Admin Tool PyInstaller specification is missing: $spec"
}

& $python.Source -m PyInstaller --noconfirm --clean --distpath $OutputRoot --workpath "build\DairyOS-Admin" $spec
if ($LASTEXITCODE -ne 0) { throw "DairyOS Admin Tool build failed." }

Write-Host "DairyOS Admin Tool build completed: $OutputRoot"
