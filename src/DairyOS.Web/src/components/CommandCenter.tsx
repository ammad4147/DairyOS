/*
 * DairyOS Dashboard — complete replacement
 * Version: 1.0.0 | 2026-08-12
 * Purpose: Replace the congested command-center projection with a focused
 * operator dashboard: compact exception icons, Quick Access navigation,
 * enlarged clickable At a Glance metrics, and operational summary panels.
 * Currency display: PKR (Pakistan Rupees).
 * Audit/UX findings addressed: dashboard clutter, oversized attention panel,
 * duplicated entry points, poor discoverability of the animal-centric surface.
 *
 * PowerShell deployment/rollback (run from D:\DairyOS after copying this file):
 * $t='D:\DairyOS\src\DairyOS.Web\src\components\CommandCenter.tsx';$b='D:\DairyOS\_backups';New-Item -ItemType Directory -Force $b|Out-Null;Copy-Item $t (Join-Path $b ('CommandCenter.tsx_'+(Get-Date -Format yyyyMMdd_HHmmss)+'.bak')) -Force;Write-Host 'Replace this file with the complete repository version, then run npm run build.'
 * Rollback: Copy-Item (Get-ChildItem 'D:\DairyOS\_backups\CommandCenter.tsx_*.bak'|Sort-Object LastWriteTime -Descending|Select-Object -First 1).FullName $t -Force
 */

import React from "react";
import type {
    DashboardResponse,
    DashboardWidget,
    OperationalAnimalState,
    OperationalDecision,
} from "../models/dashboard";
import { getDashboard } from "../api/dashboardClient";
import "./CommandCenter.css";

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

type CommandCenterProps = {
    onNavigate?: (view: ViewId) => void;
};

type Metric = {
    label: string;
    value: string;
    detail?: string;
    tone?: "default" | "attention" | "positive";
    target: ViewId;
};

type IconName =
    | "health"
    | "feed"
    | "milk"
    | "breeding"
    | "workforce"
    | "inventory"
    | "equipment"
    | "finance"
    | "animals"
    | "more";

const exceptionItems: Array<{
    label: string;
    icon: IconName;
    target: ViewId;
    color: string;
}> = [
    { label: "Health", icon: "health", target: "health", color: "red" },
    { label: "Feeding", icon: "feed", target: "feed", color: "orange" },
    { label: "Milk", icon: "milk", target: "milk", color: "blue" },
    { label: "Breeding", icon: "breeding", target: "breeding", color: "green" },
    { label: "Workforce", icon: "workforce", target: "workforce", color: "purple" },
    { label: "Inventory", icon: "inventory", target: "inventory", color: "amber" },
    { label: "Equipment", icon: "equipment", target: "equipment", color: "cyan" },
    { label: "Finance", icon: "finance", target: "finance", color: "emerald" },
];

const quickAccess: Array<{ label: string; icon: IconName; target: ViewId }> = [
    { label: "Animals", icon: "animals", target: "animals" },
    { label: "Milk", icon: "milk", target: "milk" },
    { label: "Feeding", icon: "feed", target: "feed" },
    { label: "Health", icon: "health", target: "health" },
    { label: "Breeding", icon: "breeding", target: "breeding" },
    { label: "Finance", icon: "finance", target: "finance" },
];

function Icon({ name }: { name: IconName }) {
    const common = {
        width: 20,
        height: 20,
        viewBox: "0 0 24 24",
        fill: "none",
        stroke: "currentColor",
        strokeWidth: 1.8,
        strokeLinecap: "round" as const,
        strokeLinejoin: "round" as const,
        "aria-hidden": true,
    };

    switch (name) {
        case "health":
            return <svg {...common}><path d="M20.8 8.7c0 5.1-8.8 10-8.8 10s-8.8-4.9-8.8-10A4.8 4.8 0 0 1 12 6a4.8 4.8 0 0 1 8.8 2.7Z" /><path d="M7.5 9.5h2l1-2.5 2 5 1-2.5h3" /></svg>;
        case "feed":
            return <svg {...common}><path d="M6 20v-7.5a6 6 0 0 1 12 0V20" /><path d="M4 20h16" /><path d="M8 7V4h8v3" /><path d="M8 16h8" /></svg>;
        case "milk":
            return <svg {...common}><path d="M8 3h8" /><path d="M9 3v5l-2 3v9h10v-9l-2-3V3" /><path d="M7 11h10" /></svg>;
        case "breeding":
            return <svg {...common}><path d="M5 19c2-5 4-8 7-8s5 3 7 8" /><circle cx="12" cy="7" r="3" /><path d="M4 5c1.5 1 3 1 4.5 0M15.5 5c1.5 1 3 1 4.5 0" /></svg>;
        case "workforce":
            return <svg {...common}><circle cx="9" cy="8" r="3" /><circle cx="17" cy="9" r="2.5" /><path d="M3.5 20c.5-4 2.5-6 5.5-6s5 2 5.5 6" /><path d="M14 15c2.8.2 4.5 1.8 5 5" /></svg>;
        case "inventory":
            return <svg {...common}><path d="m4 8 8-4 8 4-8 4-8-4Z" /><path d="M4 8v8l8 4 8-4V8" /><path d="M12 12v8" /></svg>;
        case "equipment":
            return <svg {...common}><path d="M14 5a4 4 0 0 0-5 5l-6 6 3 3 6-6a4 4 0 0 0 5-5l-2 2-2-2 1-3Z" /><path d="M17 4l3 3" /></svg>;
        case "finance":
            return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M15 8.5c-.8-.7-1.8-1-3-1-1.7 0-3 .8-3 2s1.2 1.8 3 2c1.8.2 3 .8 3 2s-1.3 2-3 2c-1.2 0-2.3-.3-3.1-1" /><path d="M12 5.5v2M12 16.5v2" /></svg>;
        case "animals":
            return <svg {...common}><path d="M5 10V7l3-2 4 2 4-2 3 2v3" /><path d="M6 10v7a6 6 0 0 0 12 0v-7" /><path d="M9 14h.01M15 14h.01" /><path d="M9 18c1.8 1.2 4.2 1.2 6 0" /></svg>;
        case "more":
            return <svg {...common}><circle cx="5" cy="12" r="1" fill="currentColor" /><circle cx="12" cy="12" r="1" fill="currentColor" /><circle cx="19" cy="12" r="1" fill="currentColor" /></svg>;
    }
}

function formatNumber(value: unknown, fallback = "—") {
    if (value === null || value === undefined || value === "") return fallback;
    if (typeof value === "number") return value.toLocaleString("en-PK");
    return String(value);
}

function formatPkr(value: unknown) {
    if (typeof value !== "number") return value ? String(value) : "—";
    return `PKR ${value.toLocaleString("en-PK", { maximumFractionDigits: 0 })}`;
}

function numericValue(...values: unknown[]) {
    for (const value of values) {
        if (typeof value === "number" && Number.isFinite(value)) return value;
        if (typeof value === "string" && value.trim() !== "" && Number.isFinite(Number(value))) return Number(value);
    }
    return undefined;
}

function findWidget(widgets: DashboardWidget[], terms: string[]) {
    const normalized = terms.map((term) => term.toLowerCase());
    return widgets.find((widget) => {
        const text = `${widget.widget_id} ${widget.title} ${widget.subtitle ?? ""}`.toLowerCase();
        return normalized.some((term) => text.includes(term));
    });
}

function allWidgets(dashboard: DashboardResponse) {
    return dashboard.dashboard_view?.layout?.zones?.flatMap((zone) => zone.widgets ?? []) ?? [];
}

function stateMetric(state: Record<string, unknown> | undefined, keys: string[]) {
    if (!state) return undefined;
    for (const key of keys) {
        const value = state[key];
        const number = numericValue(value);
        if (number !== undefined) return number;
        if (value && typeof value === "object") {
            const nested = value as Record<string, unknown>;
            const nestedValue = numericValue(nested.value, nested.count, nested.total, nested.today, nested.open);
            if (nestedValue !== undefined) return nestedValue;
        }
    }
    return undefined;
}

function decisionCount(decisions: OperationalDecision[], terms: string[]) {
    const normalized = terms.map((term) => term.toLowerCase());
    return decisions.filter((decision) => {
        const text = `${decision.type ?? ""} ${decision.action ?? ""} ${decision.title ?? ""} ${decision.source ?? ""}`.toLowerCase();
        return normalized.some((term) => text.includes(term));
    }).length;
}

function animalCount(animals: Record<string, OperationalAnimalState> | undefined) {
    return animals ? Object.keys(animals).length : undefined;
}

function statusText(value: unknown) {
    if (typeof value !== "string") return "";
    return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function MetricCard({ metric, onNavigate }: { metric: Metric; onNavigate: (view: ViewId) => void }) {
    return (
        <button type="button" className={`glance-card ${metric.tone ?? "default"}`} onClick={() => onNavigate(metric.target)}>
            <span className="glance-label">{metric.label}</span>
            <strong className="glance-value">{metric.value}</strong>
            {metric.detail && <span className="glance-detail">{metric.detail}</span>}
            <span className="glance-link">View details <span aria-hidden="true">→</span></span>
        </button>
    );
}

function CommandCenter({ onNavigate = () => undefined }: CommandCenterProps) {
    const [dashboard, setDashboard] = React.useState<DashboardResponse | null>(null);
    const [error, setError] = React.useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = React.useState<string>("Loading…");

    const load = React.useCallback(() => {
        setError(null);
        getDashboard()
            .then((payload) => {
                setDashboard(payload);
                setLastUpdated("Updated just now");
            })
            .catch((loadError: Error) => setError(loadError.message));
    }, []);

    React.useEffect(() => {
        load();
        const interval = window.setInterval(load, 60_000);
        return () => window.clearInterval(interval);
    }, [load]);

    if (error) {
        return (
            <section className="dashboard-error">
                <div>
                    <h2>Dashboard unavailable</h2>
                    <p>{error}</p>
                </div>
                <button type="button" onClick={load}>Retry</button>
            </section>
        );
    }

    if (!dashboard) {
        return <section className="dashboard-loading">Loading live farm picture…</section>;
    }

    const runtime = dashboard.dashboard ?? {};
    const state = dashboard.operational_state ?? {};
    const decisions = dashboard.operational_decisions ?? [];
    const widgets = allWidgets(dashboard);
    const animals = animalCount(state.animals);
    const milkState = state.milk_status as Record<string, unknown> | undefined;
    const healthState = state.health_status as Record<string, unknown> | undefined;
    const breedingState = state.breeding_status as Record<string, unknown> | undefined;
    const workforceState = state.workforce_status as Record<string, unknown> | undefined;
    const inventoryState = state.inventory_status as Record<string, unknown> | undefined;
    const equipmentState = state.equipment_status as Record<string, unknown> | undefined;
    const financialState = state.financial_status as Record<string, unknown> | undefined;

    const milkToday = numericValue(
        runtime.milk?.today_litres,
        findWidget(widgets, ["milk today", "today milk", "milk"])?.value,
        stateMetric(milkState, ["today_litres", "today_l", "today"]),
    );
    const milkingNow = numericValue(
        stateMetric(milkState, ["milking_now", "lactating", "milking"]),
        findWidget(widgets, ["milking now", "milking"] )?.value,
    );
    const healthOpen = numericValue(
        stateMetric(healthState, ["open_issues", "open", "attention", "alerts"]),
        decisionCount(decisions, ["health", "mastitis", "lameness", "treatment"]),
    );
    const breedingDue = numericValue(
        stateMetric(breedingState, ["due", "due_breeding", "upcoming"]),
        decisionCount(decisions, ["breeding", "insemination", "heat"]),
    );
    const feedLow = numericValue(
        stateMetric(inventoryState, ["feed_low", "low_feed", "feed_low_stock"]),
        decisionCount(decisions, ["feed", "low stock"]),
    );
    const workers = numericValue(
        stateMetric(workforceState, ["active_workers", "active", "on_duty"]),
    );
    const equipmentDown = numericValue(
        stateMetric(equipmentState, ["down", "equipment_down", "out_of_service"]),
        decisionCount(decisions, ["equipment", "breakdown", "out of service"]),
    );
    const expense = numericValue(
        financialState && (financialState.today_expense ?? financialState.expense_today ?? financialState.today_expenses),
        widgets.find((widget) => widget.title.toLowerCase().includes("expense"))?.value,
    );

    const metrics: Metric[] = [
        { label: "Total Animals", value: formatNumber(animals), detail: "Herd register", target: "animals" },
        { label: "Milking Now", value: formatNumber(milkingNow), detail: "Current milking herd", target: "milk" },
        { label: "Milk Today", value: milkToday === undefined ? "—" : `${milkToday.toLocaleString("en-PK")} L`, detail: "Recorded production", target: "milk", tone: "positive" },
        { label: "Open Health Issues", value: formatNumber(healthOpen), detail: "Requires attention", target: "health", tone: healthOpen ? "attention" : "default" },
        { label: "Due Breeding", value: formatNumber(breedingDue), detail: "Upcoming actions", target: "breeding" },
        { label: "Feed Low Stock", value: formatNumber(feedLow), detail: "Below minimum", target: "inventory", tone: feedLow ? "attention" : "default" },
        { label: "Active Workers", value: formatNumber(workers), detail: "Current workforce", target: "workforce" },
        { label: "Equipment Down", value: formatNumber(equipmentDown), detail: "Needs attention", target: "equipment", tone: equipmentDown ? "attention" : "default" },
        { label: "Today's Expense", value: formatPkr(expense), detail: "Recorded today", target: "finance" },
    ];

    const exceptionCounts: Record<string, number> = {
        Health: decisionCount(decisions, ["health", "mastitis", "lameness", "treatment"]),
        Feeding: decisionCount(decisions, ["feed", "feeding"]),
        Milk: decisionCount(decisions, ["milk", "milking"]),
        Breeding: decisionCount(decisions, ["breeding", "insemination", "heat"]),
        Workforce: decisionCount(decisions, ["workforce", "worker"]),
        Inventory: decisionCount(decisions, ["inventory", "stock"]),
        Equipment: decisionCount(decisions, ["equipment", "breakdown"]),
        Finance: decisionCount(decisions, ["finance", "expense", "cash"]),
    };

    return (
        <div className="command-center">
            <div className="dashboard-title-row">
                <div>
                    <h2>Dashboard</h2>
                    <p>Real-time overview of farm operations</p>
                </div>
                <div className="dashboard-controls">
                    <div className="farm-selector">Trident Dairies <span>⌄</span></div>
                    <button type="button" className="refresh-button" onClick={load} aria-label="Refresh dashboard">↻</button>
                </div>
            </div>

            <section className="dashboard-section compact-section">
                <div className="section-heading">
                    <div>
                        <h3>Exceptions &amp; Attention</h3>
                        <span className="section-hint">Select an icon to open that domain.</span>
                    </div>
                    <span className="updated-indicator"><span />{lastUpdated}</span>
                </div>
                <div className="exception-strip">
                    {exceptionItems.map((item) => (
                        <button
                            type="button"
                            key={item.label}
                            className={`exception-icon ${item.color}`}
                            onClick={() => onNavigate(item.target)}
                            title={`Open ${item.label}`}
                        >
                            <span className="exception-glyph"><Icon name={item.icon} /></span>
                            {exceptionCounts[item.label] > 0 && <span className="exception-count">{exceptionCounts[item.label]}</span>}
                            <span className="exception-label">{item.label}</span>
                        </button>
                    ))}
                    <button type="button" className="exception-icon more" onClick={() => onNavigate("alerts")} title="Open all alerts">
                        <span className="exception-glyph"><Icon name="more" /></span>
                        <span className="exception-label">More</span>
                    </button>
                </div>
            </section>

            <section className="dashboard-section quick-access-section">
                <div className="section-heading">
                    <div>
                        <h3>Quick Access</h3>
                        <span className="section-hint">Navigate directly to an operating domain.</span>
                    </div>
                </div>
                <div className="quick-access-grid">
                    {quickAccess.map((item) => (
                        <button type="button" key={item.label} className="quick-access-button" onClick={() => onNavigate(item.target)}>
                            <span className="quick-access-icon"><Icon name={item.icon} /></span>
                            <span>{item.label}</span>
                            <span className="quick-access-arrow">→</span>
                        </button>
                    ))}
                </div>
            </section>

            <section className="dashboard-section glance-section">
                <div className="section-heading">
                    <div>
                        <h3>At a Glance</h3>
                        <span className="section-hint">Every metric opens the relevant operating tab.</span>
                    </div>
                    <span className="updated-indicator"><span />Live</span>
                </div>
                <div className="glance-grid">
                    {metrics.map((metric) => <MetricCard key={metric.label} metric={metric} onNavigate={onNavigate} />)}
                </div>
            </section>

            <section className="dashboard-lower-grid">
                <article className="dashboard-card activity-card">
                    <div className="card-heading">
                        <div><h3>Recent Activities</h3><p>Latest operational events</p></div>
                        <button type="button" onClick={() => onNavigate("alerts")}>View all →</button>
                    </div>
                    <div className="activity-list">
                        {decisions.slice(0, 5).map((decision, index) => (
                            <button type="button" className="activity-row" key={`${decision.title ?? decision.action ?? "decision"}-${index}`} onClick={() => onNavigate((decision.type ?? "").toLowerCase().includes("health") ? "health" : (decision.type ?? "").toLowerCase().includes("breed") ? "breeding" : "alerts")}>
                                <span className="activity-icon"><Icon name={decision.type?.toLowerCase().includes("health") ? "health" : decision.type?.toLowerCase().includes("breed") ? "breeding" : "more"} /></span>
                                <span className="activity-copy">
                                    <strong>{decision.title ?? decision.action ?? "Operational decision"}</strong>
                                    <small>{decision.animal_id ? `Animal ${decision.animal_id}` : statusText(decision.priority ?? decision.source ?? "Operational activity")}</small>
                                </span>
                                <span className="activity-arrow">›</span>
                            </button>
                        ))}
                        {decisions.length === 0 && <div className="empty-state">No active exceptions or decisions.</div>}
                    </div>
                </article>

                <article className="dashboard-card schedule-card">
                    <div className="card-heading">
                        <div><h3>Operational Status</h3><p>Current system and farm state</p></div>
                        <span className="status-badge">{statusText(dashboard.farm_status) || "Live"}</span>
                    </div>
                    <div className="status-list">
                        <button type="button" onClick={() => onNavigate("animals")}><span>Animals</span><strong>{formatNumber(animals)}</strong></button>
                        <button type="button" onClick={() => onNavigate("milk")}><span>Milk today</span><strong>{milkToday === undefined ? "—" : `${milkToday} L`}</strong></button>
                        <button type="button" onClick={() => onNavigate("finance")}><span>Today's expense</span><strong>{formatPkr(expense)}</strong></button>
                        <button type="button" onClick={() => onNavigate("alerts")}><span>Open decisions</span><strong>{formatNumber(decisions.length)}</strong></button>
                    </div>
                </article>
            </section>
        </div>
    );
}

export default CommandCenter;
