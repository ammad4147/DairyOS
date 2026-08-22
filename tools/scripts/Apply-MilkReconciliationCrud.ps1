[CmdletBinding()]
param(
    [string]$Repo = 'D:\DairyOS',
    [switch]$AllowDirtyWorkingTree,
    [switch]$SkipValidation
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo
$branch = 'feat/milk-reconciliation-crud-2026-08-22'

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS — APPLY MILK RECONCILIATION + CRUD' -ForegroundColor Cyan
Write-Host 'MAIN IS NOT MODIFIED BY THIS SCRIPT' -ForegroundColor Yellow
Write-Host '============================================================' -ForegroundColor Cyan

$root = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Not a Git repository.' }
Set-Location $root

$dirty = @(git status --porcelain)
if ($dirty.Count -gt 0 -and -not $AllowDirtyWorkingTree) {
    $dirty | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
    throw 'Working tree is dirty. Commit/stash changes or use -AllowDirtyWorkingTree.'
}

git fetch origin $branch
if ($LASTEXITCODE -ne 0) { throw 'Unable to fetch Milk implementation branch.' }

$current = (git branch --show-current).Trim()
if ($current -ne $branch) {
    git switch $branch
    if ($LASTEXITCODE -ne 0) { throw 'Unable to switch to Milk implementation branch.' }
} else {
    git pull --ff-only origin $branch
    if ($LASTEXITCODE -ne 0) { throw 'Unable to fast-forward Milk implementation branch.' }
}

git branch --show-current
git log -1 --oneline

if (-not $SkipValidation) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\tools\scripts\Validate-MilkReconciliationCrud.ps1' -Repo $root
    if ($LASTEXITCODE -ne 0) { throw 'Milk validation failed.' }
}

Write-Host 'Milk reconciliation + CRUD branch is ready locally.' -ForegroundColor Green
Write-Host 'main has not been checked out or modified by this script.' -ForegroundColor Green
