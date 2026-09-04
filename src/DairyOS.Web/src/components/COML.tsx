import React, { useEffect, useMemo, useState } from 'react';
import {
  Calculator,
  CheckCircle2,
  RefreshCw,
  SlidersHorizontal,
} from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';
const DRAFT_KEY = 'dairyos_cop_manual_per_litre_draft';

type Mode = 'AUTO' | 'MANUAL';
type Preset = 'THIS_MONTH' | 'LAST_30_DAYS' | 'YEAR_TO_DATE' | 'CUSTOM';

type AutoData = {
  period?: { start?: string; end?: string };
  period_label?: string;
  production?: {
    totalLiters?: number;
    total_liters?: number;
    source?: string;
  };
  costs?: {
    feed_total?: number;
    opex_total?: number;
    feed_cost_per_liter?: number | null;
    opex_cost_per_liter?: number | null;
    total_coml_per_liter?: number | null;
    source?: string;
    opex_source?: string;
  };
  feed_cost_per_liter?: number | null;
  opex_cost_per_liter?: number | null;
  total_coml_per_liter?: number | null;
  message?: string;
};

type OfficialRecord = {
  month_start?: string;
  feed_cost_per_liter?: number;
  opex_cost_per_liter?: number;
  total_coml_per_liter?: number;
  updated_by?: string | null;
  locked_at?: string | null;
};

type OfficialPayload = {
  record?: OfficialRecord | null;
  has_official?: boolean;
};

const panel: React.CSSProperties = {
  background: '#111827',
  border: '1px solid #1f2937',
  borderRadius: 8,
  padding: 14,
  minWidth: 0,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  background: '#1e293b',
  border: '1px solid #334155',
  color: '#fff',
  borderRadius: 6,
  padding: '8px 9px',
  fontSize: 11,
};

const label: React.CSSProperties = {
  fontSize: 9,
  color: '#94a3b8',
  display: 'block',
  fontWeight: 800,
  textTransform: 'uppercase',
};

const button = (background: string): React.CSSProperties => ({
  background,
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
});

const money = (value: unknown) => {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? `PKR ${amount.toLocaleString('en-PK', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`
    : 'N/A';
};

const pakistanDateFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Karachi',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

const todayIso = () => pakistanDateFormatter.format(new Date());

const dateShift = (iso: string, days: number) => {
  const [year, month, day] = iso.split('-').map(Number);
  const value = new Date(Date.UTC(year, month - 1, day + days, 12));
  return value.toISOString().slice(0, 10);
};

const calendarEnd = (iso: string) => {
  const [year, month] = iso.slice(0, 7).split('-').map(Number);
  return new Date(Date.UTC(year, month, 0)).toISOString().slice(0, 10);
};

const boundsForPreset = (preset: Preset) => {
  const today = todayIso();
  if (preset === 'LAST_30_DAYS') {
    return { start: dateShift(today, -29), end: today };
  }
  if (preset === 'YEAR_TO_DATE') {
    return { start: `${today.slice(0, 4)}-01-01`, end: today };
  }
  return { start: `${today.slice(0, 7)}-01`, end: today };
};

const asNullableNumber = (value: string) => {
  if (value.trim() === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
};

export default function COML() {
  const initial = boundsForPreset('THIS_MONTH');
  const [mode, setMode] = useState<Mode>('AUTO');
  const [preset, setPreset] = useState<Preset>('THIS_MONTH');
  const [periodStart, setPeriodStart] = useState(initial.start);
  const [periodEnd, setPeriodEnd] = useState(initial.end);
  const [manualFeed, setManualFeed] = useState('');
  const [manualOpex, setManualOpex] = useState('');
  const [autoData, setAutoData] = useState<AutoData | null>(null);
  const [official, setOfficial] = useState<OfficialPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      const draft = JSON.parse(raw);
      if (draft.feedCostPerLiter != null) {
        setManualFeed(String(draft.feedCostPerLiter));
      }
      if (draft.opexCostPerLiter != null) {
        setManualOpex(String(draft.opexCostPerLiter));
      }
    } catch {
      // Ignore a corrupt local manual draft.
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        feedCostPerLiter: manualFeed,
        opexCostPerLiter: manualOpex,
        savedAt: new Date().toISOString(),
      }),
    );
  }, [manualFeed, manualOpex]);

  const officialAnchorDate = periodEnd > todayIso() ? todayIso() : periodEnd;
  const officialMonthStart = `${officialAnchorDate.slice(0, 7)}-01`;

  const load = async (quiet = false) => {
    if (!periodStart || !periodEnd || periodEnd < periodStart) {
      setError('Analysis period end must be on or after start.');
      return;
    }
    if (!quiet) setLoading(true);
    setError('');
    try {
      const integratedQuery = new URLSearchParams({
        period_start: periodStart,
        period_end: periodEnd,
      });
      const officialQuery = new URLSearchParams({
        month_start: officialMonthStart,
      });
      const [autoResponse, officialResponse] = await Promise.all([
        fetch(`${API_BASE}/farm/coml/integrated?${integratedQuery}`),
        fetch(`${API_BASE}/farm/coml?${officialQuery}`),
      ]);
      const autoBody = await autoResponse.json().catch(() => null);
      const officialBody = await officialResponse.json().catch(() => null);
      if (!autoResponse.ok) {
        throw new Error(autoBody?.detail || 'Auto COP calculation is unavailable.');
      }
      setAutoData(autoBody);
      setOfficial(officialResponse.ok ? officialBody : null);
    } catch (exc) {
      setAutoData(null);
      setError(
        exc instanceof Error ? exc.message : 'Unable to load Auto COP.',
      );
    } finally {
      if (!quiet) setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(true), 60_000);
    return () => window.clearInterval(timer);
  }, [periodStart, periodEnd, officialMonthStart]);

  const applyPreset = (next: Preset) => {
    setPreset(next);
    setMessage('');
    setError('');
    if (next === 'CUSTOM') return;
    const bounds = boundsForPreset(next);
    setPeriodStart(bounds.start);
    setPeriodEnd(bounds.end);
  };

  const autoFeed =
    autoData?.feed_cost_per_liter
    ?? autoData?.costs?.feed_cost_per_liter
    ?? null;
  const autoOpex =
    autoData?.opex_cost_per_liter
    ?? autoData?.costs?.opex_cost_per_liter
    ?? null;
  const autoTotal =
    autoData?.total_coml_per_liter
    ?? autoData?.costs?.total_coml_per_liter
    ?? null;
  const milkLitres = Number(
    autoData?.production?.totalLiters
    ?? autoData?.production?.total_liters
    ?? 0,
  );
  const feedTotal = Number(autoData?.costs?.feed_total ?? 0);
  const opexTotal = Number(autoData?.costs?.opex_total ?? 0);

  const manualFeedValue = asNullableNumber(manualFeed);
  const manualOpexValue = asNullableNumber(manualOpex);
  const manualTotal = useMemo(
    () =>
      manualFeedValue != null && manualOpexValue != null
        ? manualFeedValue + manualOpexValue
        : null,
    [manualFeedValue, manualOpexValue],
  );

  const displayedFeed = mode === 'AUTO' ? autoFeed : manualFeedValue;
  const displayedOpex = mode === 'AUTO' ? autoOpex : manualOpexValue;
  const displayedTotal = mode === 'AUTO' ? autoTotal : manualTotal;

  const canMakeAutoOfficial =
    milkLitres > 0
    && autoFeed != null
    && autoOpex != null
    && autoTotal != null;
  const canMakeManualOfficial =
    manualFeedValue != null
    && manualOpexValue != null
    && manualTotal != null
    && manualTotal > 0;

  const makeOfficial = async (source: Mode) => {
    const isAuto = source === 'AUTO';
    if (isAuto && !canMakeAutoOfficial) return;
    if (!isAuto && !canMakeManualOfficial) return;

    const feed = Number(isAuto ? autoFeed : manualFeedValue);
    const opex = Number(isAuto ? autoOpex : manualOpexValue);
    const total = feed + opex;

    setSaving(true);
    setError('');
    setMessage('');
    try {
      const response = await fetch(`${API_BASE}/farm/coml/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          month_start: officialMonthStart,
          feed_cost_per_liter: feed,
          opex_cost_per_liter: opex,
          notes: isAuto
            ? `AUTO-CALCULATED COP made official from selected period ${periodStart} to ${periodEnd}; TMR Feed/L ${feed.toFixed(4)}; Finance OPEX/L ${opex.toFixed(4)}; milk ${milkLitres} L; COP/L ${total.toFixed(4)}.`
            : `MANUAL COP made official for ${officialMonthStart}; Feed Cost/L ${feed.toFixed(4)}; OPEX/L ${opex.toFixed(4)}; COP/L ${total.toFixed(4)}.`,
          updated_by: 'UI Operator',
        }),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(
          body?.detail
          || `Unable to make ${isAuto ? 'Auto' : 'Manual'} COP official.`,
        );
      }
      setOfficial(body);
      setMessage(
        `${isAuto ? 'Auto' : 'Manual'} COP is now the official COP/L for ${officialMonthStart.slice(0, 7)}. The Dashboard will use this persisted official value.`,
      );
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : `Unable to make ${isAuto ? 'Auto' : 'Manual'} COP official.`,
      );
    } finally {
      setSaving(false);
    }
  };

  const officialRecord = official?.record ?? null;
  const isCurrentMonthToDate =
    periodStart === `${todayIso().slice(0, 7)}-01`
    && periodEnd === todayIso();

  return (
    <section
      style={{
        ...panel,
        margin: '20px',
        color: '#fff',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 10,
          flexWrap: 'wrap',
        }}
      >
        <div>
          <div
            style={{
              fontSize: 14,
              fontWeight: 900,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <Calculator size={16} />
            Cost of Production (COP)
          </div>
          <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>
            Choose a period for Auto (milk logs + ledger). Manual override is saved while you work and takes priority when selected.
          </div>
        </div>
        <button type="button" onClick={() => void load()} style={button('#334155')}>
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      <div style={{ display: 'flex', gap: 6, marginTop: 12, flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => setMode('AUTO')}
          style={button(mode === 'AUTO' ? '#7e22ce' : '#1e293b')}
        >
          Auto
        </button>
        <button
          type="button"
          onClick={() => setMode('MANUAL')}
          style={button(mode === 'MANUAL' ? '#d97706' : '#1e293b')}
        >
          <SlidersHorizontal size={12} /> Manual Override
        </button>
      </div>

      <div style={{ marginTop: 14, padding: 10, background: '#0f172a', border: '1px solid #1f2937', borderRadius: 7 }}>
        <div style={{ fontSize: 9, color: '#94a3b8', fontWeight: 900, textTransform: 'uppercase' }}>
          Analysis Period
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
          <button type="button" onClick={() => applyPreset('THIS_MONTH')} style={button(preset === 'THIS_MONTH' ? '#0369a1' : '#1e293b')}>
            This month
          </button>
          <button type="button" onClick={() => applyPreset('LAST_30_DAYS')} style={button(preset === 'LAST_30_DAYS' ? '#0369a1' : '#1e293b')}>
            Last 30 days
          </button>
          <button type="button" onClick={() => applyPreset('YEAR_TO_DATE')} style={button(preset === 'YEAR_TO_DATE' ? '#0369a1' : '#1e293b')}>
            Year to date
          </button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(160px,240px))', gap: 8, marginTop: 9 }}>
          <label style={label}>
            From
            <input
              type="date"
              value={periodStart}
              onChange={event => {
                setPreset('CUSTOM');
                setPeriodStart(event.target.value);
              }}
              style={{ ...inputStyle, marginTop: 4 }}
            />
          </label>
          <label style={label}>
            To
            <input
              type="date"
              value={periodEnd}
              onChange={event => {
                setPreset('CUSTOM');
                setPeriodEnd(event.target.value);
              }}
              style={{ ...inputStyle, marginTop: 4 }}
            />
          </label>
        </div>
        <div style={{ marginTop: 7, color: '#64748b', fontSize: 9 }}>
          Production and costs below are for this range only.
          {isCurrentMonthToDate ? ' · live month-to-date' : ''}
          {' · '}auto-refresh every 60 seconds
          {mode === 'MANUAL' ? ' · Manual draft was restored from your last session when available.' : ''}
        </div>
      </div>

      {error && <div style={{ marginTop: 10, color: '#fecaca', fontSize: 10 }}>{error}</div>}
      {message && <div style={{ marginTop: 10, color: '#bbf7d0', fontSize: 10 }}>{message}</div>}

      {mode === 'MANUAL' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 9, marginTop: 12 }}>
          <label style={label}>
            Feed Cost / Liter
            <input
              aria-label="Manual Feed Cost per Liter"
              type="number"
              min="0"
              step="0.0001"
              value={manualFeed}
              onChange={event => setManualFeed(event.target.value)}
              placeholder="PKR / L"
              style={{ ...inputStyle, marginTop: 4 }}
            />
          </label>
          <label style={label}>
            OPEX / Liter
            <input
              aria-label="Manual OPEX per Liter"
              type="number"
              min="0"
              step="0.0001"
              value={manualOpex}
              onChange={event => setManualOpex(event.target.value)}
              placeholder="PKR / L"
              style={{ ...inputStyle, marginTop: 4 }}
            />
          </label>
        </div>
      )}

      {loading ? (
        <div style={{ marginTop: 12, color: '#64748b', fontSize: 10 }}>Loading Auto COP…</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 8, marginTop: 12 }}>
          <Metric
            title="Milk in period (L)"
            value={`${milkLitres.toLocaleString('en-PK', { maximumFractionDigits: 2 })} L`}
            detail={`Selected period ${periodStart} → ${periodEnd}`}
          />
          <Metric
            title="Feed Cost / L"
            value={money(displayedFeed)}
            detail={mode === 'AUTO' ? `${money(feedTotal)} whole-herd TMR cost` : 'Manual override'}
          />
          <Metric
            title="OPEX / L"
            value={money(displayedOpex)}
            detail={mode === 'AUTO' ? `${money(opexTotal)} Finance OPEX` : 'Manual override'}
          />
          <Metric
            title="COP / L"
            value={money(displayedTotal)}
            detail={mode === 'AUTO' ? 'TMR Feed/L + Finance OPEX/L' : 'Feed Cost/L + OPEX/L'}
          />
        </div>
      )}

      {mode === 'AUTO' ? (
        <div style={{ marginTop: 10, padding: 9, background: '#0f172a', border: '1px solid #1f2937', borderRadius: 6, fontSize: 9, color: '#94a3b8' }}>
          <strong style={{ color: '#38bdf8' }}>Auto sources</strong>
          <div style={{ marginTop: 4 }}>
            Milk source: {autoData?.production?.source || 'milk_production_ledger'} · Cost source: {autoData?.costs?.source || 'TMR_HERD_COST+FINANCE_OPEX'}.
          </div>
          <div style={{ marginTop: 3 }}>
            <strong>Feed authority:</strong> Governed TMR ration × active DairyOS herd. Bulk Finance Feed purchases supply ingredient quantity and price authority but are not treated as same-day consumption in COP. A TMR ingredient explicitly set to Manual uses that governed manual price instead.
          </div>
          <div style={{ marginTop: 3 }}>
            <strong>OPEX authority:</strong> Finance OPEX / L for the selected period. If logs/ledger are incomplete, use Manual Override.
          </div>
        </div>
      ) : (
        <div style={{ marginTop: 10, padding: 9, background: '#0f172a', border: '1px solid #1f2937', borderRadius: 6, fontSize: 9, color: '#94a3b8' }}>
          Manual COP / L Calculator: enter Feed Cost / L and OPEX / L directly. Milk remains automatic from the Milk ledger. Feed Cost/L + OPEX/L gives Manual COP / L.
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: 12 }}>
        <div style={{ fontSize: 10, color: '#94a3b8' }}>
          {officialRecord
            ? `Current official for ${officialMonthStart.slice(0, 7)}: ${money(officialRecord.total_coml_per_liter)}.`
            : `No official COP record currently exists for ${officialMonthStart.slice(0, 7)}.`}
          {' '}Official COP is the persisted management benchmark used by the Dashboard.
        </div>
        {mode === 'AUTO' ? (
          <button
            type="button"
            disabled={!canMakeAutoOfficial || saving}
            onClick={() => void makeOfficial('AUTO')}
            style={{ ...button('#059669'), opacity: !canMakeAutoOfficial || saving ? 0.5 : 1 }}
          >
            <CheckCircle2 size={13} />
            {saving ? 'Making Official…' : 'Make Auto COP / L Official'}
          </button>
        ) : (
          <button
            type="button"
            disabled={!canMakeManualOfficial || saving}
            onClick={() => void makeOfficial('MANUAL')}
            style={{ ...button('#d97706'), opacity: !canMakeManualOfficial || saving ? 0.5 : 1 }}
          >
            <CheckCircle2 size={13} />
            {saving ? 'Making Official…' : 'Make Manual COP / L Official'}
          </button>
        )}
      </div>

      <div style={{ marginTop: 9, color: '#64748b', fontSize: 9 }}>
        Making Auto official replaces the month’s current official COP/L. Making Manual COP/L official replaces the month’s current official COP/L. Changing the analysis period recalculates Auto immediately; there is no separate secondary Auto calculator.
        {' '}Calendar month end reference: {calendarEnd(periodEnd)}.
      </div>
    </section>
  );
}

function Metric({
  title,
  value,
  detail,
}: {
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div style={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: 6, padding: 9 }}>
      <div style={{ fontSize: 8, color: '#64748b', textTransform: 'uppercase', fontWeight: 800 }}>
        {title}
      </div>
      <div style={{ fontSize: 16, fontWeight: 900, color: '#a78bfa', marginTop: 3 }}>
        {value}
      </div>
      <div style={{ marginTop: 3, color: '#64748b', fontSize: 8 }}>{detail}</div>
    </div>
  );
}
