[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $env:ProgramFiles "DairyOS"),
    [string]$DataRoot = (Join-Path $env:ProgramData "DairyOS"),
    [string]$DatabaseUrl = $env:DAIRYOS_DATABASE_URL,
    [ValidateSet("KeepData", "PurgeData")]
    [string]$Mode = "KeepData",
    [switch]$NoAutomaticBackup
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$DataRoot = [IO.Path]::GetFullPath($DataRoot)
$VenvPython = Join-Path $InstallRoot ".venv\Scripts\python.exe"
$LifecyclePython = if (Test-Path $VenvPython) { $VenvPython } else { (Get-Command python -ErrorAction SilentlyContinue).Source }

if (-not $LifecyclePython) {
    throw "Python is required to execute the DairyOS lifecycle uninstaller."
}

$sourceRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$env:PYTHONPATH = Join-Path $sourceRoot "src"

$common = @(
    "-m", "dairyos.lifecycle.cli",
    "--install-root", $InstallRoot,
    "--data-root", $DataRoot
)
if ($DatabaseUrl) {
    $common += @("--database-url", $DatabaseUrl)
}

Write-Step "UNINSTALL PLAN"
Write-Host "Runtime : $InstallRoot"
Write-Host "Data    : $DataRoot"
Write-Host "Mode    : $Mode"

if ($Mode -eq "PurgeData") {
    Write-Host "`nWARNING: PurgeData permanently deletes the DairyOS data root after a pre-purge backup." -ForegroundColor Yellow
    Write-Host "This includes configuration, JSON operational state, logs and lifecycle metadata." -ForegroundColor Yellow
    Write-Host "A PostgreSQL backup is also created when a database URL is configured." -ForegroundColor Yellow

    $confirmation = Read-Host "Type PURGE DAIRYOS DATA to continue"
    if ($confirmation -cne "PURGE DAIRYOS DATA") {
        throw "Purge cancelled because the confirmation text did not match exactly."
    }

    $confirmationArgs = @("uninstall", "--mode", "purge-data", "--confirm", "PURGE DAIRYOS DATA")
    if ($NoAutomaticBackup) {
        $confirmationArgs += "--no-backup-before-purge"
    }

    Write-Step "PURGE DATA AND REMOVE RUNTIME"
    & $LifecyclePython @common @confirmationArgs
    if ($LASTEXITCODE -ne 0) {
        throw "DairyOS purge uninstall failed. Existing data was not intentionally purged by this script after a lifecycle error."
    }
}
else {
    Write-Step "REMOVE RUNTIME; KEEP DATA"
    & $LifecyclePython @common "uninstall" "--mode" "keep-data"
    if ($LASTEXITCODE -ne 0) {
        throw "DairyOS keep-data uninstall failed."
    }
}

Write-Host "`nDairyOS uninstall completed in mode: $Mode" -ForegroundColor Green
Write-Host ""
if ($Mode -eq "KeepData") {
    Write-Host "Farm data retained at: $DataRoot" -ForegroundColor Green
    Write-Host "A future DairyOS installation can be pointed back to this data directory."
}
