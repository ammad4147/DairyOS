import { useEffect, useState } from 'react';
import { HeartPulse, TrendingDown, X } from 'lucide-react';
import { apiUrl } from '../config/api';
import { useAlertAudit, type AuditAlertItem } from '../context/AlertAuditContext';

type Props = {
  alert: AuditAlertItem;
  onClose: () => void;
  onOpenPassport: (animalId: string) => void;
};

type YieldDropDetail = {
  finding_id: string;
  animal_id: string;
  flagged_date?: string | null;
  prior_3_day_avg_litres?: number | null;
  current_yield_litres?: number | null;
  drop_variance_percent?: number | null;
  drop_variance_litres?: number | null;
  severity?: 'GREEN' | 'YELLOW' | 'RED' | 'UNKNOWN';
  status?: string;
};

const triageChecks = [
  'Verify Data Entry for correctness',
  'Check Health',
  'Check Intake Issues',
  'Check Environmental Stress',
  'Verify Lactating & Pregnancy Stage',
];

export default function YieldDropAlertModal({ alert, onClose, onOpenPassport }: Props) {
  const { markResolved } = useAlertAudit();
  const [detail, setDetail] = useState<YieldDropDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [observationOpen, setObservationOpen] = useState(false);
  const [observation, setObservation] = useState('');
  const [observationSeverity, setObservationSeverity] = useState('NORMAL');
  const [savingObservation, setSavingObservation] = useState(false);
  const [dismissing, setDismissing] = useState(false);

  const animalId = detail?.animal_id || alert.animalId || '';

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await fetch(
          apiUrl(`/farm/findings/${encodeURIComponent(alert.id)}/yield-drop-detail`),
          { headers: { Accept: 'application/json' } },
        );
        const body = await response.json().catch(() => null) as YieldDropDetail | { detail?: string } | null;
        if (!response.ok) {
          const problem = body && 'detail' in body ? body.detail : null;
          throw new Error(problem || `Unable to load yield-drop detail (${response.status})`);
        }
        if (!cancelled) setDetail(body as YieldDropDetail);
      } catch (exc) {
        if (!cancelled) setError(exc instanceof Error ? exc.message : 'Unable to load yield-drop detail.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    return () => { cancelled = true; };
  }, [alert.id]);

  const logClinicalObservation = async () => {
    if (!animalId || !observation.trim()) return;
    setSavingObservation(true);
    setError('');
    setMessage('');
    try {
      const response = await fetch(apiUrl('/farm/health-observations'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          animal_id: animalId,
          observation: observation.trim(),
          symptom: observation.trim(),
          severity: observationSeverity,
          operator: 'Dashboard Yield Drop Triage',
        }),
      });
      const body = await response.json().catch(() => null) as { detail?: string } | null;
      if (!response.ok) throw new Error(body?.detail || `Unable to log clinical observation (${response.status})`);
      setObservation('');
      setObservationSeverity('NORMAL');
      setObservationOpen(false);
      setMessage(`Clinical observation recorded for ${animalId}.`);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Unable to log clinical observation.');
    } finally {
      setSavingObservation(false);
    }
  };

  const dismissAlert = async () => {
    if (!window.confirm('Dismiss this yield-drop alert? It will remain in the audit history as resolved.')) return;
    setDismissing(true);
    setError('');
    try {
      await markResolved(
        alert.id,
        'Dashboard Yield Drop Triage',
        `Yield-drop alert dismissed after operator triage for ${animalId || 'linked animal'}.`,
      );
      onClose();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : 'Unable to dismiss yield-drop alert.');
    } finally {
      setDismissing(false);
    }
  };

  const flaggedDate = detail?.flagged_date || alert.createdAt?.slice(0, 10) || '—';
  const severity = detail?.severity || (alert.currentLevel === 'RED' ? 'RED' : 'YELLOW');
  const severityColor = severity === 'RED' ? '#ef4444' : severity === 'YELLOW' ? '#facc15' : '#34d399';

  return (
    <div style={overlay}>
      <div style={{ ...modal, borderColor: severityColor }}>
        <div style={header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingDown size={18} color={severityColor} />
            <h3 style={{ margin: 0, fontSize: 14 }}>Yield Drop Alert: {animalId || 'Animal ID unavailable'}</h3>
          </div>
          <button type="button" onClick={onClose} style={iconButton} aria-label="Close yield drop alert"><X size={18} /></button>
        </div>

        <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
          {error && <Notice error text={error} />}
          {message && <Notice text={message} />}
          {loading && <div style={{ fontSize: 10, color: '#94a3b8' }}>Loading authoritative milk history…</div>}

          <section style={section}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 8 }}>
              <Metric label="Flagged Date" value={flaggedDate} />
              <Metric label="Prior 3-Day Avg" value={litres(detail?.prior_3_day_avg_litres)} />
              <Metric label="Current Yield" value={litres(detail?.current_yield_litres)} />
              <Metric label="Drop Variance (%)" value={percent(detail?.drop_variance_percent)} danger={severity === 'RED'} warning={severity === 'YELLOW'} />
            </div>
            {detail?.status && detail.status !== 'CALCULATED' && (
              <div style={{ marginTop: 8, fontSize: 9, color: '#fbbf24' }}>
                Milk-history status: {detail.status.replace(/_/g, ' ')}. Missing values are shown as — rather than fabricated as zero.
              </div>
            )}
          </section>

          <section style={section}>
            <div style={sectionTitle}>Quick Triage</div>
            <div style={{ display: 'grid', gap: 7 }}>
              {triageChecks.map(item => (
                <label key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: '#e2e8f0' }}>
                  <input type="checkbox" /> {item}
                </label>
              ))}
            </div>
          </section>

          <section style={{ ...section, borderLeft: '3px solid #38bdf8' }}>
            <div style={sectionTitle}>Recommended Actions</div>
            <div style={{ fontSize: 10, color: '#cbd5e1', lineHeight: 1.5 }}>
              Complete the quick triage, inspect the Animal Passport when further context is required, record any clinical observation, and dismiss the alert only after review.
            </div>
          </section>

          {observationOpen && (
            <section style={{ ...section, borderColor: '#b91c1c' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, fontSize: 11, fontWeight: 900 }}>
                <HeartPulse size={13} color="#f87171" /> Log Clinical Observation — {animalId}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 140px', gap: 8 }}>
                <textarea
                  autoFocus
                  value={observation}
                  onChange={event => setObservation(event.target.value)}
                  placeholder="Record the observed clinical signs or examination finding."
                  style={{ ...field, minHeight: 72, resize: 'vertical' }}
                />
                <select value={observationSeverity} onChange={event => setObservationSeverity(event.target.value)} style={field}>
                  <option value="NORMAL">Normal / Monitoring</option>
                  <option value="WARNING">Warning</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 7, marginTop: 8 }}>
                <button type="button" onClick={() => setObservationOpen(false)} style={button('#334155')}>Cancel</button>
                <button type="button" disabled={savingObservation || !observation.trim()} onClick={() => void logClinicalObservation()} style={button('#b91c1c')}>
                  {savingObservation ? 'Saving…' : 'Save Clinical Observation'}
                </button>
              </div>
            </section>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" disabled={!animalId} onClick={() => animalId && onOpenPassport(animalId)} style={button('#0284c7')}>
              Open Animal Passport {animalId}
            </button>
            <button type="button" disabled={!animalId} onClick={() => setObservationOpen(true)} style={button('#b91c1c')}>
              Log Clinical Observation
            </button>
            <button type="button" disabled={dismissing} onClick={() => void dismissAlert()} style={button('#7f1d1d')}>
              {dismissing ? 'Dismissing…' : 'Dismiss Alert'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function litres(value: number | null | undefined) {
  return value == null || !Number.isFinite(Number(value)) ? '—' : `${Number(value).toFixed(1)} L`;
}

function percent(value: number | null | undefined) {
  return value == null || !Number.isFinite(Number(value)) ? '—' : `${Number(value).toFixed(1)}%`;
}

function Metric({ label, value, danger = false, warning = false }: { label: string; value: string; danger?: boolean; warning?: boolean }) {
  const color = danger ? '#ef4444' : warning ? '#facc15' : '#38bdf8';
  return <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: 10, borderRadius: 6, minWidth: 0 }}><div style={{ fontSize: 9, color: '#94a3b8' }}>{label}</div><div style={{ fontSize: 14, fontWeight: 900, color, marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis' }}>{value}</div></div>;
}

function Notice({ text, error = false }: { text: string; error?: boolean }) {
  return <div style={{ padding: 8, borderRadius: 6, fontSize: 10, background: error ? 'rgba(239,68,68,.12)' : 'rgba(34,197,94,.10)', border: `1px solid ${error ? '#ef4444' : '#22c55e'}`, color: error ? '#fecaca' : '#bbf7d0' }}>{text}</div>;
}

const overlay: React.CSSProperties = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20 };
const modal: React.CSSProperties = { background: '#111827', border: '1px solid #ef4444', borderRadius: 10, width: 680, maxWidth: '100%', maxHeight: '92vh', overflowY: 'auto' };
const header: React.CSSProperties = { background: '#1e293b', padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #334155' };
const iconButton: React.CSSProperties = { background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' };
const section: React.CSSProperties = { background: '#161f30', border: '1px solid #1f2937', padding: 12, borderRadius: 6 };
const sectionTitle: React.CSSProperties = { fontSize: 11, fontWeight: 900, color: '#f8fafc', marginBottom: 8 };
const field: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '8px 9px', borderRadius: 6, fontSize: 11 };
const button = (background: string): React.CSSProperties => ({ background, color: '#fff', border: 'none', padding: '8px 12px', borderRadius: 6, fontSize: 10, fontWeight: 800, cursor: 'pointer' });
