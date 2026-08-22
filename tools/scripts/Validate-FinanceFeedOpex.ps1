[CmdletBinding()]
param(
    [string]$Repo = (Get-Location).Path,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS — FINANCE FEED/OPEX VALIDATION' -ForegroundColor Cyan
Write-Host 'MAIN IS NOT MODIFIED BY THIS SCRIPT' -ForegroundColor Yellow
Write-Host '============================================================' -ForegroundColor Cyan

$branch = (git branch --show-current).Trim()
if ($branch -ne 'finance/feed-opex-2026-08-22') {
    throw "Expected branch finance/feed-opex-2026-08-22 but found '$branch'."
}

Write-Host "`n[1/4] Git integrity" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'git diff --check failed.' }

git status --short

Write-Host "`n[2/4] Finance/backend regression tests" -ForegroundColor Cyan
if (Test-Path '.venv\Scripts\python.exe') {
    & .venv\Scripts\python.exe -m pytest -q `
        tests/api/test_finance_feed_opex.py `
        tests/api/test_finance_transaction_integrity.py `
        tests/api/test_cost_of_production.py
} else {
    & python -m pytest -q `
        tests/api/test_finance_feed_opex.py `
        tests/api/test_finance_transaction_integrity.py `
        tests/api/test_cost_of_production.py
}
if ($LASTEXITCODE -ne 0) { throw 'Finance/backend regression tests failed.' }

if (-not $SkipFrontendBuild) {
    Write-Host "`n[3/4] React/Vite production build" -ForegroundColor Cyan
    Push-Location 'src\DairyOS.Web'
    npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'Frontend build failed.' }
    Pop-Location
} else {
    Write-Host "`n[3/4] Frontend build skipped by request" -ForegroundColor Yellow
}

Write-Host "`n[4/4] Final status" -ForegroundColor Cyan
git status --short
Write-Host "`nValidation completed successfully." -ForegroundColor Green
