[CmdletBinding()]
param(
    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")),
    [string]$InstallRoot = (Join-Path $env:ProgramFiles "DairyOS"),
    [string]$DataRoot = (Join-Path $env:ProgramData "DairyOS"),
    [string]$DatabaseUrl = $env:DAIRYOS_DATABASE_URL,
    [switch]$Upgrade,
    [switch]$SkipDatabaseValidation
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Invoke-DairyOsLifecycle([string[]]$Arguments) {
    $previousPythonPath = $env:PYTHONPATH
    try {
        $env:PYTHONPATH = Join-Path $SourceRoot "src"
        & $VenvPython -m dairyos.lifecycle.cli @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "DairyOS lifecycle command failed: $($Arguments -join ' ')"
        }
    }
    finally {
        $env:PYTHONPATH = $previousPythonPath
    }
}

$SourceRoot = (Resolve-Path $SourceRoot).Path
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$DataRoot = [IO.Path]::GetFullPath($DataRoot)

if (-not (Test-Path (Join-Path $SourceRoot "pyproject.toml"))) {
    throw "SourceRoot does not appear to be a DairyOS repository: $SourceRoot"
}

if ($env:OS -ne "Windows_NT") {
    throw "Install-DairyOS.ps1 is the Windows installer. Use the Python lifecycle CLI on other platforms."
}

Write-Step "PRE-FLIGHT"
Write-Host "Source : $SourceRoot"
Write-Host "Install: $InstallRoot"
Write-Host "Data   : $DataRoot"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python 3.12+ is required and was not found on PATH."
}

$pythonVersion = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0) { throw "Unable to determine Python version." }
$majorMinor = [version]($pythonVersion -replace '^([0-9]+\.[0-9]+).*','$1')
if ($majorMinor -lt [version]"3.12") {
    throw "Python 3.12+ is required. Found $pythonVersion"
}

$HadExistingRuntime = Test-Path $InstallRoot
New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

$VenvPython = Join-Path $InstallRoot ".venv\Scripts\python.exe"
$RuntimeBackup = $null
$DataBackup = $null

try {
    if ($Upgrade -or (Test-Path $VenvPython)) {
        Write-Step "BACKUP BEFORE CHANGE"

        $backupLabel = if ($Upgrade) { "pre-upgrade" } else { "pre-install-repair" }
        $cliArgs = @(
            "--install-root", $InstallRoot,
            "--data-root", $DataRoot
        )
        if ($DatabaseUrl) {
            $cliArgs += @("--database-url", $DatabaseUrl)
        }
        $cliArgs += @("backup", "--label", $backupLabel)

        Invoke-DairyOsLifecycle $cliArgs
        $DataBackup = Get-ChildItem (Join-Path $DataRoot "backups") -Directory |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        if (-not $DataBackup) {
            throw "Lifecycle backup command completed without producing a backup directory."
        }

        $RuntimeBackup = Join-Path $DataBackup.FullName "runtime.zip"
        $runtimeItems = Get-ChildItem $InstallRoot -Force
        if ($runtimeItems) {
            Compress-Archive -Path $runtimeItems.FullName -DestinationPath $RuntimeBackup -CompressionLevel Optimal -Force
        }
    }

    Write-Step "INSTALL / UPGRADE RUNTIME"

    if (-not (Test-Path $VenvPython)) {
        python -m venv (Join-Path $InstallRoot ".venv")
        if ($LASTEXITCODE -ne 0) { throw "Python virtual environment creation failed." }
    }

    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip bootstrap failed." }

    & $VenvPython -m pip install -e $SourceRoot
    if ($LASTEXITCODE -ne 0) { throw "DairyOS package installation failed." }

    Write-Step "VALIDATE"
    $validateArgs = @(
        "--install-root", $InstallRoot,
        "--data-root", $DataRoot
    )
    if (-not $SkipDatabaseValidation -and $DatabaseUrl) {
        $validateArgs += @("--database-url", $DatabaseUrl)
    }

    $installArgs = $validateArgs + @("install")
    Invoke-DairyOsLifecycle $installArgs

    $validateCommandArgs = $validateArgs + @("validate")
    Invoke-DairyOsLifecycle $validateCommandArgs

    Write-Step "DATABASE / PRODUCTION SECURITY GATE"
    $previousEnvironment = $env:DAIRYOS_ENV
    $previousDataDir = $env:DAIRYOS_DATA_DIR
    try {
        $env:DAIRYOS_ENV = "production"
        $env:DAIRYOS_DATA_DIR = $DataRoot

        & $VenvPython -c "from dairyos.windows.system_postgres_admin import validate_stored_admin_credential; validate_stored_admin_credential()"
        if ($LASTEXITCODE -ne 0) {
            $secureDbAdminPassword = Read-Host "Enter the system PostgreSQL dairyos_admin password for one-time secure adoption/repair" -AsSecureString
            $dbAdminPasswordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureDbAdminPassword)
            try {
                $plainDbAdminPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($dbAdminPasswordPtr)
                $env:DAIRYOS_SYSTEM_POSTGRES_ADMIN_PASSWORD = $plainDbAdminPassword
                & $VenvPython -c "import os; from dairyos.windows.system_postgres_admin import adopt_admin_password; adopt_admin_password(os.environ['DAIRYOS_SYSTEM_POSTGRES_ADMIN_PASSWORD'])"
                if ($LASTEXITCODE -ne 0) {
                    throw "The system PostgreSQL dairyos_admin credential was rejected and was not adopted."
                }
                Write-Host "System PostgreSQL migration credential adopted with Windows DPAPI protection." -ForegroundColor Green
            }
            finally {
                if ($dbAdminPasswordPtr -ne [IntPtr]::Zero) {
                    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($dbAdminPasswordPtr)
                }
                Remove-Item Env:DAIRYOS_SYSTEM_POSTGRES_ADMIN_PASSWORD -ErrorAction SilentlyContinue
            }
        }
        else {
            Write-Host "Existing DPAPI-protected system PostgreSQL migration credential is valid." -ForegroundColor Green
        }

        & $VenvPython -c "from dairyos.windows.system_postgres_admin import stage_migration_database_url; from dairyos.windows.migrations import migrate_if_needed; stage_migration_database_url(); print(migrate_if_needed())"
        if ($LASTEXITCODE -ne 0) {
            throw "DairyOS production migration gate failed during installation."
        }

        & $VenvPython -c "from dairyos.api.auth import ensure_production_admin_password_configured; ensure_production_admin_password_configured()"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Existing production admin password configuration is valid." -ForegroundColor Green
        }
        else {
            $securePassword = Read-Host "Enter the DairyOS production admin password (minimum 12 characters)" -AsSecureString
            $passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
            try {
                $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)
                $env:DAIRYOS_BOOTSTRAP_ADMIN_PASSWORD = $plainPassword
                & $VenvPython -c "import os; from dairyos.api.auth import bootstrap_production_admin_password; bootstrap_production_admin_password(os.environ['DAIRYOS_BOOTSTRAP_ADMIN_PASSWORD'])"
                if ($LASTEXITCODE -ne 0) {
                    throw "DairyOS production admin password bootstrap failed."
                }
                Write-Host "Production admin password initialized securely in the DairyOS data store." -ForegroundColor Green
            }
            finally {
                if ($passwordPtr -ne [IntPtr]::Zero) {
                    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
                }
                Remove-Item Env:DAIRYOS_BOOTSTRAP_ADMIN_PASSWORD -ErrorAction SilentlyContinue
            }
        }
    }
    finally {
        if ($null -eq $previousEnvironment) { Remove-Item Env:DAIRYOS_ENV -ErrorAction SilentlyContinue } else { $env:DAIRYOS_ENV = $previousEnvironment }
        if ($null -eq $previousDataDir) { Remove-Item Env:DAIRYOS_DATA_DIR -ErrorAction SilentlyContinue } else { $env:DAIRYOS_DATA_DIR = $previousDataDir }
    }

    Write-Step "WRITE LAUNCHER"
    $launcher = Join-Path $InstallRoot "DairyOS-Desktop.ps1"
    $launcherContent = @"
`$ErrorActionPreference = 'Stop'
`$env:DAIRYOS_ENV = 'production'
`$env:DAIRYOS_DATA_DIR = '$DataRoot'
if (-not `$env:DAIRYOS_DATABASE_URL -and (`$env:DAIRYOS_DB_PASSWORD -or `$env:DAIRYOS_DB_HOST)) {
    Write-Host 'Using DAIRYOS_DB_* environment variables for the production database.'
}
& '$VenvPython' -m dairyos.windows.supervisor
"@
    [IO.File]::WriteAllText(
        $launcher,
        $launcherContent,
        (New-Object System.Text.UTF8Encoding($false))
    )

    Write-Step "INSTALLATION COMPLETE"
    Write-Host "Runtime : $InstallRoot"
    Write-Host "Data    : $DataRoot"
    Write-Host "Launcher: $launcher"
}
catch {
    Write-Host "`nINSTALLATION / UPGRADE FAILED: $($_.Exception.Message)" -ForegroundColor Red

    if ($DataBackup -and (Test-Path $DataBackup.FullName)) {
        Write-Step "ROLLBACK DATA"
        $rollbackArgs = @(
            "--install-root", $InstallRoot,
            "--data-root", $DataRoot
        )
        if ($DatabaseUrl) {
            $rollbackArgs += @("--database-url", $DatabaseUrl)
        }
        $rollbackCommandArgs = $rollbackArgs + @("rollback", $DataBackup.FullName)
        Invoke-DairyOsLifecycle $rollbackCommandArgs

        if ($RuntimeBackup -and (Test-Path $RuntimeBackup)) {
            Write-Step "ROLLBACK RUNTIME"
            if (Test-Path $InstallRoot) {
                Remove-Item -Recurse -Force $InstallRoot
            }
            New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
            Expand-Archive -Path $RuntimeBackup -DestinationPath $InstallRoot -Force
        }
    }
    elseif (-not $HadExistingRuntime -and (Test-Path $InstallRoot)) {
        Write-Step "REMOVE PARTIAL FIRST INSTALL"
        Remove-Item -Recurse -Force $InstallRoot
    }
    else {
        Write-Warning "No pre-change runtime/data snapshot was available; no destructive rollback was attempted."
    }

    throw
}
