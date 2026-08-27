$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$releaseRoot = Join-Path $repo '..\Desktop\DairyOS-Release-Candidate'
$bundle = Join-Path $repo 'dist\DairyOS-Release\DairyOS'
$desktopRoot = Join-Path ([Environment]::GetFolderPath('Desktop')) 'DairyOS-Release-Candidate'
$desktopBundle = Join-Path $desktopRoot 'dist\DairyOS'
$iss = Join-Path $repo 'tools\windows-desktop\DairyOS-Installer.iss'

if (-not (Test-Path $bundle)) { throw "Release bundle missing: $bundle" }
if (-not (Test-Path (Join-Path $bundle 'DairyOS.exe'))) { throw 'DairyOS.exe missing from release bundle.' }

$iscc = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    throw 'Inno Setup 6 ISCC.exe was not found. Install Inno Setup 6 before creating the Windows installer.'
}

Remove-Item $desktopRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $desktopBundle -Force | Out-Null

robocopy $bundle $desktopBundle /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -gt 7) { throw "Failed to copy release bundle to Desktop (robocopy exit $LASTEXITCODE)." }

& $iscc $iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup build failed with exit code $LASTEXITCODE." }

$installer = Join-Path $repo 'dist\DairyOS-Installer\DairyOS-Windows-Installer.exe'
if (-not (Test-Path $installer)) { throw "Installer was not produced: $installer" }

$desktopInstaller = Join-Path $desktopRoot 'DairyOS-Windows-Installer.exe'
Copy-Item $installer $desktopInstaller -Force

Write-Host ''
Write-Host '=== WINDOWS INSTALLER CREATED ==='
Write-Host $desktopInstaller
Write-Host ''
Get-FileHash $desktopInstaller -Algorithm SHA256
