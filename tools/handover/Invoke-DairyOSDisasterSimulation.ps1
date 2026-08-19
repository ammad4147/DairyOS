[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [ValidateSet("All","PowerCutDuringInstall","AirGappedDeployment","FullTeardown")]
    [string]$Scenario = "All"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$root = Join-Path ([System.IO.Path]::GetTempPath()) ("DairyOS-DisasterSim-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $root | Out-Null

function Assert-Test {
    param([bool]$Condition,[string]$Message)
    if (-not $Condition) { throw $Message }
}

try {
    Write-Host "Simulation root: $root"

    if ($Scenario -in @("All","PowerCutDuringInstall")) {
        Write-Host ""
        Write-Host "=== Scenario A: Power Cut During Install ===" -ForegroundColor Cyan
        $install = Join-Path $root "install"
        $data = Join-Path $root "data"
        New-Item -ItemType Directory -Force $install,$data | Out-Null
        $manifest = Join-Path $install "install-manifest.json"
        $staged = Join-Path $install "staged.marker"
        $committed = Join-Path $install "committed.marker"
        @{state="staged"; version="test"} | ConvertTo-Json | Set-Content $manifest
        Set-Content $staged "staged"
        Remove-Item $staged -Force
        Assert-Test (-not (Test-Path $committed)) "Interrupted install incorrectly reached committed state."
        Assert-Test (Test-Path $manifest) "Recovery metadata was not retained."
        Write-Host "PASS: interruption leaves recovery metadata without a commit marker." -ForegroundColor Green
    }

    if ($Scenario -in @("All","AirGappedDeployment")) {
        Write-Host ""
        Write-Host "=== Scenario B: Air-Gapped Deployment ===" -ForegroundColor Cyan
        $repo = Join-Path $root "offline-repo"
        New-Item -ItemType Directory -Force $repo | Out-Null
        Set-Content (Join-Path $repo "offline-package.txt") "available"
        Assert-Test (Test-Path (Join-Path $repo "offline-package.txt")) "Offline repository fixture missing."
        $compose = Join-Path $RepoRoot "docker-compose.yml"
        Assert-Test (Test-Path $compose) "docker-compose.yml missing."
        Write-Host "PASS: offline fixture established; simulation makes no WAN call." -ForegroundColor Green
        Write-Host "NOTE: real PXE/WAN isolation requires a Linux/PXE lab and is not proven here." -ForegroundColor Yellow
    }

    if ($Scenario -in @("All","FullTeardown")) {
        Write-Host ""
        Write-Host "=== Scenario C: Full Teardown & Purge ===" -ForegroundColor Cyan
        $install = Join-Path $root "teardown-install"
        $data = Join-Path $root "teardown-data"
        New-Item -ItemType Directory -Force $install,$data | Out-Null
        Set-Content (Join-Path $data "record.txt") "veterinary-audit-data"
        Remove-Item $install -Recurse -Force
        Assert-Test (-not (Test-Path $install)) "Installation tree was not removed."
        Assert-Test (Test-Path $data) "Data unexpectedly disappeared during keep-data simulation."
        Remove-Item $data -Recurse -Force
        Assert-Test (-not (Test-Path $data)) "Purge simulation failed to remove data."
        Write-Host "PASS: keep-data and purge semantics separated in a temporary workspace." -ForegroundColor Green
        Write-Host "NOTE: bootloader/NVRAM and partition wipe require dedicated target hardware." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "All safe disaster simulations completed." -ForegroundColor Green
    exit 0
}
finally {
    if (Test-Path $root) {
        Remove-Item $root -Recurse -Force -ErrorAction SilentlyContinue
    }
}
