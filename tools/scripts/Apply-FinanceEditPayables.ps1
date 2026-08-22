$ErrorActionPreference = 'Stop'
Write-Host '============================================================'
Write-Host 'DAIRYOS — APPLY FINANCE EDIT/PAYABLES BRANCH LOCALLY'
Write-Host 'THIS SCRIPT NEVER CHECKS OUT OR MODIFIES MAIN'
Write-Host '============================================================'

$Root = (Get-Location).Path
if (-not (Test-Path (Join-Path $Root '.git'))) { throw "Not a Git repository: $Root" }

$branch = 'feat/finance-edit-payables-2026-08-23'
Write-Host "Repository: $Root"
Write-Host '[1/4] Protect uncommitted work'
if ((git status --porcelain)) { throw 'Working tree is not clean. Commit or stash local work before applying this branch.' }

Write-Host '[2/4] Fetch approved branch'
git fetch origin $branch

Write-Host '[3/4] Checkout approved branch'
$current = git branch --show-current
if ($current -ne $branch) { git checkout $branch }
git pull --ff-only origin $branch

Write-Host '[4/4] Run validation runner'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools/scripts/Validate-FinanceEditPayables.ps1')

if ($LASTEXITCODE -ne 0) { throw "Finance Edit/Payables validation failed with exit code $LASTEXITCODE." }
Write-Host ''
Write-Host 'Finance Edit/Payables branch is ready locally.' -ForegroundColor Green
Write-Host 'main was not checked out or modified by this script.'