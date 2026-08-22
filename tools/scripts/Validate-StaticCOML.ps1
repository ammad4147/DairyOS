$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '../..')

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS - STATIC MONTHLY COML VALIDATION' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

Write-Host "`n[1/5] Git integrity" -ForegroundColor Yellow
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'git diff --check failed.' }

Write-Host "`n[2/5] COML API tests" -ForegroundColor Yellow
pytest -q tests/api/test_coml.py
if ($LASTEXITCODE -ne 0) { throw 'COML API tests failed.' }

Write-Host "`n[3/5] Legacy frontend wiring audit" -ForegroundColor Yellow
$forbidden = @(
  'onUpdateFeedCost',
  'dairyos_tmr_data',
  'Live Farm Sync',
  'Manual Override',
  'currentView === ''cmpl''',
  'id: ''cmpl''',
  'label: ''CMPL''',
  'components/CMPL',
  'realTimeDailyFeedCost'
)
$frontend = git grep -n -i -- 'src/DairyOS.Web' 2>$null
foreach ($term in $forbidden) {
  $matches = git grep -n -i -- "$term" -- src/DairyOS.Web 2>$null
  if ($matches) {
    Write-Host "Forbidden legacy reference: $term" -ForegroundColor Red
    Write-Host $matches
    throw "Static COML audit failed for '$term'."
  }
}
if (Test-Path 'src/DairyOS.Web/src/components/CMPL.tsx') {
  throw 'Legacy CMPL.tsx still exists.'
}

Write-Host "`n[4/5] Frontend acceptance" -ForegroundColor Yellow
Set-Location src/DairyOS.Web
npm run typecheck
if ($LASTEXITCODE -ne 0) { throw 'Frontend typecheck failed.' }
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
Set-Location ../..

Write-Host "`n[5/5] Final status" -ForegroundColor Green
git status --short
Write-Host 'Static monthly COML validation completed successfully.' -ForegroundColor Green
