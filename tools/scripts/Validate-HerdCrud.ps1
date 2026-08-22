[CmdletBinding()]
param(
    [string]$Repo = (Get-Location).Path,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS — HERD CRUD VALIDATION' -ForegroundColor Cyan
Write-Host 'MAIN IS NOT MODIFIED BY THIS SCRIPT' -ForegroundColor Yellow
Write-Host '============================================================' -ForegroundColor Cyan

$branch = (git branch --show-current).Trim()
if ($branch -ne 'feat/herd-crud-2026-08-23') {
    throw "Expected branch feat/herd-crud-2026-08-23 but found '$branch'."
}

git diff --check
if ($LASTEXITCODE -ne 0) { throw 'git diff --check failed.' }

if (Test-Path '.venv\Scripts\python.exe') {
    & .venv\Scripts\python.exe -m pytest -q tests/api/test_animal_crud.py tests/api/test_animal_registration.py tests/api/test_animal_management.py
} else {
    & python -m pytest -q tests/api/test_animal_crud.py tests/api/test_animal_registration.py tests/api/test_animal_management.py
}
if ($LASTEXITCODE -ne 0) { throw 'Herd API regression tests failed.' }

if (-not $SkipFrontendBuild) {
    Push-Location 'src\DairyOS.Web'
    npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'Frontend build failed.' }
    Pop-Location
}

Write-Host 'Herd CRUD validation completed successfully.' -ForegroundColor Green
