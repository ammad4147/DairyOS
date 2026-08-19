#requires -Version 5.1

$ErrorActionPreference = "Stop"
Set-Location D:\DairyOS

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportRoot = "D:\DairyOS\.dairyo-reconciliation\iso-build-$stamp"

New-Item -ItemType Directory -Force -Path $reportRoot | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS ACTUAL ISO BUILD" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== BUILD IDENTITY ===" -ForegroundColor Yellow

$head = (git rev-parse HEAD).Trim()
$branch = (git branch --show-current).Trim()

Write-Host "HEAD   : $head"
Write-Host "Branch : $branch"
Write-Host ""

git status --short

$head |
    Set-Content -LiteralPath (Join-Path $reportRoot "build-head.txt") -Encoding UTF8

$branch |
    Set-Content -LiteralPath (Join-Path $reportRoot "build-branch.txt") -Encoding UTF8

Write-Host ""
Write-Host "=== WSL TOOLCHAIN CHECK ===" -ForegroundColor Yellow

$toolProbe = @(
    'for c in bash lb sha256sum python3 rsync debootstrap xorriso grub-mkrescue qemu-system-x86_64 qemu-img sfdisk; do'
    '    if command -v "$c" >/dev/null 2>&1; then'
    '        echo "PASS: $c -> $(command -v "$c")"'
    '    else'
    '        echo "FAIL: missing $c"'
    '        exit 10'
    '    fi'
    'done'
)

$toolProbeFile = Join-Path $reportRoot "tool-probe.sh"
$toolProbeText = ($toolProbe -join "`n") + "`n"
$utf8 = New-Object System.Text.UTF8Encoding($false)

[System.IO.File]::WriteAllText(
    $toolProbeFile,
    $toolProbeText,
    $utf8
)

$toolProbeWsl = "/mnt/d/DairyOS/.dairyo-reconciliation/iso-build-$stamp/tool-probe.sh"

@(wsl.exe bash "$toolProbeWsl" 2>&1) |
    Tee-Object -FilePath (Join-Path $reportRoot "tool-probe.txt")

if ($LASTEXITCODE -ne 0) {
    throw "WSL toolchain verification failed."
}

Write-Host ""
Write-Host "=== CLEAN BUILD OUTPUT PREPARATION ===" -ForegroundColor Yellow

$dist = "D:\DairyOS\dist\os"
$work = "D:\DairyOS\.os-build"

if (Test-Path $dist) {
    Get-ChildItem $dist -Force |
        Where-Object {
            $_.Name -match '\.(iso|img|raw|qcow2|sha256)$' -or
            $_.Name -eq 'SHA256SUMS' -or
            $_.Name -eq 'SHA256SUMS.asc'
        } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

if (Test-Path $work) {
    Remove-Item $work -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $dist | Out-Null

Write-Host "dist/os prepared:"
Get-ChildItem $dist -Force |
    Select-Object Name, Length, LastWriteTime |
    Format-Table -AutoSize

Write-Host ""
Write-Host "=== BUILD SCRIPT SNAPSHOT ===" -ForegroundColor Yellow

Get-Content "os/build/build-iso.sh" -Raw |
    Tee-Object -FilePath (Join-Path $reportRoot "build-iso.sh.snapshot") |
    Out-Null

Write-Host ""
Write-Host "=== RUNNING WSL ISO BUILD ===" -ForegroundColor Green

#
# IMPORTANT:
# Do not invoke git from the WSL/root build process.
# Git on /mnt/d rejects the repository as "dubious ownership" when the
# process runs as root while the Windows worktree belongs to the user.
# build-iso.sh itself does not require Git.
#
$buildCommand = @(
    'set -Eeuo pipefail'
    'cd /mnt/d/DairyOS'
    'echo "BUILD ROOT: $(pwd)"'
    'echo "BUILD START: $(date -Is)"'
    'bash os/build/build-iso.sh'
    'echo "BUILD END: $(date -Is)"'
)

$buildFile = Join-Path $reportRoot "run-build.sh"
$buildText = ($buildCommand -join "`n") + "`n"

[System.IO.File]::WriteAllText(
    $buildFile,
    $buildText,
    $utf8
)

$buildFileWsl = "/mnt/d/DairyOS/.dairyo-reconciliation/iso-build-$stamp/run-build.sh"
$buildTranscript = Join-Path $reportRoot "build-transcript.txt"

@(wsl.exe -u root bash "$buildFileWsl" 2>&1) |
    Tee-Object -FilePath $buildTranscript

$buildExit = $LASTEXITCODE

Write-Host ""
Write-Host "BUILD EXIT CODE: $buildExit"

if ($buildExit -ne 0) {
    throw "DairyOS ISO build failed. See $buildTranscript"
}

Write-Host ""
Write-Host "=== GENERATED ARTIFACTS ===" -ForegroundColor Yellow

if (-not (Test-Path $dist)) {
    throw "dist/os was not created."
}

Get-ChildItem $dist -Force |
    Select-Object Name, Length, LastWriteTime |
    Format-Table -AutoSize

$iso = Get-ChildItem $dist -Filter "*.iso" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($null -eq $iso) {
    throw "No ISO artifact was produced."
}

$isoSha = "$($iso.FullName).sha256"
$manifest = Join-Path $dist "SHA256SUMS"

Write-Host ""
Write-Host "ISO:" -ForegroundColor Green
Write-Host $iso.FullName

if (-not (Test-Path $isoSha)) {
    throw "Per-ISO SHA256 file is missing: $isoSha"
}

if (-not (Test-Path $manifest)) {
    Write-Host ""
    Write-Host "=== GENERATING RELEASE MANIFEST ===" -ForegroundColor Yellow

    @(wsl.exe -u root bash `
        /mnt/d/DairyOS/os/build/release-manifest.sh `
        /mnt/d/DairyOS/dist/os 2>&1) |
        Tee-Object -FilePath (Join-Path $reportRoot "manifest-generation.txt")

    if ($LASTEXITCODE -ne 0) {
        throw "Release manifest generation failed."
    }
}

if (-not (Test-Path $manifest)) {
    throw "SHA256SUMS was not created."
}

Write-Host ""
Write-Host "=== SHA256 MANIFEST ===" -ForegroundColor Yellow

Get-Content $manifest |
    Tee-Object -FilePath (Join-Path $reportRoot "SHA256SUMS.txt")

if ((Get-Item $manifest).Length -eq 0) {
    throw "SHA256SUMS exists but is empty."
}

Write-Host ""
Write-Host "=== CHECKSUM VERIFICATION ===" -ForegroundColor Yellow

$verifyCommand = @(
    'set -Eeuo pipefail'
    'cd /mnt/d/DairyOS/dist/os'
    'sha256sum -c SHA256SUMS'
)

$verifyFile = Join-Path $reportRoot "verify-checksums.sh"
$verifyText = ($verifyCommand -join "`n") + "`n"

[System.IO.File]::WriteAllText(
    $verifyFile,
    $verifyText,
    $utf8
)

$verifyFileWsl = "/mnt/d/DairyOS/.dairyo-reconciliation/iso-build-$stamp/verify-checksums.sh"

@(wsl.exe -u root bash "$verifyFileWsl" 2>&1) |
    Tee-Object -FilePath (Join-Path $reportRoot "checksum-verification.txt")

if ($LASTEXITCODE -ne 0) {
    throw "SHA256SUMS verification failed."
}

Write-Host ""
Write-Host "=== ISO DIRECT HASH ===" -ForegroundColor Yellow

$directHash = (Get-FileHash $iso.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$declaredLine = (Get-Content $isoSha | Select-Object -First 1).Trim()

Write-Host "Direct SHA256 : $directHash"
Write-Host "Declared file : $declaredLine"

if ($declaredLine -notmatch [regex]::Escape($directHash)) {
    throw "Per-ISO SHA256 does not match the generated ISO."
}

Write-Host ""
Write-Host "=== ISO STRUCTURAL INSPECTION ===" -ForegroundColor Yellow

$isoInspect = @(
    'set -Eeuo pipefail'
    'cd /mnt/d/DairyOS/dist/os'
    'ISO="$(find . -maxdepth 1 -type f -name "*.iso" -print -quit)"'
    'test -n "$ISO"'
    'echo "ISO=$ISO"'
    'file "$ISO"'
    'xorriso -indev "$ISO" -toc 2>&1 | head -80'
)

$isoInspectFile = Join-Path $reportRoot "inspect-iso.sh"
$isoInspectText = ($isoInspect -join "`n") + "`n"

[System.IO.File]::WriteAllText(
    $isoInspectFile,
    $isoInspectText,
    $utf8
)

$isoInspectWsl = "/mnt/d/DairyOS/.dairyo-reconciliation/iso-build-$stamp/inspect-iso.sh"

@(wsl.exe -u root bash "$isoInspectWsl" 2>&1) |
    Tee-Object -FilePath (Join-Path $reportRoot "iso-inspection.txt")

if ($LASTEXITCODE -ne 0) {
    throw "ISO structural inspection failed."
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " ISO BUILD GATE PASSED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "ISO:"
Write-Host $iso.FullName -ForegroundColor Green

Write-Host ""
Write-Host "ISO SHA256:"
Write-Host $directHash -ForegroundColor Green

Write-Host ""
Write-Host "Manifest:"
Write-Host $manifest -ForegroundColor Green

Write-Host ""
Write-Host "Build report:"
Write-Host $reportRoot -ForegroundColor Green

Write-Host ""
Write-Host "No target disk was touched."
Write-Host "No installer was executed."
Write-Host "No application baseline was modified."
