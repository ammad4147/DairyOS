[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Local test runner only. This script never changes the DairyOS production
# runtime, never touches the user's farm-data root, and never modifies the
# machine PostgreSQL service. It provisions an isolated temporary PostgreSQL
# cluster on a dynamically selected loopback port.

$repoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $repoRoot

function Select-FreePort {
    # Ask Windows to allocate an actually bindable ephemeral loopback port.
    # Holding the listener until the port number has been obtained avoids
    # relying on potentially stale TCP-listener enumeration.
    $probe = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )

    try {
        $probe.Start()
        return ([System.Net.IPEndPoint]$probe.LocalEndpoint).Port
    }
    finally {
        $probe.Stop()
    }
}

function Resolve-PostgreSqlBinary {
    param([Parameter(Mandatory)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @()

    foreach ($root in @(
        "$env:ProgramFiles\PostgreSQL",
        "${env:ProgramFiles(x86)}\PostgreSQL"
    )) {
        if (Test-Path $root) {
            $candidates += Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending |
                ForEach-Object {
                    Join-Path $_.FullName "bin\$Name.exe"
                }
        }
    }

    $found = $candidates |
        Where-Object { Test-Path $_ -PathType Leaf } |
        Select-Object -First 1

    if ($found) {
        return $found
    }

    return $null
}

function Wait-ForPostgres {
    param(
        [Parameter(Mandatory)][string]$PgIsReady,
        [Parameter(Mandatory)][int]$Port,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    do {
        & $PgIsReady -h 127.0.0.1 -p $Port -d dairyos_test -U postgres *> $null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    throw "Temporary PostgreSQL did not become ready on port $Port."
}

$pgCtl = Resolve-PostgreSqlBinary -Name "pg_ctl"
$initDb = Resolve-PostgreSqlBinary -Name "initdb"
$createdb = Resolve-PostgreSqlBinary -Name "createdb"
$pgIsReady = Resolve-PostgreSqlBinary -Name "pg_isready"

foreach ($item in @(
    @{ Name = "pg_ctl"; Path = $pgCtl },
    @{ Name = "initdb"; Path = $initDb },
    @{ Name = "createdb"; Path = $createdb },
    @{ Name = "pg_isready"; Path = $pgIsReady }
)) {
    if (-not $item.Path) {
        throw "Required PostgreSQL test tool '$($item.Name)' was not found. Install PostgreSQL client/server tools or use the CI PostgreSQL service."
    }
}

$port = Select-FreePort
$testRoot = Join-Path $env:TEMP ("DairyOS-TestPostgres-" + [guid]::NewGuid().ToString("N"))
$dataDir = Join-Path $testRoot "data"
$logFile = Join-Path $testRoot "postgres.log"

New-Item -ItemType Directory -Path $testRoot -Force | Out-Null

$previousEnvironment = @{}
foreach ($name in @(
    "DAIRYOS_ENV",
    "DAIRYOS_DATABASE_URL",
    "DAIRYOS_DB_HOST",
    "DAIRYOS_DB_PORT",
    "DAIRYOS_DB_NAME",
    "DAIRYOS_DB_USER",
    "DAIRYOS_DB_PASSWORD",
    "DAIRYOS_DATA_DIR",
    "DAIRYOS_INSTALL_ROOT",
    "DAIRYOS_INSTALLATION_STATE",
    "DAIRYOS_RUNTIME_LOG_DIR",
    "DAIRYOS_BACKEND_LOG",
    "DAIRYOS_BACKUP_MIRROR_ROOT",
    "DAIRYOS_RECOVERY_ROOT",
    "DAIRYOS_BACKUP_SEARCH_ROOTS",
    "DAIRYOS_PREFLIGHT_REPORT",
    "DAIRYOS_PRIVATE_POSTGRES_DATA"
)) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

$clusterInitialized = $false

try {
    Write-Host "============================================================"
    Write-Host " DAIRYOS ISOLATED LOCAL TEST RUNNER"
    Write-Host "============================================================"
    Write-Host "Repository : $repoRoot"
    Write-Host "Test port  : $port"
    Write-Host "Test root  : $testRoot"

    & $initDb `
        --pgdata="$dataDir" `
        --username=postgres `
        --auth=trust `
        --no-locale `
        --encoding=UTF8 *> (Join-Path $testRoot "initdb.log")

    if ($LASTEXITCODE -ne 0) {
        throw "initdb failed with exit code $LASTEXITCODE."
    }

    # Once initdb succeeds, this invocation owns the exact disposable cluster.
    # Cleanup must therefore attempt a targeted pg_ctl stop even when
    # pg_ctl start subsequently returns a non-zero exit code after a partial
    # server start.
    $clusterInitialized = $true

    & $pgCtl `
        -D "$dataDir" `
        -l "$logFile" `
        -o "-h 127.0.0.1 -p $port" `
        start `
        -w

    if ($LASTEXITCODE -ne 0) {
        throw "pg_ctl start failed with exit code $LASTEXITCODE."
    }

    # pg_ctl returning is not sufficient evidence that the Windows server is
    # already accepting client connections. Prove readiness before createdb.
    Wait-ForPostgres -PgIsReady $pgIsReady -Port $port

    & $createdb -h 127.0.0.1 -p $port -U postgres dairyos_test
    if ($LASTEXITCODE -ne 0) {
        throw "createdb failed with exit code $LASTEXITCODE."
    }

    # The application reads these values during module import, so they must be
    # set before pytest imports dairyos.app through tests/conftest.py. Every
    # mutable DairyOS filesystem path is redirected into this disposable test
    # root. In particular, never inherit an installed production
    # DAIRYOS_DATA_DIR or DAIRYOS_INSTALL_ROOT into a local test process.
    $env:DAIRYOS_ENV = "development"
    $env:DAIRYOS_DATA_DIR = Join-Path $testRoot "DairyOS-data"
    $env:DAIRYOS_INSTALL_ROOT = Join-Path $testRoot "DairyOS-install"
    $env:DAIRYOS_INSTALLATION_STATE = Join-Path $testRoot "installation_state.json"
    $env:DAIRYOS_RUNTIME_LOG_DIR = Join-Path $testRoot "logs"
    $env:DAIRYOS_BACKEND_LOG = Join-Path $testRoot "logs\backend.log"
    $env:DAIRYOS_BACKUP_MIRROR_ROOT = Join-Path $testRoot "backup-mirror"
    $env:DAIRYOS_RECOVERY_ROOT = Join-Path $testRoot "recovery"
    $env:DAIRYOS_BACKUP_SEARCH_ROOTS = Join-Path $testRoot "backup-search"
    $env:DAIRYOS_PREFLIGHT_REPORT = Join-Path $testRoot "preflight.json"
    $env:DAIRYOS_PRIVATE_POSTGRES_DATA = Join-Path $testRoot "private-postgres"
    $env:DAIRYOS_DB_HOST = "127.0.0.1"
    $env:DAIRYOS_DB_PORT = "$port"
    $env:DAIRYOS_DB_NAME = "dairyos_test"
    $env:DAIRYOS_DB_USER = "postgres"
    $env:DAIRYOS_DB_PASSWORD = ""
    $env:DAIRYOS_DATABASE_URL = "postgresql+psycopg://postgres@127.0.0.1:$port/dairyos_test"

    $args = @("-q") + $PytestArgs

    Write-Host ""
    Write-Host "=== TEST DATABASE ==="
    Write-Host $env:DAIRYOS_DATABASE_URL

    Write-Host ""
    Write-Host "=== PYTEST ==="

    & python -m pytest @args
    $pytestExit = $LASTEXITCODE

    if ($pytestExit -ne 0) {
        throw "pytest failed with exit code $pytestExit."
    }

    Write-Host ""
    Write-Host "PASS: ISOLATED LOCAL TEST RUN COMPLETED SUCCESSFULLY" -ForegroundColor Green
}
finally {
    if ($clusterInitialized -and (Test-Path $dataDir -PathType Container)) {
        # Stop only the disposable cluster created by this invocation.
        # Never terminate PostgreSQL by process name or PID.
        #
        # postmaster.pid is the positive evidence that this exact cluster
        # reached a state in which pg_ctl stop is meaningful. Cleanup is
        # deliberately best-effort so it cannot mask the original test or
        # startup failure.
        $postmasterPid = Join-Path $dataDir "postmaster.pid"

        if (Test-Path $postmasterPid -PathType Leaf) {
            try {
                & $pgCtl -D "$dataDir" stop -m fast -w 2>&1 | Out-Null
            }
            catch {
                Write-Warning "Disposable PostgreSQL cleanup reported: $($_.Exception.Message)"
            }
        }
    }

    foreach ($name in $previousEnvironment.Keys) {
        $value = $previousEnvironment[$name]
        if ($null -eq $value) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item "Env:$name" $value
        }
    }

    if (Test-Path $testRoot) {
        Remove-Item $testRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
