[CmdletBinding()]
param(
    [string]$Repo = 'D:\DairyOS',
    [switch]$AllowDirtyWorkingTree,
    [switch]$SkipValidation
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS — APPLY FINANCE FEED/OPEX BRANCH LOCALLY' -ForegroundColor Cyan
Write-Host 'THIS SCRIPT NEVER CHECKS OUT OR MODIFIES MAIN' -ForegroundColor Yellow
Write-Host '============================================================' -ForegroundColor Cyan

$remoteBranch = 'origin/finance/feed-opex-2026-08-22'
$localBranch = 'finance/feed-opex-2026-08-22'

Write-Host "`n[1/5] Verify Git repository" -ForegroundColor Cyan
$root = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Not a Git repository.' }
Set-Location $root

Write-Host "Repository: $root"

Write-Host "`n[2/5] Protect uncommitted work" -ForegroundColor Cyan
$dirty = @(git status --porcelain)
if ($dirty.Count -gt 0 -and -not $AllowDirtyWorkingTree) {
    Write-Host 'Working tree is dirty:' -ForegroundColor Yellow
    $dirty | ForEach-Object { Write-Host $_ }
    throw 'Refusing to switch branches with uncommitted changes. Commit/stash them or rerun with -AllowDirtyWorkingTree.'
}

Write-Host "`n[3/5] Fetch approved implementation branch" -ForegroundColor Cyan
git fetch origin $localBranch
if ($LASTEXITCODE -ne 0) { throw 'Unable to fetch the Finance Feed/OPEX branch.' }

$current = (git branch --show-current).Trim()
if ($current -ne $localBranch) {
    $exists = git show-ref --verify --quiet "refs/heads/$localBranch"
    if ($LASTEXITCODE -eq 0) {
        git switch $localBranch
    } else {
        git switch --track $remoteBranch
    }
    if ($LASTEXITCODE -ne 0) { throw 'Unable to switch to the Finance Feed/OPEX branch.' }
} else {
    git pull --ff-only origin $localBranch
    if ($LASTEXITCODE -ne 0) { throw 'Unable to fast-forward the Finance Feed/OPEX branch.' }
}

Write-Host "`n[4/5] Verify branch and recent commit" -ForegroundColor Cyan
git branch --show-current
git log -1 --oneline

if (-not $SkipValidation) {
    Write-Host "`n[5/5] Run Finance Feed/OPEX validation" -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\tools\scripts\Validate-FinanceFeedOpex.ps1' -Repo $root
    if ($LASTEXITCODE -ne 0) { throw 'Validation failed.' }
} else {
    Write-Host "`n[5/5] Validation skipped by request" -ForegroundColor Yellow
}

Write-Host "`nFinance Feed/OPEX branch is ready locally." -ForegroundColor Green
Write-Host 'Main has not been checked out or modified by this script.' -ForegroundColor Green
