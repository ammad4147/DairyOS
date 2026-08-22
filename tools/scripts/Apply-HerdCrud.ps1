[CmdletBinding()]
param(
    [string]$Repo = 'D:\DairyOS',
    [switch]$AllowDirtyWorkingTree,
    [switch]$SkipValidation
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS — APPLY HERD CRUD BRANCH LOCALLY' -ForegroundColor Cyan
Write-Host 'THIS SCRIPT NEVER CHECKS OUT OR MODIFIES MAIN' -ForegroundColor Yellow
Write-Host '============================================================' -ForegroundColor Cyan

$branch = 'feat/herd-crud-2026-08-23'
$remoteBranch = "origin/$branch"

$root = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Not a Git repository.' }
Set-Location $root

$dirty = @(git status --porcelain)
if ($dirty.Count -gt 0 -and -not $AllowDirtyWorkingTree) {
    $dirty | ForEach-Object { Write-Host $_ }
    throw 'Working tree is dirty. Commit/stash changes or rerun with -AllowDirtyWorkingTree.'
}

git fetch origin $branch
if ($LASTEXITCODE -ne 0) { throw 'Unable to fetch Herd CRUD branch.' }

$current = (git branch --show-current).Trim()
if ($current -ne $branch) {
    $exists = git show-ref --verify --quiet "refs/heads/$branch"
    if ($LASTEXITCODE -eq 0) {
        git switch $branch
    } else {
        git switch --track $remoteBranch
    }
    if ($LASTEXITCODE -ne 0) { throw 'Unable to switch to Herd CRUD branch.' }
} else {
    git pull --ff-only origin $branch
    if ($LASTEXITCODE -ne 0) { throw 'Unable to fast-forward Herd CRUD branch.' }
}

git branch --show-current
git log -1 --oneline

if (-not $SkipValidation) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\tools\scripts\Validate-HerdCrud.ps1' -Repo $root
    if ($LASTEXITCODE -ne 0) { throw 'Herd CRUD validation failed.' }
}

Write-Host 'Herd CRUD branch is ready locally.' -ForegroundColor Green
