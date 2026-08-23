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
$downloadPage = Invoke-WebRequest -Uri "https://www.enterprisedb.com/download-postgresql-binaries?lang=en" -UseBasicParsing
$html = [string]$downloadPage.Content

$downloadUri = $null
$hrefMatches = [regex]::Matches(
    $html,
    'href=["'']([^"'']+)["'']',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
)

foreach ($match in $hrefMatches) {
    $candidate = $match.Groups[1].Value
    if ($candidate -match '(?i)getfile\.jsp\?fileid=\d+' -or $candidate -match '(?i)postgresql-[0-9.]+-\d+-windows-x64-binaries\.zip') {
        if ($candidate -notmatch '^https?://') {
            if ($candidate.StartsWith('//')) {
                $candidate = "https:$candidate"
            } else {
                $candidate = [System.Uri]::new([System.Uri]"https://www.enterprisedb.com", $candidate).AbsoluteUri
            }
        }
        $downloadUri = $candidate
        break
    }
}

if (-not $downloadUri) {
    # EDB's page has historically exposed the Windows-binary download through
    # a getfile.jsp URL adjacent to the Windows x86-64 entry. Keep a second
    # pass that uses the surrounding HTML when the href itself is opaque.
    $htmlLines = $html -split "`r?`n"
    for ($i = 0; $i -lt $htmlLines.Count -and -not $downloadUri; $i++) {
        if ($htmlLines[$i] -match '(?i)Windows\s*x86-64') {
            for ($j = 1; $j -le 8 -and ($i - $j) -ge 0; $j++) {
                $previous = $htmlLines[$i - $j]
                $urlMatch = [regex]::Match(
                    $previous,
                    '(?i)https?://sbp\.enterprisedb\.com/getfile\.jsp\?fileid=\d+|https?://www\.enterprisedb\.com/getfile\.jsp\?fileid=\d+',
                )
                if ($urlMatch.Success) {
                    $downloadUri = $urlMatch.Value
                    break
                }
            }
        }
    }
}

if (-not $downloadUri) {
    throw "Could not determine a PostgreSQL Windows binary download URL from EDB's current download page."
}

Write-Host "Downloading PostgreSQL binaries from: $downloadUri"
$tempZip = Join-Path $env:TEMP "dairyos-postgresql-$PostgresVersion-$([guid]::NewGuid().ToString('N')).zip"
Invoke-WebRequest -Uri $downloadUri -OutFile $tempZip -UseBasicParsing

$tempExtract = Join-Path $env:TEMP "dairyos-pg-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $tempExtract -Force | Out-Null
Expand-Archive -LiteralPath $tempZip -DestinationPath $tempExtract -Force

$pgBin = Get-ChildItem -Path $tempExtract -Recurse -Filter "pg_ctl.exe" -File | Select-Object -First 1
if (-not $pgBin) { throw "Downloaded PostgreSQL archive does not contain pg_ctl.exe." }
$pgRoot = $pgBin.Directory.Parent
Copy-Item -LiteralPath (Join-Path $pgRoot "*") -Destination $PostgresRoot -Recurse -Force

Remove-Item -LiteralPath $tempZip -Force -ErrorAction SilentlyContinue
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
    python -m pip install --upgrade pip
    python -m pip install . pyinstaller pytest httpx2
    python -m pytest -q
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
