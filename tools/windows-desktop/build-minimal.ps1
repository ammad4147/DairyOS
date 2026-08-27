$ErrorActionPreference = "Stop"

Set-Location (Split-Path $PSScriptRoot -Parent | Split-Path -Parent)

$root = (Get-Location).Path
$out = Join-Path $root "build-windows-minimal"
$dist = Join-Path $root "dist"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

$webDist = Join-Path $root "src\DairyOS.Web\dist"
$alembic = Join-Path $root "alembic.ini"
$migrations = Join-Path $root "db_migrations"

if (-not (Test-Path $venvPython)) { throw "Virtualenv Python missing: $venvPython" }
if (-not (Test-Path $webDist)) { throw "Frontend dist missing: $webDist" }
if (-not (Test-Path $alembic)) { throw "alembic.ini missing: $alembic" }
if (-not (Test-Path $migrations)) { throw "db_migrations missing: $migrations" }

if (Test-Path $out) {
    Remove-Item $out -Recurse -Force
}

if (Test-Path $dist) {
    Remove-Item (Join-Path $dist "DairyOS-Server") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $dist "DairyOS") -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Path $out -Force | Out-Null

$commonArgs = @(
    "--clean",
    "--noconfirm",
    "--onedir",
    "--collect-submodules", "dairyos",
    "--collect-submodules", "alembic",
    "--collect-submodules", "sqlalchemy",
    "--add-data", "$alembic;.",
    "--add-data", "$migrations;db_migrations",
    "--add-data", "$webDist;src/DairyOS.Web/dist"
)

Write-Host "=== Building DairyOS-Server ==="

& $venvPython -m PyInstaller `
    @commonArgs `
    "--name", "DairyOS-Server" `
    "--console" `
    "$root\src\dairyos\server.py"

if ($LASTEXITCODE -ne 0) {
    throw "DairyOS-Server PyInstaller build failed."
}

Write-Host "=== Building DairyOS Desktop ==="

& $venvPython -m PyInstaller `
    @commonArgs `
    "--name", "DairyOS" `
    "--windowed" `
    "$root\src\dairyos\windows\supervisor.py"

if ($LASTEXITCODE -ne 0) {
    throw "DairyOS PyInstaller build failed."
}

$serverDir = Join-Path $dist "DairyOS-Server"
$dairyDir = Join-Path $dist "DairyOS"

if (-not (Test-Path (Join-Path $serverDir "DairyOS-Server.exe"))) {
    throw "DairyOS-Server bundle was not produced."
}

if (-not (Test-Path (Join-Path $dairyDir "DairyOS.exe"))) {
    throw "DairyOS bundle was not produced."
}

# Copy COMPLETE PyInstaller onedir bundles.
Copy-Item $serverDir (Join-Path $out "DairyOS-Server") -Recurse
Copy-Item $dairyDir (Join-Path $out "DairyOS") -Recurse

Write-Host "=== Copying migration/runtime data ==="

Copy-Item $alembic (Join-Path $out "DairyOS-Server\alembic.ini")
Copy-Item $migrations (Join-Path $out "DairyOS-Server\db_migrations") -Recurse
Copy-Item $webDist (Join-Path $out "DairyOS-Server\src\DairyOS.Web\dist") -Recurse

# Desktop supervisor needs the same packaged migration assets.
Copy-Item $alembic (Join-Path $out "DairyOS\alembic.ini")
Copy-Item $migrations (Join-Path $out "DairyOS\db_migrations") -Recurse
Copy-Item $webDist (Join-Path $out "DairyOS\src\DairyOS.Web\dist") -Recurse

Write-Host ""
Write-Host "=== FROZEN BUILD COMPLETE ==="

Get-ChildItem $out -Directory |
    Select-Object Name, FullName

Write-Host ""
Write-Host "Server executable:"
Get-Item (Join-Path $out "DairyOS-Server\DairyOS-Server.exe") |
    Select-Object FullName,Length

Write-Host ""
Write-Host "Desktop executable:"
Get-Item (Join-Path $out "DairyOS\DairyOS.exe") |
    Select-Object FullName,Length