[CmdletBinding()]
param(
    [string]$Repository = (Get-Location).Path,
    [switch]$CommitLocal
)

$ErrorActionPreference = 'Stop'
$finance = Join-Path $Repository 'src\DairyOS.Web\src\components\FinanceTab.tsx'
if (-not (Test-Path -LiteralPath $finance -PathType Leaf)) {
    throw "FinanceTab.tsx not found: $finance"
}

$content = Get-Content -LiteralPath $finance -Raw -Encoding UTF8
$original = $content

$replacements = [ordered]@{
    'id: REV- + Date.now().toString().slice(-4)' = "id: 'REV-' + Date.now().toString().slice(-4)"
    'refNumber: revRef || REC- + Math.floor(Math.random() * 9000 + 1000)' = "refNumber: revRef || 'REC-' + Math.floor(Math.random() * 9000 + 1000)"
    'id: EXP- + Date.now().toString().slice(-4)' = "id: 'EXP-' + Date.now().toString().slice(-4)"
    'refNumber: expRef || BILL- + Math.floor(Math.random() * 9000 + 1000)' = "refNumber: expRef || 'BILL-' + Math.floor(Math.random() * 9000 + 1000)"
    'const rows = ledger.map(l => [ l.id, l.type, " + l.category + ", l.amount, " + (l.quantity || '') + ", l.date, " + l.refNumber + ", l.description + ", l.isVoid ? ''VOIDED'' : ''ACTIVE'', " + (l.voidReason || '') + " ]);' = 'const rows = ledger.map(l => [ l.id, l.type, l.category, l.amount, l.quantity || '''', l.date, l.refNumber, l.description, l.isVoid ? ''VOIDED'' : ''ACTIVE'', l.voidReason || '''' ]);'
    'link.setAttribute(''download'', DairyOS_Financial_Statement_ + statementPeriod + _2026.csv);' = "link.setAttribute('download', 'DairyOS_Financial_Statement_' + statementPeriod + '_2026.csv');"
}

foreach ($pair in $replacements.GetEnumerator()) {
    if ($content.Contains($pair.Key)) {
        $content = $content.Replace($pair.Key, $pair.Value)
        Write-Host "[REPAIRED] $($pair.Key)"
    }
}

$required = @(
    "id: 'REV-' + Date.now().toString().slice(-4)",
    "refNumber: revRef || 'REC-' + Math.floor(Math.random() * 9000 + 1000)",
    "id: 'EXP-' + Date.now().toString().slice(-4)",
    "refNumber: expRef || 'BILL-' + Math.floor(Math.random() * 9000 + 1000)",
    'const rows = ledger.map(l => [ l.id, l.type, l.category, l.amount, l.quantity || '''', l.date, l.refNumber, l.description, l.isVoid ? ''VOIDED'' : ''ACTIVE'', l.voidReason || '''' ]);',
    "link.setAttribute('download', 'DairyOS_Financial_Statement_' + statementPeriod + '_2026.csv');"
)

foreach ($fragment in $required) {
    if (-not $content.Contains($fragment)) {
        throw "FinanceTab repair incomplete; required fragment missing: $fragment"
    }
}

Set-Content -LiteralPath $finance -Value $content -Encoding UTF8 -NoNewline

if ($content -eq $original) {
    Write-Host '[OK] FinanceTab.tsx already matched the repaired form.'
} else {
    Write-Host '[OK] FinanceTab.tsx repaired.'
}

if ($CommitLocal) {
    git -C $Repository add -- $finance
    git -C $Repository commit -m 'fix(UI): repair FinanceTab acceptance defects'
}
