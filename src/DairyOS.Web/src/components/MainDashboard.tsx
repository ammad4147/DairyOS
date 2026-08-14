/*
 * DairyOS Main Dashboard — AA-013 v1.3 §5 implementation
 * Built 2026-08-14 against docs/03_Application_Architecture/
 * AA-013_DairyOS_Operator_Interface_Design.md, the approved baseline spec
 * with fourteen binding decisions of record (D-UI-1 .. D-UI-14).
 *
 * Scope of this pass (frontend only, per D-UI-7 "first build target is the
 * main dashboard itself"): the Action Queue and the four domain panels
 * (§5.1, §5.2). Each panel is wired to whatever its domain can answer
 * today; where the backing data does not exist yet, the panel says so
 * explicitly rather than showing a zero that could be mistaken for good
 * news (§2.1). See docs/DairyOS_Execution_Roadmap.md for what unblocks the
 * remaining greyed-out panels.
 *
 * Data sources used:
 *   - Action Queue:        GET /command-center                (real decision
 *                           lifecycle -- acknowledge/resolve are live; this
 *                           is the entity §4.1 says the future Operational
 *                           Finding extends, not replaces)
 *   - Milk Production:     GET /farm/milk/next-session, GET /farm/milk
 *   - Herd Dynamics:       GET /farm/animals
 *   - Health & Vaccinations: GET /farm/health-cases, GET /farm/health-observations
 *   - Reproductive Health: none yet -- no aggregate reproduction endpoint
 *     exists (per-animal classification only), so this panel is
 *     deliberately left in the honest "not yet available" state (§2.1)
 *     rather than duplicating dairyos.herd.reproduction.services.
 *     reproductive_event_classifier client-side, which is exactly the kind
 *     of duplication that caused the three-classifiers bug this project
 *     already paid for once (G6.1).
 */

import { Component, useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { apiUrl } from "../config/api";
import "./MainDashboard.css";

// ---------------------------------------------------------------------------
// Section error boundary -- a render crash in one section (e.g. an API
// response shape this file guessed wrong) must never blank the entire
// dashboard. Confirmed necessary the hard way: ActionQueue crashed on an
// unguarded array assumption against a real backend response, and with no
// boundary in place the whole page rendered nothing at all. Function
// components can't be error boundaries (React requirement), hence the one
// class component in this file.
// ---------------------------------------------------------------------------

type SectionErrorBoundaryState = { error: Error | null };

class SectionErrorBoundary extends Component<{ label: string; children: ReactNode }, SectionErrorBoundaryState> {
    state: SectionErrorBoundaryState = { error: null };

    static getDerivedStateFromError(error: Error): SectionErrorBoundaryState {
        return { error };
    }

    componentDidCatch(error: Error) {
        // eslint-disable-next-line no-console
        console.error(`Dashboard section "${this.props.label}" crashed:`, error);
    }

    render() {
        if (this.state.error) {
            return (
                <div className="dashboard-panel panel-crashed">
                    <strong>{this.props.label} couldn't be displayed.</strong>
                    <span>{this.state.error.message}</span>
                </div>
            );
        }
        return this.props.children;
    }
}

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

// ---------------------------------------------------------------------------
// Generic, self-contained fetch hook. Each panel below owns one of these so
// a failure or slow response in one panel never blanks the others -- the
// spec's own instruction for a first build ("panels degrade gracefully
// where sections are thin").
// ---------------------------------------------------------------------------

function useApi<T>(path: string, intervalMs = 60_000) {
    const [data, setData] = useState<T | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const load = useCallback(() => {
        setError(null);
        fetch(apiUrl(path), { headers: { Accept: "application/json" } })
            .then((response) => {
                if (!response.ok) throw new Error(`Request failed: ${response.status}`);
                return response.json() as Promise<T>;
            })
            .then((payload) => {
                setData(payload);
                setLoading(false);
            })
            .catch((loadError: Error) => {
                setError(loadError.message);
                setLoading(false);
            });
    }, [path]);

    useEffect(() => {
        load();
        const timer = window.setInterval(load, intervalMs);
        return () => window.clearInterval(timer);
    }, [load, intervalMs]);

    return { data, error, loading, reload: load };
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

type Row = Record<string, any>;

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

function titleCase(value: string | null | undefined): string {
    if (!value) return "";
    return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function sourceToView(source: string | null | undefined): ViewId {
    const s = (source ?? "").toLowerCase();
    if (s.includes("health")) return "health";
    if (s.includes("breed")) return "breeding";
    if (s.includes("milk")) return "milk";
    if (s.includes("feed")) return "feed";
    if (s.includes("workforce")) return "workforce";
    if (s.includes("inventory")) return "inventory";
    if (s.includes("equipment")) return "equipment";
    if (s.includes("financ")) return "finance";
    return "alerts";
}

// ---------------------------------------------------------------------------
// Action Queue (§5.1)
// ---------------------------------------------------------------------------

type CommandCenterDecision = {
    decision_id: string;
    title: string;
    description: string;
    priority: string;
    priority_score: number;
    owner_action_required: boolean;
    status: string; // CREATED | ACKNOWLEDGED | COMPLETED
    owner: string | null;
    source: string | null;
    outcome: string | null;
    created_at: string;
};

type CommandCenterResponse = {
    status?: Record<string, unknown>;
    attention?: unknown[];
    // NOT a bare array: OperationalCommandCenterService.snapshot() (backend)
    // builds this as {"items": [...], "count": N, "active": N} and the
    // projection assembler passes it through unchanged -- confirmed against
    // a real backend response after an earlier version of this file assumed
    // a bare array here and crashed the entire dashboard on load (uncaught
    // "(...).filter is not a function", no error boundary to contain it).
    decisions?: { items?: CommandCenterDecision[]; count?: number; active?: number };
    actions?: unknown[];
    confidence?: { operational_score?: number; health_status?: string };
};

function priorityTone(priority: string): "critical" | "high" | "normal" {
    const p = priority.toUpperCase();
    if (p === "CRITICAL") return "critical";
    if (p === "HIGH") return "high";
    return "normal";
}

function ActionQueue({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    const { data, error, loading, reload } = useApi<CommandCenterResponse>("/command-center", 45_000);
    const [busyId, setBusyId] = useState<string | null>(null);

    const act = (decisionId: string, action: "acknowledge" | "resolve") => {
        setBusyId(decisionId);
        fetch(apiUrl(`/command-center/decisions/${decisionId}/${action}`), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
        })
            .finally(() => {
                setBusyId(null);
                reload();
            });
    };

    if (loading && !data) {
        return <section className="action-queue loading">Loading today's action queue…</section>;
    }

    if (error && !data) {
        return (
            <section className="action-queue error">
                <div>
                    <strong>Action queue unavailable.</strong>
                    <p>{error}</p>
                </div>
                <button type="button" onClick={reload}>Retry</button>
            </section>
        );
    }

    const domainsChecked = Object.keys(data?.status ?? {});
    const decisionItems = data?.decisions?.items;
    const items = (Array.isArray(decisionItems) ? decisionItems : [])
        .filter((d) => d.status !== "COMPLETED")
        .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0)
            || new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
        .slice(0, 5);

    return (
        <section className="action-queue">
            <div className="section-heading">
                <div>
                    <h2>Action Queue</h2>
                    <span className="section-hint">What needs a human today, across everything.</span>
                </div>
            </div>

            {items.length === 0 ? (
                <div className="action-queue-empty">
                    <strong>Nothing needs attention right now.</strong>
                    <span>
                        Checked: {domainsChecked.length > 0 ? domainsChecked.map(titleCase).join(" · ") : "no domains reported status"}
                    </span>
                </div>
            ) : (
                <div className="action-queue-list">
                    {items.map((item) => (
                        <div className={`action-row tone-${priorityTone(item.priority)}`} key={item.decision_id}>
                            <span className="action-marker" aria-hidden="true" />
                            <button type="button" className="action-body" onClick={() => onNavigate(sourceToView(item.source))}>
                                <span className="action-id">{item.decision_id}</span>
                                <span className="action-title">{item.title}</span>
                                <span className="action-detail">{item.description}</span>
                            </button>
                            <div className="action-controls">
                                {item.status === "CREATED" && (
                                    <button
                                        type="button"
                                        className="ack-button"
                                        disabled={busyId === item.decision_id}
                                        onClick={() => act(item.decision_id, "acknowledge")}
                                    >
                                        Acknowledge
                                    </button>
                                )}
                                <button
                                    type="button"
                                    className="resolve-button"
                                    disabled={busyId === item.decision_id}
                                    onClick={() => act(item.decision_id, "resolve")}
                                >
                                    Resolve
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </section>
    );
}

// ---------------------------------------------------------------------------
// Panel 1 -- Milk Production (§5.2 Panel 1)
// ---------------------------------------------------------------------------

const GOVERNED_SESSIONS = ["MORNING", "AFTERNOON", "EVENING"];

type NextSessionResponse = {
    operational_date?: string;
    sequencing_active?: boolean;
    next_session?: string | null;
    observed_sessions?: unknown[];
    settled_sessions?: unknown[];
};

function ledgerRows(rows: Row[], date: string) {
    return rows.filter((r) =>
        r.session_ledger === true
        && String(r.status ?? "").toUpperCase() !== "NOT_MILKED"
        && recordDate(r) === date);
}

function rowTotal(row: Row): number {
    const total = Number(row.total_yield);
    if (Number.isFinite(total)) return total;
    return ["morning_yield", "afternoon_yield", "evening_yield"]
        .reduce((sum, key) => sum + (Number.isFinite(Number(row[key])) ? Number(row[key]) : 0), 0);
}

function sumLitres(rows: Row[]): number {
    return rows.reduce((sum, r) => sum + rowTotal(r), 0);
}

function formatDelta(current: number, previous: number): { text: string; tone: "up" | "down" | "flat" } {
    if (previous === 0) return { text: "no prior figure to compare", tone: "flat" };
    const pct = ((current - previous) / previous) * 100;
    const rounded = Math.round(pct);
    if (rounded === 0) return { text: "flat vs prior", tone: "flat" };
    return { text: `${rounded > 0 ? "+" : ""}${rounded}%`, tone: rounded > 0 ? "up" : "down" };
}

function MilkPanel({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    const session = useApi<NextSessionResponse>("/farm/milk/next-session", 60_000);
    const milk = useApi<Row[]>("/farm/milk", 60_000);

    if ((session.loading && !session.data) || (milk.loading && !milk.data)) {
        return <PanelShell title="Milk Production" loading />;
    }
    if ((session.error && !session.data) || (milk.error && !milk.data)) {
        return <PanelShell title="Milk Production" errorText={session.error ?? milk.error ?? undefined} onRetry={() => { session.reload(); milk.reload(); }} />;
    }

    const rows = Array.isArray(milk.data) ? milk.data : [];
    const today = todayIso();
    const yesterday = yesterdayIso();
    const todayLedger = ledgerRows(rows, today);
    const yesterdayLedger = ledgerRows(rows, yesterday);

    const sequencingActive = session.data?.sequencing_active ?? false;
    const nextSession = session.data?.next_session ?? null;
    const dayComplete = sequencingActive && !nextSession;

    const todayTotal = sumLitres(todayLedger);
    const yesterdayTotal = sumLitres(yesterdayLedger);

    let headline: { label: string; value: string; comparison: ReturnType<typeof formatDelta> };

    if (dayComplete) {
        headline = {
            label: `Today ${todayTotal.toFixed(1)} L vs ${yesterdayTotal.toFixed(1)} L yesterday`,
            value: `${todayTotal.toFixed(1)} L`,
            comparison: formatDelta(todayTotal, yesterdayTotal),
        };
    } else {
        const sessionsToday = new Set(todayLedger.map((r) => String(r.milking_session ?? "").toUpperCase()));
        const lastSession = [...GOVERNED_SESSIONS].reverse().find((s) => sessionsToday.has(s)) ?? null;
        if (lastSession) {
            const currentSessionTotal = sumLitres(todayLedger.filter((r) => String(r.milking_session ?? "").toUpperCase() === lastSession));
            const priorSessionTotal = sumLitres(yesterdayLedger.filter((r) => String(r.milking_session ?? "").toUpperCase() === lastSession));
            headline = {
                label: `${titleCase(lastSession)} ${currentSessionTotal.toFixed(1)} L vs ${priorSessionTotal.toFixed(1)} L yesterday ${titleCase(lastSession).toLowerCase()}`,
                value: `${currentSessionTotal.toFixed(1)} L`,
                comparison: formatDelta(currentSessionTotal, priorSessionTotal),
            };
        } else {
            headline = { label: "No session recorded yet today", value: "—", comparison: { text: "", tone: "flat" } };
        }
    }

    const sessionLabel = sequencingActive
        ? dayComplete
            ? "All sessions settled today"
            : `Next session due: ${titleCase(String(nextSession))}`
        : "Session sequencing not active for this farm";

    return (
        <PanelShell title="Milk Production" onOpen={() => onNavigate("milk")}>
            <div className="panel-headline">
                <span className="panel-headline-value">{headline.value}</span>
                <span className={`panel-headline-delta tone-${headline.comparison.tone}`}>{headline.comparison.text}</span>
            </div>
            <p className="panel-note">{headline.label}</p>
            <p className="panel-note muted">{sessionLabel}</p>
            <div className="panel-kv-row">
                <div><span>Today's Production</span><strong>{todayTotal.toFixed(1)} L</strong></div>
                <div><span>Milk Sold</span><strong className="unavailable">Not tracked yet</strong></div>
            </div>
            <p className="panel-note muted">Drop detection not yet built — production-drop findings will appear here once G3.4 ships.</p>
        </PanelShell>
    );
}

// ---------------------------------------------------------------------------
// Panel 2 -- Herd Dynamics (§5.2 Panel 2)
// ---------------------------------------------------------------------------

const HERD_BUCKETS: Array<{ key: string; label: string; statuses: string[] }> = [
    { key: "milking", label: "Milking", statuses: ["LACTATING"] },
    { key: "dry", label: "Dry", statuses: ["DRY"] },
    { key: "closeup", label: "Close-up", statuses: ["CLOSE_UP"] },
    { key: "heifers", label: "Heifers", statuses: ["HEIFER"] },
    { key: "calves", label: "Calves", statuses: ["CALF"] },
];

function HerdPanel({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    const animals = useApi<Row[]>("/farm/animals", 90_000);

    if (animals.loading && !animals.data) return <PanelShell title="Herd Dynamics" loading />;
    if (animals.error && !animals.data) return <PanelShell title="Herd Dynamics" errorText={animals.error} onRetry={animals.reload} />;

    const rows = (Array.isArray(animals.data) ? animals.data : []).filter((a) => a.active !== false);
    const counts = HERD_BUCKETS.map((bucket) => ({
        ...bucket,
        count: rows.filter((r) => bucket.statuses.includes(String(r.lifecycle_status ?? "").toUpperCase())).length,
    }));
    const classified = counts.reduce((sum, b) => sum + b.count, 0);
    const unclassified = rows.length - classified;

    return (
        <PanelShell title="Herd Dynamics" onOpen={() => onNavigate("animals")}>
            <div className="panel-headline">
                <span className="panel-headline-value">{rows.length}</span>
                <span className="panel-headline-caption">Total animals</span>
            </div>
            <table className="panel-table">
                <tbody>
                    {counts.map((b) => (
                        <tr key={b.key}>
                            <td>{b.label}</td>
                            <td className="panel-table-value">{b.count}</td>
                        </tr>
                    ))}
                    <tr className={unclassified > 0 ? "panel-table-attention" : ""}>
                        <td>Unclassified</td>
                        <td className="panel-table-value">{unclassified}</td>
                    </tr>
                </tbody>
            </table>
        </PanelShell>
    );
}

// ---------------------------------------------------------------------------
// Panel 3 -- Health & Vaccinations (§5.2 Panel 3)
// ---------------------------------------------------------------------------

type HealthCase = {
    case_id: string;
    animal_id: string;
    severity: string | null;
    status: string;
};

function HealthPanel({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    const openCases = useApi<{ cases: HealthCase[] }>("/farm/health-cases?status=OPEN", 60_000);
    const observations = useApi<Row[]>("/farm/health-observations", 60_000);

    if ((openCases.loading && !openCases.data) || (observations.loading && !observations.data)) {
        return <PanelShell title="Health & Vaccinations" loading />;
    }
    if (openCases.error && !openCases.data) {
        return <PanelShell title="Health & Vaccinations" errorText={openCases.error} onRetry={openCases.reload} />;
    }

    const cases = openCases.data?.cases ?? [];
    const today = todayIso();
    const observedToday = new Set(
        (Array.isArray(observations.data) ? observations.data : [])
            .filter((r) => recordDate(r) === today)
            .map((r) => r.animal_id)
            .filter(Boolean),
    ).size;

    if (cases.length === 0) {
        return (
            <PanelShell title="Health & Vaccinations" onOpen={() => onNavigate("health")}>
                {observedToday > 0 ? (
                    <div className="panel-status good">
                        <strong>No open cases</strong>
                        <span>{observedToday} animal{observedToday === 1 ? "" : "s"} observed today</span>
                    </div>
                ) : (
                    <div className="panel-status unknown">
                        <strong>No open cases</strong>
                        <span>No observations recorded today</span>
                    </div>
                )}
            </PanelShell>
        );
    }

    return (
        <PanelShell title="Health & Vaccinations" onOpen={() => onNavigate("health")}>
            <div className="panel-status attention">
                <strong>{cases.length} open case{cases.length === 1 ? "" : "s"}</strong>
                <span>{observedToday} animal{observedToday === 1 ? "" : "s"} observed today</span>
            </div>
            <ul className="panel-list">
                {cases.slice(0, 4).map((c) => (
                    <li key={c.case_id}>
                        <span className="panel-list-id">{c.case_id}</span>
                        <span>{c.animal_id}</span>
                        <span className={`severity-chip ${String(c.severity ?? "").toLowerCase()}`}>{titleCase(c.severity) || "—"}</span>
                    </li>
                ))}
            </ul>
        </PanelShell>
    );
}

// ---------------------------------------------------------------------------
// Panel 4 -- Reproductive Health (§5.2 Panel 4)
//
// No aggregate reproduction endpoint exists yet -- only per-animal
// classification (GET /farm/animals/{id}/reproduction). Computing herd-wide
// Due-for-Heat/Inseminated/Pregnant/Repeaters/Miscarriages counts here would
// mean re-implementing dairyos.herd.reproduction.services.
// reproductive_event_classifier in TypeScript: a second copy of exactly the
// kind of classification logic that produced the three-disagreeing-
// classifiers bug (G6.1) this project already fixed once. Left honestly
// unavailable per §2.1 until a real backend aggregate exists.
// ---------------------------------------------------------------------------

function ReproductionPanel({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    return (
        <PanelShell title="Reproductive Health" onOpen={() => onNavigate("breeding")}>
            <div className="panel-status unknown">
                <strong>Not yet available</strong>
                <span>
                    Herd-wide reproduction counts need a backend aggregate endpoint
                    (not yet built — see the execution roadmap). Individual animal
                    status is visible from that animal's profile.
                </span>
            </div>
        </PanelShell>
    );
}

// ---------------------------------------------------------------------------
// Shared panel shell
// ---------------------------------------------------------------------------

function PanelShell({
    title,
    children,
    loading,
    errorText,
    onRetry,
    onOpen,
}: {
    title: string;
    children?: ReactNode;
    loading?: boolean;
    errorText?: string;
    onRetry?: () => void;
    onOpen?: () => void;
}) {
    return (
        <article className="dashboard-panel">
            <div className="panel-heading">
                <h3>{title}</h3>
                {onOpen && <button type="button" className="panel-open" onClick={onOpen}>Open →</button>}
            </div>
            {loading && <div className="panel-loading">Loading…</div>}
            {errorText && (
                <div className="panel-error">
                    <span>{errorText}</span>
                    {onRetry && <button type="button" onClick={onRetry}>Retry</button>}
                </div>
            )}
            {!loading && !errorText && children}
        </article>
    );
}

// ---------------------------------------------------------------------------
// Root
// ---------------------------------------------------------------------------

function MainDashboard({ onNavigate = () => undefined }: MainDashboardProps) {
    return (
        <div className="main-dashboard">
            <div className="dashboard-title-row">
                <div>
                    <h2>Dashboard</h2>
                    <p>What needs attention today, and how the farm is running.</p>
                </div>
            </div>

            <SectionErrorBoundary label="Action Queue">
                <ActionQueue onNavigate={onNavigate} />
            </SectionErrorBoundary>

            <div className="dashboard-panel-grid">
                <SectionErrorBoundary label="Milk Production">
                    <MilkPanel onNavigate={onNavigate} />
                </SectionErrorBoundary>
                <SectionErrorBoundary label="Herd Dynamics">
                    <HerdPanel onNavigate={onNavigate} />
                </SectionErrorBoundary>
                <SectionErrorBoundary label="Health & Vaccinations">
                    <HealthPanel onNavigate={onNavigate} />
                </SectionErrorBoundary>
                <SectionErrorBoundary label="Reproductive Health">
                    <ReproductionPanel onNavigate={onNavigate} />
                </SectionErrorBoundary>
            </div>
        </div>
    );
}

export default MainDashboard;
