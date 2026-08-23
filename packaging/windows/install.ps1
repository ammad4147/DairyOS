param(
    [Parameter(Mandatory = $true)][string]$AppDir,
    [Parameter(Mandatory = $true)][string]$DataDir,
    [Parameter(Mandatory = $true)][string]$PostgresInstaller
)

$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'logs') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'backups') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir 'recovery') | Out-Null

$pgDir = Join-Path $AppDir 'PostgreSQL'
$pgData = Join-Path $DataDir 'postgresql-data'
$envFile = Join-Path $DataDir 'dairyos.env'

if (-not (Test-Path (Join-Path $pgDir 'bin\pg_ctl.exe'))) {
    New-Item -ItemType Directory -Force -Path $pgDir | Out-Null
    $args = @('--mode', 'unattended', '--unattendedmodeui', 'none', '--extract-only', '1', '--prefix', $pgDir)
    $p = Start-Process -FilePath $PostgresInstaller -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
    if ($p.ExitCode -ne 0) { throw "PostgreSQL binary extraction failed with exit code $($p.ExitCode)." }
}

$pgBin = Join-Path $pgDir 'bin'
$initdb = Join-Path $pgBin 'initdb.exe'
$pgCtl = Join-Path $pgBin 'pg_ctl.exe'
$createdb = Join-Path $pgBin 'createdb.exe'
$psql = Join-Path $pgBin 'psql.exe'

if (-not (Test-Path $initdb)) { throw 'PostgreSQL initdb.exe is missing after extraction.' }

if (-not (Test-Path (Join-Path $pgData 'PG_VERSION'))) {
    New-Item -ItemType Directory -Force -Path $pgData | Out-Null
    $password = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
    $passwordFile = Join-Path $DataDir 'recovery\db-password.tmp'
    Set-Content -Path $passwordFile -Value $password -Encoding ascii -NoNewline
    try {
        $p = Start-Process -FilePath $initdb -ArgumentList @('-D', $pgData, '-U', 'postgres', '--pwfile', $passwordFile, '--auth', 'scram-sha-256', '--encoding', 'UTF8') -Wait -PassThru -WindowStyle Hidden
        if ($p.ExitCode -ne 0) { throw "PostgreSQL database initialization failed with exit code $($p.ExitCode)." }
    }
    finally {
        Remove-Item $passwordFile -Force -ErrorAction SilentlyContinue
    }

    @(
        'DAIRYOS_ENV=production'
        'DAIRYOS_DB_HOST=127.0.0.1'
        'DAIRYOS_DB_PORT=5432'
        'DAIRYOS_DB_NAME=dairyos'
        'DAIRYOS_DB_USER=postgres'
        "DAIRYOS_DB_PASSWORD=$password"
        "DAIRYOS_PG_BIN=$pgBin"
        "DAIRYOS_PG_DATA=$pgData"
        'DAIRYOS_APP_PORT=8000'
    ) | Set-Content -Path $envFile -Encoding utf8
}
else {
    if (-not (Test-Path $envFile)) { throw 'Existing DairyOS database was found but its configuration file is missing. Installation stopped to protect the farm data.' }
}

$env = Get-Content $envFile | Where-Object { $_ -match '^(DAIRYOS_[^=]+)=(.*)$' } | ForEach-Object {
    [pscustomobject]@{ Key = $Matches[1]; Value = $Matches[2] }
}
$cfg = @{}
foreach ($item in $env) { $cfg[$item.Key] = $item.Value }

$pgEnv = @{} + [System.Environment]::GetEnvironmentVariables('Process')
$pgEnv['PGPASSWORD'] = $cfg['DAIRYOS_DB_PASSWORD']

$status = Start-Process -FilePath $pgCtl -ArgumentList @('status', '-D', $pgData) -Wait -PassThru -WindowStyle Hidden
if ($status.ExitCode -ne 0) {
    $log = Join-Path $DataDir 'logs\postgresql.log'
    $p = Start-Process -FilePath $pgCtl -ArgumentList @('start', '-D', $pgData, '-l', $log, '-w', '-o', '-p 5432') -Wait -PassThru -WindowStyle Hidden
    if ($p.ExitCode -ne 0) { throw 'Unable to start the DairyOS PostgreSQL database.' }
}

$probe = & $psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='dairyos'" 2>$null
if ($probe.Trim() -ne '1') {
    & $createdb -h 127.0.0.1 -p 5432 -U postgres dairyos
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create the DairyOS database.' }
}

$recoveryScript = @'
param(
    [Parameter(Mandatory = $true)][string]$AppDir,
    [Parameter(Mandatory = $true)][string]$DataDir
)
$ErrorActionPreference = 'Stop'
$envFile = Join-Path $DataDir 'dairyos.env'
$cfg = @{}
foreach ($line in Get-Content $envFile) {
    if ($line -match '^(DAIRYOS_[^=]+)=(.*)$') { $cfg[$Matches[1]] = $Matches[2] }
}
$pgBin = $cfg['DAIRYOS_PG_BIN']
$pgData = $cfg['DAIRYOS_PG_DATA']
$pgDump = Join-Path $pgBin 'pg_dump.exe'
$pgCtl = Join-Path $pgBin 'pg_ctl.exe'
$env:PGPASSWORD = $cfg['DAIRYOS_DB_PASSWORD']
$backup = Join-Path $DataDir ('backups\pre-uninstall-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.sql')
& $pgDump -h 127.0.0.1 -p 5432 -U postgres -d dairyos --format=plain --file=$backup
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $backup) -or (Get-Item $backup).Length -lt 100) {
    throw 'DairyOS final farm-data backup failed. Uninstall aborted.'
}
Get-Process -Name 'DairyOS' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
& $pgCtl stop -D $pgData -m fast -w 2>$null
exit 0
'@
Set-Content -Path (Join-Path $DataDir 'recovery\backup-before-uninstall.ps1') -Value $recoveryScript -Encoding utf8

Write-Host 'DairyOS Windows installation initialized successfully.'
