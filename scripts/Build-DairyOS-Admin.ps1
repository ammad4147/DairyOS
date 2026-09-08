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

# The standalone Admin executable validates the private PostgreSQL runtime
# relative to its own distribution root. Keep the same version authority used
# by the desktop bundle so Admin restore mode can run before the main app.
$versionSource = Join-Path $repoRoot "runtime\postgresql.version"
if (-not (Test-Path $versionSource -PathType Leaf)) {
    throw "Bundled PostgreSQL version marker is missing: $versionSource"
}
$adminRuntime = Join-Path $OutputRoot "runtime"
New-Item -ItemType Directory -Force -Path $adminRuntime | Out-Null
Copy-Item $versionSource (Join-Path $adminRuntime "postgresql.version") -Force
if (-not (Test-Path (Join-Path $adminRuntime "postgresql.version") -PathType Leaf)) {
    throw "Admin Tool PostgreSQL version marker was not produced."
}

Write-Host "DairyOS Admin Tool build completed: $OutputRoot"
