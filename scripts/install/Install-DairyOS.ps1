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

New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $InstallRoot ".lifecycle") | Out-Null

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

        if (Test-Path $InstallRoot) {
            $RuntimeBackup = Join-Path $DataBackup.FullName "runtime.zip"
            $runtimeItems = Get-ChildItem $InstallRoot -Force | Where-Object { $_.FullName -ne $DataBackup.FullName }
            if ($runtimeItems) {
                Compress-Archive -Path $runtimeItems.FullName -DestinationPath $RuntimeBackup -CompressionLevel Optimal -Force
            }
        }
    }

    Write-Step "INSTALL / UPGRADE RUNTIME"
    New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

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
    if ($DatabaseUrl) {
        $validateArgs += @("--database-url", $DatabaseUrl)
    }
    if ($SkipDatabaseValidation) {
        $env:DAIRYOS_DATA_DIR = $DataRoot
        & $VenvPython -m dairyos.lifecycle.cli --install-root $InstallRoot --data-root $DataRoot install | Out-Host
    }
    else {
        Invoke-DairyOsLifecycle $validateArgs + @("install")
        Invoke-DairyOsLifecycle $validateArgs + @("validate")
    }

    Write-Step "WRITE LAUNCHER"
    $launcher = Join-Path $InstallRoot "DairyOS-Server.ps1"
    $launcherContent = @"
`$ErrorActionPreference = 'Stop'
`$env:DAIRYOS_DATA_DIR = '$DataRoot'
if ('$DatabaseUrl') {
    `$env:DAIRYOS_DATABASE_URL = '$DatabaseUrl'
}
& '$VenvPython' -m dairyos.server --host 127.0.0.1 --port 8000
"@
    [IO.File]::WriteAllText($launcher, $launcherContent, (New-Object System.Text.UTF8Encoding($false)))

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
        Invoke-DairyOsLifecycle $rollbackArgs + @("rollback", $DataBackup.FullName)

        if ($RuntimeBackup -and (Test-Path $RuntimeBackup)) {
            Write-Step "ROLLBACK RUNTIME"
            if (Test-Path $InstallRoot) {
                Remove-Item -Recurse -Force $InstallRoot
            }
            New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
            Expand-Archive -Path $RuntimeBackup -DestinationPath $InstallRoot -Force
        }
    }
    else {
        Write-Warning "No pre-change data backup was available; no destructive rollback was attempted."
    }

    throw
}
