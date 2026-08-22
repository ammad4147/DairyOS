$ErrorActionPreference = 'Stop'
$Root = (Get-Location).Path
Write-Host '============================================================'
Write-Host 'DAIRYOS — FINANCE EDIT/PAYABLES VALIDATION'
Write-Host '============================================================'

Write-Host '[1/3] Git integrity'
if ((git status --porcelain)) { throw 'Working tree must be clean before validation.' }
$branch = git branch --show-current
if ($branch -ne 'feat/finance-edit-payables-2026-08-23') { throw "Expected Finance Edit/Payables branch, found: $branch" }

Write-Host '[2/3] Targeted Finance regression tests'
pytest -q tests/api/test_finance_edit_payables.py
if ($LASTEXITCODE -ne 0) { throw "Targeted Finance tests failed with exit code $LASTEXITCODE." }

Write-Host '[3/3] Frontend production build'
Push-Location (Join-Path $Root 'src/DairyOS.Web')
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed with exit code $LASTEXITCODE." }
}
finally { Pop-Location }

Write-Host ''
Write-Host 'Finance Edit/Payables validation completed successfully.' -ForegroundColor Green