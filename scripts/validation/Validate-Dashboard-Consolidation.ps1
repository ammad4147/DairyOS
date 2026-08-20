[CmdletBinding()]
param(
    [string]$Repo = 'D:\DairyOS'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Branch = 'dashboard/consolidation-2026-08-20'
$ExpectedRemote = 'origin/' + $Branch

function Invoke-Git([string[]]$Args) {
    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Invoke-Checked([string]$File, [string[]]$Args) {
    & $File @Args
    if ($LASTEXITCODE -ne 0) {
        throw "$File $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

Write-Host "DairyOS Dashboard Consolidation Validation"
Write-Host "Repository: $Repo"
Write-Host "Target branch: $Branch"
Write-Host ""

if (-not (Test-Path -LiteralPath $Repo -PathType Container)) {
    throw "Repository path does not exist: $Repo"
}

Set-Location -LiteralPath $Repo

$root = (& git rev-parse --show-toplevel).Trim()
if ($root -ne $Repo.TrimEnd('\')) {
    throw "Expected Git root '$Repo' but found '$root'"
}

$status = @(git status --porcelain)
if ($status.Count -gt 0) {
    Write-Host "UNCOMMITTED LOCAL CHANGES DETECTED:" -ForegroundColor Yellow
    $status | ForEach-Object { Write-Host $_ }
    throw "Refusing to switch/reconcile branches while the working tree is dirty. Preserve or commit local work first."
}

Write-Host "[1/8] Fetching remote branch..."
Invoke-Git @('fetch', 'origin', $Branch)

$remoteSha = (& git rev-parse $ExpectedRemote).Trim()
if (-not $remoteSha) {
    throw "Remote branch could not be resolved: $ExpectedRemote"
}

$localBranch = (& git branch --show-current).Trim()
if ($localBranch -ne $Branch) {
    Write-Host "[2/8] Switching local checkout to $Branch..."
    $existing = @(git branch --list $Branch)
    if ($existing.Count -gt 0) {
        Invoke-Git @('checkout', $Branch)
    }
    else {
        Invoke-Git @('checkout', '--track', $ExpectedRemote)
    }
}
else {
    Write-Host "[2/8] Already on $Branch."
}

Write-Host "[3/8] Fast-forwarding local branch to remote..."
Invoke-Git @('pull', '--ff-only', 'origin', $Branch)

$head = (& git rev-parse HEAD).Trim()
$remoteSha = (& git rev-parse $ExpectedRemote).Trim()
if ($head -ne $remoteSha) {
    throw "Local HEAD $head does not match $ExpectedRemote $remoteSha"
}
Write-Host "Authoritative SHA: $head"

Write-Host "[4/8] Validating Python compilation..."
Invoke-Checked 'python' @('-m', 'compileall', '-q', 'src')

Write-Host "[5/8] Running authoritative tab-state and dashboard regression tests..."
Invoke-Checked 'pytest' @('-q', 'tests/api/test_s09d55_tab_state_contract.py', 'tests/dashboard/test_dashboard_projection_service.py')

Write-Host "[6/8] Running full backend regression..."
Invoke-Checked 'pytest' @('-q')

Write-Host "[7/8] Building the React/Vite operator UI..."
Push-Location (Join-Path $Repo 'src\DairyOS.Web')
try {
    if (-not (Test-Path -LiteralPath 'node_modules' -PathType Container)) {
        Write-Host "node_modules not present; running npm ci..."
        Invoke-Checked 'npm' @('ci')
    }
    else {
        Write-Host "Using existing node_modules; lockfile is unchanged by this dashboard change."
    }
    Invoke-Checked 'npm' @('run', 'build')
}
finally {
    Pop-Location
}

Write-Host "[8/8] Final repository integrity checks..."
Invoke-Git @('diff', '--check')
$finalStatus = @(git status --porcelain)
if ($finalStatus.Count -gt 0) {
    Write-Host "Tracked/uncommitted changes after validation:" -ForegroundColor Yellow
    $finalStatus | ForEach-Object { Write-Host $_ }
    throw "Validation generated tracked working-tree changes. Inspect before any publication step."
}

$finalHead = (& git rev-parse HEAD).Trim()
$finalRemote = (& git rev-parse $ExpectedRemote).Trim()
if ($finalHead -ne $finalRemote) {
    throw "Final SHA parity failed: local=$finalHead remote=$finalRemote"
}

Write-Host ""
Write-Host "VALIDATION RESULT: PASS" -ForegroundColor Green
Write-Host "Branch: $Branch"
Write-Host "Local SHA:  $finalHead"
Write-Host "Remote SHA: $finalRemote"
Write-Host "Working tree: CLEAN"
Write-Host "Python compile: PASS"
Write-Host "Targeted backend tests: PASS"
Write-Host "Full backend tests: PASS"
Write-Host "TypeScript/Vite production build: PASS"
