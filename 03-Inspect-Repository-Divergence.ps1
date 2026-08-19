#requires -Version 5.1

$ErrorActionPreference = "Stop"
Set-Location D:\DairyOS

$remote = "origin/audit/os-handover-2026-08-19"
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"

$root = Join-Path $PWD ".dairyo-reconciliation"
$out  = Join-Path $root "divergence-inspection-$stamp"

New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS Local <-> Remote Divergence Inspection" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

git fetch origin --prune

$localHead  = (git rev-parse HEAD).Trim()
$remoteHead = (git rev-parse $remote).Trim()
$mergeBase  = (git merge-base HEAD $remote).Trim()

$localCount = [int](git rev-list --count "$mergeBase..HEAD")
$remoteCount = [int](git rev-list --count "$mergeBase..$remote")

Write-Host "LOCAL HEAD :" $localHead
Write-Host "REMOTE HEAD:" $remoteHead
Write-Host "MERGE BASE :" $mergeBase
Write-Host ""
Write-Host "LOCAL-ONLY COMMITS : $localCount" -ForegroundColor Yellow
Write-Host "REMOTE-ONLY COMMITS: $remoteCount" -ForegroundColor Yellow
Write-Host ""

Write-Host "=== CURRENT WORKTREE ===" -ForegroundColor Cyan
git status --short

git status --short |
    Set-Content -LiteralPath (Join-Path $out "working-tree-status.txt") -Encoding UTF8

Write-Host ""
Write-Host "=== LOCAL-ONLY COMMITS ===" -ForegroundColor Cyan

$localCommits = @(git log --oneline --decorate "$mergeBase..HEAD")

if ($localCommits.Count -eq 0) {
    Write-Host "None." -ForegroundColor Green
}
else {
    $localCommits | ForEach-Object {
        Write-Host $_ -ForegroundColor Yellow
    }
}

$localCommits |
    Set-Content -LiteralPath (Join-Path $out "local-only-commits.txt") -Encoding UTF8

Write-Host ""
Write-Host "=== REMOTE-ONLY COMMITS ===" -ForegroundColor Cyan

$remoteCommits = @(git log --oneline --decorate "$mergeBase..$remote")

if ($remoteCommits.Count -eq 0) {
    Write-Host "None." -ForegroundColor Green
}
else {
    $remoteCommits | ForEach-Object {
        Write-Host $_ -ForegroundColor Magenta
    }
}

$remoteCommits |
    Set-Content -LiteralPath (Join-Path $out "remote-only-commits.txt") -Encoding UTF8

Write-Host ""
Write-Host "=== LOCAL-ONLY CHANGED PATHS ===" -ForegroundColor Cyan

$localPaths = @(git diff --name-status "$mergeBase..HEAD")

if ($localPaths.Count -eq 0) {
    Write-Host "None." -ForegroundColor Green
}
else {
    $localPaths | ForEach-Object {
        Write-Host $_
    }
}

$localPaths |
    Set-Content -LiteralPath (Join-Path $out "local-only-paths.txt") -Encoding UTF8

Write-Host ""
Write-Host "=== REMOTE-ONLY CHANGED PATHS ===" -ForegroundColor Cyan

$remotePaths = @(git diff --name-status "$mergeBase..$remote")

if ($remotePaths.Count -eq 0) {
    Write-Host "None." -ForegroundColor Green
}
else {
    $remotePaths | ForEach-Object {
        Write-Host $_
    }
}

$remotePaths |
    Set-Content -LiteralPath (Join-Path $out "remote-only-paths.txt") -Encoding UTF8

Write-Host ""
Write-Host "=== FILE-SPECIFIC DIVERGENCE ===" -ForegroundColor Cyan

$focusFiles = @(
    "src/dairyos/api/farm_planning.py",
    "tools/handover/Invoke-DairyOSAllTests.ps1",
    "01-Reconcile-DairyOS-Local-With-Remote.ps1",
    "src/dairyos/data/repositories/repository_factory.py",
    "src/dairyos/farm/operations/repositories/adapters/database_breeding_repository.py"
)

foreach ($file in $focusFiles) {

    Write-Host ""
    Write-Host "--- $file ---" -ForegroundColor Yellow

    $localExists  = git cat-file -e "HEAD:$file" 2>$null
    $remoteExists = git cat-file -e "$remote`:$file" 2>$null
    $baseExists   = git cat-file -e "$mergeBase`:$file" 2>$null

    Write-Host "Base exists  : $baseExists"
    Write-Host "Local exists : $localExists"
    Write-Host "Remote exists: $remoteExists"

    if ($baseExists -and $localExists) {
        $localChanged = git diff --quiet "$mergeBase" HEAD -- "$file"
        if ($LASTEXITCODE -eq 1) {
            Write-Host "LOCAL changed from merge-base: YES" -ForegroundColor Yellow
        }
        else {
            Write-Host "LOCAL changed from merge-base: NO" -ForegroundColor Green
        }
    }

    if ($baseExists -and $remoteExists) {
        $remoteChanged = git diff --quiet "$mergeBase" "$remote" -- "$file"
        if ($LASTEXITCODE -eq 1) {
            Write-Host "REMOTE changed from merge-base: YES" -ForegroundColor Magenta
        }
        else {
            Write-Host "REMOTE changed from merge-base: NO" -ForegroundColor Green
        }
    }

    $localFile = Join-Path $out (($file -replace '[\\/:]', '__') + ".local")
    $remoteFile = Join-Path $out (($file -replace '[\\/:]', '__') + ".remote")
    $diffFile = Join-Path $out (($file -replace '[\\/:]', '__') + ".diff")

    if ($localExists) {
        git show "HEAD:$file" |
            Set-Content -LiteralPath $localFile -Encoding UTF8
    }

    if ($remoteExists) {
        git show "$remote`:$file" |
            Set-Content -LiteralPath $remoteFile -Encoding UTF8
    }

    if ($localExists -and $remoteExists) {
        git diff --no-index -- "$localFile" "$remoteFile" |
            Set-Content -LiteralPath $diffFile -Encoding UTF8

        $code = $LASTEXITCODE

        if ($code -eq 0) {
            Write-Host "LOCAL HEAD == REMOTE HEAD for this file" -ForegroundColor Green
        }
        elseif ($code -eq 1) {
            Write-Host "LOCAL HEAD != REMOTE HEAD for this file" -ForegroundColor Red
            Write-Host "Diff: $diffFile" -ForegroundColor Red
        }
        else {
            throw "git diff --no-index failed for $file"
        }
    }
}

Write-Host ""
Write-Host "=== REMOTE COMMITS TOUCHING REPRODUCTIVE / INSTALLATION AREAS ===" -ForegroundColor Cyan

$patterns = @(
    "farm_planning",
    "reproductive",
    "breeding",
    "handover",
    "install",
    "uninstall",
    "os"
)

$allRemoteCommits = @(git log --oneline "$mergeBase..$remote")

$matched = @(
    $allRemoteCommits |
        Where-Object {
            $line = $_.ToLowerInvariant()
            $patterns | Where-Object { $line -like "*$_*" } | Select-Object -First 1
        }
)

if ($matched.Count -eq 0) {
    Write-Host "No matching commit subjects found."
}
else {
    $matched | ForEach-Object {
        Write-Host $_
    }
}

$matched |
    Set-Content -LiteralPath (Join-Path $out "remote-focused-commits.txt") -Encoding UTF8

Write-Host ""
Write-Host "=== INSPECTION COMPLETE ===" -ForegroundColor Green
Write-Host ""
Write-Host "Output directory:"
Write-Host $out -ForegroundColor Green
Write-Host ""
Write-Host "NO SOURCE FILE WAS MODIFIED."
Write-Host "NO RESET / CHECKOUT / MERGE / REBASE / CLEAN WAS PERFORMED."
Write-Host ""

if ($localCount -gt 0 -and $remoteCount -gt 0) {
    Write-Host "RESULT: BRANCHES HAVE DIVERGED." -ForegroundColor Red
}
elseif ($localCount -gt 0) {
    Write-Host "RESULT: LOCAL IS AHEAD OF REMOTE." -ForegroundColor Yellow
}
elseif ($remoteCount -gt 0) {
    Write-Host "RESULT: REMOTE IS AHEAD OF LOCAL." -ForegroundColor Magenta
}
else {
    Write-Host "RESULT: HISTORIES ARE IDENTICAL." -ForegroundColor Green
}

Write-Host ""
