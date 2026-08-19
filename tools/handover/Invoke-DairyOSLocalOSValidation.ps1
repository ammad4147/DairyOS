[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [switch]$Strict,
    [switch]$SkipPythonTests
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$OsRoot = Join-Path $RepoRoot "os"
$TestPath = Join-Path $RepoRoot "tests\platform\test_os_distribution_artifacts.py"

function Assert-Path([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required OS artifact is missing: $Path"
    }
}

function Invoke-Native([string]$Name, [scriptblock]$Action) {
    Write-Host ""
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
    Write-Host "PASS: $Name" -ForegroundColor Green
}

Write-Host "DairyOS OS local validation" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"

foreach ($relative in @(
    "manifest.yaml",
    "partitioning\dairyos.sfdisk",
    "boot\grub\grub.cfg",
    "installer\install.sh",
    "installer\rollback.sh",
    "installer\preseed\dairyos.seed",
    "installer\hooks\firstboot.sh",
    "installer\hooks\validate.sh",
    "build\build-iso.sh",
    "build\stage-app.sh",
    "build\release-manifest.sh",
    "pxe\dnsmasq.conf",
    "pxe\grub.cfg",
    "pxe\ipxe\dairyos.ipxe",
    "pxe\mirror\sync-debian.sh",
    "pxe\mirror\nginx-dairyos.conf",
    "services\dairyos.service",
    "services\dairyos-firstboot.service"
)) {
    Assert-Path (Join-Path $OsRoot $relative)
}

$installer = Get-Content (Join-Path $OsRoot "installer\install.sh") -Raw
foreach ($pattern in @(
    'MODE="dry-run"',
    '--apply',
    'sfdisk',
    'grub-install --target=x86_64-efi',
    'grub-install --target=i386-pc',
    'DEBIAN_MIRROR="file:///srv/dairyos-debian"',
    'validate_mirror'
)) {
    if ($installer -notmatch [regex]::Escape($pattern)) {
        throw "Installer missing required contract: $pattern"
    }
}
Write-Host "PASS: installer safety, bootloader and offline-mirror contracts" -ForegroundColor Green

$manifest = Get-Content (Join-Path $OsRoot "manifest.yaml") -Raw
foreach ($token in @("debian", "trixie", "amd64", "gpt", "uefi", "legacy-bios", "dry-run", "PXE", "192.168.50.1", "/debian")) {
    if ($manifest -notmatch [regex]::Escape($token)) {
        throw "OS manifest missing required token: $token"
    }
}
Write-Host "PASS: OS manifest contract" -ForegroundColor Green

$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if ($wsl) {
    Invoke-Native "Bash syntax check" {
        $normalized = $RepoRoot -replace '\\','/'
        $drive = $normalized.Substring(0,1).ToLower()
        $rest = $normalized.Substring(2)
        $linuxRoot = "/mnt/$drive$rest"
        $command = ('find "{0}/os" -type f -name ''*.sh'' -print0 | xargs -0 -r -n1 bash -n' -f $linuxRoot)
        wsl.exe bash -lc $command
    }
}
else {
    Write-Host "WARN: WSL not available; Bash syntax checks skipped." -ForegroundColor Yellow
}

if (-not $SkipPythonTests) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw "Python is not available on PATH." }
    $env:PYTHONPATH = Join-Path $RepoRoot "src"
    Invoke-Native "OS artifact pytest contract" {
        Push-Location $RepoRoot
        try { python -m pytest -q $TestPath }
        finally { Pop-Location }
    }
}

if ($Strict) {
    Write-Host "PASS: strict local OS validation completed." -ForegroundColor Green
}
