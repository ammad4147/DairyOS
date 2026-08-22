[CmdletBinding()]
param(
    [string]$Repo = (Get-Location).Path,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo
$expectedBranch = 'feat/milk-reconciliation-crud-2026-08-22'

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS — MILK RECONCILIATION + CRUD VALIDATION' -ForegroundColor Cyan
Write-Host 'MAIN IS NOT MODIFIED BY THIS SCRIPT' -ForegroundColor Yellow
Write-Host '============================================================' -ForegroundColor Cyan

$branch = (git branch --show-current).Trim()
if ($branch -ne $expectedBranch) { throw "Expected branch $expectedBranch but found '$branch'." }

git diff --check
if ($LASTEXITCODE -ne 0) { throw 'git diff --check failed.' }

Write-Host "`n[1/3] Milk/API regression tests" -ForegroundColor Cyan
if (Test-Path '.venv\Scripts\python.exe') {
    & .venv\Scripts\python.exe -m pytest -q tests/api/test_milk_reconciliation_crud.py
} else {
    & python -m pytest -q tests/api/test_milk_reconciliation_crud.py
}
if ($LASTEXITCODE -ne 0) { throw 'Milk regression tests failed.' }

if (-not $SkipFrontendBuild) {
    Write-Host "`n[2/3] React/Vite production build" -ForegroundColor Cyan
    Push-Location 'src\DairyOS.Web'
    npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'Frontend build failed.' }
    Pop-Location
} else {
    Write-Host "`n[2/3] Frontend build skipped" -ForegroundColor Yellow
}

Write-Host "`n[3/3] Git status" -ForegroundColor Cyan
git status --short
Write-Host "Milk validation completed successfully." -ForegroundColor Green
