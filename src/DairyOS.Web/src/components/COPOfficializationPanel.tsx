import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, RefreshCw } from 'lucide-react';
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

const localIsoDate = (value = new Date()) => {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const currentMonth = () => localIsoDate().slice(0, 7);

const boundsForMonth = (month: string) => {
  const [year, monthNumber] = month.split('-').map(Number);
  const lastDay = new Date(year, monthNumber, 0).getDate();
  const start = `${month}-01`;
  const calendarEnd = `${month}-${String(lastDay).padStart(2, '0')}`;
  const today = localIsoDate();
  const end = month === today.slice(0, 7) ? today : calendarEnd;

  return {
    start,
    end,
    calendarEnd,
    isCurrentMonth: month === today.slice(0, 7),
  };
};

type AutoData = {
  production?: {
    totalLiters?: number;
    total_liters?: number;
  };
  costs?: {
    feed_total?: number;
    opex_total?: number;
    feed_cost_per_liter?: number | null;
    opex_cost_per_liter?: number | null;
    total_coml_per_liter?: number | null;
  };
  feed_cost_per_liter?: number | null;
  opex_cost_per_liter?: number | null;
  total_coml_per_liter?: number | null;
};

type OfficialPayload = {
  record?: {
    month_start?: string;
    total_coml_per_liter?: number;
  } | null;
};

export default function COPOfficializationPanel() {
  const [month, setMonth] = useState(currentMonth());
  const [autoData, setAutoData] = useState<AutoData | null>(null);
  const [official, setOfficial] = useState<OfficialPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const range = useMemo(() => boundsForMonth(month), [month]);

  const load = async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError('');

    try {
      const integratedQuery = new URLSearchParams({
        period_start: range.start,
        period_end: range.end,
      });
      const officialQuery = new URLSearchParams({
        month_start: range.start,
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
        exc instanceof Error
          ? exc.message
          : 'Unable to load auto COP.',
      );
    } finally {
      if (!quiet) setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(true), 60_000);
    return () => window.clearInterval(timer);
  }, [month, range.start, range.end]);

  const feedPerL =
    autoData?.feed_cost_per_liter
    ?? autoData?.costs?.feed_cost_per_liter
    ?? null;

  const opexPerL =
    autoData?.opex_cost_per_liter
    ?? autoData?.costs?.opex_cost_per_liter
    ?? null;

  const totalPerL =
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

  const canLock =
    milkLitres > 0
    && feedPerL != null
    && opexPerL != null
    && totalPerL != null;

  const officialRecord = official?.record ?? null;

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
          notes:
            `AUTO-CALCULATED COP made official for ${range.start} to ${range.end}; `
            + `TMR Feed/L ${Number(feedPerL).toFixed(4)}; `
            + `Finance OPEX/L ${Number(opexPerL).toFixed(4)}; `
            + `milk ${milkLitres} L; `
            + `COP/L ${Number(totalPerL).toFixed(4)}.`,
          updated_by: 'UI Operator',
        }),
      });

      const body = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(body?.detail || 'Unable to make auto COP official.');
      }

      setOfficial(body);
      setMessage(
        `Auto COP for ${month} is now the official COP/L. The Dashboard will use this official value.`,
      );
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Unable to make auto COP official.',
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <section style={{ ...panel, margin: '0 20px 20px' }}>
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
          <div style={{ fontSize: 12, fontWeight: 900 }}>
            Auto COP / L Calculator
          </div>
          <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>
            Live Auto COP uses governed TMR whole-herd Feed Cost / L, authoritative milk production, and Finance OPEX / L.
          </div>
        </div>

        <div style={{ display: 'flex', gap: 7, alignItems: 'center' }}>
          <input
            aria-label="Auto COP month"
            type="month"
            value={month}
            onChange={event => setMonth(event.target.value)}
            style={input}
          />
          <button type="button" onClick={() => void load()} style={button('#334155')}>
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>
      </div>

      <div style={{ marginTop: 8, color: '#64748b', fontSize: 9 }}>
        Calculation period: {range.start} → {range.end}
        {range.isCurrentMonth
          ? ' · live month-to-date'
          : ' · completed calendar period'}
        {' · '}auto-refresh every 60 seconds
      </div>

      {error && (
        <div style={{ marginTop: 10, color: '#fecaca', fontSize: 10 }}>
          {error}
        </div>
      )}

      {message && (
        <div style={{ marginTop: 10, color: '#bbf7d0', fontSize: 10 }}>
          {message}
        </div>
      )}

      {loading ? (
        <div style={{ marginTop: 12, color: '#64748b', fontSize: 10 }}>
          Loading Auto COP…
        </div>
      ) : (
        <>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4,minmax(0,1fr))',
              gap: 8,
              marginTop: 12,
            }}
          >
            <Metric
              title="Milk"
              value={`${milkLitres.toLocaleString('en-PK', { maximumFractionDigits: 2 })} L`}
              detail="Authoritative production"
            />
            <Metric
              title="TMR Feed / L"
              value={money(feedPerL)}
              detail={`${money(feedTotal)} whole-herd TMR cost`}
            />
            <Metric
              title="Finance OPEX / L"
              value={money(opexPerL)}
              detail={`${money(opexTotal)} active OPEX`}
            />
            <Metric
              title="Auto COP / L"
              value={money(totalPerL)}
              detail="TMR Feed/L + Finance OPEX/L"
            />
          </div>

          <div
            style={{
              marginTop: 10,
              padding: 9,
              background: '#0f172a',
              border: '1px solid #1f2937',
              borderRadius: 6,
              fontSize: 9,
              color: '#94a3b8',
            }}
          >
            <strong style={{ color: '#38bdf8' }}>Feed authority:</strong>{' '}
            Governed TMR ration × active DairyOS herd. Bulk Finance Feed purchases supply ingredient quantity and price authority but are not treated as same-day consumption in COP.
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 10,
              flexWrap: 'wrap',
              marginTop: 12,
            }}
          >
            <div style={{ fontSize: 10, color: '#94a3b8' }}>
              {officialRecord
                ? `Current official for ${month}: ${money(officialRecord.total_coml_per_liter)}.`
                : `No official COP record currently exists for ${month}.`}
              {' '}Making Auto official replaces the month’s current official COP/L.
            </div>

            <button
              type="button"
              disabled={!canLock || saving}
              onClick={() => void makeOfficial()}
              style={{
                ...button('#059669'),
                opacity: !canLock || saving ? 0.5 : 1,
              }}
            >
              <CheckCircle2 size={13} />
              {saving ? 'Making Official…' : 'Make Auto COP / L Official'}
            </button>
          </div>
        </>
      )}
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
    <div
      style={{
        background: '#0f172a',
        border: '1px solid #1f2937',
        borderRadius: 6,
        padding: 9,
      }}
    >
      <div
        style={{
          fontSize: 8,
          color: '#64748b',
          textTransform: 'uppercase',
          fontWeight: 800,
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: 14,
          fontWeight: 900,
          color: '#a78bfa',
          marginTop: 3,
        }}
      >
        {value}
      </div>
      <div style={{ marginTop: 3, color: '#64748b', fontSize: 8 }}>
        {detail}
      </div>
    </div>
  );
}