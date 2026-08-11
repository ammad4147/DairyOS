import React, { useEffect, useMemo, useState } from "react";
import type { DashboardResponse, OperationalDecision } from "../models/dashboard";
import { getDashboard } from "../api/dashboardClient";
import "./CommandCenter.css";

function display(value: unknown, fallback = "—") {
    if (value === undefined || value === null || value === "") return fallback;
    if (typeof value === "number") {
        return Number.isInteger(value)
            ? value.toLocaleString()
            : value.toLocaleString(undefined, { maximumFractionDigits: 1 });
    }
    return String(value);
}

function firstValue(source: Record<string, unknown> | undefined, keys: string[], fallback = "—") {
    if (!source) return fallback;
    for (const key of keys) {
        const value = source[key];
        if (value !== undefined && value !== null && value !== "") return value;
    }
    return fallback;
}

function statusTone(value: unknown): "good" | "warn" | "bad" | "neutral" {
    const text = String(value ?? "").toLowerCase();
    if (["normal", "healthy", "ready", "active", "completed", "complete", "clear", "ok"].some(x => text.includes(x))) return "good";
    if (["attention", "warning", "pending", "open", "due", "amber"].some(x => text.includes(x))) return "warn";
    if (["critical", "error", "failed", "offline", "red"].some(x => text.includes(x))) return "bad";
    return "neutral";
}

function decisionText(decision: OperationalDecision) {
    return decision.title || decision.action || decision.type || "Operational decision";
}

function CommandCenter() {
    const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        getDashboard().then(setDashboard).catch((e: Error) => setError(e.message));
    }, []);

    const state = dashboard?.operational_state ?? {};
    const runtime = dashboard?.dashboard ?? {};
    const milk = runtime.milk ?? {};
    const decisions = dashboard?.operational_decisions ?? [];
    const exceptions = dashboard?.exceptions ?? [];
    const animals = state.animals ?? {};
    const animalCount = Object.keys(animals).length;

    const lactatingCount = Object.values(animals).filter(animal => {
        const status = String(animal?.status ?? animal?.lifecycle?.new_status ?? "").toLowerCase();
        return status === "milking" || status === "lactating";
    }).length;

    const healthAlerts = Array.isArray(exceptions) ? exceptions.length : 0;
    const financial = state.financial_status as Record<string, unknown> | undefined;
    const cash = firstValue(financial, ["cash_position", "cash", "balance", "closing_cash"]);
    const revenue = firstValue(financial, ["revenue", "today_revenue", "revenue_today"]);
    const expenses = firstValue(financial, ["expenses", "today_expenses", "expenses_today"]);

    const latestMilk = useMemo(() => {
        const milkStatus = state.milk_status ?? {};
        const rows = Object.entries(milkStatus);
        return rows.length ? rows[rows.length - 1][1] as Record<string, unknown> : undefined;
    }, [state.milk_status]);

    if (error) {
        return (
            <main className="command-center">
                <section className="empty-state error-state">
                    <div className="eyebrow">TRIDENT DAIRIES · DAIRYOS</div>
                    <h1>Farm Dashboard</h1>
                    <p>Unable to load the live operational picture.</p>
                    <strong>{error}</strong>
                </section>
            </main>
        );
    }

    if (!dashboard) {
        return (
            <main className="command-center">
                <section className="empty-state">
                    <div className="eyebrow">TRIDENT DAIRIES · DAIRYOS</div>
                    <h1>Farm Dashboard</h1>
                    <p>Loading the live farm picture…</p>
                </section>
            </main>
        );
    }

    return (
        <main className="command-center">
            <header className="dashboard-header">
                <div>
                    <div className="eyebrow">TRIDENT DAIRIES · DAIRYOS</div>
                    <h1>Farm Dashboard</h1>
                    <p>Today’s operational picture, exceptions and management priorities.</p>
                </div>
                <div className={`system-status ${statusTone(dashboard.health)}`}>
                    <span className="status-dot" />
                    <div>
                        <strong>{display(dashboard.health)}</strong>
                        <span>System health</span>
                    </div>
                </div>
            </header>

            <section className="kpi-grid" aria-label="Key farm indicators">
                <article className="kpi-card milk-kpi">
                    <div className="kpi-label">Milk today</div>
                    <div className="kpi-value">{display(milk.today_litres, "0")} <small>L</small></div>
                    <div className="kpi-meta">{display(milk.events, "0")} milk events · last {display(milk.last_shift, "not recorded")}</div>
                </article>

                <article className="kpi-card">
                    <div className="kpi-label">Lactating herd</div>
                    <div className="kpi-value">{display(lactatingCount, "0")} <small>cows</small></div>
                    <div className="kpi-meta">{display(animalCount, "0")} animals currently known</div>
                </article>

                <article className={`kpi-card ${healthAlerts ? "attention-kpi" : ""}`}>
                    <div className="kpi-label">Health / exceptions</div>
                    <div className="kpi-value">{display(healthAlerts, "0")}</div>
                    <div className="kpi-meta">{healthAlerts ? "Items require review" : "No active exceptions"}</div>
                </article>

                <article className="kpi-card finance-kpi">
                    <div className="kpi-label">Cash position</div>
                    <div className="kpi-value">{display(cash)}</div>
                    <div className="kpi-meta">Revenue {display(revenue)} · Expenses {display(expenses)}</div>
                </article>
            </section>

            <section className="dashboard-grid primary-grid">
                <article className="panel milk-panel">
                    <div className="panel-heading">
                        <div><h2>Milk production</h2><p>Production is the first operational priority.</p></div>
                        <span className="panel-tag">LIVE</span>
                    </div>
                    <div className="milk-hero"><strong>{display(milk.today_litres, "0")}</strong><span>litres today</span></div>
                    <div className="metric-list">
                        <div><span>Last milking</span><strong>{display(milk.last_shift, "Not recorded")}</strong></div>
                        <div><span>Latest operator</span><strong>{display(milk.last_operator, "Not recorded")}</strong></div>
                        <div><span>Latest animal</span><strong>{display(firstValue(latestMilk, ["last_animal_id", "animal_id"], firstValue(state.milk_production_summary as Record<string, unknown> | undefined, ["last_animal_id"])))}</strong></div>
                    </div>
                    <button className="action-button primary" type="button">Open milk entry</button>
                </article>

                <article className="panel attention-panel">
                    <div className="panel-heading">
                        <div><h2>Attention now</h2><p>Decisions and exceptions needing action.</p></div>
                        <span className={`count-pill ${decisions.length + healthAlerts ? "danger" : "good"}`}>{decisions.length + healthAlerts}</span>
                    </div>
                    {!decisions.length && !healthAlerts ? (
                        <div className="clear-state"><strong>Farm is clear</strong><span>No active decisions or exceptions.</span></div>
                    ) : (
                        <div className="attention-list">
                            {decisions.slice(0, 5).map((decision, index) => (
                                <div className="attention-item" key={`${decision.type}-${index}`}>
                                    <span className={`severity ${statusTone(decision.priority || decision.escalation_level)}`}>{display(decision.priority || decision.escalation_level, "REVIEW")}</span>
                                    <div><strong>{decisionText(decision)}</strong><span>{display(decision.animal_id, "Farm-level decision")}</span></div>
                                </div>
                            ))}
                            {healthAlerts > 0 && (
                                <div className="attention-item">
                                    <span className="severity bad">HEALTH</span>
                                    <div><strong>{healthAlerts} active exception{healthAlerts === 1 ? "" : "s"}</strong><span>Review the Health tab for affected animals.</span></div>
                                </div>
                            )}
                        </div>
                    )}
                    <button className="action-button" type="button">Open command center</button>
                </article>
            </section>

            <section className="dashboard-grid secondary-grid">
                <article className="panel finance-panel">
                    <div className="panel-heading"><div><h2>Financial snapshot</h2><p>Management view; detailed transactions remain under Finance.</p></div></div>
                    <div className="finance-grid">
                        <div><span>Cash</span><strong>{display(cash)}</strong></div>
                        <div><span>Revenue</span><strong>{display(revenue)}</strong></div>
                        <div><span>Expenses</span><strong>{display(expenses)}</strong></div>
                    </div>
                    <div className="finance-note">Finance data is available in the operational state and should be entered through the Finance workflow.</div>
                </article>

                <article className="panel herd-panel">
                    <div className="panel-heading"><div><h2>Herd health</h2><p>Fast view of animal status and attention.</p></div></div>
                    <div className="herd-grid">
                        <div><strong>{display(animalCount, "0")}</strong><span>Total animals</span></div>
                        <div><strong>{display(lactatingCount, "0")}</strong><span>Lactating</span></div>
                        <div className={healthAlerts ? "danger-text" : ""}><strong>{display(healthAlerts, "0")}</strong><span>Needs attention</span></div>
                    </div>
                    <button className="action-button" type="button">Open herd / health</button>
                </article>
            </section>

            <section className="panel operations-panel">
                <div className="panel-heading"><div><h2>Operational areas</h2><p>Availability at a glance; detailed records remain under their tabs.</p></div></div>
                <div className="area-grid">
                    {[
                        ["Feeding", state.feeding_status],
                        ["Breeding", state.breeding_status],
                        ["Workforce", state.workforce_status],
                        ["Inventory", state.inventory_status],
                        ["Equipment", state.equipment_status],
                    ].map(([label, value]) => {
                        const available = !!value && Object.keys(value as object).length > 0;
                        return (
                            <div className="area-card" key={label as string}>
                                <span>{label as string}</span>
                                <strong>{available ? "Recorded" : "No current data"}</strong>
                                <small className={`area-status ${available ? "good" : "neutral"}`}>{available ? "Available" : "Awaiting entry"}</small>
                            </div>
                        );
                    })}
                </div>
            </section>

            <footer className="dashboard-footer">
                <span>{display(dashboard.event_count, "0")} operational events</span>
                <span>Last event: {display(runtime.freshness?.last_event_time, "Not available")}</span>
                <span>Latest milk operator: {display(milk.last_operator, "Not recorded")}</span>
            </footer>
        </main>
    );
}

export default CommandCenter;
