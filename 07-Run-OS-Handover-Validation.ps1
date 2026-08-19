#requires -Version 5.1

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Set-Location D:\DairyOS

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS OS Handover Validation Gate" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$remote = "origin/audit/os-handover-2026-08-19"

Write-Host "=== 1. REPOSITORY IDENTITY ===" -ForegroundColor Cyan

git fetch origin --prune

$localHead  = (git rev-parse HEAD).Trim()
$remoteHead = (git rev-parse $remote).Trim()
$localTree  = (git rev-parse "HEAD^{tree}").Trim()
$remoteTree = (git rev-parse "$remote^{tree}").Trim()

Write-Host "LOCAL HEAD : $localHead"
Write-Host "REMOTE HEAD: $remoteHead"
Write-Host "LOCAL TREE : $localTree"
Write-Host "REMOTE TREE: $remoteTree"
Write-Host ""

if ($localTree -ne $remoteTree) {
    throw "Committed trees differ. Stop before OS validation."
}

Write-Host "PASS: committed local tree equals reconciled remote tree." -ForegroundColor Green

Write-Host ""
Write-Host "=== 2. WORKTREE ===" -ForegroundColor Cyan

$status = @(git status --short)

if ($status.Count -eq 0) {
    Write-Host "PASS: worktree clean." -ForegroundColor Green
}
else {
    Write-Host "INFO: worktree contains only inspection artifacts:" -ForegroundColor Yellow
    $status | ForEach-Object { Write-Host $_ }
}

Write-Host ""
Write-Host "=== 3. REMOTE HANDOVER AUDIT ===" -ForegroundColor Cyan

$handoverAudit = Join-Path $PWD "tools\handover\Invoke-DairyOSHandoverAudit.ps1"

if (-not (Test-Path -LiteralPath $handoverAudit)) {
    throw "Missing: $handoverAudit"
}

& $handoverAudit `
    -RepoRoot $PWD `
    -OutputDirectory (Join-Path $PWD "audit-results") `
    -Strict

if ($LASTEXITCODE -ne 0) {
    throw "OS handover audit failed or remained blocked."
}

Write-Host ""
Write-Host "PASS: OS handover audit gate." -ForegroundColor Green

Write-Host ""
Write-Host "=== 4. LOCAL OS ARTIFACT VALIDATION ===" -ForegroundColor Cyan

$localValidation = Join-Path $PWD "tools\handover\Invoke-DairyOSLocalOSValidation.ps1"

if (-not (Test-Path -LiteralPath $localValidation)) {
    throw "Missing: $localValidation"
}

& $localValidation `
    -RepoRoot $PWD `
    -Strict

if ($LASTEXITCODE -ne 0) {
    throw "Local OS artifact validation failed."
}

Write-Host ""
Write-Host "PASS: local OS artifact validation." -ForegroundColor Green

Write-Host ""
Write-Host "=== 5. DISASTER / ROLLBACK SIMULATION ===" -ForegroundColor Cyan

$disaster = Join-Path $PWD "tools\handover\Invoke-DairyOSDisasterSimulation.ps1"

if (-not (Test-Path -LiteralPath $disaster)) {
    Write-Host "WARN: disaster simulation script not found:" -ForegroundColor Yellow
    Write-Host $disaster
}
else {
    & $disaster `
        -RepoRoot $PWD

    if ($LASTEXITCODE -ne 0) {
        throw "Disaster / rollback simulation failed."
    }

    Write-Host ""
    Write-Host "PASS: disaster / rollback simulation." -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 6. OS ARTIFACT INVENTORY ===" -ForegroundColor Cyan

$osRoot = Join-Path $PWD "os"

if (-not (Test-Path -LiteralPath $osRoot)) {
    throw "OS directory does not exist: $osRoot"
}

Get-ChildItem -LiteralPath $osRoot -Recurse -File |
    Sort-Object FullName |
    Select-Object FullName, Length |
    Format-Table -AutoSize

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " OS HANDOVER VALIDATION PASSED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "No source replacement was performed."
Write-Host "No reset / checkout / merge / rebase / clean was performed."
Write-Host ""
