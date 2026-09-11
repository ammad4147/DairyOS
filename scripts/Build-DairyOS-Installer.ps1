[CmdletBinding()]
param(
    [string]$Bundle = "dist\DairyOS-Release\DairyOS",
    [string]$Output = "dist\DairyOS-Release\DairyOS-Windows-Installer.exe"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo

$bundlePath = [IO.Path]::GetFullPath((Join-Path $repo $Bundle))
$outputPath = [IO.Path]::GetFullPath((Join-Path $repo $Output))
$iss = Join-Path $repo "tools\windows-desktop\DairyOS-Installer.iss"
$bundleParentPath = [IO.Path]::GetFullPath((Split-Path -Parent $bundlePath))
$outputParentPath = [IO.Path]::GetFullPath((Split-Path -Parent $outputPath))

if (-not [string]::Equals($bundleParentPath, $outputParentPath, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Installer layout must place the setup executable beside the DairyOS application folder. Bundle parent=$bundleParentPath; installer parent=$outputParentPath"
}

if (-not (Test-Path (Join-Path $bundlePath "DairyOS.exe") -PathType Leaf)) { throw "Certified desktop bundle is missing DairyOS.exe: $bundlePath" }
if (-not (Test-Path (Join-Path $bundlePath "DairyOSBackup.exe") -PathType Leaf)) { throw "Certified desktop bundle is missing DairyOSBackup.exe: $bundlePath" }
$releaseManifestPath = Join-Path $bundlePath "release-manifest.json"
if (-not (Test-Path $releaseManifestPath -PathType Leaf)) { throw "Certified desktop bundle is missing release-manifest.json: $releaseManifestPath" }
$releaseManifest = Get-Content $releaseManifestPath -Raw | ConvertFrom-Json
if ([string]$releaseManifest.source_commit -notmatch '^[0-9a-f]{40}$') { throw "Desktop release manifest has no exact source commit." }
if ([string]$releaseManifest.source_tree -notmatch '^[0-9a-f]{40}$') { throw "Desktop release manifest has no exact source tree." }

Write-Host "Protected Settings controls and the embedded Assistant are the supported operator guidance surfaces." -ForegroundColor DarkGray
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

Remove-Item $outputPath -Force -ErrorAction SilentlyContinue

Write-Host "=== BUILD WINDOWS INSTALLER ===" -ForegroundColor Cyan
$isccArgs = @(
    "/O" + (Split-Path -Parent $outputPath),
    "/DSourceCommit=$($releaseManifest.source_commit)",
    "/DSourceTree=$($releaseManifest.source_tree)",
    $iss
)
& $iscc @isccArgs
if ($LASTEXITCODE -ne 0) { throw "Inno Setup build failed with exit code $LASTEXITCODE." }
if (-not (Test-Path $outputPath -PathType Leaf)) { throw "Installer was not produced: $outputPath" }

$installerHash = (Get-FileHash $outputPath -Algorithm SHA256).Hash.ToLowerInvariant()
$artifactManifest = [ordered]@{
    manifest_version = 1
    source_commit = [string]$releaseManifest.source_commit
    source_tree = [string]$releaseManifest.source_tree
    desktop_exe_sha256 = [string]$releaseManifest.desktop_exe_sha256
    backup_exe_sha256 = [string]$releaseManifest.backup_exe_sha256
    installer_sha256 = $installerHash
    postgresql_version = [string]$releaseManifest.postgresql_version
    frontend_index_sha256 = [string]$releaseManifest.frontend_index_sha256
    schema_migration_files = @($releaseManifest.schema_migration_files)
    build_timestamp_utc = [string]$releaseManifest.build_timestamp_utc
    installer_built_at_utc = (Get-Date).ToUniversalTime().ToString("o")
}
$artifactManifestPath = Join-Path (Split-Path -Parent $outputPath) "DairyOS-Windows-Installer.release.json"
$artifactManifest | ConvertTo-Json -Depth 5 | Set-Content -Path $artifactManifestPath -Encoding utf8
if (-not (Test-Path $artifactManifestPath -PathType Leaf)) { throw "Installer release manifest was not created." }

Write-Host ""
Write-Host "DAIRYOS WINDOWS INSTALLER BUILD: PASS" -ForegroundColor Green
Get-Item $outputPath | Select-Object FullName,Length
Get-FileHash $outputPath -Algorithm SHA256
Write-Host "Release manifest: $artifactManifestPath"
exit 0
