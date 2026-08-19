#requires -Version 5.1

$ErrorActionPreference = "Continue"
Set-Location D:\DairyOS

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$root = "D:\DairyOS\.dairyo-reconciliation"
$out = Join-Path $root "build-environment-$stamp"

New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS OS BUILD ENVIRONMENT PROBE - LF SAFE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== WSL STATUS ===" -ForegroundColor Yellow
$wslStatusFile = Join-Path $out "wsl-status.txt"
@(wsl.exe --status 2>&1) |
    Tee-Object -FilePath $wslStatusFile

Write-Host ""
Write-Host "=== WSL DISTRIBUTIONS ===" -ForegroundColor Yellow
$wslDistrosFile = Join-Path $out "wsl-distros.txt"
@(wsl.exe -l -v 2>&1) |
    Tee-Object -FilePath $wslDistrosFile

Write-Host ""
Write-Host "=== BUILDING LF-ONLY BASH PROBE ===" -ForegroundColor Yellow

$probeFileWindows = Join-Path $out "build-environment-probe.sh"
$probeFileWsl = "/mnt/d/DairyOS/.dairyo-reconciliation/build-environment-$stamp/build-environment-probe.sh"
$probeOutputFile = Join-Path $out "wsl-build-probe.txt"

$bashLines = @(
    'echo "=== OS ==="'
    'uname -a'
    'cat /etc/os-release 2>/dev/null || true'
    ''
    'echo "=== TOOLS ==="'
    'for c in bash sha256sum python3 rsync live-build lb debootstrap genisoimage xorriso grub-mkrescue qemu-system-x86_64 qemu-img; do'
    '    if command -v "$c" >/dev/null 2>&1; then'
    '        echo "FOUND $c -> $(command -v "$c")"'
    '    else'
    '        echo "MISSING $c"'
    '    fi'
    'done'
    ''
    'echo "=== VERSIONS ==="'
    'echo "--- python3 ---"'
    'python3 --version 2>&1 || true'
    'echo "--- rsync ---"'
    'rsync --version 2>&1 | head -1 || true'
    'echo "--- lb ---"'
    'lb --version 2>&1 || true'
    'echo "--- debootstrap ---"'
    'debootstrap --version 2>&1 || true'
    'echo "--- xorriso ---"'
    'xorriso --version 2>&1 | head -1 || true'
    'echo "--- grub-mkrescue ---"'
    'grub-mkrescue --version 2>&1 || true'
    'echo "--- qemu-system-x86_64 ---"'
    'qemu-system-x86_64 --version 2>&1 | head -1 || true'
    'echo "--- qemu-img ---"'
    'qemu-img --version 2>&1 | head -1 || true'
    ''
    'echo "=== FILESYSTEM ==="'
    'df -h /'
    ''
    'echo "=== REPOSITORY ACCESS ==="'
    'if [ -d /mnt/d/DairyOS ]; then'
    '    echo "FOUND /mnt/d/DairyOS"'
    'else'
    '    echo "MISSING /mnt/d/DairyOS"'
    'fi'
    ''
    'echo "=== GIT ==="'
    'cd /mnt/d/DairyOS'
    'git rev-parse --short HEAD 2>/dev/null || true'
    ''
    'echo "=== BUILD SCRIPT ==="'
    'sed -n "1,260p" /mnt/d/DairyOS/os/build/build-iso.sh'
    ''
    'echo "=== RELEASE MANIFEST SCRIPT ==="'
    'sed -n "1,220p" /mnt/d/DairyOS/os/build/release-manifest.sh'
    ''
    'echo "=== STAGE SCRIPT ==="'
    'sed -n "1,220p" /mnt/d/DairyOS/os/build/stage-app.sh'
    ''
    'echo "=== INSTALLER SCRIPT ==="'
    'sed -n "1,320p" /mnt/d/DairyOS/os/installer/install.sh'
    ''
    'echo "=== ROLLBACK SCRIPT ==="'
    'sed -n "1,320p" /mnt/d/DairyOS/os/installer/rollback.sh'
    ''
    'echo "=== FIRSTBOOT SCRIPT ==="'
    'sed -n "1,260p" /mnt/d/DairyOS/os/installer/hooks/firstboot.sh'
    ''
    'echo "=== VALIDATE SCRIPT ==="'
    'sed -n "1,260p" /mnt/d/DairyOS/os/installer/hooks/validate.sh'
    ''
    'exit 0'
)

# Write true LF-only bytes. Do not let Set-Content introduce CRLF.
$bashText = ($bashLines -join "`n") + "`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

[System.IO.File]::WriteAllText(
    $probeFileWindows,
    $bashText,
    $utf8NoBom
)

Write-Host "Probe written:" -ForegroundColor Green
Write-Host $probeFileWindows -ForegroundColor Green
Write-Host ""

Write-Host "=== WINDOWS BYTE CHECK ===" -ForegroundColor Yellow

$bytes = [System.IO.File]::ReadAllBytes($probeFileWindows)

$crlfCount = 0
$lfCount = 0
$crCount = 0

for ($i = 0; $i -lt $bytes.Length; $i++)
{
    if ($bytes[$i] -eq 10)
    {
        $lfCount++
        if ($i -gt 0 -and $bytes[$i - 1] -eq 13)
        {
            $crlfCount++
        }
    }

    if ($bytes[$i] -eq 13)
    {
        $crCount++
    }
}

Write-Host "LF bytes   : $lfCount"
Write-Host "CR bytes   : $crCount"
Write-Host "CRLF pairs : $crlfCount"

Write-Host ""

if ($crCount -ne 0 -or $crlfCount -ne 0)
{
    Write-Host "ERROR: probe is not LF-only." -ForegroundColor Red
    exit 2
}

Write-Host "PASS: probe is LF-only." -ForegroundColor Green

Write-Host ""
Write-Host "=== WSL FILE VISIBILITY ===" -ForegroundColor Yellow

$visibilityScript = "test -f '$probeFileWsl' && echo FOUND '$probeFileWsl' || echo MISSING '$probeFileWsl'"

wsl.exe bash -c $visibilityScript 2>&1

Write-Host ""
Write-Host "=== WSL LINE-END CHECK ===" -ForegroundColor Yellow

$lineCheckScript = "if grep -Ilr . '$probeFileWsl' >/dev/null 2>&1; then echo TEXT_READABLE; fi; if grep -n $'\r' '$probeFileWsl' >/dev/null 2>&1; then echo CR_FOUND; else echo NO_CR_FOUND; fi"

wsl.exe bash -c $lineCheckScript 2>&1

Write-Host ""
Write-Host "=== RUNNING WSL BUILD ENVIRONMENT PROBE ===" -ForegroundColor Yellow

# Bash interprets the file directly. No "bash -s" stdin conversion is involved.
@(wsl.exe bash $probeFileWsl 2>&1) |
    Tee-Object -FilePath $probeOutputFile

$wslExit = $LASTEXITCODE

Write-Host ""
Write-Host "WSL probe exit code: $wslExit"

Write-Host ""
Write-Host "=== CURRENT RELEASE OUTPUT ===" -ForegroundColor Yellow

$dist = "D:\DairyOS\dist\os"

if (Test-Path -LiteralPath $dist)
{
    Get-ChildItem -LiteralPath $dist -Force |
        Select-Object Name, Length, LastWriteTime |
        Format-Table -AutoSize
}
else
{
    Write-Host "dist\os does not exist."
}

Write-Host ""
Write-Host "=== CURRENT BUILD DIRECTORY ===" -ForegroundColor Yellow

$buildDir = "D:\DairyOS\.os-build"

if (Test-Path -LiteralPath $buildDir)
{
    Get-ChildItem -LiteralPath $buildDir -Force -Recurse |
        Select-Object FullName, Length, LastWriteTime |
        Format-Table -AutoSize
}
else
{
    Write-Host ".os-build does not exist."
}

Write-Host ""
Write-Host "=== GIT STATE ===" -ForegroundColor Yellow
git status --short
Write-Host "HEAD: $((git rev-parse HEAD).Trim())"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " BUILD ENVIRONMENT PROBE COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Diagnostic directory:"
Write-Host $out -ForegroundColor Green
Write-Host ""
Write-Host "Probe transcript:"
Write-Host $probeOutputFile -ForegroundColor Green
Write-Host ""

if ($wslExit -eq 0)
{
    Write-Host "PASS: WSL probe completed." -ForegroundColor Green
}
else
{
    Write-Host "FAIL: WSL probe exited with code $wslExit." -ForegroundColor Red
}
