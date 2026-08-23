[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallRoot,
    [Parameter(Mandatory = $true)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"
$DataRoot = Join-Path $env:ProgramData "DairyOS"
$ConfigPath = Join-Path $DataRoot "desktop-config.json"

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

if (-not (Test-Path -LiteralPath $ConfigPath)) { Fail "Missing DairyOS configuration: $ConfigPath" }
if (-not (Test-Path -LiteralPath $BackupFile)) { Fail "Backup file not found: $BackupFile" }

$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$pgBin = Join-Path $InstallRoot "resources\postgresql\bin"
$pgCtl = Join-Path $pgBin "pg_ctl.exe"
$pgRestore = Join-Path $pgBin "pg_restore.exe"
$psql = Join-Path $pgBin "psql.exe"
$dbRoot = Join-Path $DataRoot "postgresql-data"

foreach ($required in @($pgCtl, $pgRestore, $psql)) {
    if (-not (Test-Path -LiteralPath $required)) { Fail "Missing PostgreSQL recovery tool: $required" }
}

Write-Warning "RESTORE REPLACES THE CURRENT DAIRYOS DATABASE."
Write-Warning "A copy of the current database should exist before continuing."
$confirm = Read-Host 'Type RESTORE-DATABASE to continue'
if ($confirm -ne 'RESTORE-DATABASE') { Fail 'Restore cancelled.' }

$wasRunning = $false
$status = & $pgCtl status -D $dbRoot 2>$null
if ($LASTEXITCODE -eq 0) { $wasRunning = $true }
else {
    & $pgCtl start -D $dbRoot -l (Join-Path $DataRoot "postgresql.log") -w -t 30 -o "-p $($config.database_port) -h 127.0.0.1" | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail 'Could not start PostgreSQL for recovery.' }
}

try {
    $env:PGPASSWORD = [string]$config.database_password

    # Drop and recreate the application database while preserving the cluster,
    # credentials, and the surrounding ProgramData directory.
    & $psql -h 127.0.0.1 -p $config.database_port -U $config.database_user -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$($config.database_name)' AND pid <> pg_backend_pid();" | Out-Null
    & $psql -h 127.0.0.1 -p $config.database_port -U $config.database_user -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"$($config.database_name)\";" | Out-Null
    & $psql -h 127.0.0.1 -p $config.database_port -U $config.database_user -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$($config.database_name)\" OWNER \"$($config.database_user)\";" | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail 'Could not recreate the DairyOS database.' }

    & $pgRestore -h 127.0.0.1 -p $config.database_port -U $config.database_user -d $config.database_name --clean --if-exists --no-owner --no-acl $BackupFile
    if ($LASTEXITCODE -ne 0) { Fail 'pg_restore failed. The original backup file remains untouched.' }

    Write-Host "DairyOS database restored from: $BackupFile"
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    if (-not $wasRunning) {
        & $pgCtl stop -D $dbRoot -m fast -w | Out-Null
    }
}
