$ErrorActionPreference = "Stop"
Set-Location D:\DairyOS

Write-Host "`n=== DASHBOARD KPI AUTHORITY CORRECTION ===" -ForegroundColor Cyan

$target = ".\src\DairyOS.Web\src\components\MainDashboard.tsx"
if (-not (Test-Path $target)) {
    throw "Missing target: $target"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = ".\_backups\MainDashboard.tsx_kpi_authority_$stamp.bak"
New-Item -ItemType Directory -Force ".\_backups" | Out-Null
Copy-Item $target $backup -Force
Write-Host "Backup created: $backup" -ForegroundColor Yellow

$content = Get-Content $target -Raw

# ---------------------------------------------------------------------------
# 1. Extend the dashboard contract types with backend-owned KPI fields.
# ---------------------------------------------------------------------------

$content = $content.Replace(
    "      dry?: number;`r`n    };",
    "      dry?: number;`r`n      milking_percentage?: number | null;`r`n    };"
)

$content = $content.Replace(
    "      last_shift?: string | null;`r`n    };",
    "      last_shift?: string | null;`r`n      change_percent?: number | null;`r`n      comparison_status?: string | null;`r`n    };`r`n    health?: {`r`n      status?: string | null;`r`n      active_exceptions?: number | null;`r`n      critical_cases?: number | null;`r`n    };"
)

# Also support LF-only files.
$content = $content.Replace(
    "      dry?: number;`n    };",
    "      dry?: number;`n      milking_percentage?: number | null;`n    };"
)
$content = $content.Replace(
    "      last_shift?: string | null;`n    };",
    "      last_shift?: string | null;`n      change_percent?: number | null;`n      comparison_status?: string | null;`n    };`n    health?: {`n      status?: string | null;`n      active_exceptions?: number | null;`n      critical_cases?: number | null;`n    };"
)

# ---------------------------------------------------------------------------
# 2. Replace KpiStrip: display backend-owned KPI values only.
# ---------------------------------------------------------------------------

$kpiReplacement = @'
function KpiStrip({ data }: { data: DashboardPayload | null }) {
  const animals = data?.dashboard?.animals ?? {};
  const milk = data?.dashboard?.milk ?? {};

  const milking = Number(animals.milking);
  const total = Number(animals.total);
  const percentage = Number(animals.milking_percentage);
  const litres = Number(milk.litres);
  const productionDate = displayDate(milk.production_date);
  const changePercent = Number(milk.change_percent);
  const comparisonStatus = String(milk.comparison_status ?? "").toUpperCase();
  const previousDate = displayDate(milk.previous_production_date);

  const changeText = Number.isFinite(changePercent) && previousDate !== "—"
    ? `${changePercent >= 0 ? "+" : ""}${changePercent.toFixed(1)}% vs ${previousDate}`
    : null;

  return (
    <div className="kpi-strip">
      <div className="kpi-card">
        <div className="kpi-label">Total Milking Animals</div>
        <div className="kpi-value">{fmtNum(milking)}</div>
      </div>
      <div className="kpi-card">
        <div className="kpi-label">Total Animals</div>
        <div className="kpi-value">{fmtNum(total)}</div>
      </div>
      <div className="kpi-card">
        <div className="kpi-label">Milking Percentage</div>
        <div className="kpi-value accent">
          {Number.isFinite(percentage) ? `${percentage.toFixed(1)}%` : "—"}
        </div>
      </div>
      <div className="kpi-card">
        <div className="kpi-label">Production Yield</div>
        <div className="kpi-value">{fmtL(litres)}</div>
        <div className="kpi-date">
          {productionDate !== "—" ? productionDate : "Date not provided by read model"}
        </div>
        {changeText && comparisonStatus !== "NO_COMPARISON" && (
          <div className="kpi-delta">{changeText}</div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Health Status (backend authority)                                  */
/* ------------------------------------------------------------------ */
'@

$kpiPattern = '(?s)function KpiStrip\(\{ data \}: \{ data: DashboardPayload \| null \}\).*?/\* ------------------------------------------------------------------ \*/\s*/\* Health Status \(safe terminology\)\s*\*/'
if (-not [regex]::IsMatch($content, $kpiPattern)) {
    throw "Could not locate KpiStrip block. Refusing to edit the file."
}
$content = [regex]::Replace($content, $kpiPattern, $kpiReplacement, 1)

# ---------------------------------------------------------------------------
# 3. Replace HealthStatusCard: no Math.max(), no frontend severity threshold.
# ---------------------------------------------------------------------------

$healthReplacement = @'
function HealthStatusCard({
  data,
  onNavigate,
}: {
  data: DashboardPayload | null;
  onNavigate: (v: ViewId) => void;
}) {
  const health = data?.dashboard?.health ?? {};
  const status = String(health.status ?? "").toUpperCase();
  const activeExceptions = Number(health.active_exceptions);
  const criticalCases = Number(health.critical_cases);

  const known = Boolean(status)
    || Number.isFinite(activeExceptions)
    || Number.isFinite(criticalCases);

  const tone =
    status === "RED"
      ? "critical"
      : status === "AMBER"
        ? "warning"
        : status === "GREEN"
          ? "good"
          : "unknown";

  return (
    <div className={`status-card tone-${tone}`}>
      <div className="status-header">
        <h3>Health Status</h3>
        <button type="button" className="link-btn" onClick={() => onNavigate("health")}>
          Open →
        </button>
      </div>

      {known ? (
        <div className="status-body">
          <div className={`status-badge ${tone}`}>
            {tone === "critical" ? "RED" : tone === "warning" ? "AMBER" : tone === "good" ? "GREEN" : "—"}
          </div>
          <p>
            <strong>
              {Number.isFinite(activeExceptions)
                ? `${activeExceptions} animal${activeExceptions === 1 ? "" : "s"} requiring attention`
                : "Health status available"}
            </strong>
          </p>
          <p className="muted">
            Critical cases: {Number.isFinite(criticalCases) ? criticalCases : "—"}
          </p>
        </div>
      ) : (
        <div className="status-body">
          <div className="status-badge">—</div>
          <p>No health aggregate was supplied by the dashboard read model.</p>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Herd Development                                                   */
/* ------------------------------------------------------------------ */
'@

$healthPattern = '(?s)function HealthStatusCard\(.*?/\* ------------------------------------------------------------------ \*/\s*/\* Herd Development\s*\*/'
if (-not [regex]::IsMatch($content, $healthPattern)) {
    throw "Could not locate HealthStatusCard block. Refusing to edit the file."
}
$content = [regex]::Replace($content, $healthPattern, $healthReplacement, 1)

Set-Content $target $content -Encoding UTF8
Write-Host "Corrected: $target" -ForegroundColor Green

Write-Host "`n=== FRONTEND BUILD ===" -ForegroundColor Cyan
Set-Location .\src\DairyOS.Web
npm run build

Set-Location ..\..
Write-Host "`n=== PYTHON COMPILE ===" -ForegroundColor Cyan
python -m compileall -q src

Write-Host "`n=== TARGETED DASHBOARD TESTS ===" -ForegroundColor Cyan
pytest -q tests/dashboard/test_dashboard_projection_service.py

Write-Host "`n=== AUTHORITY AUDIT ===" -ForegroundColor Cyan
Get-ChildItem .\src\DairyOS.Web\src\components -Recurse -File `
    -Include *.tsx,*.ts |
    Select-String `
        -Pattern `
        "sumLitres|pctChange|Math\.max\(exceptions|Math\.max\(health|filter\(.*milking|is_currently_milking|previousDate|GOVERNED_SESSIONS" |
    Select-Object Path,LineNumber,Line

Write-Host "`nDashboard KPI authority correction complete." -ForegroundColor Green
Write-Host "Review git diff before committing/pushing the local frontend change." -ForegroundColor Yellow
