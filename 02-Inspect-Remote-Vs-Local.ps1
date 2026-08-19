#requires -Version 5.1

$ErrorActionPreference = "Stop"

Set-Location D:\DairyOS

$remote = "origin/audit/os-handover-2026-08-19"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

$root = Join-Path $PWD ".dairyo-reconciliation"
$out  = Join-Path $root "remote-inspection-$stamp"

New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS Remote-vs-Local Inspection" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

git fetch origin --prune

$localHead  = (git rev-parse HEAD).Trim()
$remoteHead = (git rev-parse $remote).Trim()

Write-Host "LOCAL HEAD : $localHead"
Write-Host "REMOTE HEAD: $remoteHead"
Write-Host ""

if ($localHead -ne $remoteHead) {
    throw "Local and remote commit histories are no longer identical. Stop before inspection."
}

$files = @(
    "src/dairyos/api/farm_planning.py",
    "tools/handover/Invoke-DairyOSAllTests.ps1"
)

foreach ($file in $files) {

    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host $file -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow

    $safe = $file -replace '[\\/:]', '__'
    $remoteFile = Join-Path $out "$safe.remote"
    $localFile  = Join-Path $out "$safe.local"
    $diffFile   = Join-Path $out "$safe.diff"

    Write-Host "Exporting remote version..."

    git show "$remote`:$file" |
        Set-Content -LiteralPath $remoteFile -Encoding UTF8

    Write-Host "Exporting local working-tree version..."

    Get-Content -LiteralPath $file -Raw |
        Set-Content -LiteralPath $localFile -Encoding UTF8

    Write-Host "Generating comparison..."

    git diff --no-index -- `
        $remoteFile `
        $localFile |
        Set-Content -LiteralPath $diffFile -Encoding UTF8

    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "IDENTICAL: local working tree matches remote." -ForegroundColor Green
    }
    elseif ($exitCode -eq 1) {
        Write-Host "DIFFERENT: local working tree differs from remote." -ForegroundColor Yellow
        Write-Host "Diff saved to: $diffFile" -ForegroundColor Yellow
    }
    else {
        throw "Comparison failed for $file"
    }
}

Write-Host ""
Write-Host "------------------------------------------------------------"
Write-Host "GENERATED INSPECTION FILES"
Write-Host "------------------------------------------------------------"
Get-ChildItem -LiteralPath $out -File |
    Select-Object Name, Length |
    Format-Table -AutoSize

Write-Host ""
Write-Host "Inspection directory:"
Write-Host $out -ForegroundColor Green
Write-Host ""

Write-Host "Important:"
Write-Host "No local source file was modified."
Write-Host "No reset, checkout, merge, rebase, clean, or replacement was performed."
Write-Host ""
