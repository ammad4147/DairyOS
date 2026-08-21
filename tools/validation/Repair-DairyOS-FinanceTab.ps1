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

$replacements = @(
    @("id:\s*REV-\s*\+\s*Date\.now\(\)\.toString\(\)\.slice\(-4\)", "id: 'REV-' + Date.now().toString().slice(-4)"),
    @("refNumber:\s*revRef\s*\|\|\s*REC-\s*\+\s*Math\.floor\(Math\.random\(\)\s*\*\s*9000\s*\+\s*1000\)", "refNumber: revRef || 'REC-' + Math.floor(Math.random() * 9000 + 1000)"),
    @("id:\s*EXP-\s*\+\s*Date\.now\(\)\.toString\(\)\.slice\(-4\)", "id: 'EXP-' + Date.now().toString().slice(-4)"),
    @("refNumber:\s*expRef\s*\|\|\s*BILL-\s*\+\s*Math\.floor\(Math\.random\(\)\s*\*\s*9000\s*\+\s*1000\)", "refNumber: expRef || 'BILL-' + Math.floor(Math.random() * 9000 + 1000)"),
    @("const rows = ledger\.map\(l => \[.*?\]\);", "const rows = ledger.map(l => [ l.id, l.type, l.category, l.amount, l.quantity || '', l.date, l.refNumber, l.description, l.isVoid ? 'VOIDED' : 'ACTIVE', l.voidReason || '' ]);"),
    @("link\.setAttribute\('download',\s*DairyOS_Financial_Statement_\s*\+\s*statementPeriod\s*\+\s*_2026\.csv\);", "link.setAttribute('download', 'DairyOS_Financial_Statement_' + statementPeriod + '_2026.csv');")
)

foreach ($replacement in $replacements) {
    $updated = [regex]::Replace($content, $replacement[0], $replacement[1])
    if ($updated -ne $content) {
        $content = $updated
        Write-Host "[REPAIRED] $($replacement[1])"
    }
}

$required = @(
    "id: 'REV-' + Date.now().toString().slice(-4)",
    "refNumber: revRef || 'REC-' + Math.floor(Math.random() * 9000 + 1000)",
    "id: 'EXP-' + Date.now().toString().slice(-4)",
    "refNumber: expRef || 'BILL-' + Math.floor(Math.random() * 9000 + 1000)",
    "const rows = ledger.map(l => [ l.id, l.type, l.category, l.amount, l.quantity || '', l.date, l.refNumber, l.description, l.isVoid ? 'VOIDED' : 'ACTIVE', l.voidReason || '' ]);",
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
