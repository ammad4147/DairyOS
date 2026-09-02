import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Lock } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

const panel: React.CSSProperties = {
  background: '#111827',
  border: '1px solid #1f2937',
  borderRadius: 8,
  padding: 14,
  color: '#fff',
};

const input: React.CSSProperties = {
  background: '#1e293b',
  border: '1px solid #334155',
  borderRadius: 6,
  color: '#fff',
  padding: '8px 9px',
  fontSize: 11,
};

const button: React.CSSProperties = {
  background: '#059669',
  color: '#fff',
  border: 0,
  borderRadius: 6,
  padding: '8px 12px',
  fontSize: 10,
  fontWeight: 900,
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
};

const money = (value: unknown) => {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? `PKR ${amount.toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : 'N/A';
};

const currentMonth = () => new Date().toISOString().slice(0, 7);

const boundsForMonth = (month: string) => {
  const [year, monthNumber] = month.split('-').map(Number);
  const lastDay = new Date(Date.UTC(year, monthNumber, 0)).getUTCDate();
  return {
    start: `${month}-01`,
    end: `${month}-${String(lastDay).padStart(2, '0')}`,
  };
};

type AutoData = {
  production?: { totalLiters?: number; total_liters?: number };
  feed_cost_per_liter?: number | null;
  opex_cost_per_liter?: number | null;
  total_coml_per_liter?: number | null;
  costs?: {
    feed_cost_per_liter?: number | null;
    opex_cost_per_liter?: number | null;
    total_coml_per_liter?: number | null;
  };
};

export default function COPOfficializationPanel() {
  const [month, setMonth] = useState(currentMonth());
  const [autoData, setAutoData] = useState<AutoData | null>(null);
  const [official, setOfficial] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const range = useMemo(() => boundsForMonth(month), [month]);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const qs = new URLSearchParams({ period_start: range.start, period_end: range.end });
      const [autoResponse, currentResponse] = await Promise.all([
        fetch(`${API_BASE}/farm/coml/integrated?${qs}`),
        fetch(`${API_BASE}/farm/coml/current`),
      ]);
      const autoBody = await autoResponse.json().catch(() => null);
      const currentBody = await currentResponse.json().catch(() => null);
      if (!autoResponse.ok) throw new Error(autoBody?.detail || 'Auto COP calculation is unavailable.');
      setAutoData(autoBody);
      setOfficial(currentResponse.ok ? currentBody : null);
    } catch (exc) {
      setAutoData(null);
      setError(exc instanceof Error ? exc.message : 'Unable to load auto COP.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [month]);

  const feedPerL = autoData?.feed_cost_per_liter ?? autoData?.costs?.feed_cost_per_liter ?? null;
  const opexPerL = autoData?.opex_cost_per_liter ?? autoData?.costs?.opex_cost_per_liter ?? null;
  const totalPerL = autoData?.total_coml_per_liter ?? autoData?.costs?.total_coml_per_liter ?? null;
  const milkLitres = Number(autoData?.production?.totalLiters ?? autoData?.production?.total_liters ?? 0);
  const canLock = milkLitres > 0 && feedPerL != null && opexPerL != null && totalPerL != null;

  const makeOfficial = async () => {
    if (!canLock) return;
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const response = await fetch(`${API_BASE}/farm/coml/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          month_start: range.start,
          feed_cost_per_liter: Number(feedPerL),
          opex_cost_per_liter: Number(opexPerL),
          notes: `AUTO-CALCULATED COP made official for ${range.start} to ${range.end}; milk ${milkLitres} L; calculated COP/L ${Number(totalPerL).toFixed(4)}.`,
          updated_by: 'UI Operator',
        }),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail || 'Unable to make auto COP official.');
      setOfficial(body);
      setMessage(`Auto-calculated COP for ${month} is now the official monthly COP record.`);
      await load();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Unable to make auto COP official.');
    } finally {
      setSaving(false);
    }
  };

  const officialRecord = official?.record || null;
  const officialMonth = String(officialRecord?.month_start || '').slice(0, 7);

  return (
    <section style={{ ...panel, margin: '0 20px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 900, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Lock size={14} /> Official COP / L
          </div>
          <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>
            Review the backend auto-calculated monthly COP and explicitly adopt it as official. Manual Override remains available above.
          </div>
        </div>
        <input type="month" value={month} onChange={event => setMonth(event.target.value)} style={input} />
      </div>

      {error && <div style={{ marginTop: 10, color: '#fecaca', fontSize: 10 }}>{error}</div>}
      {message && <div style={{ marginTop: 10, color: '#bbf7d0', fontSize: 10 }}>{message}</div>}

      {loading ? (
        <div style={{ marginTop: 12, color: '#64748b', fontSize: 10 }}>Loading monthly auto COP…</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 8, marginTop: 12 }}>
            <Metric title="Milk" value={`${milkLitres.toLocaleString('en-PK')} L`} />
            <Metric title="Feed / L" value={money(feedPerL)} />
            <Metric title="OPEX / L" value={money(opexPerL)} />
            <Metric title="Auto COP / L" value={money(totalPerL)} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: 12 }}>
            <div style={{ fontSize: 10, color: '#94a3b8' }}>
              {officialMonth === month
                ? `Official record already exists for ${month}: ${money(officialRecord?.total_coml_per_liter)}.`
                : `No official record for ${month} is currently displayed.`}
            </div>
            <button type="button" disabled={!canLock || saving} onClick={() => void makeOfficial()} style={{ ...button, opacity: !canLock || saving ? 0.5 : 1 }}>
              <CheckCircle2 size={13} /> {saving ? 'Making Official…' : 'Make Auto COP / L Official'}
            </button>
          </div>
        </>
      )}
    </section>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div style={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: 6, padding: 9 }}>
      <div style={{ fontSize: 8, color: '#64748b', textTransform: 'uppercase', fontWeight: 800 }}>{title}</div>
      <div style={{ fontSize: 14, fontWeight: 900, color: '#a78bfa', marginTop: 3 }}>{value}</div>
    </div>
  );
}
