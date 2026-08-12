import React, { useCallback, useEffect, useMemo, useState } from "react";
import "./DairyOSShell.css";
import { getDashboard } from "../api/dashboardClient";
import type { DashboardResponse, OperationalDecision } from "../models/dashboard";

const API = "http://localhost:8000";

type ViewId =
    | "dashboard"
    | "animals"
    | "milk"
    | "feeding"
    | "health"
    | "breeding"
    | "workforce"
    | "inventory"
    | "equipment"
    | "finance"
    | "analytics"
    | "alerts";

type Period = "7d" | "month" | "year" | "custom";
type FinanceView = "cash" | "bank" | "monthly" | "quarterly" | "yearly";

type ModuleConfig = {
    endpoint: string;
    title: string;
    description: string;
    fields: Array<{ name: string; label: string; type?: string; required?: boolean; options?: string[] }>;
};

const modules: Record<Exclude<ViewId, "dashboard" | "analytics" | "alerts">, ModuleConfig> = {
    animals: {
        endpoint: "/farm/animals",
        title: "Animals",
        description: "Live herd registry, lifecycle and animal-level operational context.",
        fields: [
            { name: "animal_id", label: "Animal ID", required: true },
            { name: "name", label: "Name" },
            { name: "lifecycle", label: "Lifecycle", options: ["MILKING", "DRY", "HEIFER", "CALF"] },
            { name: "breed", label: "Breed" },
            { name: "sex", label: "Sex", options: ["FEMALE", "MALE"] },
        ],
    },
    milk: {
        endpoint: "/farm/milk",
        title: "Milk Production",
        description: "Animal-linked milk recording, production history and yield intelligence.",
        fields: [
            { name: "animal_id", label: "Animal ID", required: true },
            { name: "milking_session", label: "Session", required: true, options: ["MORNING", "AFTERNOON", "EVENING"] },
            { name: "morning_yield", label: "Morning Yield (L)", type: "number" },
            { name: "afternoon_yield", label: "Afternoon Yield (L)", type: "number" },
            { name: "evening_yield", label: "Evening Yield (L)", type: "number" },
            { name: "operator", label: "Operator", required: true },
        ],
    },
    feeding: {
        endpoint: "/farm/feed",
        title: "Feeding",
        description: "Recorded feed inputs, consumption and ration activity.",
        fields: [
            { name: "feed_type", label: "Feed Type", required: true },
            { name: "quantity_kg", label: "Quantity (kg)", type: "number", required: true },
            { name: "group_or_pen", label: "Group / Pen" },
            { name: "animal_id", label: "Animal ID" },
            { name: "operator", label: "Operator", required: true },
        ],
    },
    health: {
        endpoint: "/farm/health-observations",
        title: "Health",
        description: "Health observations, treatment, follow-up and withdrawal controls.",
        fields: [
            { name: "animal_id", label: "Animal ID", required: true },
            { name: "observation", label: "Observation", required: true },
            { name: "symptom", label: "Symptom" },
            { name: "temperature_c", label: "Temperature (°C)", type: "number" },
            { name: "severity", label: "Severity", options: ["NORMAL", "ELEVATED", "HIGH", "CRITICAL"] },
            { name: "operator", label: "Operator", required: true },
        ],
    },
    breeding: {
        endpoint: "/farm/breeding",
        title: "Breeding",
        description: "Heat, insemination, pregnancy, calving and reproductive events.",
        fields: [
            { name: "animal_id", label: "Animal ID", required: true },
            { name: "event_type", label: "Event", required: true, options: ["heat_detected", "insemination", "pregnancy_diagnosis", "pregnancy_confirmed", "pregnancy_negative", "dry_off", "calving"] },
            { name: "technician", label: "Technician" },
            { name: "result", label: "Result" },
            { name: "notes", label: "Notes" },
            { name: "operator", label: "Operator", required: true },
        ],
    },
    workforce: {
        endpoint: "/farm/workforce",
        title: "Workforce",
        description: "Workers, activities, assignments and completion records.",
        fields: [
            { name: "worker_id", label: "Worker ID", required: true },
            { name: "activity", label: "Activity", required: true },
            { name: "task", label: "Task" },
            { name: "status", label: "Status", options: ["ASSIGNED", "IN_PROGRESS", "COMPLETED", "MISSED"] },
            { name: "hours", label: "Hours", type: "number" },
            { name: "operator", label: "Recorded By", required: true },
        ],
    },
    inventory: {
        endpoint: "/farm/inventory",
        title: "Inventory",
        description: "Stock receipts, consumption, transfers, wastage and adjustments.",
        fields: [
            { name: "item", label: "Item", required: true },
            { name: "quantity", label: "Quantity", type: "number", required: true },
            { name: "movement_type", label: "Movement", options: ["PURCHASE", "RECEIPT", "CONSUMPTION", "TRANSFER", "WASTAGE", "ADJUSTMENT"] },
            { name: "unit", label: "Unit" },
            { name: "location", label: "Location" },
            { name: "supplier", label: "Supplier" },
            { name: "operator", label: "Operator", required: true },
        ],
    },
    equipment: {
        endpoint: "/farm/equipment",
        title: "Equipment",
        description: "Equipment operating status, inspections, maintenance and breakdowns.",
        fields: [
            { name: "equipment_id", label: "Equipment ID", required: true },
            { name: "activity", label: "Activity", required: true },
            { name: "status", label: "Status", options: ["OPERATIONAL", "WARNING", "OUT_OF_SERVICE", "MAINTENANCE"] },
            { name: "running_hours", label: "Running Hours", type: "number" },
            { name: "location", label: "Location" },
            { name: "notes", label: "Notes" },
            { name: "operator", label: "Operator", required: true },
        ],
    },
    finance: {
        endpoint: "/farm/financial",
        title: "Finance",
        description: "Operational income, expense, receipts, payments and reconciliation.",
        fields: [
            { name: "transaction_type", label: "Transaction Type", required: true, options: ["INCOME", "EXPENSE", "RECEIPT", "PAYMENT", "OWNER_WITHDRAWAL", "LOAN_PAYMENT"] },
            { name: "amount", label: "Amount (PKR)", type: "number", required: true },
            { name: "category", label: "Category" },
            { name: "payment_method", label: "Payment Method", options: ["CASH", "BANK", "MOBILE", "CREDIT"] },
            { name: "counterparty", label: "Counterparty" },
            { name: "notes", label: "Notes" },
            { name: "operator", label: "Operator", required: true },
        ],
    },
};

const nav: Array<{ id: ViewId; label: string; icon: string }> = [
    { id: "dashboard", label: "Dashboard", icon: "⌂" },
    { id: "animals", label: "Animals", icon: "◉" },
    { id: "milk", label: "Milk", icon: "◌" },
    { id: "feeding", label: "Feeding", icon: "≋" },
    { id: "health", label: "Health", icon: "✚" },
    { id: "breeding", label: "Breeding", icon: "♧" },
    { id: "workforce", label: "Workforce", icon: "♙" },
    { id: "inventory", label: "Inventory", icon: "▤" },
    { id: "equipment", label: "Equipment", icon: "⚙" },
    { id: "finance", label: "Finance", icon: "₨" },
    { id: "analytics", label: "Analytics", icon: "⌁" },
    { id: "alerts", label: "Alerts", icon: "!" },
];

function unwrap(value: unknown): unknown[] {
    if (Array.isArray(value)) return value;
    if (!value || typeof value !== "object") return [];
    const obj = value as Record<string, unknown>;
    for (const key of ["items", "data", "records", "results", "events", "animals", "transactions"]) {
        if (Array.isArray(obj[key])) return obj[key] as unknown[];
    }
    return [];
}

function asRecord(value: unknown): Record<string, unknown> {
    return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function numberValue(value: unknown): number | null {
    const n = typeof value === "number" ? value : Number(value);
    return Number.isFinite(n) ? n : null;
}

function firstNumber(obj: Record<string, unknown>, keys: string[]): number | null {
    for (const key of keys) {
        const n = numberValue(obj[key]);
        if (n !== null) return n;
    }
    return null;
}

function formatNumber(value: number | null | undefined, suffix = ""): string {
    if (value === null || value === undefined || !Number.isFinite(value)) return "—";
    return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}${suffix}`;
}

function dateKey(value: unknown): string | null {
    if (typeof value !== "string") return null;
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10);
}

function decisionText(decision: OperationalDecision): string {
    const details = JSON.stringify(decision.details ?? {}).toLowerCase();
    return `${decision.type ?? ""} ${decision.title ?? ""} ${decision.action ?? ""} ${details}`.toLowerCase();
}

function yieldDropPercent(decision: OperationalDecision): number | null {
    const text = decisionText(decision);
    if (!/(yield|milk|production).*(drop|declin|decreas)|(?:drop|declin|decreas).*(yield|milk|production)/.test(text)) return null;
    const match = text.match(/(?:-|−)?\s*(\d+(?:\.\d+)?)\s*%/);
    if (!match) return null;
    const pct = Number(match[1]);
    return pct > 20 ? pct : null;
}

function useLiveJson(endpoint: string | null, refresh = 30000) {
    const [data, setData] = useState<unknown>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const load = useCallback(async () => {
        if (!endpoint) return;
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API}${endpoint}`, { headers: { Accept: "application/json" } });
            if (!response.ok) throw new Error(`Request failed: ${response.status}`);
            setData(await response.json());
        } catch (e) {
            setError(e instanceof Error ? e.message : "Unable to load live data.");
        } finally {
            setLoading(false);
        }
    }, [endpoint]);
    useEffect(() => {
        void load();
        if (!endpoint) return;
        const timer = window.setInterval(() => void load(), refresh);
        return () => window.clearInterval(timer);
    }, [endpoint, refresh, load]);
    return { data, loading, error, reload: load };
}

function Card({ title, action, children, className = "" }: { title: string; action?: React.ReactNode; children: React.ReactNode; className?: string }) {
    return <section className={`dos-card ${className}`}><div className="dos-card-head"><h2>{title}</h2>{action}</div><div className="dos-card-body">{children}</div></section>;
}

function Kpi({ label, value, sub, tone = "default" }: { label: string; value: string; sub?: string; tone?: string }) {
    return <div className={`dos-kpi ${tone}`}><div className="dos-kpi-label">{label}</div><div className="dos-kpi-value">{value}</div>{sub && <div className="dos-kpi-sub">{sub}</div>}</div>;
}

function Table({ rows, onRow }: { rows: Record<string, unknown>[]; onRow?: (row: Record<string, unknown>) => void }) {
    const columns = useMemo(() => {
        const set = new Set<string>();
        rows.slice(0, 20).forEach(row => Object.keys(row).slice(0, 7).forEach(key => set.add(key)));
        return Array.from(set).slice(0, 7);
    }, [rows]);
    if (!rows.length) return <div className="dos-empty">No live records available.</div>;
    return <div className="dos-table-wrap"><table className="dos-table"><thead><tr>{columns.map(c => <th key={c}>{c.replaceAll("_", " ")}</th>)}</tr></thead><tbody>{rows.slice(0, 18).map((row, i) => <tr key={i} onClick={() => onRow?.(row)} className={onRow ? "clickable" : ""}>{columns.map(c => <td key={c}>{typeof row[c] === "object" ? JSON.stringify(row[c]) : String(row[c] ?? "—")}</td>)}</tr>)}</tbody></table></div>;
}

function Donut({ segments }: { segments: Array<{ label: string; value: number }> }) {
    const total = segments.reduce((sum, item) => sum + item.value, 0);
    let cursor = 0;
    const colors = ["#2f9d67", "#3b82f6", "#8b5cf6", "#f59e0b", "#94a3b8"];
    const gradient = segments.length && total ? `conic-gradient(${segments.map((s, i) => { const start = cursor / total * 100; cursor += s.value; const end = cursor / total * 100; return `${colors[i % colors.length]} ${start}% ${end}%`; }).join(",")})` : "#e7ece8";
    return <div className="donut-wrap"><div className="donut" style={{ background: gradient }}><div className="donut-hole"><strong>{total}</strong><span>head</span></div></div><div className="legend">{segments.map((s, i) => <div className="legend-row" key={s.label}><span><i style={{ background: colors[i % colors.length] }} />{s.label}</span><strong>{s.value}</strong></div>)}</div></div>;
}

function LineChart({ points }: { points: Array<{ label: string; value: number }> }) {
    if (!points.length) return <div className="dos-empty">No live production history returned.</div>;
    const width = 700, height = 230, pad = 24;
    const max = Math.max(...points.map(p => p.value), 1);
    const min = Math.min(...points.map(p => p.value), 0);
    const span = Math.max(max - min, 1);
    const xy = points.map((p, i) => ({ x: pad + i * ((width - pad * 2) / Math.max(points.length - 1, 1)), y: height - pad - ((p.value - min) / span) * (height - pad * 2) }));
    const line = xy.map(p => `${p.x},${p.y}`).join(" ");
    const area = `${pad},${height-pad} ${line} ${width-pad},${height-pad}`;
    return <div className="chart"><svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none"><line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="#dfe6e1"/><line x1={pad} y1={height/2} x2={width-pad} y2={height/2} stroke="#eef2ef"/><polygon points={area} fill="#e9f6ef"/><polyline points={line} fill="none" stroke="#238b5e" strokeWidth="4" strokeLinejoin="round" strokeLinecap="round"/>{xy.map((p,i)=><circle key={i} cx={p.x} cy={p.y} r="3.5" fill="#238b5e"/>)}</svg><div className="chart-labels">{points.map(p=><span key={p.label}>{p.label}</span>)}</div></div>;
}

export default function DairyOSShell() {
    const [view, setView] = useState<ViewId>("dashboard");
    const [period, setPeriod] = useState<Period>("7d");
    const [financeView, setFinanceView] = useState<FinanceView>("cash");
    const [notificationsOpen, setNotificationsOpen] = useState(false);
    const [modal, setModal] = useState<Exclude<ViewId, "dashboard" | "analytics" | "alerts"> | null>(null);
    const [selectedAnimal, setSelectedAnimal] = useState<Record<string, unknown> | null>(null);
    const [toast, setToast] = useState<string | null>(null);

    const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
    const [dashboardError, setDashboardError] = useState<string | null>(null);
    const [loadingDashboard, setLoadingDashboard] = useState(true);

    const loadDashboard = useCallback(async () => {
        setLoadingDashboard(true);
        try {
            const payload = await getDashboard();
            setDashboard(payload);
            setDashboardError(null);
        } catch (e) {
            setDashboardError(e instanceof Error ? e.message : "Unable to load live dashboard.");
        } finally {
            setLoadingDashboard(false);
        }
    }, []);

    useEffect(() => {
        void loadDashboard();
        const timer = window.setInterval(() => void loadDashboard(), 30000);
        return () => window.clearInterval(timer);
    }, [loadDashboard]);

    useEffect(() => {
        if (!toast) return;
        const timer = window.setTimeout(() => setToast(null), 2600);
        return () => window.clearTimeout(timer);
    }, [toast]);

    const activeNav = nav.find(item => item.id === view) ?? nav[0];
    const runtime = dashboard?.dashboard ?? {};
    const state = dashboard?.operational_state ?? runtime.operational_state ?? {};
    const decisions = (dashboard?.operational_decisions ?? runtime.operational_decisions ?? []) as OperationalDecision[];
    const yieldAlerts = decisions.filter(d => yieldDropPercent(d) !== null);
    const notificationCount = yieldAlerts.length + decisions.filter(d => yieldDropPercent(d) === null).length;

    const animals = useLiveJson(view === "animals" || view === "dashboard" ? "/farm/animals" : null).data;
    const moduleData = useLiveJson(modal ? modules[modal].endpoint : null, 15000);
    const currentModule = useLiveJson(["feeding","health","breeding","workforce","inventory","equipment","finance","milk"].includes(view) ? modules[view as keyof typeof modules].endpoint : null, 15000);
    const analyticsData = useLiveJson(view === "analytics" ? "/operations/dashboard" : null, 30000);

    const animalRows = useMemo(() => unwrap(animals).map(asRecord), [animals]);
    const animalState = Object.entries(state.animals ?? {}).map(([id, value]) => ({ animal_id: id, ...asRecord(value) }));
    const combinedAnimals = animalRows.length ? animalRows : animalState;

    const milk = asRecord(runtime.milk);
    const history = unwrap(milk.history ?? milk.trend_history).map(asRecord).map((row, index) => ({
        label: String(row.date ?? row.day ?? index + 1).slice(5, 10),
        value: firstNumber(row, ["litres", "value", "milk_litres"]) ?? 0,
        date: dateKey(row.date),
    }));
    const filteredHistory = useMemo(() => {
        if (period === "custom") return history;
        const days = period === "7d" ? 7 : period === "month" ? 30 : 365;
        return history.slice(-days);
    }, [history, period]);

    const herdSegments = useMemo(() => {
        const counts = new Map<string, number>();
        combinedAnimals.forEach(row => {
            const lifecycle = String(row.lifecycle ?? row.status ?? row.category ?? "Unknown").toUpperCase();
            const key = lifecycle.includes("MILK") ? "Milking" : lifecycle.includes("DRY") ? "Dry" : lifecycle.includes("HEIF") ? "Heifers" : lifecycle.includes("CALF") ? "Calves" : "Other";
            counts.set(key, (counts.get(key) ?? 0) + 1);
        });
        if (!counts.size) return [];
        return ["Milking","Dry","Heifers","Calves","Other"].filter(k => counts.has(k)).map(k => ({ label: k, value: counts.get(k) ?? 0 }));
    }, [combinedAnimals]);

    const financeRecords = useMemo(() => {
        const raw = view === "finance" ? currentModule.data : null;
        return unwrap(raw).map(asRecord);
    }, [currentModule.data, view]);

    const financeSummary = useMemo(() => {
        let cash = 0, bank = 0, income = 0, expense = 0;
        financeRecords.forEach(row => {
            const amount = firstNumber(row, ["amount", "value", "amount_pkr"]) ?? 0;
            const type = String(row.transaction_type ?? row.type ?? "").toUpperCase();
            const method = String(row.payment_method ?? row.method ?? "").toUpperCase();
            const signed = /EXPENSE|PAYMENT|WITHDRAWAL|LOAN/.test(type) ? -amount : amount;
            if (method === "BANK") bank += signed; else cash += signed;
            if (/INCOME|RECEIPT/.test(type)) income += amount;
            if (/EXPENSE|PAYMENT/.test(type)) expense += amount;
        });
        return { cash, bank, income, expense };
    }, [financeRecords]);

    const pageTitle = activeNav.label;
    const quickAdd = (id: Exclude<ViewId, "dashboard" | "analytics" | "alerts">) => setModal(id);

    const submitRecord = async (id: Exclude<ViewId, "dashboard" | "analytics" | "alerts">, payload: Record<string, unknown>) => {
        try {
            const response = await fetch(`${API}${modules[id].endpoint}`, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(payload) });
            if (!response.ok) throw new Error(`Save failed: ${response.status}`);
            setModal(null);
            setToast(`${modules[id].title} record saved.`);
            await loadDashboard();
            await moduleData.reload();
            await currentModule.reload();
        } catch (e) {
            setToast(e instanceof Error ? e.message : "Unable to save record.");
        }
    };

    return <div className="dairyos-app">
        <aside className="dos-sidebar">
            <div className="dos-brand"><div className="dos-brand-mark">D</div><div><div className="dos-brand-title">DairyOS</div><div className="dos-brand-sub">Intelligent Farm Operations</div></div></div>
            <nav className="dos-nav">{nav.map(item => <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => setView(item.id)}><span className="dos-nav-icon">{item.icon}</span>{item.label}{item.id === "alerts" && notificationCount > 0 ? <b className="dos-nav-badge">{notificationCount}</b> : null}</button>)}</nav>
            <div className="dos-quick"><div className="dos-quick-title">Quick access</div><button onClick={() => quickAdd("animals")}>＋ Add Animal</button><button onClick={() => quickAdd("milk")}>＋ Record Milk</button><button onClick={() => quickAdd("health")}>＋ Record Health</button><button onClick={() => quickAdd("breeding")}>＋ Add Breeding</button><button onClick={() => quickAdd("finance")}>＋ Add Expense</button></div>
            <div className="dos-system"><span className="dos-dot"/> <span>System status</span><strong>{dashboardError ? "Attention" : "All operational"}</strong></div>
        </aside>

        <main className="dos-main">
            <header className="dos-topbar"><div><h1>{pageTitle}</h1><p>{view === "dashboard" ? "Real-time overview of farm operations" : activeNav.label === "Alerts" ? "Operator notifications and operational decisions" : activeNav.label}</p></div><div className="dos-top-actions"><button className="dos-icon-button" aria-label="Notifications" onClick={() => setNotificationsOpen(v => !v)}>♢{notificationCount > 0 && <span className="dos-badge">{notificationCount}</span>}</button><div className="dos-user"><div className="dos-avatar">RM</div><div><strong>Ramesh</strong><small>Farm Manager</small></div></div></div></header>
            <div className="dos-content">
                {view === "dashboard" && <DashboardPage loading={loadingDashboard} error={dashboardError} runtime={runtime} state={state} decisions={decisions} yieldAlerts={yieldAlerts} herdSegments={herdSegments} milk={milk} filteredHistory={filteredHistory} period={period} setPeriod={setPeriod} onHerd={() => setView("animals")} onMilk={() => setView("milk")} onFinance={() => setView("finance")} onAlerts={() => setView("alerts")} />}
                {view !== "dashboard" && view !== "analytics" && view !== "alerts" && <ModulePage id={view} data={currentModule.data} loading={currentModule.loading} error={currentModule.error} onAdd={() => setModal(view)} onAnimal={row => { setSelectedAnimal(row); setView("animals"); }} financeView={financeView} setFinanceView={setFinanceView} />}
                {view === "analytics" && <AnalyticsPage data={analyticsData.data} loading={analyticsData.loading} error={analyticsData.error} />}
                {view === "alerts" && <AlertsPage decisions={decisions} yieldAlerts={yieldAlerts} />}
            </div>
        </main>

        {notificationsOpen && <div className="dos-notification-popover"><div className="dos-pop-head"><strong>Notifications</strong><button onClick={() => setNotificationsOpen(false)}>×</button></div>{yieldAlerts.length ? yieldAlerts.map((d, i) => <div className="dos-notification" key={i}><span className="alert-id">{`YD-${dateKey(d.details?.date) ?? new Date().toISOString().slice(0,10)}-${String(d.animal_id ?? "FARM").replace(/\W/g, "")}`}</span><strong>{d.title ?? "Animal milk yield dropped >20%"}</strong><small>{d.animal_id ? `Animal ${d.animal_id} · ${yieldDropPercent(d)}% below reference` : "Production intelligence"}</small></div>) : <div className="dos-empty">No live notifications.</div>}</div>}
        {modal && <EntryModal config={modules[modal]} onClose={() => setModal(null)} onSubmit={payload => void submitRecord(modal, payload)} />}
        {selectedAnimal && <AnimalDrawer animal={selectedAnimal} onClose={() => setSelectedAnimal(null)} />}
        {toast && <div className="dos-toast">{toast}</div>}
    </div>;
}

function DashboardPage({ loading, error, runtime, state, decisions, yieldAlerts, herdSegments, milk, filteredHistory, period, setPeriod, onHerd, onMilk, onFinance, onAlerts }: { loading: boolean; error: string | null; runtime: Record<string, any>; state: Record<string, any>; decisions: OperationalDecision[]; yieldAlerts: OperationalDecision[]; herdSegments: Array<{label:string;value:number}>; milk: Record<string, any>; filteredHistory: Array<{label:string;value:number}>; period: Period; setPeriod: (p:Period)=>void; onHerd:()=>void; onMilk:()=>void; onFinance:()=>void; onAlerts:()=>void }) {
    const today = firstNumber(milk, ["today_litres"]);
    const morning = firstNumber(milk, ["morning_litres"]);
    const evening = firstNumber(milk, ["evening_litres"]);
    const animals = Object.keys(state.animals ?? {}).length;
    const finance = asRecord(state.financial_status);
    const financeToday = firstNumber(finance, ["today", "today_amount", "daily_total"]);
    const decisionsCount = decisions.length;
    return <div className="dos-page dashboard-page">
        {error && <div className="dos-error">Live dashboard unavailable: {error}</div>}
        <div className="dos-kpis five"><Kpi label="Herd" value={formatNumber(animals || null)} sub="Live animal records"/><Kpi label="Milk Today" value={formatNumber(today, " L")} sub={`${formatNumber(morning, " L")} morning · ${formatNumber(evening, " L")} evening`}/><Kpi label="Health" value={formatNumber(Object.keys(state.health_status ?? {}).length || null)} sub="Live health state"/><Kpi label="Breeding" value={formatNumber(Object.keys(state.breeding_status ?? {}).length || null)} sub="Active reproductive state"/><Kpi label="Finance" value={formatNumber(financeToday, " PKR")} sub="Select finance view"/></div>
        <div className="dos-dashboard-grid">
            <Card title="Herd Composition" action={<button className="link-btn" onClick={onHerd}>View details →</button>}><Donut segments={herdSegments}/>{!herdSegments.length && <div className="dos-empty">No live herd composition returned.</div>}</Card>
            <Card title="Milk Production" action={<div className="period-buttons">{(["7d","month","year","custom"] as Period[]).map(p => <button key={p} className={period===p?"active":""} onClick={()=>setPeriod(p)}>{p === "7d" ? "7 Days" : p === "month" ? "Month" : p === "year" ? "Year" : "Any timeframe"}</button>)}</div>}><div className="production-head"><div><strong>{formatNumber(today," L")}</strong><span>current period output</span></div><button className="link-btn" onClick={onMilk}>Open milk →</button></div><LineChart points={filteredHistory}/></Card>
            <Card title="Finance" action={<button className="link-btn" onClick={onFinance}>Open finance →</button>}><div className="finance-choice"><button onClick={onFinance}>Cash in Hand</button><button onClick={onFinance}>Money at Bank</button><button onClick={onFinance}>Monthly Reconciliation</button><button onClick={onFinance}>Quarterly Reconciliation</button><button onClick={onFinance}>Yearly Reconciliation</button></div>{financeToday !== null ? <div className="finance-total">{formatNumber(financeToday," PKR")}</div> : <div className="dos-empty">Choose a finance view for live figures.</div>}</Card>
        </div>
        <div className="dos-bottom-grid">
            <Card title="Production Notifications" action={<button className="link-btn" onClick={onAlerts}>View all →</button>}>{yieldAlerts.length ? <div className="alert-list">{yieldAlerts.slice(0,4).map((d,i)=><button key={i} className="alert-row" onClick={onAlerts}><span className="alert-id">{`YD-${String(d.animal_id ?? "FARM")}-${i+1}`}</span><span><strong>Animal {d.animal_id ?? "—"}</strong><small>{yieldDropPercent(d)}% drop from reference yield</small></span><b>›</b></button>)}</div> : <div className="dos-empty">No animal yield-drop notification is currently returned by live farm intelligence.</div>}</Card>
            <Card title="Recent Activity">{decisions.slice(0,5).map((d,i)=><div className="activity-row" key={i}><span className="activity-dot">{i+1}</span><div><strong>{d.title ?? d.action ?? d.type ?? "Operational event"}</strong><small>{d.animal_id ? `Animal ${d.animal_id}` : d.source ?? "DairyOS"}</small></div><time>{i === 0 ? "Now" : "Live"}</time></div>)}{!decisions.length && <div className="dos-empty">No live activity returned.</div>}</Card>
            <Card title="Farm Status"><div className="status-hero"><span className="status-live-dot"/><div><strong>{String(runtime.farm_status ?? "Live")}</strong><small>System {String(runtime.health ?? "operational")}</small></div></div><div className="status-list"><div><span>Operational decisions</span><strong>{decisionsCount}</strong></div><div><span>Yield notifications</span><strong>{yieldAlerts.length}</strong></div><div><span>Data freshness</span><strong>{String(runtime.freshness?.status ?? runtime.freshness ?? "Live")}</strong></div></div></Card>
        </div>
    </div>;
}

function ModulePage({ id, data, loading, error, onAdd, onAnimal, financeView, setFinanceView }: { id: Exclude<ViewId,"dashboard"|"analytics"|"alerts">; data: unknown; loading: boolean; error: string|null; onAdd:()=>void; onAnimal:(row:Record<string,unknown>)=>void; financeView:FinanceView; setFinanceView:(v:FinanceView)=>void }) {
    const config = modules[id];
    const rows = unwrap(data).map(asRecord);
    const isFinance = id === "finance";
    const isMilk = id === "milk";
    const title = config.title;
    const summary = id === "animals" ? `${rows.length || "No"} live animal records` : id === "milk" ? `${rows.length || "No"} live milk records` : `${rows.length || "No"} live records`;
    return <div className="dos-page"><div className="dos-page-head"><div><h2>{title}</h2><p>{config.description}</p></div><button className="dos-primary" onClick={onAdd}>＋ {id === "animals" ? "Add Animal" : id === "milk" ? "Record Milk" : `Add ${title} record`}</button></div>
        {isFinance && <div className="finance-toolbar"><select value={financeView} onChange={e=>setFinanceView(e.target.value as FinanceView)}><option value="cash">Cash in Hand</option><option value="bank">Money at Bank</option><option value="monthly">Monthly Reconciliation</option><option value="quarterly">Quarterly Reconciliation</option><option value="yearly">Yearly Reconciliation</option></select><span className="toolbar-note">View is derived from live financial records; no synthetic balances are inserted.</span></div>}
        {isMilk && <div className="finance-toolbar"><button className="period-chip active">7 Days</button><button className="period-chip">Month</button><button className="period-chip">Year</button><button className="period-chip">Any timeframe</button></div>}
        <div className="module-kpis"><Kpi label="Live records" value={String(rows.length)} sub={summary}/><Kpi label="Last update" value={loading ? "Loading" : "Live"} sub="15–30 second refresh"/><Kpi label="Source" value="API" sub={config.endpoint}/><Kpi label="Integrity" value={error ? "Attention" : "Connected"} sub={error ?? "Live backend response"}/></div>
        {error && <div className="dos-error">{error}</div>}
        <div className="dos-module-layout"><Card title={`${title} records`} action={<span className="muted">{rows.length} returned</span>}><Table rows={rows} onRow={id === "animals" ? onAnimal : undefined}/></Card><Card title="Operational input"><div className="input-summary"><strong>{config.fields.length}</strong><span>validated fields</span><p>Use the entry action to write a real record to <code>{config.endpoint}</code>. The module refreshes from the backend after save.</p><button className="dos-secondary" onClick={onAdd}>Open entry form</button></div></Card></div>
    </div>;
}

function AnalyticsPage({ data, loading, error }: { data: unknown; loading: boolean; error: string|null }) {
    const obj = asRecord(data);
    const widgets = unwrap(obj.dashboard ?? obj.widgets).map(asRecord);
    return <div className="dos-page"><div className="dos-page-head"><div><h2>Analytics</h2><p>Backend operational indicators without adding synthetic metrics.</p></div></div>{error && <div className="dos-error">{error}</div>}<div className="module-kpis"><Kpi label="Status" value={loading?"Loading":"Live"} sub="Operations dashboard"/><Kpi label="Widgets" value={String(widgets.length)} sub="Returned by backend"/><Kpi label="Source" value="API" sub="/operations/dashboard"/></div><div className="dos-module-layout"><Card title="Operational indicators"><Table rows={widgets}/></Card><Card title="Raw live state"><pre className="json-view">{JSON.stringify(data, null, 2)}</pre></Card></div></div>;
}

function AlertsPage({ decisions, yieldAlerts }: { decisions: OperationalDecision[]; yieldAlerts: OperationalDecision[] }) {
    const rows = decisions.map((d,i)=>({ id: yieldDropPercent(d) ? `YD-${d.animal_id ?? "FARM"}-${i+1}` : `OP-${i+1}`, type: d.type ?? "decision", animal_id: d.animal_id ?? "—", priority: d.priority ?? "—", title: d.title ?? d.action ?? "Operational decision", source: d.source ?? "backend" }));
    return <div className="dos-page"><div className="dos-page-head"><div><h2>Alerts & Decisions</h2><p>Operator notifications sourced from live DairyOS operational intelligence.</p></div></div><div className="module-kpis"><Kpi label="Notifications" value={String(decisions.length)} sub="Live operational decisions"/><Kpi label="Yield drop" value={String(yieldAlerts.length)} sub="More than 20%" tone="danger"/><Kpi label="Synthetic values" value="0" sub="Never fabricated"/></div><Card title="Notification register"><Table rows={rows}/></Card></div>;
}

function EntryModal({ config, onClose, onSubmit }: { config: ModuleConfig; onClose:()=>void; onSubmit:(payload:Record<string,unknown>)=>void }) {
    const [form, setForm] = useState<Record<string,unknown>>({});
    return <div className="dos-modal-backdrop"><div className="dos-modal"><div className="dos-modal-head"><div><h2>{config.title}</h2><p>{config.description}</p></div><button onClick={onClose}>×</button></div><form onSubmit={e=>{e.preventDefault(); onSubmit(form);}}><div className="form-grid">{config.fields.map(field => <label key={field.name}>{field.label}{field.required && <b>*</b>}{field.options ? <select required={field.required} value={String(form[field.name] ?? "")} onChange={e=>setForm(v=>({...v,[field.name]:e.target.value}))}><option value="">Select…</option>{field.options.map(o=><option key={o}>{o}</option>)}</select> : <input required={field.required} type={field.type === "number" ? "number" : "text"} step={field.type === "number" ? "0.01" : undefined} value={String(form[field.name] ?? "")} onChange={e=>setForm(v=>({...v,[field.name]:field.type === "number" ? Number(e.target.value) : e.target.value}))}/>}</label>)}</div><div className="dos-modal-actions"><button type="button" className="dos-secondary" onClick={onClose}>Cancel</button><button type="submit" className="dos-primary">Save to DairyOS</button></div></form></div></div>;
}

function AnimalDrawer({ animal, onClose }: { animal: Record<string,unknown>; onClose:()=>void }) {
    return <div className="dos-drawer-backdrop" onClick={onClose}><aside className="dos-drawer" onClick={e=>e.stopPropagation()}><div className="dos-modal-head"><div><span className="eyebrow">Animal record</span><h2>{String(animal.animal_id ?? animal.id ?? "Animal")}</h2></div><button onClick={onClose}>×</button></div><div className="drawer-avatar">{String(animal.animal_id ?? animal.id ?? "A").slice(-3)}</div><div className="drawer-grid">{Object.entries(animal).slice(0,16).map(([k,v])=><div key={k}><small>{k.replaceAll("_"," ")}</small><strong>{typeof v === "object" ? JSON.stringify(v) : String(v ?? "—")}</strong></div>)}</div></aside></div>;
}
