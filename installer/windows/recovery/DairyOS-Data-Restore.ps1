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
if (-not (Test-Path -LiteralPath $ConfigPath)) { throw "DairyOS configuration not found: $ConfigPath" }
if (-not (Test-Path -LiteralPath $BackupFile)) { throw "Backup file not found: $BackupFile" }

$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$pgBin = Join-Path $InstallRoot "resources\postgresql\bin"
$pgCtl = Join-Path $pgBin "pg_ctl.exe"
$pgRestore = Join-Path $pgBin "pg_restore.exe"
$psql = Join-Path $pgBin "psql.exe"
$dbRoot = Join-Path $DataRoot "postgresql-data"
foreach ($required in @($pgCtl, $pgRestore, $psql)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing PostgreSQL recovery file: $required" }
}

Write-Warning "RESTORE REPLACES THE CURRENT DAIRYOS DATABASE."
if ((Read-Host 'Type RESTORE-DATABASE to continue') -ne 'RESTORE-DATABASE') { throw "Restore cancelled." }

$startedHere = $false
& $pgCtl status -D $dbRoot 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    & $pgCtl start -D $dbRoot -l (Join-Path $DataRoot "postgresql.log") -w -t 30 -o "-p $($config.database_port) -h 127.0.0.1" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not start PostgreSQL for recovery." }
    $startedHere = $true
}

try {
    $env:PGPASSWORD = [string]$config.database_password
    & $psql -h 127.0.0.1 -p $config.database_port -U $config.database_user -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$($config.database_name)' AND pid <> pg_backend_pid();" | Out-Null
    & $psql -h 127.0.0.1 -p $config.database_port -U $config.database_user -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"$($config.database_name)\";" | Out-Null
    & $psql -h 127.0.0.1 -p $config.database_port -U $config.database_user -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$($config.database_name)\" OWNER \"$($config.database_user)\";" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not recreate the DairyOS database." }

    & $pgRestore -h 127.0.0.1 -p $config.database_port -U $config.database_user -d $config.database_name --clean --if-exists --no-owner --no-acl $BackupFile
    if ($LASTEXITCODE -ne 0) { throw "pg_restore failed. The backup file remains untouched." }
    Write-Host "DairyOS database restored successfully from $BackupFile"
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    if ($startedHere) { & $pgCtl stop -D $dbRoot -m fast -w | Out-Null }
}
