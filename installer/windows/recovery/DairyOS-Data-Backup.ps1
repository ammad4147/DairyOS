[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallRoot,
    [string]$Reason = "scheduled"
)

$ErrorActionPreference = "Stop"
$DataRoot = Join-Path $env:ProgramData "DairyOS"
$ConfigPath = Join-Path $DataRoot "desktop-config.json"
$BackupRoot = Join-Path $DataRoot "backups"

if (-not (Test-Path -LiteralPath $ConfigPath)) { throw "DairyOS configuration not found: $ConfigPath" }
$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$pgBin = Join-Path $InstallRoot "resources\postgresql\bin"
$pgCtl = Join-Path $pgBin "pg_ctl.exe"
$pgDump = Join-Path $pgBin "pg_dump.exe"
$pgIsReady = Join-Path $pgBin "pg_isready.exe"
$dbRoot = Join-Path $DataRoot "postgresql-data"

foreach ($required in @($pgCtl, $pgDump, $pgIsReady)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required PostgreSQL recovery file is missing: $required" }
}

New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
$wasRunning = (& $pgCtl status -D $dbRoot 2>$null) -eq $null
$startedHere = $false
if ($LASTEXITCODE -ne 0) {
    & $pgCtl start -D $dbRoot -l (Join-Path $DataRoot "postgresql.log") -w -t 30 -o "-p $($config.database_port) -h 127.0.0.1" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not start PostgreSQL for the data-protection backup." }
    $startedHere = $true
}

try {
    $env:PGPASSWORD = [string]$config.database_password
    & $pgIsReady -h 127.0.0.1 -p $config.database_port -U $config.database_user -d $config.database_name 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "DairyOS database is not ready for backup." }

    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmssZ")
    $safeReason = ($Reason -replace '[^A-Za-z0-9_-]', '_')
    $backupFile = Join-Path $BackupRoot "$stamp-$safeReason.dump"

    & $pgDump -h 127.0.0.1 -p $config.database_port -U $config.database_user -d $config.database_name -F c --no-owner --no-acl -f $backupFile
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $backupFile)) {
        throw "pg_dump failed; no trustworthy backup was produced."
    }

    Get-ChildItem -LiteralPath $BackupRoot -Filter "*.dump" -File |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -Skip 30 |
        Remove-Item -Force

    $settingsPath = Join-Path $DataRoot "backup-settings.json"
    if (Test-Path -LiteralPath $settingsPath) {
        $settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
        if ($settings.secondary_backup_dir) {
            $secondary = [Environment]::ExpandEnvironmentVariables([string]$settings.secondary_backup_dir)
            New-Item -ItemType Directory -Force -Path $secondary | Out-Null
            Copy-Item -LiteralPath $backupFile -Destination (Join-Path $secondary (Split-Path $backupFile -Leaf)) -Force
        }
    }

    Write-Host "DairyOS backup created: $backupFile"
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    if ($startedHere) {
        & $pgCtl stop -D $dbRoot -m fast -w | Out-Null
    }
}
