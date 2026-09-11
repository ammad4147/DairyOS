import React, { useCallback, useEffect, useState } from 'react';
import { Activity, BarChart3, HeartPulse, Milk, RefreshCw, Wheat } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

type AnalyticsPayload = {
  data_status?: string;
  period?: { start?: string; end?: string; days?: number };
  kpis?: {
    milk_litres?: number | null;
    feed_cost_per_litre?: number | null;
    opex_cost_per_litre?: number | null;
    cost_of_milk_production_per_litre?: number | null;
    active_herd?: number;
    open_health_cases?: number;
    conception_rate_percent?: number | null;
  };
  financial?: {
    feed_cost_complete?: boolean;
    feed_cost_missing_authority_days?: string[];
  };
  health_summary?: {
    new_cases?: number;
    resolved_cases?: number;
    open_cases?: number;
    treatments?: number;
    withdrawal_animals?: number;
    withdrawal_days?: number;
    open_cases_by_severity?: Record<string, number>;
    open_cases_by_diagnosis?: Array<{ diagnosis: string; count: number }>;
  };
  breeding_cycle_analytics?: {
    cycle_count?: number;
    documented_conceptions?: number;
    calvings?: number;
    pregnancy_losses?: number;
    herd_conception_rate_percent?: number | null;
    by_animal?: Array<{ key: string; cycles: number; conception_rate_percent?: number | null }>;
    by_inseminator?: Array<{ key: string; cycles: number; conception_rate_percent?: number | null }>;
    by_semen_lot?: Array<{ key: string; cycles: number; conception_rate_percent?: number | null }>;
    by_sire?: Array<{ key: string; cycles: number; conception_rate_percent?: number | null }>;
  };
  herd_dynamics?: { active_herd?: number; lifecycle_counts?: Record<string, number> };
  milk_environment?: Array<{ period: string; thi: number; yield: number }>;
  health?: Array<{ period: string; observations: number; treatments: number }>;
  breeding?: Array<{ period: string; inseminations: number; conception_rate_percent?: number | null }>;
};

type Props = { refreshVersion?: number };
const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

const numberOrDash = (value: number | null | undefined, suffix = '') =>
  value === null || value === undefined || !Number.isFinite(Number(value))
    ? '—'
    : `${Number(value).toLocaleString('en-PK', { maximumFractionDigits: 2 })}${suffix}`;

export default function AnalyticsTab({ refreshVersion = 0 }: Props) {
  const [days, setDays] = useState(30);
  const [payload, setPayload] = useState<AnalyticsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/farm/analytics/integrated?days=${days}`, {
        headers: { Accept: 'application/json' },
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.detail || `Analytics request failed: ${response.status}`);
      setPayload(body as AnalyticsPayload);
    } catch (exc) {
      setPayload(null);
      setError(exc instanceof Error ? exc.message : 'Analytics is unavailable.');
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { void load(); }, [load, refreshVersion]);

  const health = payload?.health_summary;
  const breeding = payload?.breeding_cycle_analytics;
  const lifecycle = payload?.herd_dynamics?.lifecycle_counts || {};

  return (
    <div style={{ minHeight: '100%', boxSizing: 'border-box', padding: 14, background: '#0b1120', color: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, color: '#c4b5fd', fontWeight: 900, fontSize: 16 }}><BarChart3 size={18} /> Analytics</div>
          <div style={{ color: '#94a3b8', fontSize: 10, marginTop: 3 }}>Server-produced projections from governed Animals, Milk, TMR, Finance, Health and Breeding authorities.</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <select aria-label="Analytics period" value={days} onChange={event => setDays(Number(event.target.value))} style={selectStyle}>
            {[7, 30, 90, 180, 365].map(value => <option key={value} value={value}>{value} days</option>)}
          </select>
          <button type="button" onClick={() => void load()} style={buttonStyle}><RefreshCw size={12} /> Refresh</button>
        </div>
      </div>

      {error && <div style={errorStyle}>{error}</div>}
      {loading && !payload ? <div style={{ color: '#94a3b8', fontSize: 11 }}>Loading governed analytics...</div> : payload && (
        <>
          <div style={gridStyle}>
            <Metric title="Milk litres" value={numberOrDash(payload.kpis?.milk_litres, ' L')} icon={<Milk size={14} />} color="#38bdf8" />
            <Metric title="Feed Cost / L" value={numberOrDash(payload.kpis?.feed_cost_per_litre, ' PKR')} icon={<Wheat size={14} />} color="#34d399" />
            <Metric title="OPEX / L" value={numberOrDash(payload.kpis?.opex_cost_per_litre, ' PKR')} icon={<Activity size={14} />} color="#f59e0b" />
            <Metric title="COP / L" value={numberOrDash(payload.kpis?.cost_of_milk_production_per_litre, ' PKR')} icon={<BarChart3 size={14} />} color="#c4b5fd" />
            <Metric title="Open health cases" value={numberOrDash(payload.kpis?.open_health_cases)} icon={<HeartPulse size={14} />} color="#f87171" />
            <Metric title="Conception rate" value={numberOrDash(payload.kpis?.conception_rate_percent, '%')} icon={<Activity size={14} />} color="#fb923c" />
          </div>

          <div style={twoColumnStyle}>
            <Panel title="Herd dynamics">
              <div style={rowStyle}><span>Active herd</span><strong>{numberOrDash(payload.kpis?.active_herd)}</strong></div>
              {Object.entries(lifecycle).map(([key, value]) => <div key={key} style={rowStyle}><span>{key}</span><strong>{value}</strong></div>)}
            </Panel>
            <Panel title="Health outcomes">
              <div style={rowStyle}><span>New / resolved cases</span><strong>{health?.new_cases ?? 0} / {health?.resolved_cases ?? 0}</strong></div>
              <div style={rowStyle}><span>Open cases / treatments</span><strong>{health?.open_cases ?? 0} / {health?.treatments ?? 0}</strong></div>
              <div style={rowStyle}><span>Withdrawal burden</span><strong>{health?.withdrawal_animals ?? 0} animals · {health?.withdrawal_days ?? 0} days</strong></div>
              <div style={{ marginTop: 7, color: '#94a3b8', fontSize: 10 }}>Severity: {Object.entries(health?.open_cases_by_severity || {}).map(([key, value]) => `${key} ${value}`).join(' · ') || 'none'}</div>
            </Panel>
          </div>

          <Panel title="Breeding cycle analytics">
            <div style={gridStyle}>
              <Metric title="Governed AI cycles" value={numberOrDash(breeding?.cycle_count)} color="#fb923c" />
              <Metric title="Documented conceptions" value={numberOrDash(breeding?.documented_conceptions)} color="#a78bfa" />
              <Metric title="Calvings" value={numberOrDash(breeding?.calvings)} color="#34d399" />
              <Metric title="Pregnancy losses" value={numberOrDash(breeding?.pregnancy_losses)} color="#f87171" />
            </div>
            <DimensionTable title="By animal" rows={breeding?.by_animal} />
            <DimensionTable title="By technician" rows={breeding?.by_inseminator} />
            <DimensionTable title="By semen lot" rows={breeding?.by_semen_lot} />
            <DimensionTable title="By sire" rows={breeding?.by_sire} />
          </Panel>

          <div style={{ marginTop: 9, color: '#64748b', fontSize: 9 }}>
            Period: {payload.period?.start || '—'} → {payload.period?.end || '—'} · {payload.data_status || 'UNKNOWN'} · COP is Feed Cost/L + OPEX/L.
          </div>
        </>
      )}
    </div>
  );
}

function Metric({ title, value, icon, color = '#fff' }: { title: string; value: string; icon?: React.ReactNode; color?: string }) {
  return <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 7, padding: 10 }}><div style={{ color, display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, fontWeight: 800 }}>{icon}{title}</div><div style={{ marginTop: 5, fontSize: 17, fontWeight: 900 }}>{value}</div></div>;
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 11, marginTop: 10 }}><div style={{ color: '#cbd5e1', fontSize: 12, fontWeight: 900, marginBottom: 8 }}>{title}</div>{children}</section>;
}

function DimensionTable({ title, rows }: { title: string; rows?: Array<{ key: string; cycles: number; conception_rate_percent?: number | null }> }) {
  if (!rows?.length) return null;
  return <div style={{ marginTop: 10, overflow: 'auto' }}><div style={{ color: '#94a3b8', fontSize: 10, fontWeight: 800, marginBottom: 4 }}>{title}</div><table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}><thead><tr style={{ color: '#64748b', textAlign: 'left' }}><th style={cellStyle}>Key</th><th style={cellStyle}>Cycles</th><th style={cellStyle}>Conception</th></tr></thead><tbody>{rows.slice(0, 20).map(row => <tr key={`${title}-${row.key}`} style={{ borderTop: '1px solid #1f2937' }}><td style={cellStyle}>{row.key}</td><td style={cellStyle}>{row.cycles}</td><td style={cellStyle}>{row.conception_rate_percent == null ? '—' : `${row.conception_rate_percent.toFixed(1)}%`}</td></tr>)}</tbody></table></div>;
}

const gridStyle: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(145px,1fr))', gap: 8 };
const twoColumnStyle: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))', gap: 9 };
const rowStyle: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', gap: 8, padding: '5px 0', borderBottom: '1px solid #1f2937', color: '#cbd5e1', fontSize: 10 };
const selectStyle: React.CSSProperties = { background: '#1e293b', color: '#e2e8f0', border: '1px solid #475569', borderRadius: 5, padding: '6px 8px', fontSize: 10 };
const buttonStyle: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: 5, background: '#1e293b', color: '#cbd5e1', border: '1px solid #475569', borderRadius: 5, padding: '6px 9px', fontSize: 10, cursor: 'pointer' };
const errorStyle: React.CSSProperties = { background: '#450a0a', border: '1px solid #7f1d1d', color: '#fecaca', borderRadius: 6, padding: 8, fontSize: 10, marginBottom: 9 };
const cellStyle: React.CSSProperties = { padding: '5px 4px', textAlign: 'left' };
