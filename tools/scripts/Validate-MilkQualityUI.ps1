$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '../..')

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS - MILK QUALITY UI VALIDATION' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

Write-Host "`n[1/4] Git integrity" -ForegroundColor Yellow
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'git diff --check failed.' }

Write-Host "`n[2/4] Milk quality backend tests" -ForegroundColor Yellow
pytest -q tests/api/test_milk_quality.py
if ($LASTEXITCODE -ne 0) { throw 'Milk quality backend tests failed.' }

Write-Host "`n[3/4] Frontend typecheck/build" -ForegroundColor Yellow
Set-Location src/DairyOS.Web
npm run typecheck
if ($LASTEXITCODE -ne 0) { throw 'Frontend typecheck failed.' }
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }

Write-Host "`n[4/4] Final status" -ForegroundColor Green
git status --short
Write-Host 'Milk Quality UI validation completed successfully.' -ForegroundColor Green
