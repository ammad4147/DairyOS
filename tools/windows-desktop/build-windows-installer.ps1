$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$portableBuild = Join-Path $repo 'tools\windows-desktop\build-release-candidate.ps1'
$bundle = Join-Path $repo 'dist\DairyOS-Release\DairyOS'
$desktopRoot = Join-Path ([Environment]::GetFolderPath('Desktop')) 'DairyOS-Release-Candidate'
$desktopBundle = Join-Path $desktopRoot 'dist\DairyOS'
$iss = Join-Path $repo 'tools\windows-desktop\DairyOS-Installer.iss'

if (-not (Test-Path $portableBuild)) {
    throw "Release-candidate build script missing: $portableBuild"
}

# Support both Inno Setup 6 and 7. The compiler executable is stable across
# major versions; do not require a particular installed major version.
$isccCandidates = @(
    "$env:ProgramFiles\Inno Setup 7\ISCC.exe",
    "$env:ProgramFiles(x86)\Inno Setup 7\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe"
)

$iscc = $isccCandidates |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1

if (-not $iscc) {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        $iscc = $command.Source
    }
}

if (-not $iscc) {
    throw 'Inno Setup ISCC.exe was not found. Install a supported Inno Setup release (6.x or 7.x) before creating the Windows installer.'
}

Write-Host "Using Inno Setup compiler: $iscc"

Write-Host '=== BUILDING FRESH RELEASE-CANDIDATE BUNDLE ==='
& $portableBuild
if ($LASTEXITCODE -ne 0) {
    throw "Release-candidate bundle build failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path $bundle)) { throw "Release bundle missing: $bundle" }
if (-not (Test-Path (Join-Path $bundle 'DairyOS.exe'))) { throw 'DairyOS.exe missing from release bundle.' }

Write-Host '=== STAGING FINAL RC ON DESKTOP ==='
Remove-Item $desktopRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $desktopBundle -Force | Out-Null

robocopy $bundle $desktopBundle /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -gt 7) { throw "Failed to copy release bundle to Desktop (robocopy exit $LASTEXITCODE)." }

Write-Host '=== BUILDING WINDOWS INSTALLER ==='
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
Write-Host ''
Write-Host '=== DESKTOP RELEASE CONTENTS ==='
Get-ChildItem $desktopRoot -Force | Select-Object Name,Mode,Length,LastWriteTime
