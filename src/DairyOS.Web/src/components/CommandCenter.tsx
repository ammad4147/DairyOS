import React, { useEffect, useMemo, useState } from "react";
import type {
    DashboardResponse,
    DashboardRuntime,
    OperationalAnimalState,
    OperationalDecision,
    OperationalState,
} from "../models/dashboard";
import { getDashboard } from "../api/dashboardClient";
import "./CommandCenter.css";

type Props = { onNavigate: (view: string) => void; };

type MilkPeriod = "7d" | "month" | "year" | "custom";
type FinanceView = "cash" | "bank" | "monthly" | "quarterly" | "yearly";

type HerdRow = {
    id: string;
    animal: OperationalAnimalState;
    lifecycle: string;
};

type YieldAlert = {
    id: string;
    animalId: string;
    dropPercent: number;
    current: number | null;
    previous: number | null;
};

function numberValue(value: unknown): number | null {
    return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function displayNumber(value: unknown, suffix = ""): string {
    const number = numberValue(value);
    return number === null ? "â€”" : `${number.toLocaleString(undefined, { maximumFractionDigits: 1 })}${suffix}`;
}

function displayMoney(value: unknown): string {
    const number = numberValue(value);
    return number === null
        ? "â€”"
        : `PKR ${number.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function normalizedKey(value: string): string {
    return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function findNumeric(source: Record<string, unknown> | undefined, aliases: string[]): number | null {
    if (!source) return null;
    const entries = Object.entries(source);
    for (const alias of aliases) {
        const target = normalizedKey(alias);
        const found = entries.find(([key]) => normalizedKey(key) === target);
        const value = numberValue(found?.[1]);
        if (value !== null) return value;
    }
    return null;
}

function animalRows(state: OperationalState): HerdRow[] {
    return Object.entries(state.animals ?? {}).map(([id, animal]) => ({
        id,
        animal,
        lifecycle: String(
            animal.lifecycle_status
            ?? animal.lifecycle_stage
            ?? animal.animal_status
            ?? "UNKNOWN",
        ),
    }));
}

function isLifecycle(row: HerdRow, values: string[]): boolean {
    const lifecycle = row.lifecycle.toLowerCase();
    return values.some((value) => lifecycle.includes(value));
}

function buildYieldAlerts(rows: HerdRow[]): YieldAlert[] {
    const alerts: YieldAlert[] = [];
    const today = new Date().toISOString().slice(0, 10);

    for (const row of rows) {
        const animal = row.animal as Record<string, unknown>;
        const current = numberValue(animal.milk_today_litres);
        const deviation = numberValue(animal.milk_deviation_percentage);
        const history = Array.isArray(animal.daily_milk_history)
            ? animal.daily_milk_history
                .map((item) => ({
                    date: String((item as Record<string, unknown>).date ?? ""),
                    litres: numberValue(
                        (item as Record<string, unknown>).litres
                        ?? (item as Record<string, unknown>).value,
                    ),
                }))
                .filter((item) => item.litres !== null)
                .sort((a, b) => a.date.localeCompare(b.date))
            : [];

        let dropPercent: number | null = null;
        let previous: number | null = null;

        if (deviation !== null && deviation <= -20) {
            dropPercent = Math.abs(deviation);
            previous = history.length > 1 ? history[history.length - 2].litres : null;
        } else if (history.length > 1) {
            const latest = history[history.length - 1].litres;
            previous = history[history.length - 2].litres;
            if (latest !== null && previous !== null && previous > 0) {
                const computed = ((latest - previous) / previous) * 100;
                if (computed <= -20) dropPercent = Math.abs(computed);
            }
        }

        if (dropPercent !== null) {
            alerts.push({
                id: `MILK-DROP-${row.id}-${today}`,
                animalId: row.id,
                dropPercent,
                current,
                previous,
            });
        }
    }

    return alerts;
}

function periodHistory(milk: DashboardRuntime["milk"], period: MilkPeriod, from: string, to: string) {
    const raw = milk?.trend_history ?? milk?.history ?? [];
    if (!Array.isArray(raw)) return [];

    const points = raw
        .map((item) => ({
            date: String(item.date ?? ""),
            litres: numberValue(item.litres ?? item.value),
        }))
        .filter((item) => item.litres !== null)
        .sort((a, b) => a.date.localeCompare(b.date));

    if (period === "custom") {
        return points.filter((point) =>
            (!from || point.date >= from) && (!to || point.date <= to),
        );
    }

    const days = period === "7d" ? 7 : period === "month" ? 30 : 365;
    return points.slice(-days);
}

function CommandCenter({ onNavigate }: Props) {
    const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);
    const [milkPeriod, setMilkPeriod] = useState<MilkPeriod>("7d");
    const [customFrom, setCustomFrom] = useState("");
    const [customTo, setCustomTo] = useState("");
    const [financeView, setFinanceView] = useState<FinanceView>("cash");
    const [showNotifications, setShowNotifications] = useState(false);
    const [herdDetail, setHerdDetail] = useState<string | null>(null);

    const loadDashboard = async () => {
        setLoading(true);
        setError(null);
        try {
            const payload = await getDashboard();
            setDashboard(payload);
            setLastUpdated(new Date().toLocaleTimeString());
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Unable to load live farm operations.",
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        void loadDashboard();
        const timer = window.setInterval(() => void loadDashboard(), 60_000);
        return () => window.clearInterval(timer);
    }, []);

    const runtimeDashboard: DashboardRuntime = dashboard?.dashboard ?? {};
    const operationalState: OperationalState =
        dashboard?.operational_state ?? runtimeDashboard.operational_state ?? {};
    const rows = useMemo(() => animalRows(operationalState), [operationalState]);
    const yieldAlerts = useMemo(() => buildYieldAlerts(rows), [rows]);

    const decisions: OperationalDecision[] =
        dashboard?.operational_decisions
        ?? runtimeDashboard.operational_decisions
        ?? [];

    const attention = useMemo(() => {
        const decisionItems = decisions.filter((decision) =>
            decision.owner_action_required
            || ["critical", "high", "medium"].includes(String(decision.priority).toLowerCase()),
        );
        return [...yieldAlerts, ...decisionItems];
    }, [decisions, yieldAlerts]);

    const milk = runtimeDashboard.milk ?? {};
    const history = useMemo(
        () => periodHistory(milk, milkPeriod, customFrom, customTo),
        [milk, milkPeriod, customFrom, customTo],
    );

    const totalForPeriod = history.length
        ? history.reduce((sum, point) => sum + (point.litres ?? 0), 0)
        : milkPeriod === "7d"
            ? numberValue(milk.seven_day_total_litres)
            : milkPeriod === "month"
                ? numberValue(milk.thirty_day_average_litres) !== null
                    ? (numberValue(milk.thirty_day_average_litres) ?? 0) * 30
                    : null
                : null;

    const averageForPeriod = history.length
        ? (totalForPeriod ?? 0) / history.length
        : milkPeriod === "7d"
            ? numberValue(milk.seven_day_average_litres)
            : milkPeriod === "month"
                ? numberValue(milk.thirty_day_average_litres)
                : null;

    const herdCounts = useMemo(() => ({
        milking: rows.filter((row) => isLifecycle(row, ["milking"])).length,
        dry: rows.filter((row) => isLifecycle(row, ["dry"])).length,
        heifers: rows.filter((row) => isLifecycle(row, ["heifer"])).length,
        calves: rows.filter((row) => isLifecycle(row, ["calf"])).length,
        other: rows.filter((row) => !isLifecycle(row, ["milking", "dry", "heifer", "calf"])).length,
    }), [rows]);

    const herdGroups: Record<string, HerdRow[]> = {
        milking: rows.filter((row) => isLifecycle(row, ["milking"])),
        dry: rows.filter((row) => isLifecycle(row, ["dry"])),
        heifers: rows.filter((row) => isLifecycle(row, ["heifer"])),
        calves: rows.filter((row) => isLifecycle(row, ["calf"])),
        other: rows.filter((row) => !isLifecycle(row, ["milking", "dry", "heifer", "calf"])),
    };

    const financial = operationalState.financial_status;
    const financeMap: Record<FinanceView, { label: string; value: number | null }> = {
        cash: {
            label: "Cash in Hand",
            value: findNumeric(financial, ["cash_in_hand", "cash", "cash_balance"]),
        },
        bank: {
            label: "Money at Bank",
            value: findNumeric(financial, ["money_at_bank", "bank_balance", "bank", "cash_at_bank"]),
        },
        monthly: {
            label: "Monthly Reconciliation",
            value: findNumeric(financial, ["monthly_reconciliation", "monthly_balance", "monthly"]),
        },
        quarterly: {
            label: "Quarterly Reconciliation",
            value: findNumeric(financial, ["quarterly_reconciliation", "quarterly_balance", "quarterly"]),
        },
        yearly: {
            label: "Yearly Reconciliation",
            value: findNumeric(financial, ["yearly_reconciliation", "annual_reconciliation", "yearly_balance", "yearly"]),
        },
    };

    if (loading && !dashboard) {
        return <main className="command-center"><div className="farm-loading">Loading live farm operationsâ€¦</div></main>;
    }

    if (error && !dashboard) {
        return (
            <main className="command-center">
                <div className="farm-error">
                    <div><strong>Unable to load live farm operations.</strong><p>{error}</p></div>
                    <button type="button" onClick={() => void loadDashboard()}>Retry</button>
                </div>
            </main>
        );
    }

    if (!dashboard) return null;

    const activeHerdRows = herdDetail ? herdGroups[herdDetail] ?? [] : [];

    return (
        <main className="command-center">
            <header className="farm-header">
                <div>
                    <span className="farm-eyebrow">TRIDENT DAIRIES Â· INTELLIGENT FARM OPERATIONS</span>
                    <h1>Command Center</h1>
                    <p>Live production, herd composition, finance and operator notifications.</p>
                </div>
                <div className="farm-header-actions">
                    <span className="farm-live-indicator"><span className="live-dot" />Live {lastUpdated && <small>{lastUpdated}</small>}</span>
                    <div className="notification-wrap">
                        <button
                            type="button"
                            className={`notification-button${attention.length ? " has-alerts" : ""}`}
                            aria-label="Open notifications"
                            onClick={() => setShowNotifications((value) => !value)}
                        >
                            <span aria-hidden="true">â™¢</span>
                            {attention.length > 0 && <b>{attention.length}</b>}
                        </button>
                        {showNotifications && (
                            <div className="notification-popover">
                                <div className="popover-heading"><strong>Notifications</strong><span>{attention.length}</span></div>
                                {yieldAlerts.map((alert) => (
                                    <button key={alert.id} type="button" className="notification-row" onClick={() => onNavigate("animals")}>
                                        <span className="notification-id">{alert.id}</span>
                                        <strong>{alert.animalId}: milk yield down {alert.dropPercent.toFixed(1)}%</strong>
                                        <small>Current {displayNumber(alert.current, " L")} Â· Previous {displayNumber(alert.previous, " L")}</small>
                                    </button>
                                ))}
                                {decisions.slice(0, 8).map((decision, index) => (
                                    <button key={`${decision.type ?? "decision"}-${decision.animal_id ?? index}`} type="button" className="notification-row" onClick={() => decision.animal_id && onNavigate("animals")}>
                                        <span className="notification-id">DEC-{index + 1}</span>
                                        <strong>{decision.title ?? decision.action ?? decision.type ?? "Operational decision"}</strong>
                                        <small>{decision.animal_id ?? "Farm-level"} Â· {String(decision.priority ?? "attention")}</small>
                                    </button>
                                ))}
                                {!attention.length && <div className="notification-empty">No active notifications.</div>}
                            </div>
                        )}
                    </div>
                    <button type="button" className="farm-refresh" onClick={() => void loadDashboard()} disabled={loading}>Refresh</button>
                </div>
            </header>

            {error && <div className="farm-refresh-warning"><strong>Refresh warning</strong><span>{error}</span></div>}

            <section className="command-grid">
                <article className="dashboard-card milk-card">
                    <div className="card-heading">
                        <div><span className="card-eyebrow">MILK PRODUCTION</span><h2>Milk Production</h2></div>
                        <select value={milkPeriod} onChange={(event) => setMilkPeriod(event.target.value as MilkPeriod)} aria-label="Milk production period">
                            <option value="7d">7 days</option>
                            <option value="month">Month</option>
                            <option value="year">Year</option>
                            <option value="custom">Any timeframe</option>
                        </select>
                    </div>
                    {milkPeriod === "custom" && (
                        <div className="date-range"><input type="date" value={customFrom} onChange={(event) => setCustomFrom(event.target.value)} /><span>to</span><input type="date" value={customTo} onChange={(event) => setCustomTo(event.target.value)} /></div>
                    )}
                    <div className="metric-hero"><strong>{displayNumber(milk.today_litres, " L")}</strong><span>Today</span></div>
                    <div className="milk-metrics">
                        <div><span>Period total</span><strong>{displayNumber(totalForPeriod, " L")}</strong></div>
                        <div><span>Period average</span><strong>{displayNumber(averageForPeriod, " L")}</strong></div>
                        <div><span>Yesterday</span><strong>{displayNumber(milk.yesterday_litres ?? milk.previous_day_litres, " L")}</strong></div>
                    </div>
                    <div className="trend-chart compact" aria-label={`Milk production for ${milkPeriod}`}>
                        {history.length ? history.slice(-14).map((point, index, list) => {
                            const max = Math.max(...list.map((item) => item.litres ?? 0), 1);
                            return <div className="trend-point" key={`${point.date}-${index}`}><div className="trend-bar-wrap"><div className="trend-bar" style={{ height: `${Math.max(8, ((point.litres ?? 0) / max) * 100)}%` }} /></div><span>{point.date.slice(5)}</span></div>;
                        }) : <div className="chart-empty">No historical records are available for this period.</div>}
                    </div>
                </article>

                <article className="dashboard-card herd-card">
                    <div className="card-heading"><div><span className="card-eyebrow">HERD COMPOSITION</span><h2>Herd Composition</h2></div><span className="card-total">{rows.length} head</span></div>
                    <div className="herd-composition">
                        {(["milking", "dry", "heifers", "calves", "other"] as const).map((group) => (
                            <button key={group} type="button" className={`herd-segment ${group}`} onClick={() => setHerdDetail(group)}>
                                <span>{group === "other" ? "Other" : group[0].toUpperCase() + group.slice(1)}</span><strong>{herdCounts[group]}</strong>
                            </button>
                        ))}
                    </div>
                    <button type="button" className="text-link" onClick={() => setHerdDetail("milking")}>View herd details â†’</button>
                </article>

                <article className="dashboard-card finance-card">
                    <div className="card-heading"><div><span className="card-eyebrow">FINANCE</span><h2>{financeMap[financeView].label}</h2></div><select value={financeView} onChange={(event) => setFinanceView(event.target.value as FinanceView)} aria-label="Finance view"><option value="cash">Cash in Hand</option><option value="bank">Money at Bank</option><option value="monthly">Monthly Reconciliation</option><option value="quarterly">Quarterly Reconciliation</option><option value="yearly">Yearly Reconciliation</option></select></div>
                    <div className="finance-value">{displayMoney(financeMap[financeView].value)}</div>
                    <p>Live value from the farm financial state. Detailed reconciliation remains in Finance.</p>
                </article>

                <article className="dashboard-card attention-card">
                    <div className="card-heading"><div><span className="card-eyebrow">OPERATOR ATTENTION</span><h2>Notifications</h2></div><span className={`attention-count ${attention.length ? "active" : ""}`}>{attention.length}</span></div>
                    <div className="attention-preview">
                        {yieldAlerts.slice(0, 3).map((alert) => <button key={alert.id} type="button" onClick={() => onNavigate("animals")}><span>{alert.id}</span><strong>{alert.animalId} Â· âˆ’{alert.dropPercent.toFixed(1)}% daily yield</strong></button>)}
                        {!yieldAlerts.length && <div className="attention-ok">No animal yield drop above 20% detected.</div>}
                    </div>
                    <button type="button" className="text-link" onClick={() => setShowNotifications(true)}>Open notifications â†’</button>
                </article>
            </section>

            {herdDetail && (
                <div className="modal-backdrop" role="presentation" onMouseDown={() => setHerdDetail(null)}>
                    <section className="herd-modal" role="dialog" aria-modal="true" aria-label="Herd details" onMouseDown={(event) => event.stopPropagation()}>
                        <div className="modal-heading"><div><span className="card-eyebrow">HERD DETAILS</span><h2>{herdDetail === "other" ? "Other" : herdDetail[0].toUpperCase() + herdDetail.slice(1)}</h2></div><button type="button" onClick={() => setHerdDetail(null)}>Close</button></div>
                        <div className="animal-detail-list">
                            {activeHerdRows.length ? activeHerdRows.map((row) => <button key={row.id} type="button" onClick={() => onNavigate("animals")}><strong>{row.id}</strong><span>{row.lifecycle}</span></button>) : <div className="notification-empty">No animals in this category.</div>}
                        </div>
                    </section>
                </div>
            )}
        </main>
    );
}

export default CommandCenter;
