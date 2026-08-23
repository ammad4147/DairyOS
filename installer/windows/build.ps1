[CmdletBinding()]
param(
    [string]$Configuration = "Release",
    [string]$PostgresVersion = "18.6"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.." )).Path
$WebRoot = Join-Path $RepoRoot "src\DairyOS.Web"
$InstallerRoot = Join-Path $RepoRoot "installer\windows"
$RuntimeRoot = Join-Path $InstallerRoot "runtime"
$AppRoot = Join-Path $InstallerRoot "app"
$SourceRecoveryRoot = Join-Path $InstallerRoot "recovery"
$DistRoot = Join-Path $RepoRoot "dist-installer"
$BackendRoot = Join-Path $RuntimeRoot "backend"
$FrontendRoot = Join-Path $RuntimeRoot "frontend"
$PostgresRoot = Join-Path $RuntimeRoot "postgresql"
$RecoveryRoot = Join-Path $RuntimeRoot "recovery"

function Reset-Directory([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

Write-Host "=== DAIRYOS WINDOWS INSTALLER BUILD ===" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"
Write-Host "PostgreSQL binary version: $PostgresVersion"

Reset-Directory $RuntimeRoot
Reset-Directory $DistRoot
New-Item -ItemType Directory -Path $BackendRoot,$FrontendRoot,$PostgresRoot,$RecoveryRoot -Force | Out-Null

Write-Host "`n=== POSTGRESQL WINDOWS BINARIES ===" -ForegroundColor Cyan
$downloadUri = "https://get.enterprisedb.com/postgresql/postgresql-18.6-1-windows-x64-binaries.zip"

Write-Host "Downloading PostgreSQL binaries from: $downloadUri"
$tempZip = Join-Path $env:TEMP "dairyos-postgresql-$PostgresVersion-win-x64.zip"
if (-not (Test-Path $tempZip) -or (Get-Item $tempZip).Length -lt 100000000) {
    curl.exe -L -f --retry 3 -o $tempZip $downloadUri
}

$tempExtract = Join-Path $env:TEMP "dairyos-pg-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $tempExtract -Force | Out-Null
Expand-Archive -LiteralPath $tempZip -DestinationPath $tempExtract -Force

$pgBin = Get-ChildItem -Path $tempExtract -Recurse -Filter "pg_ctl.exe" -File | Select-Object -First 1
if (-not $pgBin) { throw "Downloaded PostgreSQL archive does not contain pg_ctl.exe." }
$pgRoot = $pgBin.Directory.Parent
Get-ChildItem -LiteralPath $pgRoot -Force | Copy-Item -Destination $PostgresRoot -Recurse -Force

Remove-Item -LiteralPath $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

$ciPgData = $null
$ciPgRunning = $false
if ($env:CI -eq "true") {
    Write-Host "`n=== CI POSTGRESQL TEST INSTANCE ===" -ForegroundColor Cyan
    $ciPgData = Join-Path $env:TEMP "dairyos-ci-pg-$([guid]::NewGuid().ToString('N'))"
    $pgCtl = Join-Path $PostgresRoot "bin\pg_ctl.exe"
    $initDb = Join-Path $PostgresRoot "bin\initdb.exe"
    $createdb = Join-Path $PostgresRoot "bin\createdb.exe"
    if (-not (Test-Path $pgCtl)) { throw "pg_ctl.exe was not found in the bundled PostgreSQL runtime." }
    if (-not (Test-Path $initDb)) { throw "initdb.exe was not found in the bundled PostgreSQL runtime." }
    if (-not (Test-Path $createdb)) { throw "createdb.exe was not found in the bundled PostgreSQL runtime." }

    & $initDb -D $ciPgData -U postgres --auth=trust --encoding=UTF8 --locale=C
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL initdb failed." }

    & $pgCtl -D $ciPgData -w start -o "-h 127.0.0.1 -p 5432"
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL test server failed to start." }
    $ciPgRunning = $true

    & $createdb -h 127.0.0.1 -p 5432 -U postgres dairyos
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL test database creation failed." }

    $env:DAIRYOS_DB_HOST = "127.0.0.1"
    $env:DAIRYOS_DB_PORT = "5432"
    $env:DAIRYOS_DB_NAME = "dairyos"
    $env:DAIRYOS_DB_USER = "postgres"
    $env:DAIRYOS_DB_PASSWORD = "postgres"
    Write-Host "CI PostgreSQL test instance is ready on 127.0.0.1:5432."
}

try {
    Write-Host "`n=== BACKEND TEST / PACKAGE ===" -ForegroundColor Cyan
    Set-Location $RepoRoot
    $PythonExe = if (Test-Path "$RepoRoot\.venv\Scripts\python.exe") { "$RepoRoot\.venv\Scripts\python.exe" } else { "python" }
    & $PythonExe -m pip install -e . pytest pyinstaller
    if ($LASTEXITCODE -ne 0) { throw "Backend test/package dependencies failed to install." }
    & $PythonExe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Backend regression failed." }
} finally {
    if ($ciPgRunning) {
        $pgCtl = Join-Path $PostgresRoot "bin\pg_ctl.exe"
        & $pgCtl -D $ciPgData -m fast -w stop
        $ciPgRunning = $false
    }
    if ($ciPgData -and (Test-Path $ciPgData)) {
        Remove-Item -LiteralPath $ciPgData -Recurse -Force -ErrorAction SilentlyContinue
    }
}

& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name dairyos-server `
    --paths src `
    --collect-all dairyos `
    src\dairyos\server.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

Copy-Item -LiteralPath (Join-Path $RepoRoot "dist\dairyos-server.exe") -Destination $BackendRoot -Force

Write-Host "`n=== FRONTEND TEST / BUILD ===" -ForegroundColor Cyan
Set-Location $WebRoot
npm ci --no-audit --fund=false
if ($LASTEXITCODE -ne 0) { throw "Frontend npm ci failed." }
npm run typecheck
if ($LASTEXITCODE -ne 0) { throw "Frontend typecheck failed." }
npm run build
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
Copy-Item -LiteralPath (Join-Path $WebRoot "dist\*") -Destination $FrontendRoot -Recurse -Force

Write-Host "`n=== RECOVERY TOOLS ===" -ForegroundColor Cyan
Copy-Item -LiteralPath (Join-Path $SourceRecoveryRoot "DairyOS-Data-Backup.ps1") -Destination $RecoveryRoot -Force
Copy-Item -LiteralPath (Join-Path $SourceRecoveryRoot "DairyOS-Data-Restore.ps1") -Destination $RecoveryRoot -Force
Copy-Item -LiteralPath (Join-Path $SourceRecoveryRoot "README.txt") -Destination $RecoveryRoot -Force

Write-Host "`n=== ELECTRON DESKTOP INSTALLER ===" -ForegroundColor Cyan
Set-Location $AppRoot
Write-Host "Skipping redundant npm install as dependencies are already installed via npm ci."
if ($LASTEXITCODE -ne 0) { throw "Windows desktop packaging dependencies failed to install." }
npx electron-builder --win nsis
if ($LASTEXITCODE -ne 0) { throw "Electron/NSIS installer build failed." }

Write-Host "`nInstaller artifacts:" -ForegroundColor Green
Get-ChildItem $DistRoot -File | Select-Object Name,Length,LastWriteTime

$TargetDesktop = "C:\Users\ammad\Desktop\DairyOS_USB_Installer"
if (-not (Test-Path $TargetDesktop)) {
    New-Item -ItemType Directory -Path $TargetDesktop -Force | Out-Null
}

$SetupExe = Get-ChildItem $DistRoot -Filter "*.exe" -File | Select-Object -First 1
if ($SetupExe) {
    Copy-Item -Path $SetupExe.FullName -Destination (Join-Path $TargetDesktop $SetupExe.Name) -Force
    Write-Host "`n>>> Successfully placed $($SetupExe.Name) on Desktop: $TargetDesktop <<<" -ForegroundColor Green
}
