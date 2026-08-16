$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

Write-Host '=== DairyOS backend validation gate ==='
Write-Host 'Working directory:' (Get-Location)

if (-not (Test-Path '.\src\dairyos')) { throw 'Run this script from D:\DairyOS.' }

$env:PYTHONPATH = (Join-Path (Get-Location) 'src')

Write-Host '[1/3] Python compileall'
python -m compileall -q src
if ($LASTEXITCODE -ne 0) { throw 'compileall failed.' }

Write-Host '[2/3] Backend tests'
if (Test-Path '.\tests') {
    python -m pytest -q tests
    if ($LASTEXITCODE -ne 0) { throw 'pytest failed.' }
} else {
    Write-Host 'No tests directory present; compile gate passed.'
}

Write-Host '[3/3] Git state'
git status --short --branch

Write-Host '=== Backend validation gate complete ==='
