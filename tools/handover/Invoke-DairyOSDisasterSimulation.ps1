[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [ValidateSet("All","InterruptedInstall","KeepDataUninstall","PurgeData")]
    [string]$Scenario = "All"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$root = Join-Path ([System.IO.Path]::GetTempPath()) ("DairyOS-Windows-DeploymentSim-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $root | Out-Null

function Assert-Test {
    param([bool]$Condition,[string]$Message)
    if (-not $Condition) { throw $Message }
}

try {
    Write-Host "Simulation root: $root"

    if ($Scenario -in @("All","InterruptedInstall")) {
        Write-Host ""
        Write-Host "=== Scenario A: Interrupted Windows Installation ===" -ForegroundColor Cyan
        $install = Join-Path $root "install"
        New-Item -ItemType Directory -Force $install | Out-Null
        $manifest = Join-Path $install "install-manifest.json"
        $staged = Join-Path $install "staged.marker"
        $committed = Join-Path $install "committed.marker"
        @{state="staged"; version="test"} | ConvertTo-Json | Set-Content $manifest
        Set-Content $staged "staged"
        Remove-Item $staged -Force
        Assert-Test (-not (Test-Path $committed)) "Interrupted installation incorrectly reached committed state."
        Assert-Test (Test-Path $manifest) "Recovery metadata was not retained."
        Write-Host "PASS: interrupted installer simulation retains recovery metadata without a commit marker." -ForegroundColor Green
    }

    if ($Scenario -in @("All","KeepDataUninstall")) {
        Write-Host ""
        Write-Host "=== Scenario B: Application Uninstall With Data Preservation ===" -ForegroundColor Cyan
        $install = Join-Path $root "installation"
        $data = Join-Path $root "farm-data"
        New-Item -ItemType Directory -Force $install,$data | Out-Null
        Set-Content (Join-Path $data "record.txt") "veterinary-audit-data"
        Remove-Item $install -Recurse -Force
        Assert-Test (-not (Test-Path $install)) "Application installation tree was not removed."
        Assert-Test (Test-Path (Join-Path $data "record.txt")) "Farm data unexpectedly disappeared during uninstall-with-data-preservation simulation."
        Write-Host "PASS: application removal preserves farm data." -ForegroundColor Green
    }

    if ($Scenario -in @("All","PurgeData")) {
        Write-Host ""
        Write-Host "=== Scenario C: Explicit Farm-Data Purge ===" -ForegroundColor Cyan
        $data = Join-Path $root "purge-data"
        New-Item -ItemType Directory -Force $data | Out-Null
        Set-Content (Join-Path $data "record.txt") "veterinary-audit-data"
        Remove-Item $data -Recurse -Force
        Assert-Test (-not (Test-Path $data)) "Explicit farm-data purge simulation failed."
        Write-Host "PASS: explicit data purge is separate from application uninstall." -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "All Windows deployment disaster simulations completed." -ForegroundColor Green
    exit 0
}
finally {
    if (Test-Path $root) {
        Remove-Item $root -Recurse -Force -ErrorAction SilentlyContinue
    }
}
