[CmdletBinding()]
param(
    [string]$DistRoot = "dist\\DairyOS-Release",
    [string]$BuildRoot = "build\\DairyOS-Release"
)

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo

$webRoot = Join-Path $repo "src\\DairyOS.Web"
$webDist = Join-Path $webRoot "dist"
$webIndex = Join-Path $webDist "index.html"
$spec = Join-Path $repo "DairyOS.spec"
$runtimeSource = Join-Path $repo "runtime\\PostgreSQL"
$versionSource = Join-Path $repo "runtime\\postgresql.version"

if (-not (Test-Path $spec -PathType Leaf)) { throw "DairyOS PyInstaller specification is missing: $spec" }
if (-not (Test-Path $runtimeSource -PathType Container)) { throw "Bundled PostgreSQL runtime is missing: $runtimeSource" }
if (-not (Test-Path $versionSource -PathType Leaf)) { throw "Bundled PostgreSQL version marker is missing: $versionSource" }

Write-Host "=== BUILD FRONTEND ===" -ForegroundColor Cyan
npm --prefix $webRoot run build
if ($LASTEXITCODE -ne 0) { throw "DairyOS frontend production build failed." }
if (-not (Test-Path $webIndex -PathType Leaf)) { throw "Frontend build completed without dist/index.html." }

Write-Host "=== BUILD FROZEN DESKTOP ===" -ForegroundColor Cyan
python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Unable to install PyInstaller." }

Remove-Item $DistRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $BuildRoot -Recurse -Force -ErrorAction SilentlyContinue

$pyinstallerArgs = @("--noconfirm", "--clean", "--distpath", $DistRoot, "--workpath", $BuildRoot, $spec)
python -m PyInstaller @pyinstallerArgs
if ($LASTEXITCODE -ne 0) { throw "DairyOS desktop PyInstaller build failed." }

$bundle = Join-Path $DistRoot "DairyOS"
$exe = Join-Path $bundle "DairyOS.exe"
$backupExe = Join-Path $bundle "DairyOSBackup.exe"
if (-not (Test-Path $exe -PathType Leaf)) { throw "Frozen DairyOS.exe was not produced: $exe" }
if (-not (Test-Path $backupExe -PathType Leaf)) { throw "Frozen DairyOSBackup.exe was not produced: $backupExe" }

Write-Host "=== COPY PRIVATE POSTGRESQL RUNTIME ===" -ForegroundColor Cyan
$runtimeTarget = Join-Path $bundle "runtime\\PostgreSQL"
New-Item -ItemType Directory -Force -Path $runtimeTarget | Out-Null
$excludeDirs = @((Join-Path $runtimeSource "pgAdmin 4"), (Join-Path $runtimeSource "StackBuilder"), (Join-Path $runtimeSource "lib\\pgxs\\src\\test"))
$robocopyArgs = @($runtimeSource, $runtimeTarget, "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/XD") + $excludeDirs
& robocopy @robocopyArgs | Out-Null
if ($LASTEXITCODE -gt 7) { throw "PostgreSQL runtime copy failed with exit code $LASTEXITCODE." }

$runtimeDir = Join-Path $bundle "runtime"
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
Copy-Item $versionSource (Join-Path $runtimeDir "postgresql.version") -Force

$required = @(
    $exe,
    $backupExe,
    (Join-Path $runtimeTarget "bin\\postgres.exe"),
    (Join-Path $runtimeTarget "bin\\pg_ctl.exe"),
    (Join-Path $runtimeTarget "bin\\initdb.exe"),
    (Join-Path $runtimeTarget "bin\\createdb.exe"),
    (Join-Path $runtimeTarget "bin\\psql.exe"),
    (Join-Path $runtimeDir "postgresql.version"),
    (Join-Path $bundle "_internal\\src\\DairyOS.Web\\dist\\index.html"),
    (Join-Path $bundle "_internal\\alembic.ini")
)
foreach ($path in $required) {
    if (-not (Test-Path $path -PathType Leaf)) { throw "Desktop release validation failed; required file is missing: $path" }
}

Write-Host "=== VERIFY FROZEN ENTRY POINT ===" -ForegroundColor Cyan
$process = Start-Process -FilePath $exe -ArgumentList "--help" -PassThru -Wait
if ($process.ExitCode -ne 0) { throw "Frozen DairyOS.exe --help exited with code $($process.ExitCode)." }

Write-Host ""
Write-Host "DAIRYOS DESKTOP RELEASE BUILD: PASS" -ForegroundColor Green
Write-Host "Bundle: $bundle"
Get-FileHash $exe -Algorithm SHA256
