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

function Stop-DairyOSProcesses {
    Write-Step "STOP DAIRYOS APPLICATION"

    $processes = @(Get-Process -Name "DairyOS" -ErrorAction SilentlyContinue)

    foreach ($process in $processes) {
        Write-Host "Stopping DairyOS PID $($process.Id)..."

        try {
            if (-not $process.HasExited) {
                $null = $process.CloseMainWindow()
            }
        }
        catch {
            Write-Host "Graceful close unavailable for PID $($process.Id)." -ForegroundColor Yellow
        }
    }

    Start-Sleep -Seconds 2

    $remaining = @(Get-Process -Name "DairyOS" -ErrorAction SilentlyContinue)

    foreach ($process in $remaining) {
        Write-Host "Forcing DairyOS PID $($process.Id) to exit..." -ForegroundColor Yellow
        Stop-Process -Id $process.Id -Force -ErrorAction Stop
    }

    Start-Sleep -Seconds 1

    $remaining = @(Get-Process -Name "DairyOS" -ErrorAction SilentlyContinue)

    if ($remaining.Count -gt 0) {
        throw "DairyOS process(es) are still running and runtime removal cannot safely continue."
    }

    Write-Host "DairyOS processes stopped." -ForegroundColor Green
}

function Stop-DairyOSPostgres {
    Write-Step "STOP BUNDLED POSTGRESQL"

    $pgData = Join-Path $DataRoot "postgresql-data"
    $pgCtl = Join-Path $InstallRoot "resources\postgresql\bin\pg_ctl.exe"

    if (-not (Test-Path $pgData)) {
        Write-Host "PostgreSQL data directory does not exist; nothing to stop."
        return
    }

    if (-not (Test-Path $pgCtl)) {
        Write-Host "Bundled pg_ctl.exe not found; checking for PostgreSQL processes." -ForegroundColor Yellow
    }
    else {
        $status = & $pgCtl -D $pgData status 2>&1
        $statusText = ($status | Out-String).Trim()

        if ($statusText -match "server is running") {
            Write-Host "Stopping PostgreSQL cluster..."

            & $pgCtl -D $pgData stop -m fast

            if ($LASTEXITCODE -ne 0) {
                Write-Host "Fast PostgreSQL shutdown failed; attempting immediate shutdown." -ForegroundColor Yellow
                & $pgCtl -D $pgData stop -m immediate
            }

            Start-Sleep -Seconds 2
        }
        else {
            Write-Host "PostgreSQL cluster is not running."
        }
    }

    $postgresProcesses = @(
        Get-Process -Name "postgres" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Path -and
                $_.Path.StartsWith(
                    (Join-Path $InstallRoot "resources\postgresql"),
                    [StringComparison]::OrdinalIgnoreCase
                )
            }
    )

    foreach ($process in $postgresProcesses) {
        Write-Host "Stopping remaining bundled PostgreSQL PID $($process.Id)..." -ForegroundColor Yellow
        Stop-Process -Id $process.Id -Force -ErrorAction Stop
    }

    Start-Sleep -Seconds 1

    $remaining = @(
        Get-Process -Name "postgres" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Path -and
                $_.Path.StartsWith(
                    (Join-Path $InstallRoot "resources\postgresql"),
                    [StringComparison]::OrdinalIgnoreCase
                )
            }
    )

    if ($remaining.Count -gt 0) {
        throw "Bundled PostgreSQL process(es) are still running; runtime removal cannot safely continue."
    }

    Write-Host "Bundled PostgreSQL processes stopped." -ForegroundColor Green
}

$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$DataRoot = [IO.Path]::GetFullPath($DataRoot)

$VenvPython = Join-Path $InstallRoot ".venv\Scripts\python.exe"
$LifecyclePython = if (Test-Path $VenvPython) {
    $VenvPython
}
else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonCommand.Source
    }
    else {
        $null
    }
}

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

    $confirmationArgs = @(
        "uninstall",
        "--mode", "purge-data",
        "--confirm", "PURGE DAIRYOS DATA",
        "--keep-runtime"
    )

    if ($NoAutomaticBackup) {
        $confirmationArgs += "--no-backup-before-purge"
    }

    Write-Step "BACKUP, PURGE DATA"

    & $LifecyclePython @common @confirmationArgs

    if ($LASTEXITCODE -ne 0) {
        throw "DairyOS purge data operation failed. Runtime removal was not attempted."
    }
}
else {
    Write-Step "KEEP DATA; PREPARE RUNTIME REMOVAL"

    & $LifecyclePython @common `
        "uninstall" `
        "--mode" "keep-data" `
        "--keep-runtime"

    if ($LASTEXITCODE -ne 0) {
        throw "DairyOS keep-data lifecycle operation failed. Runtime removal was not attempted."
    }
}

Stop-DairyOSProcesses
Stop-DairyOSPostgres

Write-Step "VERIFY RUNTIME PROCESSES STOPPED"

$lockedProcesses = @(
    Get-Process -Name "DairyOS", "postgres" -ErrorAction SilentlyContinue |
        Where-Object {
            if ($_.ProcessName -eq "DairyOS") {
                $true
            }
            elseif ($_.Path) {
                $_.Path.StartsWith(
                    (Join-Path $InstallRoot "resources\postgresql"),
                    [StringComparison]::OrdinalIgnoreCase
                )
            }
            else {
                $false
            }
        }
)

if ($lockedProcesses.Count -gt 0) {
    $details = $lockedProcesses |
        ForEach-Object { "$($_.ProcessName) PID=$($_.Id)" } |
        Sort-Object

    throw "Runtime processes remain active: $($details -join ', ')"
}

Write-Step "REMOVE RUNTIME"

if (Test-Path $InstallRoot) {
    Remove-Item -Recurse -Force $InstallRoot -ErrorAction Stop
}

if (Test-Path $InstallRoot) {
    throw "Runtime directory still exists after removal attempt: $InstallRoot"
}

Write-Host "`nDairyOS uninstall completed in mode: $Mode" -ForegroundColor Green

if ($Mode -eq "KeepData") {
    Write-Host "Farm data retained at: $DataRoot" -ForegroundColor Green

    if (-not (Test-Path $DataRoot)) {
        throw "KeepData completed but the DairyOS data root is missing: $DataRoot"
    }

    Write-Host "A future DairyOS installation can be pointed back to this data directory." -ForegroundColor Green
}
else {
    Write-Host "Farm data purge completed. Pre-purge backup remains in the external backup location when enabled." -ForegroundColor Green
}