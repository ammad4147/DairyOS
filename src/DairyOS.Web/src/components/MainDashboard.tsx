import { Component, useCallback, useEffect, useState } from "react";
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
        animals?: { total?: number; milking?: number; dry?: number };
        milk?: { today_litres?: number; events?: number; last_operator?: string | null; last_shift?: string | null };
    };
    exceptions?: any[];
};

type CommandCenterDecision = {
    decision_id: string;
    title: string;
    description: string;
    priority: string;
    priority_score?: number;
    status: string;
    source?: string | null;
    created_at?: string;
};

type CommandCenterResponse = {
    status?: Record<string, unknown>;
    decisions?: { items?: CommandCenterDecision[] };
};

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

function priorityTone(priority: string): "critical" | "high" | "normal" {
    const p = priority.toUpperCase();
    if (p === "CRITICAL") return "critical";
    if (p === "HIGH") return "high";
    return "normal";
}

class SectionErrorBoundary extends Component<{ label: string; children: ReactNode }, { error: Error | null }> {
    state = { error: null as Error | null };
    static getDerivedStateFromError(error: Error) { return { error }; }
    componentDidCatch(error: Error) { console.error(`Dashboard section "${this.props.label}" crashed:`, error); }
    render() {
        if (this.state.error) {
            return <div className="dashboard-panel panel-crashed"><strong>{this.props.label} couldn't be displayed.</strong><span>{this.state.error.message}</span></div>;
        }
        return this.props.children;
    }
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
        }).finally(() => { setBusyId(null); reload(); });
    };

    if (loading && !data) return <section className="action-queue loading">Loading today's action queue…</section>;
    if (error && !data) {
        return <section className="action-queue error"><div><strong>Action queue unavailable.</strong><p>{error}</p></div><button type="button" onClick={reload}>Retry</button></section>;
    }

    const domainsChecked = Object.keys(data?.status ?? {});
    const items = (Array.isArray(data?.decisions?.items) ? data?.decisions?.items : [])
        .filter((d) => d.status !== "COMPLETED")
        .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0)
            || new Date(a.created_at ?? 0).getTime() - new Date(b.created_at ?? 0).getTime())
        .slice(0, 5);

    return (
        <section className="action-queue">
            <div className="section-heading"><div><h2>Action Queue</h2><span className="section-hint">What needs a human across the authoritative operational picture.</span></div></div>
            {items.length === 0 ? (
                <div className="action-queue-empty"><strong>Nothing needs attention right now.</strong><span>Checked: {domainsChecked.length ? domainsChecked.map(titleCase).join(" · ") : "no domains reported status"}</span></div>
            ) : (
                <div className="action-queue-list">
                    {items.map((item) => (
                        <div className={`action-row tone-${priorityTone(item.priority)}`} key={item.decision_id}>
                            <span className="action-marker" aria-hidden="true" />
                            <button type="button" className="action-body" onClick={() => onNavigate(sourceToView(item.source))}>
                                <span className="action-id">{item.decision_id}</span><span className="action-title">{item.title}</span><span className="action-detail">{item.description}</span>
                            </button>
                            <div className="action-controls">
                                {item.status === "CREATED" && <button type="button" className="ack-button" disabled={busyId === item.decision_id} onClick={() => act(item.decision_id, "acknowledge")}>Acknowledge</button>}
                                <button type="button" className="resolve-button" disabled={busyId === item.decision_id} onClick={() => act(item.decision_id, "resolve")}>Resolve</button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </section>
    );
}

function MilkPanel({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    const dashboard = useApi<DashboardPayload>("/dashboard", 60_000);
    if (dashboard.loading && !dashboard.data) return <PanelShell title="Milk Production" loading />;
    if (dashboard.error && !dashboard.data) return <PanelShell title="Milk Production" errorText={dashboard.error} onRetry={dashboard.reload} />;

    const readModel = dashboard.data?.dashboard?.milk ?? {};
    const state = dashboard.data?.operational_state ?? {};
    const productionDate = typeof state.operational_date === "string" ? state.operational_date.slice(0, 10) : null;
    const litres = Number(readModel.today_litres);
    const events = Number(readModel.events);
    const shift = readModel.last_shift ? titleCase(readModel.last_shift) : "No completed session recorded";
    const operator = readModel.last_operator ?? "No operator recorded";

    return (
        <PanelShell title="Milk Production" onOpen={() => onNavigate("milk")}>
            <div className="panel-headline"><span className="panel-headline-value">{Number.isFinite(litres) ? `${litres.toFixed(1)} L` : "—"}</span><span className="panel-headline-caption">Authoritative production</span></div>
            <p className="panel-note">{productionDate ? `Production date: ${productionDate}` : "Production date unavailable"}</p>
            <p className="panel-note muted">Last settled session: {shift} · Operator: {operator}</p>
            <div className="panel-kv-row">
                <div><span>Milk production</span><strong>{Number.isFinite(litres) ? `${litres.toFixed(1)} L` : "—"}</strong></div>
                <div><span>Recorded events</span><strong>{Number.isFinite(events) ? events : "—"}</strong></div>
            </div>
            <p className="panel-note muted">This panel renders the DairyOS dashboard read model; it does not re-sum the milk ledger in the browser.</p>
        </PanelShell>
    );
}

function HerdPanel({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    const dashboard = useApi<DashboardPayload>("/dashboard", 90_000);
    if (dashboard.loading && !dashboard.data) return <PanelShell title="Herd Dynamics" loading />;
    if (dashboard.error && !dashboard.data) return <PanelShell title="Herd Dynamics" errorText={dashboard.error} onRetry={dashboard.reload} />;

    const animals = dashboard.data?.dashboard?.animals ?? {};
    const total = Number(animals.total);
    const milking = Number(animals.milking);
    const dry = Number(animals.dry);
    const classified = (Number.isFinite(milking) ? milking : 0) + (Number.isFinite(dry) ? dry : 0);
    const unclassified = Number.isFinite(total) ? Math.max(total - classified, 0) : 0;

    return (
        <PanelShell title="Herd Dynamics" onOpen={() => onNavigate("animals")}>
            <div className="panel-headline"><span className="panel-headline-value">{Number.isFinite(total) ? total : "—"}</span><span className="panel-headline-caption">Authoritative animal count</span></div>
            <table className="panel-table"><tbody>
                <tr><td>Milking</td><td className="panel-table-value">{Number.isFinite(milking) ? milking : "—"}</td></tr>
                <tr><td>Dry</td><td className="panel-table-value">{Number.isFinite(dry) ? dry : "—"}</td></tr>
                <tr className={unclassified > 0 ? "panel-table-attention" : ""}><td>Other / unclassified</td><td className="panel-table-value">{unclassified}</td></tr>
            </tbody></table>
            <p className="panel-note muted">Milking status is read from Farm Operational State; the browser does not infer lifecycle status from registry rows.</p>
        </PanelShell>
    );
}

function HealthPanel({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    const dashboard = useApi<DashboardPayload>("/dashboard", 60_000);
    if (dashboard.loading && !dashboard.data) return <PanelShell title="Health & Vaccinations" loading />;
    if (dashboard.error && !dashboard.data) return <PanelShell title="Health & Vaccinations" errorText={dashboard.error} onRetry={dashboard.reload} />;

    const exceptions = Array.isArray(dashboard.data?.exceptions) ? dashboard.data?.exceptions : [];
    const state = dashboard.data?.operational_state ?? {};
    const healthAlerts = Array.isArray(state.health_alerts) ? state.health_alerts : [];
    const count = Math.max(exceptions.length, healthAlerts.length);

    return (
        <PanelShell title="Health & Vaccinations" onOpen={() => onNavigate("health")}>
            {count === 0 ? (
                <div className="panel-status good"><strong>No dashboard health exceptions</strong><span>Authoritative operational read model reports no active exception.</span></div>
            ) : (
                <div className="panel-status attention"><strong>{count} active exception{count === 1 ? "" : "s"}</strong><span>See the Health module for the underlying records.</span></div>
            )}
        </PanelShell>
    );
}

function ReproductionPanel({ onNavigate }: { onNavigate: (view: ViewId) => void }) {
    return <PanelShell title="Reproductive Health" onOpen={() => onNavigate("breeding")}><div className="panel-status unknown"><strong>Not yet available</strong><span>Herd-wide reproduction counts require a backend aggregate read model.</span></div></PanelShell>;
}

function PanelShell({ title, children, loading, errorText, onRetry, onOpen }: { title: string; children?: ReactNode; loading?: boolean; errorText?: string; onRetry?: () => void; onOpen?: () => void }) {
    return <article className="dashboard-panel">
        <div className="panel-heading"><h3>{title}</h3>{onOpen && <button type="button" className="panel-open" onClick={onOpen}>Open →</button>}</div>
        {loading && <div className="panel-loading">Loading…</div>}
        {errorText && <div className="panel-error"><span>{errorText}</span>{onRetry && <button type="button" onClick={onRetry}>Retry</button>}</div>}
        {!loading && !errorText && children}
    </article>;
}

function MainDashboard({ onNavigate = () => undefined }: MainDashboardProps) {
    return <div className="main-dashboard">
        <div className="dashboard-title-row"><div><h2>Dashboard</h2><p>Authoritative operational read model for the farm.</p></div></div>
        <SectionErrorBoundary label="Action Queue"><ActionQueue onNavigate={onNavigate} /></SectionErrorBoundary>
        <div className="dashboard-panel-grid">
            <SectionErrorBoundary label="Milk Production"><MilkPanel onNavigate={onNavigate} /></SectionErrorBoundary>
            <SectionErrorBoundary label="Herd Dynamics"><HerdPanel onNavigate={onNavigate} /></SectionErrorBoundary>
            <SectionErrorBoundary label="Health & Vaccinations"><HealthPanel onNavigate={onNavigate} /></SectionErrorBoundary>
            <SectionErrorBoundary label="Reproductive Health"><ReproductionPanel onNavigate={onNavigate} /></SectionErrorBoundary>
        </div>
    </div>;
}

export default MainDashboard;
