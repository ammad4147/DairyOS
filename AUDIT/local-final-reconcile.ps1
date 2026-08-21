#requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-Location D:\DairyOS

Write-Host "`n=== FINAL MAIN RECONCILIATION ===" -ForegroundColor Cyan
git fetch origin
$remote = (git rev-parse origin/main).Trim()
Write-Host "origin/main : $remote"
if ((git branch --show-current).Trim() -ne "main") { git switch main }
if ((git status --porcelain)) { git status --short }

git reset --hard origin/main
if ($LASTEXITCODE -ne 0) { throw "git reset --hard origin/main failed." }
git clean -fd
if ($LASTEXITCODE -ne 0) { throw "git clean -fd failed." }
git fetch origin

$head = (git rev-parse HEAD).Trim()
$remote2 = (git rev-parse origin/main).Trim()
$status = git status --porcelain
if ($head -ne $remote2) { throw "HEAD does not equal origin/main." }
if ($status) { throw "Working tree is not clean." }
if ((git branch --show-current).Trim() -ne "main") { throw "Branch is not main." }

Write-Host "`nHEAD        : $head" -ForegroundColor Green
Write-Host "origin/main : $remote2" -ForegroundColor Green
Write-Host "Branch      : main" -ForegroundColor Green
Write-Host "Status      : CLEAN" -ForegroundColor Green
Write-Host "`nFINAL RECONCILIATION PASSED" -ForegroundColor Green
