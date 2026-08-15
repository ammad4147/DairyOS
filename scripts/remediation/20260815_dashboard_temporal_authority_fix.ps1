$ErrorActionPreference = "Stop"

$repo = (Get-Location).Path
$expectedHead = "35dbd8344d914f722971cc4853cd36f785f412de"

$head = (git -C $repo rev-parse HEAD).Trim()
if ($head -ne $expectedHead) {
    throw "Refusing to modify repository: expected HEAD $expectedHead, found $head"
}

$status = (git -C $repo status --porcelain).Trim()
if ($status) {
    throw "Refusing to modify repository: working tree is not clean."
}

$target = Join-Path $repo "src\DairyOS.Web\src\components\MainDashboard.tsx"
if (-not (Test-Path -LiteralPath $target)) {
    throw "Missing target: $target"
}

$backupDir = Join-Path $repo "_backups\audit_20260815"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$backup = Join-Path $backupDir "MainDashboard.tsx.before_temporal_authority_fix.bak"
Copy-Item -LiteralPath $target -Destination $backup -Force

$utf8 = [System.Text.UTF8Encoding]::new($false)
$text = [System.IO.File]::ReadAllText($target, $utf8)

$oldHelpers = @'
function todayIso() {
    return new Date().toISOString().slice(0, 10);
}

function yesterdayIso() {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString().slice(0, 10);
}

function recordDate(row: Row): string | null {
    const raw = row.production_date ?? row.observed_at ?? row.timestamp ?? row.created_at;
    if (!raw) return null;
    const parsed = new Date(raw);
    return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString().slice(0, 10);
}
'@

$newHelpers = @'
function shiftIsoDate(baseIso: string, days: number): string {
    const [year, month, day] = baseIso.slice(0, 10).split("-").map(Number);
    const value = new Date(Date.UTC(year, month - 1, day));
    value.setUTCDate(value.getUTCDate() + days);
    return value.toISOString().slice(0, 10);
}

function recordDate(row: Row): string | null {
    const raw = row.production_date ?? row.observed_at ?? row.timestamp ?? row.created_at;
    if (!raw) return null;

    // Persisted production/observation dates are authoritative calendar dates.
    // Preserve an ISO date prefix verbatim instead of converting it through the
    // browser timezone and potentially shifting the farm date by one day.
    const text = String(raw);
    if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
        return text.slice(0, 10);
    }

    const parsed = new Date(text);
    return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString().slice(0, 10);
}
'@

if (-not $text.Contains($oldHelpers)) {
    Copy-Item -LiteralPath $backup -Destination $target -Force
    throw "Expected temporal helper block was not found; backup restored."
}
$text = $text.Replace($oldHelpers, $newHelpers)

$oldDates = @'
    const rows = Array.isArray(milk.data) ? milk.data : [];
    const today = todayIso();
    const yesterday = yesterdayIso();
    const todayLedger = ledgerRows(rows, today);
    const yesterdayLedger = ledgerRows(rows, yesterday);
'@

$newDates = @'
    const rows = Array.isArray(milk.data) ? milk.data : [];
    const operationalDate = session.data?.operational_date?.slice(0, 10) ?? null;

    if (!operationalDate) {
        return (
            <PanelShell
                title="Milk Production"
                errorText="The farm API did not provide an operational date; production is not projected until the authoritative date is available."
                onRetry={() => { session.reload(); milk.reload(); }}
            />
        );
    }

    const previousDate = shiftIsoDate(operationalDate, -1);
    const todayLedger = ledgerRows(rows, operationalDate);
    const yesterdayLedger = ledgerRows(rows, previousDate);
'@

if (-not $text.Contains($oldDates)) {
    Copy-Item -LiteralPath $backup -Destination $target -Force
    throw "Expected milk date block was not found; backup restored."
}
$text = $text.Replace($oldDates, $newDates)
$text = $text.Replace('label: `Today ${todayTotal.toFixed(1)} L vs ${yesterdayTotal.toFixed(1)} L yesterday`,', 'label: `${operationalDate} ${todayTotal.toFixed(1)} L vs ${previousDate} ${yesterdayTotal.toFixed(1)} L`,')
$text = $text.Replace('label: `${titleCase(lastSession)} ${currentSessionTotal.toFixed(1)} L vs ${priorSessionTotal.toFixed(1)} L yesterday ${titleCase(lastSession).toLowerCase()}`,', 'label: `${operationalDate} ${titleCase(lastSession)} ${currentSessionTotal.toFixed(1)} L vs ${previousDate} ${priorSessionTotal.toFixed(1)} L ${titleCase(lastSession).toLowerCase()}`,')
$text = $text.Replace('headline = { label: "No session recorded yet today", value: "—", comparison: { text: "", tone: "flat" } };', 'headline = { label: `No ${operationalDate} session recorded yet`, value: "—", comparison: { text: "", tone: "flat" } };')
$text = $text.Replace('            ? "All sessions settled today"', '            ? `All sessions settled on ${operationalDate}`')
$text = $text.Replace('            : `Next session due: ${titleCase(String(nextSession))}`', '            : `Next session for ${operationalDate}: ${titleCase(String(nextSession))}`')
$text = $text.Replace('<span>Today\'s Production</span><strong>{todayTotal.toFixed(1)} L</strong>', '<span>Production ({operationalDate})</span><strong>{todayTotal.toFixed(1)} L</strong>')

[System.IO.File]::WriteAllText($target, $text, $utf8)

Write-Host "Dashboard temporal-authority replacement written." -ForegroundColor Green
Write-Host "Backup: $backup" -ForegroundColor DarkGray
Write-Host "" 
Write-Host "Validation:" -ForegroundColor Cyan
Write-Host "  npm --prefix src\DairyOS.Web run build"
Write-Host "  git diff --check"
Write-Host "  git diff -- src/DairyOS.Web/src/components/MainDashboard.tsx"
Write-Host "" 
Write-Host "This package intentionally changes only MainDashboard.tsx." -ForegroundColor Yellow
Write-Host "It removes browser-local 'today/yesterday' as the production date source and anchors the panel to /farm/milk/next-session operational_date." -ForegroundColor Yellow
