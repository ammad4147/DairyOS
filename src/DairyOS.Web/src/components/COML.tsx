import React, { useEffect, useState } from 'react';
import { Calculator, Lock, TrendingUp, AlertTriangle, Milk, Wheat, DollarSign, Plus, Trash2, SlidersHorizontal } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

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
const newLine = (item = ''): Line => ({ id: `${Date.now()}-${Math.random()}`, item, quantity: '', unit: 'kg', unitRate: '' });
const money = (v: number) => `PKR ${v.toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

function LineTable({ title, rows, setRows, options, accent }: { title: string; rows: Line[]; setRows: React.Dispatch<React.SetStateAction<Line[]>>; options: string[]; accent: string }) {
  return (
    <section style={panel}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 style={{ margin: 0, fontSize: 13, color: accent }}>{title}</h3>
        <button type="button" onClick={() => setRows(x => [...x, newLine()])} style={button('#1e293b')}><Plus size={12} /> Add Item</button>
      </div>
      {rows.length === 0 ? (
        <div style={{ fontSize: 10, color: '#64748b', padding: '14px 0' }}>No line items. Add an item to calculate this cost category.</div>
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

  // Auto / integrated
  const [metrics, setMetrics] = useState<any>(null);
  const [production, setProduction] = useState<any>(null);
  const [contracts, setContracts] = useState<any[]>([]);
  const [autoLoading, setAutoLoading] = useState(true);

  // Manual override
  const [periodStart, setPeriodStart] = useState(monthStart());
  const [periodEnd, setPeriodEnd] = useState(today());
  const [milkProduced, setMilkProduced] = useState('');
  const [feedRows, setFeedRows] = useState<Line[]>([]);
  const [opexRows, setOpexRows] = useState<Line[]>([]);
  const [result, setResult] = useState<any>(null);
  const [official, setOfficial] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    setAutoLoading(true);
    Promise.all([
      fetch(`${API_BASE}/farm/coml/integrated`).then(r => (r.ok ? r.json() : null)).catch(() => null),
      fetch(`${API_BASE}/farm/coml/contracts`).then(r => (r.ok ? r.json() : { contracts: [] })).catch(() => ({ contracts: [] })),
      fetch(`${API_BASE}/farm/coml/current`).then(r => (r.ok ? r.json() : null)).catch(() => null),
    ]).then(([metricsData, contractsData, officialData]) => {
      setMetrics(metricsData);
      setContracts(contractsData?.contracts || []);
      setProduction(metricsData?.production || { totalLiters: 0, batches: [] });
      setOfficial(officialData);
    }).finally(() => setAutoLoading(false));
  }, []);

  const calculate = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setError('');
    setMessage('');
    setResult(null);
    setLoading(true);
    try {
      if (new Date(periodEnd) < new Date(periodStart)) throw new Error('Calculation end date must be on or after start date.');
      if (!(Number(milkProduced) > 0)) throw new Error('Milk produced must be greater than zero.');
      const clean = (rows: Line[]) =>
        rows
          .filter(r => r.item && Number(r.quantity) > 0 && Number(r.unitRate) >= 0)
          .map(r => ({ item: r.item, quantity: Number(r.quantity), unit: r.unit, unit_rate: Number(r.unitRate) }));
      const response = await fetch(`${API_BASE}/farm/coml/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          period_start: periodStart,
          period_end: periodEnd,
          milk_produced_liters: Number(milkProduced),
          feed_items: clean(feedRows),
          operating_items: clean(opexRows),
        }),
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
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'COML calculation failed.');
    } finally {
      setLoading(false);
    }
  };

  const lock = async () => {
    if (!result) return;
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const response = await fetch(`${API_BASE}/farm/coml/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          month_start: periodStart.slice(0, 8) + '01',
          feed_cost_per_liter: Number(result.feed_cost_per_liter),
          opex_cost_per_liter: Number(result.opex_cost_per_liter),
          notes: `Manual calculation ${result.period_start} to ${result.period_end}; ${result.period_days} days.`,
          updated_by: 'UI Operator',
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to lock COML record.');
      setOfficial(data);
      // Reflect locked official values in Auto KPI cards immediately
      const rec = data?.record || data;
      if (rec) {
        setMetrics((prev: any) => ({
          ...(prev || {}),
          feed_cost_per_liter: Number(rec.feed_cost_per_liter ?? prev?.feed_cost_per_liter ?? 0),
          opex_cost_per_liter: Number(rec.opex_cost_per_liter ?? prev?.opex_cost_per_liter ?? 0),
          total_coml_per_liter: Number(rec.total_coml_per_liter ?? prev?.total_coml_per_liter ?? 0),
          source: 'official_lock',
        }));
      }
      setMessage('COML result persisted and locked as the official monthly record.');
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Unable to lock COML record.');
    } finally {
      setSaving(false);
    }
  };

  const days = result?.period_days || 0;

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: 18, color: '#a78bfa', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Calculator size={20} /> Cost of Milk Production (COML)
          </h2>
          <p style={{ margin: 0, fontSize: 12, color: '#94a3b8' }}>
            Auto view uses integrated backend data. Switch to Manual Override when feed/finance/milk data is incomplete.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setMode('auto')}
            style={{
              background: mode === 'auto' ? '#7c3aed' : '#1e293b',
              border: '1px solid #334155',
              color: '#fff',
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: 11,
              cursor: 'pointer',
              fontWeight: 700,
            }}
          >
            Auto Integrated
          </button>
          <button
            onClick={() => setMode('manual')}
            style={{
              background: mode === 'manual' ? '#f59e0b' : '#1e293b',
              border: '1px solid #334155',
              color: '#fff',
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: 11,
              cursor: 'pointer',
              fontWeight: 700,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <SlidersHorizontal size={12} /> Manual Override
          </button>
        </div>
      </div>

      {mode === 'auto' && (
        <>
          {autoLoading ? (
            <div style={{ color: '#64748b', fontSize: 12 }}>Loading integrated COML data...</div>
          ) : (
            <>
              
              {/** Prefer official locked COML when integrated endpoint returns zeros */}<div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
                <MetricCard title="Total Production" value={`${production?.totalLiters?.toLocaleString() || 0} L`} subtitle="Auto from Milk Tab" color="#38bdf8" icon={<Milk size={16} />} />
                <MetricCard title="Feed Cost / L" value={`PKR ${Number(metrics?.feed_cost_per_liter || official?.record?.feed_cost_per_liter || official?.feed_cost_per_liter || 0).toFixed(2)}`} subtitle={Number(metrics?.feed_cost_per_liter) ? "Auto from Feed Tab" : "Official locked record"} color="#34d399" icon={<Wheat size={16} />} />
                <MetricCard title="OPEX / L" value={`PKR ${Number(metrics?.opex_cost_per_liter || official?.record?.opex_cost_per_liter || official?.opex_cost_per_liter || 0).toFixed(2)}`} subtitle={Number(metrics?.opex_cost_per_liter) ? "Auto from Finance Tab" : "Official locked record"} color="#f59e0b" icon={<DollarSign size={16} />} />
                <MetricCard title="Total COML / L" value={`PKR ${Number(metrics?.total_coml_per_liter || official?.record?.total_coml_per_liter || official?.total_coml_per_liter || 0).toFixed(2)}`} subtitle={Number(metrics?.total_coml_per_liter) ? "Fully loaded cost" : "Official locked record"} color="#a78bfa" icon={<Calculator size={16} />} />
              </div>

              <div style={{ ...panel, marginBottom: 12, borderColor: '#334155' }}>
                <div style={{ fontSize: 12, color: '#fbbf24', fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AlertTriangle size={14} /> Backend data may be incomplete
                </div>
                <div style={{ fontSize: 12, color: '#cbd5e1' }}>
                  If auto figures look wrong or zero, use <strong>Manual Override</strong> to enter feed/OPEX lines and lock an official monthly COML.
                </div>
              </div>

              {official && (
                <section style={{ ...panel, borderColor: '#22c55e', marginBottom: 12 }}>
                  <div style={{ fontSize: 11, fontWeight: 900, color: '#86efac' }}>Official Backend COML</div>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>
                    {official.month_label || official.record?.month_label || 'Current month'} | Status: {official.record?.status || official.status || 'UNKNOWN'}
                  </div>
                  {official.record && (
                    <div style={{ marginTop: 7, fontSize: 11 }}>
                      Feed/L: <strong>{money(Number(official.record.feed_cost_per_liter))}</strong> | OPEX/L: <strong>{money(Number(official.record.opex_cost_per_liter))}</strong> | COML/L: <strong>{money(Number(official.record.total_coml_per_liter))}</strong>
                    </div>
                  )}
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
              <div style={{ fontSize: 11, fontWeight: 900, color: '#cbd5e1', marginBottom: 8 }}>Calculation Period & Production</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 7 }}>
                <label style={label}>Period Start<input required type="date" value={periodStart} onChange={e => setPeriodStart(e.target.value)} style={inputStyle} /></label>
                <label style={label}>Period End<input required type="date" value={periodEnd} onChange={e => setPeriodEnd(e.target.value)} style={inputStyle} /></label>
                <label style={label}>Milk Produced (litres)<input required type="number" min="0.01" step="0.01" value={milkProduced} onChange={e => setMilkProduced(e.target.value)} placeholder="Total litres for period" style={inputStyle} /></label>
              </div>
              <div style={{ fontSize: 9, color: '#64748b', marginTop: 6 }}>
                Enter quantities and per-unit rates below. This override does not depend on feed/finance auto aggregation.
              </div>
            </section>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 9 }}>
              <LineTable title="Feed Cost Inputs" rows={feedRows} setRows={setFeedRows} options={FEED} accent="#34d399" />
              <LineTable title="Operating Cost Inputs" rows={opexRows} setRows={setOpexRows} options={OPEX} accent="#f59e0b" />
            </div>

            <button disabled={loading} type="submit" style={{ ...button('#7c3aed'), width: '100%', justifyContent: 'center', marginTop: 9 }}>
              {loading ? 'Calculating…' : 'Calculate COML from Defined Inputs'}
            </button>
          </form>

          {result && (
            <section style={{ ...panel, marginTop: 9 }}>
              <div style={{ fontSize: 11, fontWeight: 900, marginBottom: 8 }}>
                Calculated Result — {result.period_start} to {result.period_end} ({days} days)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 7 }}>
                <Metric title="Feed Cost" value={money(Number(result.feed_total))} />
                <Metric title="OPEX" value={money(Number(result.operating_total))} />
                <Metric title="Feed Cost / L" value={money(Number(result.feed_cost_per_liter))} />
                <Metric title="COML / L" value={money(Number(result.total_coml_per_liter))} />
              </div>
              <div style={{ marginTop: 8, display: 'flex', justifyContent: 'flex-end' }}>
                <button disabled={saving} onClick={() => void lock()} style={button('#059669')}>
                  <Lock size={12} />{saving ? 'Locking…' : 'Lock Official Monthly COML'}
                </button>
              </div>
            </section>
          )}

          {official && (
            <section style={{ ...panel, marginTop: 9, borderColor: '#22c55e' }}>
              <div style={{ fontSize: 11, fontWeight: 900, color: '#86efac' }}>Official Backend COML</div>
              <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>
                {official.month_label || official.record?.month_label || 'Current month'} | Status: {official.record?.status || official.status || 'UNKNOWN'}
              </div>
              {official.record && (
                <div style={{ marginTop: 7, fontSize: 11 }}>
                  Feed/L: <strong>{money(Number(official.record.feed_cost_per_liter))}</strong> | OPEX/L: <strong>{money(Number(official.record.opex_cost_per_liter))}</strong> | COML/L: <strong>{money(Number(official.record.total_coml_per_liter))}</strong>
                </div>
              )}
              {!official.record && (
                <div style={{ marginTop: 7, fontSize: 10, color: '#fbbf24' }}>
                  No official COML is recorded for this month.
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}

