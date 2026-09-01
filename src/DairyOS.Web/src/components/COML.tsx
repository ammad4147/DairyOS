import React, { useEffect, useMemo, useState } from 'react';
import { Calculator, Lock, AlertTriangle, Milk, Wheat, DollarSign, Plus, Trash2, SlidersHorizontal } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';
const DRAFT_KEY = 'dairyos_coml_manual_draft';

type Line = { id: string; item: string; quantity: string; unit: string; unitRate: string };
export type COMLOutput = {
  milkProduced: number;
  feedTotal: number;
  opexTotal: number;
  feedCostPerLiter: number;
  opexCostPerLiter: number;
  costOfMilkProductionPerLiter: number;
};

const FEED = ['Silage','Alfalfa','Berseem','Wheat Straw','Vanda / Compound Feed','Maize / Corn','Wheat Bran','Rice Polish','Soybean Meal','Canola Meal','Cottonseed Cake','Bypass Fat','Mineral Premix','Sodium Bicarbonate','Toxin Binder','Molasses','Other'];
const OPEX = ['Veterinary','Vaccination','Breeding / AI','Milker Wages','Feeder / Shed Worker Wages','Manager Salary','Electricity','Generator Fuel','Water Pumping','Equipment Maintenance','Shed Maintenance','Hygiene Chemicals','Bedding','Milk Transport','Rent / Lease','Banking / Accounting','Other'];

const inputStyle: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', border: '1px solid #334155', color: '#fff', borderRadius: 6, padding: '8px 9px', fontSize: 11 };
const panel: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 14, minWidth: 0 };
const button = (bg: string): React.CSSProperties => ({ background: bg, color: '#fff', border: 0, borderRadius: 6, padding: '8px 11px', fontSize: 10, fontWeight: 900, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 5 });
const label: React.CSSProperties = { fontSize: 9, color: '#94a3b8', display: 'block', fontWeight: 800, textTransform: 'uppercase' };

const today = () => new Date().toISOString().slice(0, 10);
const monthStart = () => {
  const d = new Date();
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1)).toISOString().slice(0, 10);
};
const daysAgo = (n: number) => {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
};
const newLine = (item = ''): Line => ({ id: `${Date.now()}-${Math.random()}`, item, quantity: '', unit: 'kg', unitRate: '' });
const money = (v: number | null | undefined) => {
  if (v == null) return 'N/A';
  const n = Number(v);
  return Number.isFinite(n) ? `PKR ${n.toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A';
};

function LineTable({ title, rows, setRows, options, accent }: { title: string; rows: Line[]; setRows: React.Dispatch<React.SetStateAction<Line[]>>; options: string[]; accent: string }) {
  return (
    <section style={panel}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 style={{ margin: 0, fontSize: 13, color: accent }}>{title}</h3>
        <button type="button" onClick={() => setRows(x => [...x, newLine()])} style={button('#1e293b')}><Plus size={12} /> Add Item</button>
      </div>
      {rows.length === 0 ? (
        <div style={{ fontSize: 10, color: '#64748b', padding: '14px 0' }}>No line items yet. Draft is saved automatically while you work.</div>
      ) : rows.map(row => (
        <div key={row.id} style={{ display: 'grid', gridTemplateColumns: '1.4fr .8fr .7fr .8fr 34px', gap: 6, alignItems: 'center', marginBottom: 6 }}>
          <select value={row.item} onChange={e => setRows(x => x.map(r => r.id === row.id ? { ...r, item: e.target.value } : r))} style={inputStyle}>
            <option value="">Select item…</option>
            {options.map(item => <option key={item} value={item}>{item}</option>)}
          </select>
          <input type="number" min="0" step="0.001" placeholder="Quantity" value={row.quantity} onChange={e => setRows(x => x.map(r => r.id === row.id ? { ...r, quantity: e.target.value } : r))} style={inputStyle} />
          <select value={row.unit} onChange={e => setRows(x => x.map(r => r.id === row.id ? { ...r, unit: e.target.value } : r))} style={inputStyle}>
            <option>kg</option><option>g</option><option>L</option><option>unit</option><option>visit</option><option>day</option><option>month</option><option>dose</option>
          </select>
          <input type="number" min="0" step="0.01" placeholder="PKR / unit" value={row.unitRate} onChange={e => setRows(x => x.map(r => r.id === row.id ? { ...r, unitRate: e.target.value } : r))} style={inputStyle} />
          <button type="button" onClick={() => setRows(x => x.filter(r => r.id !== row.id))} style={{ width: 30, height: 30, borderRadius: 5, border: '1px solid #334155', background: '#1e293b', color: '#94a3b8', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <Trash2 size={12} />
          </button>
        </div>
      ))}
    </section>
  );
}

function MetricCard({ title, value, subtitle, color, icon }: { title: string; value: string; subtitle: string; color: string; icon: React.ReactNode }) {
  return (
    <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: `4px solid ${color}` }}>
      <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        {icon} {title}
      </div>
      <div style={{ fontSize: '22px', fontWeight: 'bold', color, marginBottom: '2px' }}>{value}</div>
      <div style={{ fontSize: '10px', color: '#64748b' }}>{subtitle}</div>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div style={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: 6, padding: 9 }}>
      <div style={{ fontSize: 8, color: '#64748b', textTransform: 'uppercase', fontWeight: 800 }}>{title}</div>
      <div style={{ fontSize: 15, fontWeight: 900, color: '#a78bfa', marginTop: 3 }}>{value}</div>
    </div>
  );
}

interface COMLProps { onOutputChange?: (output: COMLOutput) => void }

export default function COML({ onOutputChange }: COMLProps) {
  const [mode, setMode] = useState<'auto' | 'manual'>('auto');
  const [periodStart, setPeriodStart] = useState(monthStart());
  const [periodEnd, setPeriodEnd] = useState(today());
  const [autoLoading, setAutoLoading] = useState(true);
  const [autoData, setAutoData] = useState<any>(null);
  const [official, setOfficial] = useState<any>(null);
  const [milkProduced, setMilkProduced] = useState('');
  const [feedRows, setFeedRows] = useState<Line[]>([]);
  const [opexRows, setOpexRows] = useState<Line[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [draftRestored, setDraftRestored] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      const d = JSON.parse(raw);
      if (d.periodStart) setPeriodStart(d.periodStart);
      if (d.periodEnd) setPeriodEnd(d.periodEnd);
      if (d.milkProduced != null) setMilkProduced(String(d.milkProduced));
      if (Array.isArray(d.feedRows)) setFeedRows(d.feedRows);
      if (Array.isArray(d.opexRows)) setOpexRows(d.opexRows);
      setDraftRestored(true);
      setMessage('Restored unsaved manual COML draft.');
    } catch {
      // ignore corrupt draft
    }
  }, []);

  useEffect(() => {
    const payload = { periodStart, periodEnd, milkProduced, feedRows, opexRows, savedAt: new Date().toISOString() };
    localStorage.setItem(DRAFT_KEY, JSON.stringify(payload));
  }, [periodStart, periodEnd, milkProduced, feedRows, opexRows]);

  const loadAuto = async () => {
    setAutoLoading(true);
    try {
      const qs = new URLSearchParams({ period_start: periodStart, period_end: periodEnd });
      const [integrated, current] = await Promise.all([
        fetch(`${API_BASE}/farm/coml/integrated?${qs}`).then(r => (r.ok ? r.json() : null)).catch(() => null),
        fetch(`${API_BASE}/farm/coml/current`).then(r => (r.ok ? r.json() : null)).catch(() => null),
      ]);
      setAutoData(integrated);
      setOfficial(current);
    } finally {
      setAutoLoading(false);
    }
  };

  useEffect(() => { void loadAuto(); }, [periodStart, periodEnd]);

  const setPreset = (preset: 'month' | '30' | 'year') => {
    if (preset === 'month') {
      setPeriodStart(monthStart());
      setPeriodEnd(today());
    } else if (preset === '30') {
      setPeriodStart(daysAgo(30));
      setPeriodEnd(today());
    } else {
      const y = new Date().getUTCFullYear();
      setPeriodStart(`${y}-01-01`);
      setPeriodEnd(today());
    }
  };

  const calculate = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setError('');
    setMessage('');
    setResult(null);
    setLoading(true);
    try {
      if (new Date(periodEnd) < new Date(periodStart)) throw new Error('End date must be on or after start date.');
      if (!(Number(milkProduced) > 0)) throw new Error('Milk produced must be greater than zero.');
      const clean = (rows: Line[]) => rows.filter(r => r.item && Number(r.quantity) > 0 && Number(r.unitRate) >= 0).map(r => ({ item: r.item, quantity: Number(r.quantity), unit: r.unit, unit_rate: Number(r.unitRate) }));
      const response = await fetch(`${API_BASE}/farm/coml/calculate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ period_start: periodStart, period_end: periodEnd, milk_produced_liters: Number(milkProduced), feed_items: clean(feedRows), operating_items: clean(opexRows) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'COML calculation failed.');
      setResult(data);
      onOutputChange?.({
        milkProduced: Number(data.milk_produced_liters),
        feedTotal: Number(data.feed_total),
        opexTotal: Number(data.operating_total),
        feedCostPerLiter: Number(data.feed_cost_per_liter),
        opexCostPerLiter: Number(data.opex_cost_per_liter),
        costOfMilkProductionPerLiter: Number(data.total_coml_per_liter),
      });
      setMessage('Manual calculation ready. These values take priority over Auto until you clear or lock.');
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'COML calculation failed.');
    } finally { setLoading(false); }
  };

  const lock = async () => {
    if (!result) return;
    setSaving(true); setError(''); setMessage('');
    try {
      const response = await fetch(`${API_BASE}/farm/coml/lock`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ month_start: periodStart.slice(0, 8) + '01', feed_cost_per_liter: Number(result.feed_cost_per_liter), opex_cost_per_liter: Number(result.opex_cost_per_liter), notes: `Manual calculation ${result.period_start} to ${result.period_end}; milk ${result.milk_produced_liters} L; ${result.period_days} days.`, updated_by: 'UI Operator' }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to lock COML record.');
      setOfficial(data); localStorage.removeItem(DRAFT_KEY); setMessage('Official monthly COML locked. Manual draft cleared.'); void loadAuto();
    } catch (exc) { setError(exc instanceof Error ? exc.message : 'Unable to lock COML record.'); }
    finally { setSaving(false); }
  };

  const clearDraft = () => {
    localStorage.removeItem(DRAFT_KEY); setFeedRows([]); setOpexRows([]); setMilkProduced(''); setResult(null); setMessage('Manual draft cleared.');
  };

  const manualActive = mode === 'manual' && !!result;
  const officialRec = official?.record || null;

  const displayMilk = useMemo(() => {
    if (manualActive) return Number(result.milk_produced_liters || milkProduced || 0);
    return Number(autoData?.production?.totalLiters || autoData?.production?.total_liters || 0);
  }, [manualActive, result, milkProduced, autoData]);

  const displayFeedPerL = useMemo(() => {
    if (manualActive) return Number(result.feed_cost_per_liter || 0);
    const value = autoData?.feed_cost_per_liter ?? autoData?.costs?.feed_cost_per_liter;
    return value == null ? null : Number(value);
  }, [manualActive, result, autoData]);

  const displayOpexPerL = useMemo(() => {
    if (manualActive) return Number(result.opex_cost_per_liter || 0);
    const value = autoData?.opex_cost_per_liter ?? autoData?.costs?.opex_cost_per_liter;
    return value == null ? null : Number(value);
  }, [manualActive, result, autoData]);

  const displayTotalPerL = useMemo(() => {
    if (manualActive) return Number(result.total_coml_per_liter || 0);
    const value = autoData?.total_coml_per_liter ?? autoData?.costs?.total_coml_per_liter;
    return value == null ? null : Number(value);
  }, [manualActive, result, autoData]);

  const milkSubtitle = manualActive ? 'Manual override (priority)' : `Selected period ${periodStart} → ${periodEnd}`;
  const costSubtitle = manualActive ? 'Manual override (priority)' : `Auto ledger cost for ${periodStart} → ${periodEnd}`;
  const days = result?.period_days || 0;

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: 18, color: '#a78bfa', display: 'flex', alignItems: 'center', gap: 8 }}><Calculator size={20} /> Cost of Milk Production (COML)</h2>
          <p style={{ margin: 0, fontSize: 12, color: '#94a3b8' }}>Choose a period for Auto (milk logs + ledger). Manual override is saved while you work and takes priority when calculated.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setMode('auto')} style={{ background: mode === 'auto' ? '#7c3aed' : '#1e293b', border: '1px solid #334155', color: '#fff', padding: '8px 14px', borderRadius: 6, fontSize: 11, cursor: 'pointer', fontWeight: 700 }}>Auto</button>
          <button onClick={() => setMode('manual')} style={{ background: mode === 'manual' ? '#f59e0b' : '#1e293b', border: '1px solid #334155', color: '#fff', padding: '8px 14px', borderRadius: 6, fontSize: 11, cursor: 'pointer', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 6 }}><SlidersHorizontal size={12} /> Manual Override</button>
        </div>
      </div>

      <section style={{ ...panel, marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 900, color: '#cbd5e1', marginBottom: 8 }}>Analysis Period</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
          <button type="button" onClick={() => setPreset('month')} style={button('#1e293b')}>This month</button>
          <button type="button" onClick={() => setPreset('30')} style={button('#1e293b')}>Last 30 days</button>
          <button type="button" onClick={() => setPreset('year')} style={button('#1e293b')}>Year to date</button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <label style={label}>From<input type="date" value={periodStart} onChange={e => setPeriodStart(e.target.value)} style={inputStyle} /></label>
          <label style={label}>To<input type="date" value={periodEnd} onChange={e => setPeriodEnd(e.target.value)} style={inputStyle} /></label>
        </div>
        <div style={{ fontSize: 10, color: '#64748b', marginTop: 6 }}>Production and costs below are for this range only.{draftRestored ? ' · Manual draft was restored from your last session.' : ''}</div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
        <MetricCard title="Milk in period (L)" value={`${Number(displayMilk || 0).toLocaleString()} L`} subtitle={milkSubtitle} color="#38bdf8" icon={<Milk size={16} />} />
        <MetricCard title="Feed Cost / L" value={money(displayFeedPerL)} subtitle={costSubtitle} color="#34d399" icon={<Wheat size={16} />} />
        <MetricCard title="OPEX / L" value={money(displayOpexPerL)} subtitle={costSubtitle} color="#f59e0b" icon={<DollarSign size={16} />} />
        <MetricCard title="COML / L" value={money(displayTotalPerL)} subtitle={costSubtitle} color="#a78bfa" icon={<Calculator size={16} />} />
      </div>

      {mode === 'auto' && (
        <>
          {autoLoading ? <div style={{ color: '#64748b', fontSize: 12 }}>Loading auto COML for selected period…</div> : (
            <>
              <div style={{ ...panel, marginBottom: 12 }}>
                <div style={{ fontSize: 12, color: '#fbbf24', fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}><AlertTriangle size={14} /> Auto sources</div>
                <div style={{ fontSize: 12, color: '#cbd5e1' }}>Milk source: <strong>{autoData?.production?.source || 'n/a'}</strong>{' · '}Cost source: <strong>{autoData?.costs?.source || autoData?.message || 'n/a'}</strong>{' · '}If logs/ledger are incomplete, use Manual Override.</div>
              </div>
              {officialRec && (
                <section style={{ ...panel, borderColor: '#22c55e', marginBottom: 12 }}>
                  <div style={{ fontSize: 11, fontWeight: 900, color: '#86efac' }}>Official Backend COML (monthly lock — reference only)</div>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>{official?.month_label || officialRec.month_label || 'Current month'} | Status: {officialRec.status || official?.status || 'UNKNOWN'}</div>
                  <div style={{ marginTop: 7, fontSize: 11 }}>Feed/L: <strong>{money(Number(officialRec.feed_cost_per_liter))}</strong>{' | '}OPEX/L: <strong>{money(Number(officialRec.opex_cost_per_liter))}</strong>{' | '}COML/L: <strong>{money(Number(officialRec.total_coml_per_liter))}</strong></div>
                </section>
              )}
            </>
          )}
        </>
      )}

      {mode === 'manual' && (
        <>
          {error && <div style={{ ...panel, borderColor: '#ef4444', color: '#fecaca', fontSize: 10, marginBottom: 9 }}>{error}</div>}
          {message && <div style={{ ...panel, borderColor: '#34d399', color: '#bbf7d0', fontSize: 10, marginBottom: 9 }}>{message}</div>}
          <form onSubmit={calculate}>
            <section style={{ ...panel, marginBottom: 9 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}><div style={{ fontSize: 11, fontWeight: 900, color: '#cbd5e1' }}>Manual inputs (auto-saved draft)</div><button type="button" onClick={clearDraft} style={button('#7f1d1d')}>Clear draft</button></div>
              <label style={label}>Milk produced in period (litres)<input required type="number" min="0.01" step="0.01" value={milkProduced} onChange={e => setMilkProduced(e.target.value)} placeholder="Total litres for selected period" style={inputStyle} /></label>
              <div style={{ fontSize: 9, color: '#64748b', marginTop: 6 }}>Period dates above apply to this calculation. Draft survives tab switches until Lock or Clear.</div>
            </section>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 9 }}>
              <LineTable title="Feed Cost Inputs" rows={feedRows} setRows={setFeedRows} options={FEED} accent="#34d399" />
              <LineTable title="Operating Cost Inputs" rows={opexRows} setRows={setOpexRows} options={OPEX} accent="#f59e0b" />
            </div>
            <button disabled={loading} type="submit" style={{ ...button('#7c3aed'), width: '100%', justifyContent: 'center', marginTop: 9 }}>{loading ? 'Calculating…' : 'Calculate COML from Manual Inputs'}</button>
          </form>
          {result && (
            <section style={{ ...panel, marginTop: 9 }}>
              <div style={{ fontSize: 11, fontWeight: 900, marginBottom: 8 }}>Manual result — {result.period_start} to {result.period_end} ({days} days) · {Number(result.milk_produced_liters).toLocaleString()} L</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 7 }}>
                <Metric title="Feed Cost" value={money(Number(result.feed_total))} />
                <Metric title="OPEX" value={money(Number(result.operating_total))} />
                <Metric title="Feed Cost / L" value={money(Number(result.feed_cost_per_liter))} />
                <Metric title="COML / L" value={money(Number(result.total_coml_per_liter))} />
              </div>
              <div style={{ marginTop: 8, display: 'flex', justifyContent: 'flex-end' }}><button disabled={saving} onClick={() => void lock()} style={button('#059669')}><Lock size={12} />{saving ? 'Locking…' : 'Lock Official Monthly COML'}</button></div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
