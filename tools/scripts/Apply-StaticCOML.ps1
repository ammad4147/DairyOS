$ErrorActionPreference = 'Stop'

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS - APPLY STATIC MONTHLY COML BRANCH LOCALLY' -ForegroundColor Cyan
Write-Host 'THIS SCRIPT NEVER CHECKS OUT OR MODIFIES MAIN DIRECTLY' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

$repo = (Get-Location).Path
$origin = git remote get-url origin
if (-not $origin) { throw 'No origin remote is configured.' }

Write-Host "`n[1/5] Verify Git repository" -ForegroundColor Yellow
if (-not (Test-Path '.git')) { throw "Not a Git repository: $repo" }
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Working tree has whitespace errors.' }

Write-Host "`n[2/5] Protect current local branch" -ForegroundColor Yellow
$currentBranch = git branch --show-current
if (-not $currentBranch) { throw 'Detached HEAD is not supported by this runner.' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = "backup-before-static-coml-$stamp"
git branch $backup
Write-Host "Recovery branch: $backup" -ForegroundColor Green

Write-Host "`n[3/5] Fetch approved branch" -ForegroundColor Yellow
git fetch origin --prune
git switch -C feat/static-coml-monthly-2026-08-23 origin/feat/static-coml-monthly-2026-08-23

Write-Host "`n[4/5] Validate" -ForegroundColor Yellow
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\tools\scripts\Validate-StaticCOML.ps1'
if ($LASTEXITCODE -ne 0) { throw 'Static COML validation failed.' }

Write-Host "`n[5/5] Final status" -ForegroundColor Green
git status --short
git branch --show-current
git rev-parse HEAD
Write-Host '`nStatic monthly COML branch is ready locally. Main was not checked out or modified by this script.' -ForegroundColor Green
