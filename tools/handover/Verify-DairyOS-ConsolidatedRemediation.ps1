#requires -Version 7.0
[CmdletBinding()]
param([string]$Repo = 'D:\DairyOS',[Parameter(Mandatory=$true)][string]$ExpectedSha)
$ErrorActionPreference = 'Stop'
Set-Location $Repo
$Head = (git rev-parse HEAD).Trim()
$Remote = (git rev-parse origin/main).Trim()
if ($Head -ne $ExpectedSha -or $Remote -ne $ExpectedSha) { throw "Exact-SHA gate failed. HEAD=$Head origin/main=$Remote expected=$ExpectedSha" }
if (@(git status --porcelain).Count -gt 0) { throw 'Worktree is not clean. STOP.' }
Write-Host '=== TARGETED REMEDIATION REGRESSION ==='
python -m pytest -q tests/remediation/test_consolidated_remediation.py tests/remediation/test_forensic_integrity.py tests/api/test_health_case.py tests/api/test_coml.py tests/api/test_coml_operational_date_authority.py tests/api/test_treatment_withdrawal_api.py tests/milk/test_withdrawal_milk_wastage_service.py
if ($LASTEXITCODE -ne 0) { throw 'Targeted remediation regression failed.' }
Write-Host '=== FULL REGRESSION ==='
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Full regression failed.' }
Write-Host ''
Write-Host 'LOCAL REMEDIATION VERIFICATION: PASS'
Write-Host "TESTED SHA: $Head"