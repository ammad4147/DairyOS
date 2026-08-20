import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "../config/api";
import "./UnifiedDashboard.css";

type ViewId =
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

type Props = { onNavigate?: (view: ViewId) => void };
type Row = Record<string, unknown>;

type DashboardPayload = {
    farm_status?: string;
    operational_state?: { operational_date?: string; animals?: Record<string, Row> };
    dashboard?: {
        animals?: { total?: number; milking?: number; dry?: number; milking_percentage?: number | null };
        milk?: { production_date?: string | null; litres?: number | null; morning_litres?: number | null; afternoon_litres?: number | null; evening_litres?: number | null; last_operator?: string | null; last_shift?: string | null; previous_production_date?: string | null; change_percent?: number | null; comparison_status?: string | null };
        health?: { status?: string | null; active_exceptions?: number | null; critical_cases?: number | null };
        feed?: { today_kg?: number | null; events?: number | null; last_feed_type?: string | null };
        freshness?: { last_event?: string | null; last_event_time?: string | null };
        operational_decisions?: Row[];
        operational_decision_summary?: Row;
        exceptions?: Row[];
        heads_up_notifications?: Row[];
    };
    dashboard_view?: {
        quick_actions?: Row[];
        farm_timeline?: Row[];
        owner_attention?: Row[];
    };
    operational_decisions?: Row[];
    operational_decision_summary?: Row;
    exceptions?: Row[];
};

function value(value: unknown): string {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
}

function dateOnly(value: unknown): string {
    return value ? String(value).slice(0, 10) : "—";
}

function numberValue(value: unknown): string {
    if (typeof value !== "number" || !Number.isFinite(value)) return "—";
    return value.toLocaleString();
}

function litres(value: unknown): string {
    if (typeof value !== "number" || !Number.isFinite(value)) return "—";
    return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} L`;
}

function tone(value: unknown): string {
    const normalized = String(value ?? "").toUpperCase();
    if (/RED|CRITICAL|FAILED|ERROR/.test(normalized)) return "danger";
    if (/AMBER|WARNING|OPEN|PENDING/.test(normalized)) return "warning";
    return "good";
}

function title(value: unknown): string {
    return String(value ?? "—").replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function UnifiedDashboard({ onNavigate = () => undefined }: Props) {
    const [data, setData] = useState<DashboardPayload | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setError(null);
        try {
            const response = await fetch(apiUrl("/dashboard"), { headers: { Accept: "application/json" } });
            if (!response.ok) throw new Error(`Dashboard request failed: ${response.status}`);
            setData((await response.json()) as DashboardPayload);
        } catch (exc) {
            setError(exc instanceof Error ? exc.message : "Unable to load the dashboard");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void load();
        const timer = window.setInterval(() => void load(), 45_000);
        return () => window.clearInterval(timer);
    }, [load]);

    const animals = data?.dashboard?.animals ?? {};
    const milk = data?.dashboard?.milk ?? {};
    const health = data?.dashboard?.health ?? {};
    const feed = data?.dashboard?.feed ?? {};
    const freshness = data?.dashboard?.freshness ?? {};
    const animalRows = Object.values(data?.operational_state?.animals ?? {});
    const decisions = data?.operational_decisions ?? data?.dashboard?.operational_decisions ?? [];
    const exceptions = data?.exceptions ?? data?.dashboard?.exceptions ?? [];
    const attention = [...decisions, ...exceptions];
    const quickActions = data?.dashboard_view?.quick_actions ?? [];

    if (loading && !data) {
        return <section className="unified-dashboard"><div className="dashboard-loading">Loading the authoritative farm dashboard…</div></section>;
    }

    return (
        <section className="unified-dashboard">
            <div className="dashboard-header">
                <div>
                    <div className="dashboard-kicker">DAIRYOS COMMAND DASHBOARD</div>
                    <h1>Farm Operations</h1>
                    <p>Server-produced operational picture. No frontend business classification or metric reconciliation.</p>
                </div>
                <div className="dashboard-header-meta">
                    <span>Operational date <strong>{dateOnly(data?.operational_state?.operational_date)}</strong></span>
                    <span>Farm <strong>{title(data?.farm_status)}</strong></span>
                    <button type="button" onClick={() => void load()}>Refresh</button>
                </div>
            </div>

            {error && <div className="dashboard-warning"><strong>Refresh warning:</strong> {error}</div>}

            <div className="dashboard-kpis">
                <Kpi label="Total Animals" value={numberValue(animals.total)} />
                <Kpi label="Milking Animals" value={numberValue(animals.milking)} />
                <Kpi label="Milking Percentage" value={animals.milking_percentage == null ? "—" : `${animals.milking_percentage}%`} />
                <Kpi label="Milk Production" value={litres(milk.litres)} detail={dateOnly(milk.production_date)} />
                <Kpi label="Health" value={title(health.status)} tone={tone(health.status)} detail={`Critical ${numberValue(health.critical_cases)}`} />
                <Kpi label="Feed" value={feed.today_kg == null ? "—" : `${numberValue(feed.today_kg)} kg`} detail={feed.last_feed_type ? title(feed.last_feed_type) : "No latest feed type"} />
            </div>

            <div className="dashboard-grid">
                <section className="dashboard-panel attention-panel">
                    <div className="panel-heading"><div><span>ATTENTION</span><h2>Decisions & Exceptions</h2></div><button type="button" onClick={() => onNavigate("alerts")}>Open alerts →</button></div>
                    {attention.length ? (
                        <div className="attention-list">
                            {attention.slice(0, 8).map((item, index) => (
                                <div className="attention-item" key={String(item.id ?? item.decision_id ?? index)}>
                                    <span className={`attention-priority ${tone(item.priority ?? item.severity)}`}>{value(item.priority ?? item.severity ?? "ATTENTION")}</span>
                                    <div><strong>{value(item.title ?? item.event_type ?? item.observation ?? item.message ?? "Operational item")}</strong><small>{value(item.animal_id ?? item.source ?? item.status)}</small></div>
                                    <span>{value(item.action ?? item.recommended_action ?? item.status)}</span>
                                </div>
                            ))}
                        </div>
                    ) : <Empty text="No active attention items supplied by the command-center projection." />}
                </section>

                <section className="dashboard-panel milk-panel">
                    <div className="panel-heading"><div><span>PRODUCTION</span><h2>Milk Snapshot</h2></div><button type="button" onClick={() => onNavigate("milk")}>Open milk →</button></div>
                    <div className="milk-total">{litres(milk.litres)}</div>
                    <div className="milk-date">Production date: {dateOnly(milk.production_date)}</div>
                    <div className="milk-sessions">
                        <Metric label="Morning" value={litres(milk.morning_litres)} />
                        <Metric label="Afternoon" value={litres(milk.afternoon_litres)} />
                        <Metric label="Evening" value={litres(milk.evening_litres)} />
                    </div>
                    <div className="panel-foot">Last operator: <strong>{value(milk.last_operator)}</strong> · Last session: <strong>{title(milk.last_shift)}</strong></div>
                </section>

                <section className="dashboard-panel freshness-panel">
                    <div className="panel-heading"><div><span>OPERATING STATE</span><h2>Farm Pulse</h2></div></div>
                    <div className="pulse-grid">
                        <Metric label="Health exceptions" value={numberValue(health.active_exceptions)} />
                        <Metric label="Critical cases" value={numberValue(health.critical_cases)} />
                        <Metric label="Feed events" value={numberValue(feed.events)} />
                        <Metric label="Last event" value={title(freshness.last_event)} />
                    </div>
                    <div className="panel-foot">Latest event time: <strong>{value(freshness.last_event_time)}</strong></div>
                </section>

                <section className="dashboard-panel herd-panel">
                    <div className="panel-heading"><div><span>HERD</span><h2>Current Milking State</h2></div><button type="button" onClick={() => onNavigate("animals")}>Open animals →</button></div>
                    <div className="herd-summary"><strong>{numberValue(animals.milking)}</strong><span>currently milking</span><strong>{numberValue(animals.dry)}</strong><span>dry / non-milking</span></div>
                    <div className="herd-table-wrap">
                        <table><thead><tr><th>Animal</th><th>Lifecycle</th><th>Operational state</th><th>Plan</th></tr></thead><tbody>
                            {animalRows.slice(0, 12).map((animal, index) => <tr key={String(animal.animal_id ?? index)}><td><strong>{value(animal.animal_id)}</strong></td><td>{title(animal.lifecycle_status)}</td><td>{animal.is_currently_milking ? "MILKING" : value(animal.non_milking_reason ?? animal.status)}</td><td>{value(animal.milking_frequency)}</td></tr>)}
                        </tbody></table>
                    </div>
                    {!animalRows.length && <Empty text="No authoritative animal projection supplied." />}
                </section>
            </div>

            <section className="dashboard-panel quick-panel">
                <div className="panel-heading"><div><span>WORKFLOW</span><h2>Quick Actions</h2></div></div>
                <div className="quick-actions">
                    {(quickActions.length ? quickActions : [{ id: "record_milk", title: "Record Milk" }, { id: "feed_animals", title: "Feed Animals" }, { id: "health_check", title: "Health Check" }, { id: "record_treatment", title: "Treatment" }]).map((action) => <button type="button" key={String(action.id)} onClick={() => onNavigate(action.id === "record_milk" ? "milk" : action.id === "feed_animals" ? "feed" : action.id === "health_check" ? "health" : "health")}>{value(action.title)}</button>)}
                </div>
            </section>
        </section>
    );
}

function Kpi({ label, value, detail, tone: kpiTone }: { label: string; value: string; detail?: string; tone?: string }) {
    return <div className={`dashboard-kpi ${kpiTone ?? ""}`}><span>{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</div>;
}

function Metric({ label, value }: { label: string; value: string }) {
    return <div className="dashboard-metric"><span>{label}</span><strong>{value}</strong></div>;
}

function Empty({ text }: { text: string }) {
    return <div className="dashboard-empty">{text}</div>;
}
