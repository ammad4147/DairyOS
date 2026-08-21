#requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-Location D:\DairyOS

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$report = Join-Path "D:\DairyOS\.dairyo-reconciliation" "closing-audit-$stamp"
New-Item -ItemType Directory -Force -Path $report | Out-Null

Write-Host "`n=== AUTHORITATIVE MAIN ===" -ForegroundColor Cyan
git fetch origin
$remote = (git rev-parse origin/main).Trim()
$local = (git rev-parse HEAD).Trim()
Write-Host "origin/main : $remote"
Write-Host "HEAD        : $local"
if ((git branch --show-current).Trim() -ne "main") { throw "Local branch is not main." }

Write-Host "`n=== WORKTREE ===" -ForegroundColor Cyan
git status --short | Tee-Object (Join-Path $report "status.txt")
git diff --stat HEAD origin/main | Tee-Object (Join-Path $report "divergence.txt")

Write-Host "`n=== PYTHON ENVIRONMENT ===" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" --version
& ".\.venv\Scripts\python.exe" -c "import sys; print('Executable:',sys.executable); print('Prefix:',sys.prefix); print('Base prefix:',sys.base_prefix); print('Isolated:',sys.prefix != sys.base_prefix)"
& ".\.venv\Scripts\python.exe" -m pytest --version

Write-Host "`n=== FULL REGRESSION ===" -ForegroundColor Cyan
$env:PYTHONPATH = "$PWD\src"
& ".\.venv\Scripts\python.exe" -m pytest -q 2>&1 | Tee-Object (Join-Path $report "pytest-full.txt")
if ($LASTEXITCODE -ne 0) { throw "Full regression failed." }

Write-Host "`n=== PLATFORM DISTRIBUTION CONTRACT ===" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pytest tests/platform/test_os_distribution_artifacts.py -q 2>&1 | Tee-Object (Join-Path $report "platform.txt")
if ($LASTEXITCODE -ne 0) { throw "Platform contract failed." }

Write-Host "`n=== FRONTEND ===" -ForegroundColor Cyan
Push-Location "src\DairyOS.Web"
npm ci 2>&1 | Tee-Object (Join-Path $report "npm-ci.txt")
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "npm ci failed." }
npm run typecheck 2>&1 | Tee-Object (Join-Path $report "typecheck.txt")
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Frontend typecheck failed." }
npm run build 2>&1 | Tee-Object (Join-Path $report "build.txt")
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { throw "Frontend build failed." }

Write-Host "`n=== FINAL AUDIT RESULT ===" -ForegroundColor Green
@"
Remote main: $remote
Local HEAD: $local
Report: $report
Python regression: PASS
Platform distribution contract: PASS
Frontend typecheck: PASS
Frontend build: PASS
No target disk touched.
No installer executed.
"@ | Tee-Object (Join-Path $report "FINAL.txt")
Write-Host "REPORT: $report" -ForegroundColor Green
