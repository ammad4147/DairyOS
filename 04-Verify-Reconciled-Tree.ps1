#requires -Version 5.1

$ErrorActionPreference = "Stop"
Set-Location D:\DairyOS

$remote = "origin/audit/os-handover-2026-08-19"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS Final Commit-Tree Reconciliation Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

git fetch origin --prune

$local  = (git rev-parse HEAD).Trim()
$remoteHead = (git rev-parse $remote).Trim()
$treeLocal = (git rev-parse "HEAD^{tree}").Trim()
$treeRemote = (git rev-parse "$remote^{tree}").Trim()
$mergeBase = (git merge-base HEAD $remote).Trim()

Write-Host "LOCAL HEAD        : $local"
Write-Host "REMOTE HEAD       : $remoteHead"
Write-Host "MERGE BASE        : $mergeBase"
Write-Host ""
Write-Host "LOCAL TREE        : $treeLocal"
Write-Host "REMOTE TREE       : $treeRemote"
Write-Host ""

Write-Host "=== MERGE COMMIT PARENTS ===" -ForegroundColor Cyan
$parents = @(git rev-list --parents -n 1 HEAD)
$parents | ForEach-Object {
    Write-Host $_
}

Write-Host ""
Write-Host "=== TREE EQUALITY ===" -ForegroundColor Cyan

if ($treeLocal -eq $treeRemote) {
    Write-Host "COMMITTED TREES IDENTICAL" -ForegroundColor Green
}
else {
    Write-Host "COMMITTED TREES DIFFER" -ForegroundColor Red
    throw "Local HEAD and remote branch do not contain identical committed trees."
}

Write-Host ""
Write-Host "=== DIRECT FILE DIFF: LOCAL HEAD VS REMOTE HEAD ===" -ForegroundColor Cyan

git diff --name-status HEAD "$remote"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "No committed file differences." -ForegroundColor Green
}
else {
    throw "git diff comparison failed."
}

Write-Host ""
Write-Host "=== COMMITS LOCAL HAS BEYOND REMOTE ===" -ForegroundColor Cyan

git log --oneline "$remote..HEAD"

Write-Host ""
Write-Host "=== CURRENT WORKTREE ===" -ForegroundColor Cyan

git status --short

Write-Host ""
Write-Host "=== RECONCILIATION RESULT ===" -ForegroundColor Cyan

if ($treeLocal -eq $treeRemote) {
    Write-Host ""
    Write-Host "RECONCILED:" -ForegroundColor Green
    Write-Host "The local committed source tree is identical to remote."
    Write-Host "Local is ahead only by merge history."
    Write-Host "No reset, checkout, merge, rebase, or clean was performed by this script."
}
else {
    throw "RECONCILIATION FAILED."
}

Write-Host ""
