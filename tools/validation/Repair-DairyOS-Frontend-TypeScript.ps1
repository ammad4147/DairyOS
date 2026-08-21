[CmdletBinding()]
param(
    [string]$Repository = (Get-Location).Path,
    [switch]$CommitLocal
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $Repository

function Replace-Required {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Replacement,
        [string]$Label
    )

    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $updated = [regex]::Replace($text, $Pattern, $Replacement, [System.Text.RegularExpressions.RegexOptions]::Multiline)
    if ($updated -eq $text) {
        throw "Required frontend repair fragment not found: $Label`nFile: $Path"
    }
    Set-Content -LiteralPath $Path -Value $updated -Encoding UTF8 -NoNewline
    Write-Host "[REPAIRED] $Label"
}

$app = Join-Path $Repository 'src\DairyOS.Web\src\App.tsx'
$audit = Join-Path $Repository 'src\DairyOS.Web\src\components\AuditTab.tsx'
$dashboard = Join-Path $Repository 'src\DairyOS.Web\src\components\UnifiedDashboard.tsx'

foreach ($path in @($app, $audit, $dashboard)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required frontend source file not found: $path"
    }
}

Replace-Required `
    -Path $app `
    -Pattern "(?m)^function MainAppShell\(\) \{" `
    -Replacement @"
interface HerdAnimal {
  id: string;
  breed: string;
  category: string;
  age: string;
  status: string;
  frequency: string;
  earTag: string;
  gender?: string;
  stage?: string;
}

function MainAppShell() {
"@ `
    -Label 'App.tsx herd animal type declaration'

Replace-Required `
    -Path $app `
    -Pattern "const \[animals, setAnimals\] = useState\(\[" `
    -Replacement "const [animals, setAnimals] = useState<HerdAnimal[]>([" `
    -Label 'App.tsx typed animals state'

Replace-Required `
    -Path $audit `
    -Pattern "a\.resolutionReason" `
    -Replacement "a.resolutionNotes" `
    -Label 'AuditTab resolution notes property'

Replace-Required `
    -Path $audit `
    -Pattern "a\.reinstatementReason" `
    -Replacement "a.reinstateReason" `
    -Label 'AuditTab reinstatement reason property'

Replace-Required `
    -Path $dashboard `
    -Pattern "const reproData = data\?\.reproduction \|\| \{ onHeat: 1, inseminated: 1, pregnant: 2, conceptionRatio: '62%' \};" `
    -Replacement @"
const reproSource = data?.reproduction as {
  onHeat?: number;
  inseminated?: number;
  pregnant?: number;
  conceptionRatio?: string;
} | undefined;
const reproData = {
  onHeat: reproSource?.onHeat ?? 1,
  inseminated: reproSource?.inseminated ?? 1,
  pregnant: reproSource?.pregnant ?? 2,
  conceptionRatio: reproSource?.conceptionRatio ?? '62%'
};
"@ `
    -Label 'UnifiedDashboard reproduction data normalization'

Write-Host '[OK] Frontend TypeScript semantic repairs applied.'

if ($CommitLocal) {
    $status = git status --porcelain -- `
        src/DairyOS.Web/src/App.tsx `
        src/DairyOS.Web/src/components/AuditTab.tsx `
        src/DairyOS.Web/src/components/UnifiedDashboard.tsx

    if (-not $status) {
        Write-Host '[OK] No TypeScript source changes required.'
        exit 0
    }

    git add -- `
        src/DairyOS.Web/src/App.tsx `
        src/DairyOS.Web/src/components/AuditTab.tsx `
        src/DairyOS.Web/src/components/UnifiedDashboard.tsx

    git commit -m 'fix(UI): resolve frontend TypeScript semantic errors'
    if ($LASTEXITCODE -ne 0) {
        throw 'Frontend TypeScript repair commit failed.'
    }
}
