#requires -Version 5.1

<#
.SYNOPSIS
    Reconcile the local DairyOS repository against its configured remote.

.DESCRIPTION
    Safety-first repository reconciliation.

    The script:
      1. Verifies this is the expected DairyOS Git repository.
      2. Captures the current branch, HEAD, worktree and configured remotes.
      3. Fetches all remote refs and prunes deleted remote refs.
      4. Detects the current branch's upstream tracking branch.
      5. Creates a timestamped local safety branch before any movement.
      6. Classifies local/remote divergence.
      7. Performs only a safe fast-forward when the local branch is strictly
         behind its upstream and the worktree/index are clean.
      8. Refuses to overwrite or reset local commits.
      9. Produces a reconciliation report under .dairyo-reconciliation.

    IMPORTANT:
      - No git reset --hard.
      - No git clean.
      - No forced checkout.
      - No destructive deletion of local commits.
      - No automatic merge/rebase of divergent histories.
#>

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DairyOS Local <-> Remote Reconciliation" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# 0. Repository safety
# ------------------------------------------------------------

if (-not (Test-Path ".git")) {
    throw "D:\DairyOS is not a Git working tree. .git was not found."
}

$topLevel = (git rev-parse --show-toplevel).Trim()

if ($LASTEXITCODE -ne 0) {
    throw "Unable to resolve Git repository root."
}

if ([System.IO.Path]::GetFullPath($topLevel).TrimEnd('\') -ne `
    [System.IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\')) {
    throw "Run this script from D:\DairyOS."
}

# ------------------------------------------------------------
# 1. Configuration
# ------------------------------------------------------------

$reportDir = Join-Path $PWD ".dairyo-reconciliation"

if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $reportDir "reconciliation-$timestamp.txt"

$report = New-Object System.Collections.Generic.List[string]

function Write-Report {
    param(
        [string]$Text = ""
    )

    $report.Add($Text)
    Write-Host $Text
}

function Invoke-GitText {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $output = & git @Arguments 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git $($Arguments -join ' ')`n$($output -join "`n")"
    }

    return ($output -join "`n").Trim()
}

# ------------------------------------------------------------
# 2. Initial repository state
# ------------------------------------------------------------

$currentBranch = Invoke-GitText @("branch", "--show-current")
$currentHead   = Invoke-GitText @("rev-parse", "HEAD")

$statusShort = Invoke-GitText @("status", "--short")
$isDirty = -not [string]::IsNullOrWhiteSpace($statusShort)

$originUrl = ""
try {
    $originUrl = Invoke-GitText @("remote", "get-url", "origin")
}
catch {
    throw "Remote 'origin' is not configured."
}

$upstream = ""
try {
    $upstream = Invoke-GitText @(
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}"
    )
}
catch {
    $upstream = ""
}

Write-Report "Repository root : $topLevel"
Write-Report "Current branch   : $currentBranch"
Write-Report "Current HEAD     : $currentHead"
Write-Report "Origin           : $originUrl"
Write-Report "Upstream         : $(if ($upstream) { $upstream } else { '<none>' })"
Write-Report "Worktree dirty   : $isDirty"
Write-Report ""

if (-not $currentBranch) {
    throw "Repository is in detached HEAD state. Reconciliation aborted."
}

# ------------------------------------------------------------
# 3. Capture complete pre-reconciliation state
# ------------------------------------------------------------

Write-Report "=== PRE-RECONCILIATION STATE ==="
Write-Report ""

Write-Report "Branches:"
Write-Report (Invoke-GitText @("branch", "-vv"))
Write-Report ""

Write-Report "Remotes:"
Write-Report (Invoke-GitText @("remote", "-v"))
Write-Report ""

Write-Report "Recent commits:"
Write-Report (Invoke-GitText @(
    "log",
    "--oneline",
    "--decorate",
    "-20"
))
Write-Report ""

Write-Report "Status:"
if ($statusShort) {
    Write-Report $statusShort
}
else {
    Write-Report "<clean>"
}
Write-Report ""

# ------------------------------------------------------------
# 4. Refuse unsafe automatic reconciliation
# ------------------------------------------------------------

if ($isDirty) {
    Write-Report "WORKTREE STATE: DIRTY"
    Write-Report ""
    Write-Report "Local modifications are present."
    Write-Report "Automatic branch movement is therefore prohibited."
    Write-Report ""
    Write-Report "No reset, clean, merge, rebase, or checkout was performed."
    Write-Report ""

    $report | Set-Content -LiteralPath $reportPath -Encoding UTF8

    Write-Host ""
    Write-Host "RECONCILIATION STOPPED SAFELY." -ForegroundColor Yellow
    Write-Host "Reason: working tree contains local modifications." -ForegroundColor Yellow
    Write-Host "Report : $reportPath" -ForegroundColor Green
    Write-Host ""

    exit 0
}

# ------------------------------------------------------------
# 5. Fetch remote safely
# ------------------------------------------------------------

Write-Report "=== FETCH REMOTE ==="
Write-Report ""

$fetchOutput = & git fetch origin --prune 2>&1

if ($LASTEXITCODE -ne 0) {
    $text = $fetchOutput -join "`n"
    Write-Report $text
    $report | Set-Content -LiteralPath $reportPath -Encoding UTF8
    throw "git fetch origin --prune failed."
}

if ($fetchOutput) {
    Write-Report ($fetchOutput -join "`n")
}
else {
    Write-Report "<no fetch messages>"
}

Write-Report ""

# ------------------------------------------------------------
# 6. Resolve upstream after fetch
# ------------------------------------------------------------

if (-not $upstream) {
    $candidate = "origin/$currentBranch"

    $remoteBranchExists = & git show-ref --verify --quiet "refs/remotes/$candidate"
    if ($LASTEXITCODE -eq 0) {
        $upstream = $candidate
        Write-Report "No configured upstream was present."
        Write-Report "Detected matching remote branch: $candidate"
        Write-Report ""
    }
    else {
        Write-Report "No upstream tracking branch exists."
        Write-Report "No automatic reconciliation was performed."
        Write-Report ""

        $report | Set-Content -LiteralPath $reportPath -Encoding UTF8

        Write-Host ""
        Write-Host "NO UPSTREAM BRANCH FOUND." -ForegroundColor Yellow
        Write-Host "Report : $reportPath" -ForegroundColor Green
        Write-Host ""

        exit 0
    }
}

# ------------------------------------------------------------
# 7. Create safety branch
# ------------------------------------------------------------

$safetyBranch = "reconcile-safety/$currentBranch-$timestamp"

# Replace characters Git does not permit in branch names.
$safetyBranch = $safetyBranch -replace '[^A-Za-z0-9._/-]', '-'
$safetyBranch = $safetyBranch -replace '/+', '/'

Write-Report "=== SAFETY CHECKPOINT ==="
Write-Report "Creating safety branch: $safetyBranch"

& git branch $safetyBranch $currentHead 2>&1 | Tee-Object -Variable branchOutput | Out-Null

if ($LASTEXITCODE -ne 0) {
    $report | Set-Content -LiteralPath $reportPath -Encoding UTF8
    throw "Failed to create safety branch '$safetyBranch'."
}

Write-Report "Safety branch created."
Write-Report ""

# ------------------------------------------------------------
# 8. Compare local and remote histories
# ------------------------------------------------------------

$remoteHead = Invoke-GitText @("rev-parse", "$upstream")

$localAhead  = [int](Invoke-GitText @(
    "rev-list",
    "--count",
    "$upstream..HEAD"
))

$localBehind = [int](Invoke-GitText @(
    "rev-list",
    "--count",
    "HEAD..$upstream"
))

$commonBase = Invoke-GitText @(
    "merge-base",
    "HEAD",
    "$upstream"
)

Write-Report "=== DIVERGENCE ANALYSIS ==="
Write-Report "Local HEAD      : $currentHead"
Write-Report "Remote HEAD     : $remoteHead"
Write-Report "Common ancestor : $commonBase"
Write-Report "Local ahead     : $localAhead commit(s)"
Write-Report "Local behind    : $localBehind commit(s)"
Write-Report ""

# ------------------------------------------------------------
# 9. Classify reconciliation state
# ------------------------------------------------------------

if ($currentHead -eq $remoteHead) {

    Write-Report "RECONCILIATION STATE: IDENTICAL"
    Write-Report "Local and remote point to the same commit."
    Write-Report ""

    $result = "IDENTICAL"
}
elseif ($localAhead -gt 0 -and $localBehind -eq 0) {

    Write-Report "RECONCILIATION STATE: LOCAL_AHEAD"
    Write-Report "Local contains commits not present on the remote."
    Write-Report "No automatic push will be performed."
    Write-Report ""

    Write-Report "Local-only commits:"
    Write-Report (Invoke-GitText @(
        "log",
        "--oneline",
        "$upstream..HEAD"
    ))
    Write-Report ""

    $result = "LOCAL_AHEAD"
}
elseif ($localAhead -eq 0 -and $localBehind -gt 0) {

    Write-Report "RECONCILIATION STATE: REMOTE_AHEAD"
    Write-Report "Local is strictly behind remote."
    Write-Report "Worktree is clean."
    Write-Report "Fast-forward is safe."
    Write-Report ""

    Write-Report "Remote-only commits:"
    Write-Report (Invoke-GitText @(
        "log",
        "--oneline",
        "HEAD..$upstream"
    ))
    Write-Report ""

    Write-Report "Performing fast-forward:"
    $ffOutput = & git merge --ff-only $upstream 2>&1

    if ($LASTEXITCODE -ne 0) {
        $text = $ffOutput -join "`n"
        Write-Report $text
        $report | Set-Content -LiteralPath $reportPath -Encoding UTF8
        throw "Fast-forward reconciliation failed."
    }

    Write-Report ($ffOutput -join "`n")
    Write-Report ""

    $result = "FAST_FORWARD_APPLIED"
}
else {

    Write-Report "RECONCILIATION STATE: DIVERGED"
    Write-Report "Local and remote both contain commits absent from the other."
    Write-Report "Automatic merge/rebase is prohibited by this safety script."
    Write-Report ""

    Write-Report "LOCAL-ONLY COMMITS:"
    Write-Report (Invoke-GitText @(
        "log",
        "--oneline",
        "$upstream..HEAD"
    ))
    Write-Report ""

    Write-Report "REMOTE-ONLY COMMITS:"
    Write-Report (Invoke-GitText @(
        "log",
        "--oneline",
        "HEAD..$upstream"
    ))
    Write-Report ""

    Write-Report "No destructive reconciliation was attempted."

    $result = "DIVERGED"
}

# ------------------------------------------------------------
# 10. Final state
# ------------------------------------------------------------

$finalHead = Invoke-GitText @("rev-parse", "HEAD")
$finalStatus = Invoke-GitText @("status", "--short")
$finalTracking = ""

try {
    $finalTracking = Invoke-GitText @(
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}"
    )
}
catch {
    $finalTracking = $upstream
}

Write-Report ""
Write-Report "=== FINAL STATE ==="
Write-Report "Result          : $result"
Write-Report "Branch          : $currentBranch"
Write-Report "HEAD            : $finalHead"
Write-Report "Upstream        : $finalTracking"
Write-Report "Safety branch   : $safetyBranch"
Write-Report ""

Write-Report "Final status:"
if ($finalStatus) {
    Write-Report $finalStatus
}
else {
    Write-Report "<clean>"
}

Write-Report ""

Write-Report "Final branch graph:"
Write-Report (Invoke-GitText @(
    "log",
    "--oneline",
    "--decorate",
    "--graph",
    "-20"
))

Write-Report ""

# ------------------------------------------------------------
# 11. Save report
# ------------------------------------------------------------

$report.Add("Reconciliation report generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')")

$report | Set-Content -LiteralPath $reportPath -Encoding UTF8

# ------------------------------------------------------------
# 12. Console conclusion
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

switch ($result) {

    "IDENTICAL" {
        Write-Host "LOCAL AND REMOTE ARE ALREADY RECONCILED." -ForegroundColor Green
    }

    "FAST_FORWARD_APPLIED" {
        Write-Host "REMOTE CHANGES WERE FAST-FORWARDED SAFELY." -ForegroundColor Green
    }

    "LOCAL_AHEAD" {
        Write-Host "LOCAL IS AHEAD OF REMOTE." -ForegroundColor Yellow
        Write-Host "NO PUSH WAS PERFORMED." -ForegroundColor Yellow
    }

    "DIVERGED" {
        Write-Host "LOCAL AND REMOTE HAVE DIVERGED." -ForegroundColor Red
        Write-Host "NO AUTOMATIC MERGE/REBASE WAS PERFORMED." -ForegroundColor Red
    }
}

Write-Host "Safety branch : $safetyBranch" -ForegroundColor Green
Write-Host "Report        : $reportPath" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($result -eq "DIVERGED") {
    Write-Host "NEXT ACTION REQUIRED: reconcile the divergent histories explicitly." -ForegroundColor Yellow
}

