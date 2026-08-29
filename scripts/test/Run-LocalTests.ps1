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

function Test-TcpPort {
    param([int]$Port)

    try {
        $listener = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
        return ($listener | Where-Object { $_.Port -eq $Port }).Count -gt 0
    }
    catch {
        return $false
    }
}

function Select-FreePort {
    foreach ($port in 55432..55462) {
        if (-not (Test-TcpPort -Port $port)) {
            return $port
        }
    }

    throw "No free local test PostgreSQL port was found in 55432-55462."
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
    "DAIRYOS_DB_PASSWORD"
)) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

$started = $false

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

    & $pgCtl `
        -D "$dataDir" `
        -l "$logFile" `
        -o "-h 127.0.0.1 -p $port" `
        start `
        -w

    if ($LASTEXITCODE -ne 0) {
        throw "pg_ctl start failed with exit code $LASTEXITCODE."
    }

    $started = $true

    & $createdb -h 127.0.0.1 -p $port -U postgres dairyos_test
    if ($LASTEXITCODE -ne 0) {
        throw "createdb failed with exit code $LASTEXITCODE."
    }

    Wait-ForPostgres -PgIsReady $pgIsReady -Port $port

    # The application reads these values during module import, so they must be
    # set before pytest imports dairyos.app through tests/conftest.py.
    $env:DAIRYOS_ENV = "development"
    $env:DAIRYOS_DB_HOST = "127.0.0.1"
    $env:DAIRYOS_DB_PORT = "$port"
    $env:DAIRYOS_DB_NAME = "dairyos_test"
    $env:DAIRYOS_DB_USER = "postgres"
    $env:DAIRYOS_DB_PASSWORD = ""
    Remove-Item Env:DAIRYOS_DATABASE_URL -ErrorAction SilentlyContinue

    $args = @("-q") + $PytestArgs

    Write-Host ""
    Write-Host "=== TEST DATABASE ==="
    Write-Host "postgresql+psycopg://postgres@127.0.0.1:$port/dairyos_test"

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
    if ($started) {
        & $pgCtl -D "$dataDir" stop -m fast -w *> $null
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
