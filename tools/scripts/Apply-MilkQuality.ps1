$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'DAIRYOS — APPLY MILK QUALITY BRANCH LOCALLY' -ForegroundColor Cyan
Write-Host 'MAIN IS NOT MODIFIED BY THIS SCRIPT' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

$Root = 'D:\DairyOS'
$Branch = 'feat/milk-quality-2026-08-23'

if (-not (Test-Path $Root)) {
    throw "DairyOS repository was not found at $Root"
}

Set-Location $Root

Write-Host "`n[1/5] Verify Git repository" -ForegroundColor Yellow
git rev-parse --show-toplevel | Out-Host

Write-Host "`n[2/5] Protect uncommitted work" -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host 'Uncommitted work detected. No checkout performed.' -ForegroundColor Red
    $status
    throw 'Commit/stash local work before applying the approved branch.'
}

Write-Host "`n[3/5] Fetch approved Milk Quality branch" -ForegroundColor Yellow
git fetch origin $Branch
git switch --track "origin/$Branch"

Write-Host "`n[4/5] Verify branch and commit" -ForegroundColor Yellow
git branch --show-current
git log -1 --oneline

Write-Host "`n[5/5] Run Milk Quality validation" -ForegroundColor Yellow
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\tools\scripts\Validate-MilkQuality.ps1'

Write-Host "`nMilk Quality branch is ready locally." -ForegroundColor Green
Write-Host 'Main was not checked out or modified by this script.' -ForegroundColor Green
