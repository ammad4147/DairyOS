[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path,
    [switch]$SkipFrontend,
    [switch]$SkipDatabaseBackup,
    [switch]$SkipOSAudit,
    [switch]$ContinueOnFailure
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

function Invoke-Step {
    param([string]$Name,[scriptblock]$Action)
    Write-Host ""
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    try {
        & $Action
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "Exit code $LASTEXITCODE" }
        Write-Host "PASS: $Name" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "FAIL: $Name :: $($_.Exception.Message)" -ForegroundColor Red
        if (-not $ContinueOnFailure) { throw }
        return $false
    }
}

$results = [System.Collections.Generic.List[object]]::new()
Push-Location $RepoRoot
try {
    if (-not (Test-Path "pyproject.toml")) { throw "pyproject.toml not found at repository root." }

    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { throw "Python is not available on PATH." }

    $results.Add([pscustomobject]@{
        Name="Python compileall"; Passed=(Invoke-Step "Python compileall" { python -m compileall -q src })
    })

    $results.Add([pscustomobject]@{
        Name="Full pytest regression"; Passed=(Invoke-Step "Full pytest regression" { pytest -q })
    })

    if (-not $SkipFrontend) {
        if (-not (Test-Path "src\DairyOS.Web\package-lock.json")) {
            throw "Frontend package-lock.json is missing; cannot run npm ci reproducibly."
        }
        $results.Add([pscustomobject]@{
            Name="Frontend npm ci"
            Passed=(Invoke-Step "Frontend npm ci" {
                Push-Location "src\DairyOS.Web"
                try { npm ci } finally { Pop-Location }
            })
        })
        $results.Add([pscustomobject]@{
            Name="Frontend production build"
            Passed=(Invoke-Step "Frontend production build" {
                Push-Location "src\DairyOS.Web"
                try { npm run build } finally { Pop-Location }
            })
        })
    }

    if (-not $SkipDatabaseBackup) {
        $backupScript = "scripts\database_backup.py"
        if (Test-Path $backupScript) {
            New-Item -ItemType Directory -Force -Path "backups" | Out-Null
            $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
            $dump = "backups\forensic-acceptance-$stamp.dump"
            $results.Add([pscustomobject]@{
                Name="Database backup"; Passed=(Invoke-Step "Database backup" { python $backupScript backup --output $dump })
            })
            $results.Add([pscustomobject]@{
                Name="Database backup verification"; Passed=(Invoke-Step "Database backup verification" { python $backupScript verify --input $dump })
            })
        } else {
            Write-Host "WARN: scripts\database_backup.py not found; backup stage skipped." -ForegroundColor Yellow
            $results.Add([pscustomobject]@{Name="Database backup"; Passed=$false})
        }
    }

    if (-not $SkipOSAudit) {
        $audit = Join-Path $PSScriptRoot "Invoke-DairyOSHandoverAudit.ps1"
        $results.Add([pscustomobject]@{
            Name="OS handover Phase 0 audit"
            Passed=(Invoke-Step "OS handover Phase 0 audit" {
                & $audit -RepoRoot $RepoRoot -Strict
                if ($LASTEXITCODE -eq 2) { throw "OS handover gate is BLOCKED." }
            })
        })
    }
}
finally {
    Pop-Location
}

$failed = @($results | Where-Object { -not $_.Passed })
$results | Format-Table -AutoSize
Write-Host ""
Write-Host "Completed stages: $($results.Count); failed/blocked: $($failed.Count)" -ForegroundColor $(if ($failed.Count) { "Red" } else { "Green" })

if ($failed.Count -gt 0) { exit 2 }
exit 0
