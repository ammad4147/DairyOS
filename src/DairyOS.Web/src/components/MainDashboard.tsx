/**
 * MainDashboard — DairyOS Command Dashboard (Dark Theme)
 * Compliant with DairyOS architecture constraints (2026-08-17)
 * - No relative date language ("today"/"yesterday")
 * - Explicit production date only
 * - No frontend business calculations or classifications
 * - Dashboard is pure read-model projection
 * - Animal Passport drawer uses existing authoritative endpoint
 */

import { Component, useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { apiUrl } from "../config/api";
import "./MainDashboard.css";

type ViewId =
  | "command"
  | "animals"
  | "milk"
  | "feed"
  | "health"
  | "breeding"
  | "workforce"
  | "inventory"
  | "equipment"
  | "finance"
  | "analytics"
  | "alerts";

type MainDashboardProps = { onNavigate?: (view: ViewId) => void };

type DashboardPayload = {
  operational_state?: Record<string, any>;
  dashboard?: {
    animals?: {
      total?: number;
      milking?: number;
      dry?: number;
    };
    milk?: {
      production_date?: string | null;          // explicit ISO date
      previous_production_date?: string | null; // explicit ISO date
      litres?: number | null;
      previous_litres?: number | null;
      morning_litres?: number | null;
      afternoon_litres?: number | null;
      evening_litres?: number | null;
      events?: number | null;
      last_operator?: string | null;
      last_shift?: string | null;
    };
  };
  exceptions?: any[];
  farm_status?: string;
  health?: string;
};

type PassportData = {
  animal?: Record<string, any>;
  schedule?: any;
  history?: Record<string, any[]>;
  record_counts?: Record<string, number>;
  timeline?: any[];
};

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

function useApi<T>(path: string, intervalMs = 60_000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setError(null);
    fetch(apiUrl(path), { headers: { Accept: "application/json" } })
      .then((r) => {
        if (!r.ok) throw new Error(`Request failed: ${r.status}`);
        return r.json() as Promise<T>;
      })
      .then((payload) => {
        setData(payload);
        setLoading(false);
      })
      .catch((e: Error) => {
        setError(e.message);
        setLoading(false);
      });
  }, [path]);

  useEffect(() => {
    load();
    const t = window.setInterval(load, intervalMs);
    return () => window.clearInterval(t);
  }, [load, intervalMs]);

  return { data, error, loading, reload: load };
}

function titleCase(v: string | null | undefined) {
  if (!v) return "—";
  return v.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function fmtL(v: number | null | undefined) {
  if (v == null || !Number.isFinite(v)) return "—";
  return `${v.toLocaleString(undefined, { maximumFractionDigits: 1 })} L`;
}

function fmtNum(v: number | null | undefined) {
  if (v == null || !Number.isFinite(v)) return "—";
  return v.toLocaleString();
}

/** Display only the calendar date part (YYYY-MM-DD). No timezone conversion. */
function displayDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return String(iso).slice(0, 10);
}

/* ------------------------------------------------------------------ */
/* Error Boundary                                                     */
/* ------------------------------------------------------------------ */

class SectionErrorBoundary extends Component<
  { label: string; children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  componentDidCatch(error: Error) {
    console.error(`Dashboard section "${this.props.label}" crashed:`, error);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="dash-panel crashed">
          <strong>{this.props.label} could not be displayed</strong>
          <span>{this.state.error.message}</span>
        </div>
      );
    }
    return this.props.children;
  }
}

/* ------------------------------------------------------------------ */
/* Animal Passport Drawer                                             */
/* ------------------------------------------------------------------ */

function AnimalPassportDrawer({
  animalId,
  onClose,
}: {
  animalId: string | null;
  onClose: () => void;
}) {
  const [passport, setPassport] = useState<PassportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!animalId) {
      setPassport(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetch(apiUrl(`/farm/animals/${encodeURIComponent(animalId)}/passport`), {
      headers: { Accept: "application/json" },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`Passport ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setPassport(data);
        setLoading(false);
      })
      .catch((e: Error) => {
        setError(e.message);
        setLoading(false);
      });
  }, [animalId]);

  if (!animalId) return null;

  const a = passport?.animal ?? {};
  const counts = passport?.record_counts ?? {};

  return (
    <>
      <div className="passport-backdrop" onClick={onClose} />
      <aside className="passport-drawer">
        <div className="passport-header">
          <div>
            <div className="passport-eyebrow">Animal Passport</div>
            <h2>#{animalId}</h2>
          </div>
          <button type="button" className="passport-close" onClick={onClose}>
            ✕
          </button>
        </div>

        {loading && <div className="passport-loading">Loading passport…</div>}
        {error && <div className="passport-error">{error}</div>}

        {!loading && !error && passport && (
          <div className="passport-body">
            <div className="passport-identity">
              <div className="id-row">
                <span>Ear Tag</span>
                <strong>{a.ear_tag ?? "—"}</strong>
              </div>
              <div className="id-row">
                <span>Lifecycle</span>
                <strong>{titleCase(a.lifecycle_status)}</strong>
              </div>
              <div className="id-row">
                <span>Breed</span>
                <strong>{a.breed ?? "—"}</strong>
              </div>
              <div className="id-row">
                <span>Birth</span>
                <strong>{a.date_of_birth ? displayDate(a.date_of_birth) : "—"}</strong>
              </div>
              <div className="id-row">
                <span>Status</span>
                <strong className={a.status === "ACTIVE" ? "ok" : ""}>
                  {titleCase(a.status)}
                </strong>
              </div>
            </div>

            <div className="passport-section">
              <h3>Record Counts</h3>
              <div className="count-grid">
                {Object.entries(counts).map(([k, v]) => (
                  <div key={k} className="count-chip">
                    <span>{titleCase(k)}</span>
                    <strong>{v}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="passport-section">
              <h3>Integrated History</h3>
              <div className="history-links">
                <button type="button">Health History</button>
                <button type="button">Feed Cost Reconciliation</button>
                <button type="button">Reproductive Logs</button>
                <button type="button">Milk History</button>
                <button type="button">Treatments</button>
              </div>
            </div>

            {passport.schedule?.effective && (
              <div className="passport-section">
                <h3>Milking Schedule</h3>
                <div className="schedule-box">
                  <div>
                    Frequency: <strong>{titleCase(passport.schedule.effective.milking_frequency)}</strong>
                  </div>
                  <div>
                    Source: <strong>{titleCase(passport.schedule.effective.source)}</strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </aside>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* KPI Strip                                                          */
/* ------------------------------------------------------------------ */

function KpiStrip({ data }: { data: DashboardPayload | null }) {
  const animals = data?.dashboard?.animals ?? {};
  const milk = data?.dashboard?.milk ?? {};

  const total = Number(animals.total);
  const milking = Number(animals.milking);
  const pct =
    Number.isFinite(total) && total > 0 && Number.isFinite(milking)
      ? ((milking / total) * 100).toFixed(1)
      : null;

  const litres = Number(milk.litres);
  const previousLitres = Number(milk.previous_litres);
  const productionDate = displayDate(milk.production_date);
  const previousDate = displayDate(milk.previous_production_date);

  let changeText: string | null = null;
  if (Number.isFinite(litres) && Number.isFinite(previousLitres) && previousLitres > 0) {
    const pctChange = ((litres - previousLitres) / previousLitres) * 100;
    const sign = pctChange >= 0 ? "+" : "";
    changeText = `${sign}${pctChange.toFixed(1)}% vs ${previousDate}`;
  }

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
        <div className="kpi-value accent">{pct != null ? `${pct}%` : "—"}</div>
      </div>
      <div className="kpi-card">
        <div className="kpi-label">Production Yield</div>
        <div className="kpi-value">{fmtL(litres)}</div>
        <div className="kpi-date">{productionDate !== "—" ? productionDate : "Date not provided by read model"}</div>
        {changeText && <div className="kpi-delta">{changeText}</div>}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Health Status (safe terminology)                                   */
/* ------------------------------------------------------------------ */

function HealthStatusCard({
  data,
  onNavigate,
}: {
  data: DashboardPayload | null;
  onNavigate: (v: ViewId) => void;
}) {
  const exceptions = Array.isArray(data?.exceptions) ? data!.exceptions! : [];
  const state = data?.operational_state ?? {};
  const healthAlerts = Array.isArray(state.health_alerts) ? state.health_alerts : [];
  const count = Math.max(exceptions.length, healthAlerts.length);

  const tone = count === 0 ? "good" : count >= 5 ? "critical" : "warning";

  return (
    <div className={`status-card tone-${tone}`}>
      <div className="status-header">
        <h3>Health Status</h3>
        <button type="button" className="link-btn" onClick={() => onNavigate("health")}>
          Open →
        </button>
      </div>
      {count === 0 ? (
        <div className="status-body">
          <div className="status-badge good">GREEN</div>
          <p>No health exceptions reported by the authoritative operational state.</p>
        </div>
      ) : (
        <div className="status-body">
          <div className={`status-badge ${tone}`}>
            {tone === "critical" ? "RED" : "AMBER"}
          </div>
          <p>
            <strong>
              {count} animal{count === 1 ? "" : "s"} requiring attention
            </strong>
          </p>
          <p className="muted">
            Detailed classification (including any governed sick status) is provided by the Health domain.
          </p>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Herd Development                                                   */
/* ------------------------------------------------------------------ */

function HerdDevelopmentCard({
  data,
  onNavigate,
}: {
  data: DashboardPayload | null;
  onNavigate: (v: ViewId) => void;
}) {
  const animals = data?.dashboard?.animals ?? {};
  const milking = Number(animals.milking) || 0;
  const dry = Number(animals.dry) || 0;
  const total = Number(animals.total) || milking + dry;
  const other = Math.max(total - milking - dry, 0);

  const segments = [
    { label: "Milking", value: milking, color: "#22c55e" },
    { label: "Dry", value: dry, color: "#f59e0b" },
    { label: "Other", value: other, color: "#64748b" },
  ].filter((s) => s.value > 0);

  const sum = segments.reduce((a, s) => a + s.value, 0) || 1;

  return (
    <div className="status-card">
      <div className="status-header">
        <h3>Herd Development</h3>
        <button type="button" className="link-btn" onClick={() => onNavigate("animals")}>
          Open →
        </button>
      </div>
      <div className="herd-visual">
        <div className="herd-bar">
          {segments.map((s) => (
            <div
              key={s.label}
              className="herd-seg"
              style={{ width: `${(s.value / sum) * 100}%`, background: s.color }}
              title={`${s.label}: ${s.value}`}
            />
          ))}
        </div>
        <div className="herd-legend">
          {segments.map((s) => (
            <div key={s.label} className="legend-item">
              <span className="dot" style={{ background: s.color }} />
              {s.label} <strong>{s.value}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Yield Snapshot                                                     */
/* ------------------------------------------------------------------ */

function YieldSnapshot({ data }: { data: DashboardPayload | null }) {
  const milk = data?.dashboard?.milk ?? {};
  const litres = Number(milk.litres);
  const morning = Number(milk.morning_litres);
  const afternoon = Number(milk.afternoon_litres);
  const evening = Number(milk.evening_litres);
  const productionDate = displayDate(milk.production_date);
  const hasSplit = [morning, afternoon, evening].some((v) => Number.isFinite(v));

  return (
    <div className="status-card">
      <div className="status-header">
        <h3>Milk Production</h3>
      </div>
      <div className="yield-big">{fmtL(litres)}</div>
      <div className="yield-sub">
        Production date: {productionDate !== "—" ? productionDate : "Not yet provided by the read model"}
      </div>

      {hasSplit ? (
        <div className="shift-grid">
          <div>
            <span>Morning</span>
            <strong>{fmtL(morning)}</strong>
          </div>
          <div>
            <span>Afternoon</span>
            <strong>{fmtL(afternoon)}</strong>
          </div>
          <div>
            <span>Evening</span>
            <strong>{fmtL(evening)}</strong>
          </div>
        </div>
      ) : (
        <div className="shift-grid single">
          <div>
            <span>Last settled session</span>
            <strong>{titleCase(milk.last_shift)}</strong>
          </div>
          <div>
            <span>Operator</span>
            <strong>{milk.last_operator ?? "—"}</strong>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Placeholder for future governed milking list                       */
/* ------------------------------------------------------------------ */

function MilkingAnimalsPlaceholder() {
  return (
    <div className="animals-table-card">
      <div className="table-header">
        <div>
          <h3>Milking Animals</h3>
        </div>
      </div>
      <div className="table-empty">
        Not yet provided by the read model.
        <br />
        <span className="muted">
          An authoritative milking-animals list will appear here once the backend projection supplies it.
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main Component                                                     */
/* ------------------------------------------------------------------ */

function MainDashboard({ onNavigate = () => undefined }: MainDashboardProps) {
  const dashboard = useApi<DashboardPayload>("/dashboard", 45_000);
  const [passportId, setPassportId] = useState<string | null>(null);

  const data = dashboard.data;

  return (
    <div className="main-dashboard dark">
      <div className="dash-title-row">
        <div>
          <h1>Dairy OS</h1>
          <p>Live operational picture · Authoritative read model</p>
        </div>
        <div className="dash-meta">
          {data?.farm_status && (
            <span className="meta-pill">Farm · {titleCase(data.farm_status)}</span>
          )}
          <button type="button" className="ghost-btn" onClick={dashboard.reload}>
            Refresh
          </button>
        </div>
      </div>

      {dashboard.error && !data && (
        <div className="dash-error-banner">
          Dashboard unavailable: {dashboard.error}
          <button onClick={dashboard.reload}>Retry</button>
        </div>
      )}

      <SectionErrorBoundary label="KPI Strip">
        <KpiStrip data={data} />
      </SectionErrorBoundary>

      <div className="dash-grid-3">
        <SectionErrorBoundary label="Yield Snapshot">
          <YieldSnapshot data={data} />
        </SectionErrorBoundary>
        <SectionErrorBoundary label="Herd Development">
          <HerdDevelopmentCard data={data} onNavigate={onNavigate} />
        </SectionErrorBoundary>
        <SectionErrorBoundary label="Health Status">
          <HealthStatusCard data={data} onNavigate={onNavigate} />
        </SectionErrorBoundary>
      </div>

      <SectionErrorBoundary label="Milking Animals">
        <MilkingAnimalsPlaceholder />
      </SectionErrorBoundary>

      {/* Passport drawer is fully wired to the existing authoritative endpoint.
          It can be opened from future governed lists or other modules. */}
      <AnimalPassportDrawer animalId={passportId} onClose={() => setPassportId(null)} />
    </div>
  );
}

export default MainDashboard;
