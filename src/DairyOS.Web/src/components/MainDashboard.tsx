/**
 * MainDashboard — DairyOS Command Dashboard
 * Compliant with DairyOS architecture constraints (2026-08-18)
 *
 * Operator-facing rules:
 * - No relative date language ("today"/"yesterday").
 * - Explicit production date only.
 * - No frontend business calculations or classifications of farm facts.
 * - Dashboard is a read-model projection.
 * - Normal operator UI describes an animal as:
 *       MILKING → 2 sessions
 *       MILKING → 3 sessions
 *       NON-MILKING → governed operational reason
 * - Frequency history/change governance remains a backend/veterinary concern.
 * - Animal Passport drawer uses the existing authoritative endpoint.
 */

import {
  Component,
  useCallback,
  useEffect,
  useState,
} from "react";
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

type MainDashboardProps = {
  onNavigate?: (view: ViewId) => void;
};

type DashboardPayload = {
  operational_state?: Record<string, any>;

  dashboard?: {
    animals?: {
      total?: number;
      milking?: number;
      dry?: number;
      milking_percentage?: number | null;
    };

    milk?: {
      production_date?: string | null;
      previous_production_date?: string | null;
      litres?: number | null;
      previous_litres?: number | null;
      morning_litres?: number | null;
      afternoon_litres?: number | null;
      evening_litres?: number | null;
      events?: number | null;
      last_operator?: string | null;
      last_shift?: string | null;
      change_percent?: number | null;
      comparison_status?: string | null;
    };

    health?: {
      status?: string | null;
      active_exceptions?: number | null;
      critical_cases?: number | null;
    };
  };

  exceptions?: any[];
  farm_status?: string;
  health?: string;
};

type PassportData = {
  animal?: Record<string, any>;
  schedule?: {
    effective?: {
      milking_frequency?: string | null;
      expected_sessions?: string[] | null;
      source?: string | null;
    } | null;
  };
  history?: Record<string, any[]>;
  record_counts?: Record<string, number>;
  timeline?: any[];
};

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

function useApi<T>(
  path: string,
  intervalMs = 60_000,
) {
  const [data, setData] =
    useState<T | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(true);

  const load = useCallback(() => {
    setError(null);

    fetch(apiUrl(path), {
      headers: {
        Accept: "application/json",
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Request failed: ${response.status}`,
          );
        }

        return response.json() as Promise<T>;
      })
      .then((payload) => {
        setData(payload);
        setLoading(false);
      })
      .catch((exc: Error) => {
        setError(exc.message);
        setLoading(false);
      });
  }, [path]);

  useEffect(() => {
    load();

    const timer =
      window.setInterval(
        load,
        intervalMs,
      );

    return () =>
      window.clearInterval(timer);
  }, [
    load,
    intervalMs,
  ]);

  return {
    data,
    error,
    loading,
    reload: load,
  };
}

function titleCase(
  value:
    | string
    | null
    | undefined,
) {
  if (!value) {
    return "—";
  }

  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}

function fmtL(
  value:
    | number
    | null
    | undefined,
) {
  if (
    value == null ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  return `${value.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 1,
    },
  )} L`;
}

function fmtNum(
  value:
    | number
    | null
    | undefined,
) {
  if (
    value == null ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  return value.toLocaleString();
}

/**
 * Display only the persisted calendar date.
 * No timezone conversion is performed.
 */
function displayDate(
  iso:
    | string
    | null
    | undefined,
): string {
  if (!iso) {
    return "—";
  }

  return String(iso).slice(0, 10);
}

/**
 * Operator vocabulary for the animal's current milking state.
 *
 * This deliberately hides backend vocabulary such as:
 *   TWICE_DAILY
 *   THRICE_DAILY
 *
 * Frequency history and effective-date governance remain available
 * to backend/veterinary workflows and are not represented as normal
 * operator controls here.
 */
function milkingPlanLabel(
  frequency:
    | string
    | null
    | undefined,
  expectedSessions?:
    | string[]
    | null,
): string {
  if (
    Array.isArray(
      expectedSessions,
    ) &&
    expectedSessions.length === 2
  ) {
    return "2 sessions";
  }

  if (
    Array.isArray(
      expectedSessions,
    ) &&
    expectedSessions.length === 3
  ) {
    return "3 sessions";
  }

  const normalized =
    String(
      frequency ?? "",
    )
      .trim()
      .toUpperCase();

  if (
    normalized ===
      "TWICE_DAILY" ||
    normalized === "TWICE" ||
    normalized === "2" ||
    normalized === "2X"
  ) {
    return "2 sessions";
  }

  if (
    normalized ===
      "THRICE_DAILY" ||
    normalized ===
      "THREE_TIMES_DAILY" ||
    normalized === "THRICE" ||
    normalized === "3" ||
    normalized === "3X"
  ) {
    return "3 sessions";
  }

  return "Plan unavailable";
}

function operationalMilkingLabel(
  animal: Record<string, any>,
): {
  status: "MILKING" | "NON-MILKING";
  detail: string;
} {
  const isMilking =
    animal.is_currently_milking ===
    true;

  if (isMilking) {
    const plan =
      milkingPlanLabel(
        animal.milking_frequency,
        animal.expected_sessions,
      );

    return {
      status: "MILKING",
      detail: plan,
    };
  }

  const reason =
    animal.non_milking_reason ??
    animal.non_milking_category ??
    animal.operational_category ??
    animal.lifecycle_status ??
    "Reason recorded";

  return {
    status: "NON-MILKING",
    detail: titleCase(
      String(reason),
    ),
  };
}

/* ------------------------------------------------------------------ */
/* Error Boundary                                                     */
/* ------------------------------------------------------------------ */

class SectionErrorBoundary extends Component<
  {
    label: string;
    children: ReactNode;
  },
  {
    error: Error | null;
  }
> {
  state = {
    error: null as Error | null,
  };

  static getDerivedStateFromError(
    error: Error,
  ) {
    return {
      error,
    };
  }

  componentDidCatch(
    error: Error,
  ) {
    console.error(
      `Dashboard section "${this.props.label}" crashed:`,
      error,
    );
  }

  render() {
    if (this.state.error) {
      return (
        <div className="dash-panel crashed">
          <strong>
            {this.props.label} could not
            be displayed
          </strong>

          <span>
            {this.state.error.message}
          </span>
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
  const [
    passport,
    setPassport,
  ] =
    useState<PassportData | null>(
      null,
    );

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(
      null,
    );

  useEffect(() => {
    if (!animalId) {
      setPassport(null);
      return;
    }

    setLoading(true);
    setError(null);

    fetch(
      apiUrl(
        `/farm/animals/${encodeURIComponent(
          animalId,
        )}/passport`,
      ),
      {
        headers: {
          Accept:
            "application/json",
        },
      },
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Passport ${response.status}`,
          );
        }

        return response.json();
      })
      .then((payload) => {
        setPassport(payload);
        setLoading(false);
      })
      .catch((exc: Error) => {
        setError(exc.message);
        setLoading(false);
      });
  }, [animalId]);

  if (!animalId) {
    return null;
  }

  const animal =
    passport?.animal ?? {};

  const counts =
    passport?.record_counts ?? {};

  const schedule =
    passport?.schedule?.effective ??
    null;

  const operationalState =
    operationalMilkingLabel({
      ...animal,
      milking_frequency:
        animal.milking_frequency ??
        schedule?.milking_frequency,
      expected_sessions:
        schedule?.expected_sessions,
    });

  return (
    <>
      <div
        className="passport-backdrop"
        onClick={onClose}
      />

      <aside className="passport-drawer">
        <div className="passport-header">
          <div>
            <div className="passport-eyebrow">
              Animal Passport
            </div>

            <h2>
              #{animalId}
            </h2>
          </div>

          <button
            type="button"
            className="passport-close"
            onClick={onClose}
            aria-label="Close Animal Passport"
          >
            ×
          </button>
        </div>

        {loading && (
          <div className="passport-loading">
            Loading passport…
          </div>
        )}

        {error && (
          <div className="passport-error">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          passport && (
            <div className="passport-body">
              <div className="passport-identity">
                <div className="id-row">
                  <span>
                    Ear Tag
                  </span>

                  <strong>
                    {animal.ear_tag ??
                      "—"}
                  </strong>
                </div>

                <div className="id-row">
                  <span>
                    Lifecycle
                  </span>

                  <strong>
                    {titleCase(
                      animal.lifecycle_status,
                    )}
                  </strong>
                </div>

                <div className="id-row">
                  <span>
                    Breed
                  </span>

                  <strong>
                    {animal.breed ??
                      "—"}
                  </strong>
                </div>

                <div className="id-row">
                  <span>
                    Birth
                  </span>

                  <strong>
                    {animal.date_of_birth
                      ? displayDate(
                          animal.date_of_birth,
                        )
                      : "—"}
                  </strong>
                </div>

                <div className="id-row">
                  <span>
                    Operational status
                  </span>

                  <strong
                    className={
                      operationalState.status ===
                      "MILKING"
                        ? "ok"
                        : ""
                    }
                  >
                    {operationalState.status}
                  </strong>
                </div>

                <div className="id-row">
                  <span>
                    Milking plan
                  </span>

                  <strong>
                    {operationalState.detail}
                  </strong>
                </div>
              </div>

              <div className="passport-section">
                <h3>
                  Record Counts
                </h3>

                <div className="count-grid">
                  {Object.entries(
                    counts,
                  ).map(
                    ([key, value]) => (
                      <div
                        key={key}
                        className="count-chip"
                      >
                        <span>
                          {titleCase(
                            key,
                          )}
                        </span>

                        <strong>
                          {value}
                        </strong>
                      </div>
                    ),
                  )}
                </div>
              </div>

              <div className="passport-section">
                <h3>
                  Integrated History
                </h3>

                <div className="history-links">
                  <button type="button">
                    Health History
                  </button>

                  <button type="button">
                    Feed Cost Reconciliation
                  </button>

                  <button type="button">
                    Reproductive Logs
                  </button>

                  <button type="button">
                    Milk History
                  </button>

                  <button type="button">
                    Treatments
                  </button>
                </div>
              </div>

              {schedule && (
                <div className="passport-section">
                  <h3>
                    Milking Plan
                  </h3>

                  <div className="schedule-box">
                    <div>
                      Status:{" "}
                      <strong>
                        {
                          operationalState.status
                        }
                      </strong>
                    </div>

                    <div>
                      Plan:{" "}
                      <strong>
                        {
                          operationalState.detail
                        }
                      </strong>
                    </div>
                  </div>

                  {operationalState.status ===
                    "NON-MILKING" && (
                    <div className="passport-note">
                      <span>
                        Operational reason:
                      </span>

                      <strong>
                        {
                          operationalState.detail
                        }
                      </strong>
                    </div>
                  )}
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

function KpiStrip({
  data,
}: {
  data: DashboardPayload | null;
}) {
  const animals =
    data?.dashboard?.animals ??
    {};

  const milk =
    data?.dashboard?.milk ??
    {};

  const milking =
    Number(animals.milking);

  const total =
    Number(animals.total);

  const percentage =
    Number(
      animals.milking_percentage,
    );

  const litres =
    Number(milk.litres);

  const productionDate =
    displayDate(
      milk.production_date,
    );

  const changePercent =
    Number(
      milk.change_percent,
    );

  const comparisonStatus =
    String(
      milk.comparison_status ??
        "",
    ).toUpperCase();

  const previousDate =
    displayDate(
      milk.previous_production_date,
    );

  const changeText =
    Number.isFinite(
      changePercent,
    ) &&
    previousDate !== "—"
      ? `${
          changePercent >= 0
            ? "+"
            : ""
        }${changePercent.toFixed(
          1,
        )}% vs ${previousDate}`
      : null;

  return (
    <div className="kpi-strip">
      <div className="kpi-card">
        <div className="kpi-label">
          Total Milking Animals
        </div>

        <div className="kpi-value">
          {fmtNum(milking)}
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-label">
          Total Animals
        </div>

        <div className="kpi-value">
          {fmtNum(total)}
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-label">
          Milking Percentage
        </div>

        <div className="kpi-value accent">
          {Number.isFinite(
            percentage,
          )
            ? `${percentage.toFixed(
                1,
              )}%`
            : "—"}
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-label">
          Production Yield
        </div>

        <div className="kpi-value">
          {fmtL(litres)}
        </div>

        <div className="kpi-date">
          {productionDate !==
          "—"
            ? productionDate
            : "Date not provided by read model"}
        </div>

        {changeText &&
          comparisonStatus !==
            "NO_COMPARISON" && (
            <div className="kpi-delta">
              {changeText}
            </div>
          )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Health Status                                                      */
/* ------------------------------------------------------------------ */

function HealthStatusCard({
  data,
  onNavigate,
}: {
  data: DashboardPayload | null;
  onNavigate: (
    view: ViewId,
  ) => void;
}) {
  const health =
    data?.dashboard?.health ??
    {};

  const status =
    String(
      health.status ?? "",
    ).toUpperCase();

  const activeExceptions =
    Number(
      health.active_exceptions,
    );

  const criticalCases =
    Number(
      health.critical_cases,
    );

  const known =
    Boolean(status) ||
    Number.isFinite(
      activeExceptions,
    ) ||
    Number.isFinite(
      criticalCases,
    );

  const tone =
    status === "RED"
      ? "critical"
      : status ===
          "AMBER"
        ? "warning"
        : status ===
            "GREEN"
          ? "good"
          : "unknown";

  return (
    <div
      className={`status-card tone-${tone}`}
    >
      <div className="status-header">
        <h3>
          Health Status
        </h3>

        <button
          type="button"
          className="link-btn"
          onClick={() =>
            onNavigate(
              "health",
            )
          }
        >
          Open →
        </button>
      </div>

      {known ? (
        <div className="status-body">
          <div
            className={`status-badge ${tone}`}
          >
            {tone ===
            "critical"
              ? "RED"
              : tone ===
                  "warning"
                ? "AMBER"
                : tone ===
                    "good"
                  ? "GREEN"
                  : "—"}
          </div>

          <p>
            <strong>
              {Number.isFinite(
                activeExceptions,
              )
                ? `${activeExceptions} animal${
                    activeExceptions ===
                    1
                      ? ""
                      : "s"
                  } requiring attention`
                : "Health status available"}
            </strong>
          </p>

          <p className="muted">
            Critical cases:{" "}
            {Number.isFinite(
              criticalCases,
            )
              ? criticalCases
              : "—"}
          </p>
        </div>
      ) : (
        <div className="status-body">
          <div className="status-badge">
            —
          </div>

          <p>
            No health aggregate was
            supplied by the dashboard
            read model.
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
  onNavigate: (
    view: ViewId,
  ) => void;
}) {
  const animals =
    data?.dashboard?.animals ??
    {};

  const milking =
    Number(animals.milking) ||
    0;

  const dry =
    Number(animals.dry) ||
    0;

  const total =
    Number(animals.total) ||
    milking + dry;

  const other =
    Math.max(
      total -
        milking -
        dry,
      0,
    );

  const segments = [
    {
      label: "Milking",
      value: milking,
      color: "#22c55e",
    },
    {
      label: "Dry",
      value: dry,
      color: "#f59e0b",
    },
    {
      label: "Other",
      value: other,
      color: "#64748b",
    },
  ].filter(
    (segment) =>
      segment.value > 0,
  );

  const sum =
    segments.reduce(
      (totalValue, segment) =>
        totalValue +
        segment.value,
      0,
    ) || 1;

  return (
    <div className="status-card">
      <div className="status-header">
        <h3>
          Herd Development
        </h3>

        <button
          type="button"
          className="link-btn"
          onClick={() =>
            onNavigate(
              "animals",
            )
          }
        >
          Open →
        </button>
      </div>

      <div className="herd-visual">
        <div className="herd-bar">
          {segments.map(
            (segment) => (
              <div
                key={
                  segment.label
                }
                className="herd-seg"
                style={{
                  width: `${
                    (segment.value /
                      sum) *
                    100
                  }%`,
                  background:
                    segment.color,
                }}
                title={`${segment.label}: ${segment.value}`}
              />
            ),
          )}
        </div>

        <div className="herd-legend">
          {segments.map(
            (segment) => (
              <div
                key={
                  segment.label
                }
                className="legend-item"
              >
                <span
                  className="dot"
                  style={{
                    background:
                      segment.color,
                  }}
                />

                {segment.label}{" "}
                <strong>
                  {
                    segment.value
                  }
                </strong>
              </div>
            ),
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Yield Snapshot                                                     */
/* ------------------------------------------------------------------ */

function YieldSnapshot({
  data,
}: {
  data: DashboardPayload | null;
}) {
  const milk =
    data?.dashboard?.milk ??
    {};

  const litres =
    Number(milk.litres);

  const morning =
    Number(
      milk.morning_litres,
    );

  const afternoon =
    Number(
      milk.afternoon_litres,
    );

  const evening =
    Number(
      milk.evening_litres,
    );

  const productionDate =
    displayDate(
      milk.production_date,
    );

  const hasSplit = [
    morning,
    afternoon,
    evening,
  ].some((value) =>
    Number.isFinite(value),
  );

  return (
    <div className="status-card">
      <div className="status-header">
        <h3>
          Milk Production
        </h3>
      </div>

      <div className="yield-big">
        {fmtL(litres)}
      </div>

      <div className="yield-sub">
        Production date:{" "}
        {productionDate !==
        "—"
          ? productionDate
          : "Not yet provided by the read model"}
      </div>

      {hasSplit ? (
        <div className="shift-grid">
          <div>
            <span>
              Morning
            </span>

            <strong>
              {fmtL(morning)}
            </strong>
          </div>

          <div>
            <span>
              Afternoon
            </span>

            <strong>
              {fmtL(afternoon)}
            </strong>
          </div>

          <div>
            <span>
              Evening
            </span>

            <strong>
              {fmtL(evening)}
            </strong>
          </div>
        </div>
      ) : (
        <div className="shift-grid single">
          <div>
            <span>
              Last settled
              session
            </span>

            <strong>
              {titleCase(
                milk.last_shift,
              )}
            </strong>
          </div>

          <div>
            <span>
              Operator
            </span>

            <strong>
              {milk.last_operator ??
                "—"}
            </strong>
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
          <h3>
            Milking Animals
          </h3>
        </div>
      </div>

      <div className="table-empty">
        Not yet provided by the read
        model.
        <br />

        <span className="muted">
          An authoritative
          milking-animals list will
          appear here once the
          backend projection supplies
          it.
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main Component                                                     */
/* ------------------------------------------------------------------ */

function MainDashboard({
  onNavigate = () =>
    undefined,
}: MainDashboardProps) {
  const dashboard =
    useApi<DashboardPayload>(
      "/dashboard",
      45_000,
    );

  const [
    passportId,
    setPassportId,
  ] =
    useState<string | null>(
      null,
    );

  const data =
    dashboard.data;

  return (
    <div className="main-dashboard dark">
      <div className="dash-title-row">
        <div>
          <h1>
            Dairy OS
          </h1>

          <p>
            Live operational
            picture · Authoritative
            read model
          </p>
        </div>

        <div className="dash-meta">
          {data?.farm_status && (
            <span className="meta-pill">
              Farm ·{" "}
              {titleCase(
                data.farm_status,
              )}
            </span>
          )}

          <button
            type="button"
            className="ghost-btn"
            onClick={
              dashboard.reload
            }
          >
            Refresh
          </button>
        </div>
      </div>

      {dashboard.error &&
        !data && (
          <div className="dash-error-banner">
            Dashboard unavailable:{" "}
            {
              dashboard.error
            }

            <button
              onClick={
                dashboard.reload
              }
            >
              Retry
            </button>
          </div>
        )}

      <SectionErrorBoundary label="KPI Strip">
        <KpiStrip
          data={data}
        />
      </SectionErrorBoundary>

      <div className="dash-grid-3">
        <SectionErrorBoundary label="Yield Snapshot">
          <YieldSnapshot
            data={data}
          />
        </SectionErrorBoundary>

        <SectionErrorBoundary label="Herd Development">
          <HerdDevelopmentCard
            data={data}
            onNavigate={
              onNavigate
            }
          />
        </SectionErrorBoundary>

        <SectionErrorBoundary label="Health Status">
          <HealthStatusCard
            data={data}
            onNavigate={
              onNavigate
            }
          />
        </SectionErrorBoundary>
      </div>

      <SectionErrorBoundary label="Milking Animals">
        <MilkingAnimalsPlaceholder />
      </SectionErrorBoundary>

      <AnimalPassportDrawer
        animalId={passportId}
        onClose={() =>
          setPassportId(null)
        }
      />
    </div>
  );
}

export default MainDashboard;
