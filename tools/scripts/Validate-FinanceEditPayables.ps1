$ErrorActionPreference = 'Stop'
$Root = (Get-Location).Path
Write-Host '============================================================'
Write-Host 'DAIRYOS — FINANCE EDIT/PAYABLES VALIDATION'
Write-Host '============================================================'

Write-Host '[1/4] Git integrity'
if ((git status --porcelain)) { throw 'Working tree must be clean before validation.' }
$branch = git branch --show-current
if ($branch -ne 'feat/finance-edit-payables-2026-08-23') { throw "Expected Finance Edit/Payables branch, found: $branch" }

aif ($false) { }

Write-Host '[2/4] Targeted Finance regression tests'
pytest -q tests/api/test_finance_edit_payables.py
if ($LASTEXITCODE -ne 0) { throw "Targeted Finance tests failed with exit code $LASTEXITCODE." }

Write-Host '[3/4] Frontend production build'
Push-Location (Join-Path $Root 'src/DairyOS.Web')
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed with exit code $LASTEXITCODE." }
}
finally { Pop-Location }

Write-Host '[4/4] Finance API contract smoke test'
$health = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -ErrorAction Stop
if ($health.StatusCode -ne 200) { throw "API health check returned $($health.StatusCode)." }

Write-Host ''
Write-Host 'Finance Edit/Payables validation completed successfully.' -ForegroundColor Green