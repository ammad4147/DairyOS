import React, { useCallback, useEffect, useMemo, useState } from "react";
import { getDashboard } from "../api/dashboardClient";
import type { DashboardResponse } from "../models/dashboard";
import "./CommandCenter.css";

type ViewId = "command" | "animals" | "milk" | "feed" | "health" | "breeding" | "workforce" | "inventory" | "equipment" | "finance" | "analytics" | "alerts";
type Props = { onNavigate?: (view: ViewId) => void };
type MilkRow = { animal_id?: string; timestamp?: string; date?: string; total_yield?: number; litres?: number; morning_yield?: number; afternoon_yield?: number; evening_yield?: number };
type FinanceRow = { timestamp?: string; date?: string; transaction_type?: string; amount?: number; payment_method?: string; category?: string };

const API = "http://localhost:8000";
const n = (v: unknown) => Number.isFinite(Number(v)) ? Number(v) : 0;
const milkValue = (r: MilkRow) => n(r.total_yield ?? r.litres ?? (n(r.morning_yield) + n(r.afternoon_yield) + n(r.evening_yield)));
const rowTime = (r: { timestamp?: string; date?: string }) => new Date(r.timestamp ?? r.date ?? 0).getTime();
const pkr = (v: number) => `PKR ${Math.round(v).toLocaleString("en-PK")}`;
const dayKey = (r: { timestamp?: string; date?: string }) => { const t = rowTime(r); return Number.isFinite(t) ? new Date(t).toISOString().slice(0, 10) : ""; };
const go = (onNavigate: Props["onNavigate"], view: ViewId) => () => onNavigate?.(view);

function sumMilk(rows: MilkRow[], start: Date, end = new Date()) {
    return rows.filter(r => { const t = rowTime(r); return t >= start.getTime() && t <= end.getTime(); }).reduce((a, r) => a + milkValue(r), 0);
}

function dailyAnimalDrops(rows: MilkRow[]) {
    const byAnimal = new Map<string, Map<string, number>>();
    rows.forEach(r => {
        if (!r.animal_id) return;
        const day = dayKey(r);
        if (!day) return;
        const days = byAnimal.get(r.animal_id) ?? new Map<string, number>();
        days.set(day, (days.get(day) ?? 0) + milkValue(r));
        byAnimal.set(r.animal_id, days);
    });
    return [...byAnimal.entries()].flatMap(([animal, days]) => {
        const sorted = [...days.entries()].sort((a, b) => a[0].localeCompare(b[0]));
        if (sorted.length < 2) return [];
        const [previousDay, previous] = sorted[sorted.length - 2];
        const [latestDay, latest] = sorted[sorted.length - 1];
        if (previous <= 0 || latest >= previous * 0.8) return [];
        return [{ id: `MILK-${animal}-${latestDay.replaceAll("-", "")}`, animal, latestDay, previousDay, drop: Math.round((1 - latest / previous) * 100), latest, previous }];
    });
}

function periodStart(period: string) {
    const d = new Date();
    if (period === "7d") d.setDate(d.getDate() - 7);
    else if (period === "month") d.setMonth(d.getMonth() - 1);
    else if (period === "year") d.setFullYear(d.getFullYear() - 1);
    else return new Date(new Date().setHours(0, 0, 0, 0));
    return d;
}

function HerdCard({ state, onNavigate }: { state: any; onNavigate: Props["onNavigate"] }) {
    const mix = state.lifecycle_mix ?? state.lifecycle ?? state.herd_composition ?? {};
    const rows = Object.entries(mix).filter(([, v]) => Number.isFinite(Number(v))).slice(0, 6);
    const total = n(state.total_animals ?? state.animals_count ?? Object.keys(state.animals ?? {}).length);
    return <button type="button" className="dashboard-card herd-card" onClick={go(onNavigate, "animals")}>
        <div className="card-top"><div><div className="card-kicker">HERD</div><h3>Herd Composition</h3></div><span className="card-arrow">→</span></div>
        <div className="herd-total">{total}</div><div className="herd-total-label">Total animals</div>
        <div className="herd-list">{rows.length ? rows.map(([k, v]) => <div key={k}><span>{String(k).replaceAll("_", " ")}</span><strong>{n(v)}</strong></div>) : <span className="data-note">Composition will appear from live herd state.</span>}</div>
        <div className="card-link">View herd details →</div>
    </button>;
}

function MilkCard({ rows, onNavigate }: { rows: MilkRow[]; onNavigate: Props["onNavigate"] }) {
    const [period, setPeriod] = useState("today");
    const start = periodStart(period);
    const total = sumMilk(rows, start);
    const labels: Record<string, string> = { today: "Today", "7d": "7 Days", month: "Month", year: "Year" };
    return <section className="dashboard-card milk-card">
        <button type="button" className="card-click-layer" onClick={go(onNavigate, "milk")} aria-label="Open milk production">
            <div className="card-top"><div><div className="card-kicker">MILK PRODUCTION</div><h3>Production overview</h3></div><span className="card-arrow">→</span></div>
            <div className="big-number">{total.toFixed(1)} <small>L</small></div>
            <div className="metric-caption">Actual recorded milk for selected period</div>
        </button>
        <div className="period-switch" role="group" aria-label="Milk production period">{Object.keys(labels).map(p => <button key={p} type="button" className={period === p ? "selected" : ""} onClick={() => setPeriod(p)}>{labels[p]}</button>)}</div>
        <div className="card-link">Open production trends & custom timeframe →</div>
    </section>;
}

function YieldAlertCard({ drops, onNavigate }: { drops: ReturnType<typeof dailyAnimalDrops>; onNavigate: Props["onNavigate"] }) {
    return <button type="button" className={`dashboard-card alert-card ${drops.length ? "attention" : ""}`} onClick={go(onNavigate, "milk")}>
        <div className="card-top"><div><div className="card-kicker">MILK NOTIFICATIONS</div><h3>Animal yield alerts</h3></div><span className="card-count">{drops.length}</span></div>
        <div className="alert-rule">Daily yield down &gt;20% versus the animal's previous measured day.</div>
        {drops.length ? <div className="alert-list">{drops.slice(0, 3).map(a => <div className="yield-alert" key={a.id}><strong>{a.id}</strong><span>Animal {a.animal} · down {a.drop}% · {a.latest.toFixed(1)} L vs {a.previous.toFixed(1)} L</span></div>)}</div> : <div className="clear-state">No measured animal daily yield drop greater than 20%.</div>}
        <div className="card-link">Review notifications →</div>
    </button>;
}

function FinanceCard({ rows, state, onNavigate }: { rows: FinanceRow[]; state: any; onNavigate: Props["onNavigate"] }) {
    const [view, setView] = useState("cash");
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const quarterMonth = Math.floor(now.getMonth() / 3) * 3;
    const quarterStart = new Date(now.getFullYear(), quarterMonth, 1);
    const yearStart = new Date(now.getFullYear(), 0, 1);
    const rangeStart = view === "month" ? monthStart : view === "quarter" ? quarterStart : view === "year" ? yearStart : null;
    const inRange = rangeStart ? rows.filter(r => rowTime(r) >= rangeStart.getTime()) : rows;
    const income = inRange.filter(r => /income|sale|receipt/i.test(r.transaction_type ?? "")).reduce((a, r) => a + n(r.amount), 0);
    const expense = inRange.filter(r => /expense|purchase|payment|cost/i.test(r.transaction_type ?? "")).reduce((a, r) => a + n(r.amount), 0);
    const cash = n(state.cash_in_hand ?? state.cash ?? state.cash_balance);
    const bank = n(state.money_at_bank ?? state.bank_balance ?? state.bank);
    const selectedValue = view === "cash" ? cash : view === "bank" ? bank : income - expense;
    const title = view === "cash" ? "Cash in Hand" : view === "bank" ? "Money at Bank" : `${view[0].toUpperCase()}${view.slice(1)} Reconciliation`;
    return <section className="dashboard-card finance-card">
        <button type="button" className="card-click-layer" onClick={go(onNavigate, "finance")} aria-label="Open finance">
            <div className="card-top"><div><div className="card-kicker">FINANCE</div><h3>{title}</h3></div><span className="card-arrow">→</span></div>
            <div className="finance-primary">{pkr(selectedValue)}</div>
            <div className="finance-label">{view === "cash" || view === "bank" ? "Current recorded position" : "Actual recorded income less expenses"}</div>
        </button>
        <div className="finance-switch" role="group" aria-label="Finance view">
            {[['cash','Cash'],['bank','Bank'],['month','Monthly'],['quarter','Quarterly'],['year','Yearly']].map(([key, label]) => <button key={key} type="button" className={view === key ? "selected" : ""} onClick={() => setView(key)}>{label}</button>)}
        </div>
        <div className="finance-foot"><span>Cash {pkr(cash)}</span><span>Bank {pkr(bank)}</span></div>
        <div className="card-link">Open finance & reconciliation →</div>
    </section>;
}

export default function CommandCenter({ onNavigate = () => undefined }: Props) {
    const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
    const [milk, setMilk] = useState<MilkRow[]>([]);
    const [finance, setFinance] = useState<FinanceRow[]>([]);
    const [error, setError] = useState<string | null>(null);
    const load = useCallback(async () => {
        try {
            setError(null);
            const [d, m, f] = await Promise.all([
                getDashboard(),
                fetch(`${API}/farm/milk`).then(r => r.ok ? r.json() : []).catch(() => []),
                fetch(`${API}/farm/financial`).then(r => r.ok ? r.json() : []).catch(() => []),
            ]);
            setDashboard(d);
            setMilk(Array.isArray(m) ? m : []);
            setFinance(Array.isArray(f) ? f : []);
        } catch (e) { setError(e instanceof Error ? e.message : "Dashboard unavailable"); }
    }, []);
    useEffect(() => { load(); const t = window.setInterval(load, 60000); return () => window.clearInterval(t); }, [load]);

    const state: any = dashboard?.operational_state ?? {};
    const decisions: any[] = dashboard?.operational_decisions ?? [];
    const drops = useMemo(() => dailyAnimalDrops(milk), [milk]);
    const attention = decisions.length + drops.length;
    const recent = [...decisions].sort((a, b) => new Date(b.timestamp ?? b.created_at ?? 0).getTime() - new Date(a.timestamp ?? a.created_at ?? 0).getTime()).slice(0, 5);
    const totalAnimals = n(state.total_animals ?? state.animals_count ?? Object.keys(state.animals ?? {}).length);
    const todayMilk = sumMilk(milk, periodStart("today"));

    if (error) return <div className="dashboard-error"><strong>Dashboard unavailable</strong><span>{error}</span><button onClick={load}>Retry</button></div>;
    if (!dashboard) return <div className="dashboard-loading">Loading live farm picture…</div>;

    return <div className="command-center">
        <header className="dashboard-header">
            <div><div className="eyebrow">TRIDENT DAIRIES · OPERATIONS</div><h1>Farm Dashboard</h1><p>Real-time operating picture from recorded DairyOS data.</p></div>
            <div className="dashboard-header-actions"><button className="bell-button" type="button" onClick={go(onNavigate, "alerts")} aria-label="Notifications"><span className="bell-icon">♢</span>{attention > 0 && <span className="notification-badge">{attention}</span>}</button><button className="refresh-button" type="button" onClick={load} aria-label="Refresh">↻</button></div>
        </header>

        <section className="dashboard-grid">
            <HerdCard state={state} onNavigate={onNavigate} />
            <MilkCard rows={milk} onNavigate={onNavigate} />
            <YieldAlertCard drops={drops} onNavigate={onNavigate} />
            <FinanceCard rows={finance} state={state.financial_status ?? {}} onNavigate={onNavigate} />
        </section>

        <section className="dashboard-bottom">
            <div className="dashboard-card activity-card">
                <div className="card-top"><div><div className="card-kicker">RECENT ACTIVITY</div><h3>Latest operational events</h3></div><span className="activity-count">{recent.length}</span></div>
                <div className="activity-list">{recent.map((d, i) => <div className="activity-row" key={d.decision_id ?? i}><span className="activity-dot"/><div><strong>{d.title ?? d.action ?? "Operational event"}</strong><small>{d.animal_id ? `Animal ${d.animal_id}` : d.source ?? "DairyOS"}</small></div><span className="activity-time">{d.timestamp ? new Date(d.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}</span></div>)}{!recent.length && <div className="data-note">No recent operational decision records.</div>}</div>
            </div>
            <div className="dashboard-card pulse-card">
                <div className="card-kicker">FARM PULSE</div><h3>Recorded today</h3>
                <div className="pulse-grid"><div><strong>{totalAnimals}</strong><span>animals</span></div><div><strong>{todayMilk.toFixed(1)} L</strong><span>milk</span></div><div><strong>{attention}</strong><span>notifications</span></div></div>
                <button type="button" className="text-button" onClick={go(onNavigate, "analytics")}>Open analytics →</button>
            </div>
        </section>
    </div>;
}
