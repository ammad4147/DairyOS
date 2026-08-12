import React, { useEffect, useMemo, useState } from "react";
import "./OperationalModule.css";
import OperationalEntryPanel, { type OperationalEntryConfig } from "./OperationalEntryPanel";

type Mode = "cards" | "entries" | "decisions" | "state";
type Props = { title: string; endpoint: string; selector?: string; mode: Mode; entry?: OperationalEntryConfig };
type Row = Record<string, any>;
const API = "http://localhost:8000";
const n = (v: any) => Number.isFinite(Number(v)) ? Number(v) : 0;
const txt = (v: any) => v === null || v === undefined || v === "" ? "—" : typeof v === "object" ? JSON.stringify(v) : String(v);
const timeOf = (r: Row) => new Date(r.timestamp ?? r.date ?? r.created_at ?? 0).getTime();
const label = (v: string) => v.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
const milkTotal = (r: Row) => n(r.total_yield ?? r.litres ?? (n(r.morning_yield) + n(r.afternoon_yield) + n(r.evening_yield)));
const statusClass = (v: any) => /critical|failed|error|overdue|out_of_service|missed|negative/i.test(String(v)) ? "danger" : /warning|watch|pending|open|due|elevated|maintenance/i.test(String(v)) ? "warning" : "good";

function periodStart(period: string) {
    const d = new Date();
    if (period === "7d") d.setDate(d.getDate() - 7);
    if (period === "month") d.setMonth(d.getMonth() - 1);
    if (period === "quarter") d.setMonth(d.getMonth() - 3);
    if (period === "year") d.setFullYear(d.getFullYear() - 1);
    if (period === "today") d.setHours(0, 0, 0, 0);
    return d;
}

function inPeriod(r: Row, period: string, from: string, to: string) {
    const t = timeOf(r);
    if (!Number.isFinite(t)) return period === "all";
    if (period === "custom") return Boolean(from && to) && t >= new Date(from).getTime() && t < new Date(to).getTime() + 86400000;
    return t >= periodStart(period).getTime();
}

function money(v: number) { return `PKR ${Math.round(v).toLocaleString("en-PK")}`; }

export default function OperationalModule({ title, endpoint, selector, mode, entry }: Props) {
    const lower = title.toLowerCase();
    const isMilk = lower.includes("milk");
    const isFinance = lower.includes("finance");
    const isAnimals = lower.includes("animal");
    const [payload, setPayload] = useState<any>(null);
    const [financeState, setFinanceState] = useState<Row>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [updated, setUpdated] = useState<string | null>(null);
    const [period, setPeriod] = useState(isMilk ? "7d" : isFinance ? "month" : "all");
    const [from, setFrom] = useState("");
    const [to, setTo] = useState("");
    const [query, setQuery] = useState("");

    const load = async () => {
        setLoading(true); setError(null);
        try {
            const response = await fetch(`${API}${endpoint}`);
            if (!response.ok) throw new Error(`Request failed: ${response.status}`);
            const raw = await response.json();
            const selected = selector ? selector.split(".").reduce((v: any, key) => v?.[key], raw) : raw;
            setPayload(selected);
            if (isFinance) {
                try {
                    const d = await fetch(`${API}/dashboard`);
                    if (d.ok) {
                        const dashboard = await d.json();
                        setFinanceState(dashboard?.operational_state?.financial_status ?? {});
                    }
                } catch { /* finance endpoint remains authoritative for transactions */ }
            }
            setUpdated(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
        } catch (e) { setError(e instanceof Error ? e.message : "Unable to load live data"); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); const t = window.setInterval(load, 60000); return () => window.clearInterval(t); }, [endpoint, selector]);

    const rows: Row[] = useMemo(() => Array.isArray(payload) ? payload : [], [payload]);
    const filtered = useMemo(() => rows.filter(r => inPeriod(r, period, from, to)).filter(r => !query || JSON.stringify(r).toLowerCase().includes(query.toLowerCase())), [rows, period, from, to, query]);
    const titleLabel = title.replace(/\s+/g, " ");

    if (loading && payload === null) return <section className="module-view">{entry && <OperationalEntryPanel config={entry} onSaved={load} />}<div className="module-loading"><span className="loading-mark"/><strong>Loading {titleLabel.toLowerCase()}</strong><span>Reading live DairyOS records…</span></div></section>;
    if (error && payload === null) return <section className="module-view">{entry && <OperationalEntryPanel config={entry} onSaved={load} />}<div className="module-error"><div><strong>Unable to load live data.</strong><p>{error}</p></div><button onClick={load}>Retry</button></div></section>;

    const summary = <ModuleSummary title={titleLabel} rows={filtered} isMilk={isMilk} isFinance={isFinance} isAnimals={isAnimals} financeState={financeState} />;
    return <section className="module-view">
        {entry && <OperationalEntryPanel config={entry} onSaved={load} />}
        <div className="module-header-row"><div><div className="module-kicker">LIVE OPERATIONS</div><h2>{titleLabel}</h2><p>Actual records only. Missing measures remain visible as unavailable rather than being guessed.</p></div><div className="module-actions"><span className="live-chip"><i/>LIVE</span><button onClick={load}>Refresh</button></div></div>
        {(isMilk || isFinance) && <PeriodBar finance={isFinance} period={period} setPeriod={setPeriod} from={from} to={to} setFrom={setFrom} setTo={setTo} />}
        {summary}
        {mode !== "state" && <div className="module-toolbar"><div><strong>{filtered.length.toLocaleString()} record{filtered.length === 1 ? "" : "s"}</strong>{updated && <span>Updated {updated}</span>}</div><label className="search-box"><span>⌕</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search records" /></label></div>}
        {mode === "cards" ? <AnimalGrid rows={filtered} /> : mode === "state" ? <StateGrid payload={payload} /> : <RecordTable rows={filtered} decision={mode === "decisions"} finance={isFinance} milk={isMilk} />}
    </section>;
}

function PeriodBar({ finance, period, setPeriod, from, to, setFrom, setTo }: { finance: boolean; period: string; setPeriod: (v: string) => void; from: string; to: string; setFrom: (v: string) => void; setTo: (v: string) => void }) {
    const options = finance ? [["cash", "Cash"], ["bank", "Bank"], ["month", "Monthly"], ["quarter", "Quarterly"], ["year", "Yearly"]] : [["7d", "7 Days"], ["month", "Month"], ["year", "Year"], ["custom", "Custom"]];
    return <div className="period-bar"><div><strong>{finance ? "Finance view" : "Production period"}</strong><span>{finance ? "Choose the balance or reconciliation window." : "Choose the production window; calculations use recorded milk events."}</span></div><div className="period-controls">{options.map(([key, name]) => <button key={key} type="button" className={period === key ? "selected" : ""} onClick={() => setPeriod(key)}>{name}</button>)}{period === "custom" && <><input type="date" value={from} onChange={e => setFrom(e.target.value)} /><input type="date" value={to} onChange={e => setTo(e.target.value)} /></>}</div></div>;
}

function ModuleSummary({ title, rows, isMilk, isFinance, isAnimals, financeState }: { title: string; rows: Row[]; isMilk: boolean; isFinance: boolean; isAnimals: boolean; financeState: Row }) {
    if (isAnimals) {
        const milking = rows.filter(r => r.is_currently_milking === true || /milk/i.test(String(r.lifecycle_status ?? ""))).length;
        return <div className="module-summary"><Summary label="Animals in view" value={rows.length} /><Summary label="Milking" value={milking || "—"} /><Summary label="Dry / other" value={rows.length && milking ? rows.length - milking : "—"} /><Summary label="Source" value="Live registry" /></div>;
    }
    if (isMilk) {
        const litres = rows.reduce((a, r) => a + milkTotal(r), 0);
        const animals = new Set(rows.map(r => r.animal_id).filter(Boolean)).size;
        return <div className="module-summary"><Summary label="Recorded litres" value={`${litres.toFixed(1)} L`} tone={litres ? "good" : "neutral"} /><Summary label="Animals measured" value={animals || "—"} /><Summary label="Records" value={rows.length} /><Summary label="Withdrawal" value={rows.some(r => /withheld/i.test(r.status)) ? "ACTIVE" : "Clear"} tone={rows.some(r => /withheld/i.test(r.status)) ? "danger" : "good"} /></div>;
    }
    if (isFinance) {
        const income = rows.filter(r => /income|sale|receipt/i.test(r.transaction_type ?? "")).reduce((a, r) => a + n(r.amount), 0);
        const expense = rows.filter(r => /expense|purchase|payment|cost/i.test(r.transaction_type ?? "")).reduce((a, r) => a + n(r.amount), 0);
        const cash = n(financeState.cash_in_hand ?? financeState.cash ?? financeState.cash_balance);
        const bank = n(financeState.money_at_bank ?? financeState.bank_balance ?? financeState.bank);
        return <div className="module-summary"><Summary label="Cash in hand" value={money(cash)} /><Summary label="Money at bank" value={money(bank)} /><Summary label="Income" value={money(income)} tone="good" /><Summary label="Net reconciliation" value={money(income - expense)} tone={income - expense >= 0 ? "good" : "danger"} /></div>;
    }
    const open = rows.filter(r => /open|pending|active|warning|high|critical/i.test(`${r.status} ${r.priority} ${r.severity}`)).length;
    return <div className="module-summary"><Summary label="Records" value={rows.length} /><Summary label="Attention" value={open} tone={open ? "warning" : "good"} /><Summary label="Latest" value={rows[0] ? new Date(timeOf(rows[0])).toLocaleDateString() : "—"} /><Summary label="Source" value="Live API" /></div>;
}
function Summary({ label: text, value, tone = "neutral" }: { label: string; value: any; tone?: string }) { return <div className={`summary-box ${tone}`}><span>{text}</span><strong>{txt(value)}</strong></div>; }

function AnimalGrid({ rows }: { rows: Row[] }) {
    const [selected, setSelected] = useState<Row | null>(null);
    return <>{rows.length ? <div className="animal-grid">{rows.map((r, i) => <button type="button" className="animal-card" key={i} onClick={() => setSelected(r)}><div className="animal-card-top"><span className="animal-tag">{txt(r.ear_tag ?? r.animal_id)}</span><span className={`status-chip ${statusClass(r.lifecycle_status ?? r.status)}`}>{txt(r.lifecycle_status ?? r.status ?? "ACTIVE")}</span></div><h3>{txt(r.animal_id ?? r.ear_tag)}</h3><div className="animal-meta"><div><span>Breed</span><strong>{txt(r.breed)}</strong></div><div><span>Sex</span><strong>{txt(r.sex)}</strong></div><div><span>Milking</span><strong>{r.is_currently_milking ? "Yes" : "No"}</strong></div></div></button>)}</div> : <EmptyState title="No animal records in this view" />}{selected && <Detail value={selected} onClose={() => setSelected(null)} />}</>;
}

function RecordTable({ rows, decision, finance, milk }: { rows: Row[]; decision: boolean; finance: boolean; milk: boolean }) {
    if (!rows.length) return <EmptyState title="No records in this view" />;
    const cols = decision ? ["priority", "title", "animal_id", "action", "source", "status"] : finance ? ["timestamp", "transaction_type", "category", "amount", "payment_method", "counterparty", "operator"] : milk ? ["timestamp", "animal_id", "morning_yield", "afternoon_yield", "evening_yield", "total_yield", "status", "operator"] : ["timestamp", "animal_id", "item", "feed_type", "quantity_kg", "worker_id", "equipment_id", "event_type", "severity", "status", "operator"];
    const visible = cols.filter(c => rows.some(r => r[c] !== undefined && r[c] !== null && r[c] !== ""));
    return <div className="data-table-wrap"><table className="data-table"><thead><tr>{visible.map(c => <th key={c}>{label(c)}</th>)}</tr></thead><tbody>{rows.slice(0, 150).map((r, i) => <tr key={i} className={decision ? "decision-row" : ""}>{visible.map(c => <td key={c}>{c === "amount" ? money(n(r[c])) : c === "total_yield" ? `${milkTotal(r).toFixed(2)} L` : <Cell value={r[c]} />}</td>)}</tr>)}</tbody></table></div>;
}
function Cell({ value }: { value: any }) { const s = txt(value); return <span className={s.length < 24 && /critical|warning|open|active|completed|recorded|operational|out_of_service|maintenance/i.test(s) ? `status-chip ${statusClass(s)}` : "cell-text"}>{s}</span>; }
function StateGrid({ payload }: { payload: any }) { const entries = Object.entries(payload ?? {}); return entries.length ? <div className="state-grid">{entries.map(([k, v]) => <div className="state-card" key={k}><div className="state-card-title">{label(k)}</div><div className="state-card-value">{typeof v === "object" ? <pre>{JSON.stringify(v, null, 2)}</pre> : txt(v)}</div></div>)}</div> : <EmptyState title="No operational state yet" />; }
function Detail({ value, onClose }: { value: Row; onClose: () => void }) { return <div className="record-detail-backdrop" onClick={onClose}><div className="record-detail" onClick={e => e.stopPropagation()}><div className="record-detail-head"><div><div className="module-kicker">RECORD DETAIL</div><h2>{txt(value.animal_id ?? value.ear_tag ?? value.item ?? value.equipment_id ?? "Record")}</h2></div><button onClick={onClose}>×</button></div>{Object.entries(value).map(([k, v]) => <div className="detail-row" key={k}><span>{label(k)}</span><strong>{txt(v)}</strong></div>)}</div></div>; }
function EmptyState({ title }: { title: string }) { return <div className="empty-state"><strong>{title}</strong><span>The API is available, but no recorded data matches this view.</span></div>; }
