$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS — MILK QUALITY VALIDATION' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

$Root = (Get-Location).Path
if (-not (Test-Path (Join-Path $Root 'pyproject.toml'))) {
    throw "Run this validator from the DairyOS repository root. Current path: $Root"
}

Write-Host "`n[1/4] Git integrity" -ForegroundColor Yellow
git status --short
git branch --show-current
git log -1 --oneline

Write-Host "`n[2/4] Milk quality tests" -ForegroundColor Yellow
pytest -q tests/api/test_milk_quality.py

Write-Host "`n[3/4] Full Python regression" -ForegroundColor Yellow
pytest -q

$Web = Join-Path $Root 'src\DairyOS.Web'
if (Test-Path (Join-Path $Web 'package.json')) {
    Write-Host "`n[4/4] React/Vite production build" -ForegroundColor Yellow
    Push-Location $Web
    try {
        npm run build
    }
    finally {
        Pop-Location
    }
} else {
    Write-Warning 'Frontend package.json not found; frontend build skipped.'
}

Write-Host "`nValidation completed successfully." -ForegroundColor Green
