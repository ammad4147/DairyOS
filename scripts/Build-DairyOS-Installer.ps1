[CmdletBinding()]
param(
    [string]$Bundle = "dist\DairyOS-Release\DairyOS",
    [string]$Output = "dist\DairyOS-Installer\DairyOS-Windows-Installer.exe"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo

$bundlePath = [IO.Path]::GetFullPath((Join-Path $repo $Bundle))
$outputPath = [IO.Path]::GetFullPath((Join-Path $repo $Output))
$iss = Join-Path $repo "tools\windows-desktop\DairyOS-Installer.iss"

if (-not (Test-Path (Join-Path $bundlePath "DairyOS.exe") -PathType Leaf)) { throw "Certified desktop bundle is missing DairyOS.exe: $bundlePath" }
if (-not (Test-Path (Join-Path $bundlePath "DairyOSBackup.exe") -PathType Leaf)) { throw "Certified desktop bundle is missing DairyOSBackup.exe: $bundlePath" }

Write-Host "=== BUILD STANDALONE ADMIN TOOL ===" -ForegroundColor Cyan
& (Join-Path $repo "scripts\Build-DairyOS-Admin.ps1")
if ($LASTEXITCODE -ne 0) { throw "DairyOS Admin Tool build failed." }
$adminExe = Join-Path $repo "dist\DairyOS-Admin\DairyOS-Admin.exe"
if (-not (Test-Path $adminExe -PathType Leaf)) { throw "DairyOS-Admin.exe was not produced: $adminExe" }
Copy-Item $adminExe (Join-Path $bundlePath "DairyOS-Admin.exe") -Force
if (-not (Test-Path $iss -PathType Leaf)) { throw "Inno Setup definition is missing: $iss" }

$pf86 = [Environment]::GetFolderPath("ProgramFilesX86")
$candidates = @(
    (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe"),
    (Join-Path $pf86 "Inno Setup 7\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path $pf86 "Inno Setup 6\ISCC.exe")
)
$iscc = $candidates | Where-Object { $_ -and (Test-Path $_ -PathType Leaf) } | Select-Object -First 1
if (-not $iscc) {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) { $iscc = $command.Source }
}
if (-not $iscc) { throw "Inno Setup ISCC.exe was not found. Install Inno Setup 6 or 7." }

Write-Host "=== BUILD WINDOWS INSTALLER ===" -ForegroundColor Cyan
& $iscc $iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup build failed with exit code $LASTEXITCODE." }
if (-not (Test-Path $outputPath -PathType Leaf)) { throw "Installer was not produced: $outputPath" }

Write-Host ""
Write-Host "DAIRYOS WINDOWS INSTALLER BUILD: PASS" -ForegroundColor Green
Get-Item $outputPath | Select-Object FullName,Length
Get-FileHash $outputPath -Algorithm SHA256
exit 0
