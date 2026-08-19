Set-Location (Join-Path $PSScriptRoot "..\..")
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PWD\src"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DAIRYOS LIFETIME-BIOLOGICAL ANIMAL PASSPORT VALIDATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`n=== 1. REPOSITORY ===" -ForegroundColor Yellow
Write-Host "Branch: $(git branch --show-current)"
Write-Host "HEAD:   $(git rev-parse HEAD)"

git status --short
if ($LASTEXITCODE -ne 0) {
    throw "git status failed"
}

Write-Host "`n=== 2. PYTHON COMPILE ===" -ForegroundColor Yellow
python -m compileall -q src tests
if ($LASTEXITCODE -ne 0) {
    throw "Python compilation failed"
}

Write-Host "`n=== 3. ANIMAL PASSPORT REGRESSION SUITE ===" -ForegroundColor Yellow
pytest -q tests/api/test_animal_passport.py
$pytestExit = $LASTEXITCODE

Write-Host "`nPytest exit code: $pytestExit"
if ($pytestExit -ne 0) {
    throw "Animal Passport regression suite failed"
}

Write-Host "`n=== 4. FULL REGRESSION (OPTIONAL LONG GATE) ===" -ForegroundColor Yellow
Write-Host "Run manually with: pytest -q"

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host " VALIDATION PASSED: lifetime-biological Animal Passport" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
