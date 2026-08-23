[CmdletBinding()]
param(
    [string]$Configuration = "Release",
    [string]$PostgresVersion = "18.6"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
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

Write-Host "`n=== BACKEND TEST / PACKAGE ===" -ForegroundColor Cyan
Set-Location $RepoRoot
python -m pip install --upgrade pip
python -m pip install . pyinstaller pytest
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Backend regression failed." }

python -m PyInstaller `
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

Write-Host "`n=== POSTGRESQL WINDOWS BINARIES ===" -ForegroundColor Cyan
$zipName = "postgresql-$PostgresVersion-1-windows-x64-binaries.zip"
$tempZip = Join-Path $env:TEMP $zipName
$downloadPage = Invoke-WebRequest -Uri "https://www.enterprisedb.com/download-postgresql-binaries" -UseBasicParsing
$pattern = 'href=["'']([^"'']*' + [regex]::Escape($zipName) + ')["'']'
$match = [regex]::Match($downloadPage.Content, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
if (-not $match.Success) {
    throw "Could not locate the PostgreSQL binary archive for $zipName on EDB's current download page."
}
$href = $match.Groups[1].Value
if ($href -notmatch '^https?://') {
    $href = "https://www.enterprisedb.com$href"
}
Write-Host "Downloading $href"
Invoke-WebRequest -Uri $href -OutFile $tempZip -UseBasicParsing

$tempExtract = Join-Path $env:TEMP "dairyos-pg-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $tempExtract -Force | Out-Null
Expand-Archive -LiteralPath $tempZip -DestinationPath $tempExtract -Force

$pgBin = Get-ChildItem -Path $tempExtract -Recurse -Filter "pg_ctl.exe" -File | Select-Object -First 1
if (-not $pgBin) { throw "Downloaded PostgreSQL archive does not contain pg_ctl.exe." }
$pgRoot = $pgBin.Directory.Parent
Copy-Item -LiteralPath (Join-Path $pgRoot "*") -Destination $PostgresRoot -Recurse -Force

Remove-Item -LiteralPath $tempZip -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n=== RECOVERY TOOLS ===" -ForegroundColor Cyan
Copy-Item -LiteralPath (Join-Path $SourceRecoveryRoot "DairyOS-Data-Backup.ps1") -Destination $RecoveryRoot -Force
Copy-Item -LiteralPath (Join-Path $SourceRecoveryRoot "DairyOS-Data-Restore.ps1") -Destination $RecoveryRoot -Force
Copy-Item -LiteralPath (Join-Path $SourceRecoveryRoot "README.txt") -Destination $RecoveryRoot -Force

Write-Host "`n=== ELECTRON DESKTOP INSTALLER ===" -ForegroundColor Cyan
Set-Location $AppRoot
npm ci --no-audit --fund=false
if ($LASTEXITCODE -ne 0) { throw "Windows desktop packaging dependencies failed to install." }
npx electron-builder --win nsis
if ($LASTEXITCODE -ne 0) { throw "Electron/NSIS installer build failed." }

Write-Host "`nInstaller artifacts:" -ForegroundColor Green
Get-ChildItem $DistRoot -File | Select-Object Name,Length,LastWriteTime
