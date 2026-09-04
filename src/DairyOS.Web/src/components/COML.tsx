import React, { useEffect, useMemo, useState } from 'react';
import { Calculator, CheckCircle2, SlidersHorizontal } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';
const DRAFT_KEY = 'dairyos_cop_manual_per_litre_draft';

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

const localIsoDate = (value = new Date()) => {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const currentMonth = () => localIsoDate().slice(0, 7);

const money = (value: unknown) => {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? `PKR ${amount.toLocaleString('en-PK', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`
    : 'N/A';
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

export default function COML() {
  const [month, setMonth] = useState(currentMonth());
  const [feedCostPerLiter, setFeedCostPerLiter] = useState('');
  const [opexCostPerLiter, setOpexCostPerLiter] = useState('');
  const [official, setOfficial] = useState<OfficialPayload | null>(null);
  const [saving, setSaving] = useState(false);
  const [loadingOfficial, setLoadingOfficial] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      const draft = JSON.parse(raw);
      if (draft.month) setMonth(String(draft.month));
      if (draft.feedCostPerLiter != null) {
        setFeedCostPerLiter(String(draft.feedCostPerLiter));
      }
      if (draft.opexCostPerLiter != null) {
        setOpexCostPerLiter(String(draft.opexCostPerLiter));
      }
    } catch {
      // Ignore a corrupt local draft.
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        month,
        feedCostPerLiter,
        opexCostPerLiter,
        savedAt: new Date().toISOString(),
      }),
    );
  }, [month, feedCostPerLiter, opexCostPerLiter]);

  const totalPerLiter = useMemo(() => {
    const feed = Number(feedCostPerLiter);
    const opex = Number(opexCostPerLiter);
    if (!Number.isFinite(feed) || !Number.isFinite(opex)) return null;
    if (feed < 0 || opex < 0) return null;
    return feed + opex;
  }, [feedCostPerLiter, opexCostPerLiter]);

  const canMakeOfficial =
    !!month
    && totalPerLiter != null
    && totalPerLiter > 0;

  const loadOfficial = async () => {
    if (!month) return;
    setLoadingOfficial(true);
    try {
      const query = new URLSearchParams({ month_start: `${month}-01` });
      const response = await fetch(`${API_BASE}/farm/coml?${query}`);
      const body = await response.json().catch(() => null);
      setOfficial(response.ok ? body : null);
    } finally {
      setLoadingOfficial(false);
    }
  };

  useEffect(() => {
    void loadOfficial();
  }, [month]);

  const makeManualOfficial = async () => {
    if (!canMakeOfficial || totalPerLiter == null) return;

    setSaving(true);
    setError('');
    setMessage('');

    try {
      const feed = Number(feedCostPerLiter);
      const opex = Number(opexCostPerLiter);
      const response = await fetch(`${API_BASE}/farm/coml/lock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          month_start: `${month}-01`,
          feed_cost_per_liter: feed,
          opex_cost_per_liter: opex,
          notes:
            `MANUAL COP made official for ${month}; `
            + `Feed Cost/L ${feed.toFixed(4)}; `
            + `OPEX/L ${opex.toFixed(4)}; `
            + `COP/L ${totalPerLiter.toFixed(4)}.`,
          updated_by: 'UI Operator',
        }),
      });

      const body = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(body?.detail || 'Unable to make manual COP official.');
      }

      setOfficial(body);
      setMessage(
        `Manual COP for ${month} is now the official COP/L. The Dashboard will use this official value.`,
      );
    } catch (exc) {
      setError(
        exc instanceof Error
          ? exc.message
          : 'Unable to make manual COP official.',
      );
    } finally {
      setSaving(false);
    }
  };

  const officialRecord = official?.record ?? null;

  return (
    <section
      style={{
        ...panel,
        margin: '20px 20px 12px',
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
              fontSize: 12,
              fontWeight: 900,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <SlidersHorizontal size={14} />
            Manual COP / L Calculator
          </div>
          <div
            style={{
              fontSize: 10,
              color: '#94a3b8',
              marginTop: 3,
            }}
          >
            Enter Feed Cost / L and OPEX / L directly. Manual COP / L is their sum.
          </div>
        </div>

        <input
          aria-label="Manual COP month"
          type="month"
          value={month}
          onChange={event => setMonth(event.target.value)}
          style={{ ...inputStyle, width: 'auto' }}
        />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3,minmax(0,1fr))',
          gap: 9,
          marginTop: 12,
        }}
      >
        <label style={label}>
          Feed Cost / Liter
          <input
            aria-label="Manual Feed Cost per Liter"
            type="number"
            min="0"
            step="0.0001"
            value={feedCostPerLiter}
            onChange={event => setFeedCostPerLiter(event.target.value)}
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
            value={opexCostPerLiter}
            onChange={event => setOpexCostPerLiter(event.target.value)}
            placeholder="PKR / L"
            style={{ ...inputStyle, marginTop: 4 }}
          />
        </label>

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
            Manual COP / L
          </div>
          <div
            style={{
              fontSize: 18,
              fontWeight: 900,
              color: '#f59e0b',
              marginTop: 6,
            }}
          >
            {totalPerLiter == null ? 'N/A' : money(totalPerLiter)}
          </div>
          <div style={{ marginTop: 3, color: '#64748b', fontSize: 8 }}>
            Feed Cost/L + OPEX/L
          </div>
        </div>
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
          {loadingOfficial
            ? 'Loading current official COP…'
            : officialRecord
              ? `Current official for ${month}: ${money(officialRecord.total_coml_per_liter)}.`
              : `No official COP record currently exists for ${month}.`}
        </div>

        <button
          type="button"
          disabled={!canMakeOfficial || saving}
          onClick={() => void makeManualOfficial()}
          style={{
            ...button('#d97706'),
            opacity: !canMakeOfficial || saving ? 0.5 : 1,
          }}
        >
          <CheckCircle2 size={13} />
          {saving ? 'Making Official…' : 'Make Manual COP / L Official'}
        </button>
      </div>

      <div
        style={{
          marginTop: 9,
          padding: 9,
          background: '#0f172a',
          border: '1px solid #1f2937',
          borderRadius: 6,
          fontSize: 9,
          color: '#94a3b8',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <Calculator size={12} />
        Making Manual COP/L official replaces the month’s current official COP/L. The Auto calculator remains live and can be made official again at any time.
      </div>
    </section>
  );
}