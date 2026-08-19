#requires -Version 5.1

$ErrorActionPreference = "Stop"
Set-Location D:\DairyOS

$inspectionRoot = "D:\DairyOS\.dairyo-reconciliation\os-handover-inspection-20260820-010309"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path `
    "D:\DairyOS\.dairyo-reconciliation" `
    "authority-comparison-$stamp"

New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS Remote Authority <-> Local Working Tree Comparison" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$pairs = @(
    @{
        Local  = "tools/handover/Invoke-DairyOSAllTests.ps1"
        Remote = "tools__handover__Invoke-DairyOSAllTests.ps1.remote"
    },
    @{
        Local  = "src/dairyos/api/farm_planning.py"
        Remote = "src__dairyos__api__farm_planning.py.remote"
    },
    @{
        Local  = "src/dairyos/data/repositories/repository_factory.py"
        Remote = "src__dairyos__data__repositories__repository_factory.py.remote"
    },
    @{
        Local  = "src/dairyos/farm/operations/repositories/adapters/database_breeding_repository.py"
        Remote = "src__dairyos__farm__operations__repositories__adapters__database_breeding_repository.py.remote"
    }
)

$summary = @()

foreach ($pair in $pairs) {

    $localPath = Join-Path $PWD $pair.Local
    $remotePath = Join-Path $inspectionRoot $pair.Remote

    $safe = $pair.Local -replace '[\\/:]', '__'

    $localCopy = Join-Path $out "$safe.local"
    $remoteCopy = Join-Path $out "$safe.remote"
    $diffPath = Join-Path $out "$safe.diff"

    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host $pair.Local -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------"

    if (-not (Test-Path -LiteralPath $localPath)) {
        Write-Host "LOCAL FILE MISSING" -ForegroundColor Red
        $summary += [pscustomobject]@{
            File = $pair.Local
            LocalExists = $false
            RemoteExists = (Test-Path -LiteralPath $remotePath)
            Identical = $false
            Difference = "LOCAL_MISSING"
        }
        continue
    }

    if (-not (Test-Path -LiteralPath $remotePath)) {
        Write-Host "REMOTE SNAPSHOT MISSING" -ForegroundColor Red
        $summary += [pscustomobject]@{
            File = $pair.Local
            LocalExists = $true
            RemoteExists = $false
            Identical = $false
            Difference = "REMOTE_SNAPSHOT_MISSING"
        }
        continue
    }

    Copy-Item `
        -LiteralPath $localPath `
        -Destination $localCopy `
        -Force

    Copy-Item `
        -LiteralPath $remotePath `
        -Destination $remoteCopy `
        -Force

    $localHash = (Get-FileHash -Algorithm SHA256 $localCopy).Hash
    $remoteHash = (Get-FileHash -Algorithm SHA256 $remoteCopy).Hash

    Write-Host "LOCAL SHA256 : $localHash"
    Write-Host "REMOTE SHA256: $remoteHash"

    if ($localHash -eq $remoteHash) {

        Write-Host "RESULT: IDENTICAL" -ForegroundColor Green

        $summary += [pscustomobject]@{
            File = $pair.Local
            LocalExists = $true
            RemoteExists = $true
            Identical = $true
            Difference = "NONE"
        }

        continue
    }

    Write-Host "RESULT: DIFFERENT" -ForegroundColor Red

    & git diff --no-index -- `
        $remoteCopy `
        $localCopy `
        *> $diffPath

    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 1) {
        Write-Host "Diff saved: $diffPath" -ForegroundColor Yellow
    }
    elseif ($exitCode -ne 0) {
        throw "git diff --no-index failed for $($pair.Local)"
    }

    $summary += [pscustomobject]@{
        File = $pair.Local
        LocalExists = $true
        RemoteExists = $true
        Identical = $false
        Difference = "DIFFERENT"
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TARGETED REPRODUCTIVE / DATE-AUTHORITY INSPECTION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$reproLocal = "src/dairyos/api/farm_planning.py"
$reproDiff = Join-Path `
    $out `
    "REPRODUCTIVE-DATE-AUTHORITY-FOCUS.txt"

$localText = Get-Content `
    -LiteralPath $reproLocal `
    -Raw

$remoteText = Get-Content `
    -LiteralPath (
        Join-Path `
            $inspectionRoot `
            "src__dairyos__api__farm_planning.py.remote"
    ) `
    -Raw

$patterns = @(
    "utcnow().date()",
    "OperationalDateAuthority",
    "event_date",
    "as_of_date",
    "_resolve_current_reproductive_state",
    "_breeding_record_to_resolver_event",
    "last_insemination_date"
)

"LOCAL VS REMOTE REPRODUCTIVE / DATE-AUTHORITY MARKERS" |
    Set-Content -LiteralPath $reproDiff -Encoding UTF8

foreach ($pattern in $patterns) {

    Add-Content `
        -LiteralPath $reproDiff `
        -Value ""

    Add-Content `
        -LiteralPath $reproDiff `
        -Value "=== $pattern ==="

    Add-Content `
        -LiteralPath $reproDiff `
        -Value "--- LOCAL ---"

    $localMatches = $localText -split "`r?`n" |
        Select-String -Pattern $pattern -SimpleMatch

    if ($localMatches) {
        $localMatches |
            ForEach-Object {
                Add-Content `
                    -LiteralPath $reproDiff `
                    -Value $_.Line
            }
    }
    else {
        Add-Content `
            -LiteralPath $reproDiff `
            -Value "(no local match)"
    }

    Add-Content `
        -LiteralPath $reproDiff `
        -Value "--- REMOTE ---"

    $remoteMatches = $remoteText -split "`r?`n" |
        Select-String -Pattern $pattern -SimpleMatch

    if ($remoteMatches) {
        $remoteMatches |
            ForEach-Object {
                Add-Content `
                    -LiteralPath $reproDiff `
                    -Value $_.Line
            }
    }
    else {
        Add-Content `
            -LiteralPath $reproDiff `
            -Value "(no remote match)"
    }
}

Write-Host "Reproductive focus report:" -ForegroundColor Green
Write-Host $reproDiff

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " COMPARISON SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$summary |
    Format-Table -AutoSize

$summary |
    Export-Csv `
        -LiteralPath (Join-Path $out "comparison-summary.csv") `
        -NoTypeInformation `
        -Encoding UTF8

Write-Host ""
Write-Host "Output directory:" -ForegroundColor Green
Write-Host $out -ForegroundColor Green
Write-Host ""

Write-Host "NO SOURCE FILE WAS MODIFIED."
Write-Host "NO REPLACEMENT WAS PERFORMED."
Write-Host "NO RESET / CHECKOUT / MERGE / REBASE / CLEAN WAS PERFORMED."
Write-Host ""
