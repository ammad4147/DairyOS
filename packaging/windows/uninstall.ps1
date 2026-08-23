param(
    [Parameter(Mandatory = $true)][string]$AppDir,
    [Parameter(Mandatory = $true)][string]$DataDir
)
$ErrorActionPreference = 'Stop'
$script = Join-Path $DataDir 'recovery\backup-before-uninstall.ps1'
if (-not (Test-Path $script)) { throw 'DairyOS recovery/backup script is missing. Uninstall aborted.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -AppDir $AppDir -DataDir $DataDir
if ($LASTEXITCODE -ne 0) { throw 'DairyOS final backup failed. Uninstall aborted.' }
Write-Host 'Farm data preserved under ProgramData; application uninstall may proceed.'
