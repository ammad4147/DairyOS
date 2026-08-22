import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CalendarDays, CheckCircle2, Clock3, LockKeyhole, Save, Settings2 } from 'lucide-react';
import TMRPreparationTool from './TMRPreparationTool';

const API_BASE = 'http://localhost:8000';

type COMLRecord = {
  id: number;
  month_start: string;
  month_label: string;
  feed_cost_per_liter: number;
  opex_cost_per_liter: number;
  total_coml_per_liter: number;
  status: string;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  locked_at?: string | null;
  updated_by: string;
};

type COMLStatus = {
  month_start: string;
  month_label: string;
  has_official: boolean;
  record: COMLRecord | null;
  reminder_day: number;
  reminder_status: 'LOCKED' | 'UPCOMING' | 'DUE' | 'OVERDUE';
  reminder_due: boolean;
};

const firstOfMonth = (value = new Date()) => `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-01`;
const monthLabel = (value: string) => new Date(`${value.slice(0, 7)}-01T00:00:00`).toLocaleDateString('en-PK', { month: 'long', year: 'numeric' });
const formatDate = (value?: string | null) => value ? new Date(value).toLocaleDateString('en-PK', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
const money = (value: number) => `PKR ${value.toFixed(2)} / L`;

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try { const body = await response.json() as { detail?: unknown }; if (body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail); } catch { /* ignore */ }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export default function COML() {
  const [selectedMonth, setSelectedMonth] = useState(firstOfMonth());
  const [status, setStatus] = useState<COMLStatus | null>(null);
  const [history, setHistory] = useState<COMLRecord[]>([]);
  const [feedCost, setFeedCost] = useState('');
  const [opexCost, setOpexCost] = useState('');
  const [notes, setNotes] = useState('');
  const [reminderDay, setReminderDay] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = async (month = selectedMonth) => {
    setLoading(true); setError(''); setMessage('');
    try {
      const [current, historyResult, settings] = await Promise.all([
        request<COMLStatus>(`/farm/coml?month_start=${month}`),
        request<{ records: COMLRecord[] }>('/farm/coml/history'),
        request<{ reminder_day: number }>('/farm/coml/settings'),
      ]);
      setStatus(current);
      setHistory(historyResult.records || []);
      setReminderDay(settings.reminder_day || 1);
      const record = current.record;
      setFeedCost(record ? String(record.feed_cost_per_liter) : '');
      setOpexCost(record ? String(record.opex_cost_per_liter) : '');
      setNotes(record?.notes || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load COML.');
    } finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, [selectedMonth]);

  const total = useMemo(() => (Number(feedCost) || 0) + (Number(opexCost) || 0), [feedCost, opexCost]);
  const isCurrentMonth = selectedMonth === firstOfMonth();

  const lock = async () => {
    setSaving(true); setError(''); setMessage('');
    try {
      await request<COMLStatus>('/farm/coml/lock', {
        method: 'POST',
        body: JSON.stringify({ month_start: selectedMonth, feed_cost_per_liter: Number(feedCost), opex_cost_per_liter: Number(opexCost), notes: notes || null, updated_by: 'UI Operator' }),
      });
      setMessage(`Official COML locked for ${monthLabel(selectedMonth)}.`);
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to lock COML.'); }
    finally { setSaving(false); }
  };

  const saveReminder = async () => {
    setError(''); setMessage('');
    try {
      await request('/farm/coml/settings', { method: 'PUT', body: JSON.stringify({ reminder_day: reminderDay }) });
      setMessage(`Monthly COML reminder is set for day ${reminderDay}.`);
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save reminder setting.'); }
  };

  return (
    <div style={{ padding: 16, color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
        <div>
          <h2 style={{ margin: 0, color: '#34d399', fontSize: 20, display: 'flex', alignItems: 'center', gap: 8 }}> <LockKeyhole size={21} /> Static Monthly COML</h2>
          <p style={{ margin: '5px 0 0', color: '#94a3b8', fontSize: 11 }}>Official Cost of Milk Production per liter. Month-specific, user-locked, historical, and independent of live transactions.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, background: '#111827', border: '1px solid #1f2937', borderRadius: 7, padding: 8 }}>
          <CalendarDays size={14} color="#38bdf8" />
          <label style={{ color: '#94a3b8', fontSize: 9, textTransform: 'uppercase', fontWeight: 800 }}>Month / Year</label>
          <input type="month" value={selectedMonth.slice(0, 7)} onChange={e => setSelectedMonth(`${e.target.value}-01`)} style={inputStyle} />
        </div>
      </div>

      {error && <Banner tone="#ef4444">{error}</Banner>}
      {message && <Banner tone="#34d399"><CheckCircle2 size={13} /> {message}</Banner>}

      {status?.reminder_due && !status.has_official && (
        <Banner tone="#f59e0b"><AlertTriangle size={14} /> {isCurrentMonth ? `No official COML is locked for ${status.month_label}. Monthly calculation is due.` : `No official COML is locked for ${status.month_label}.`}</Banner>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 12 }}>
        <Metric label={`Official COML · ${monthLabel(selectedMonth)}`} value={status?.has_official ? money(status.record!.total_coml_per_liter) : 'Not locked'} accent={status?.has_official ? '#34d399' : '#f59e0b'} />
        <Metric label="Feed Cost / L · Static" value={status?.has_official ? money(status.record!.feed_cost_per_liter) : `${Number(feedCost || 0).toFixed(2)} / L`} accent="#38bdf8" />
        <Metric label="OPEX / L · Static" value={status?.has_official ? money(status.record!.opex_cost_per_liter) : `${Number(opexCost || 0).toFixed(2)} / L`} accent="#a78bfa" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.15fr .85fr', gap: 12, marginBottom: 12 }}>
        <section style={card}>
          <div style={sectionTitle}><span>Official Monthly COML Record</span><span style={{ color: status?.has_official ? '#34d399' : '#f59e0b', fontSize: 9 }}>{status?.has_official ? 'OFFICIAL / LOCKED' : 'NO OFFICIAL RECORD'}</span></div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 9 }}>
            <Field label="Feed Cost per Liter" value={feedCost} onChange={setFeedCost} />
            <Field label="OPEX per Liter" value={opexCost} onChange={setOpexCost} />
          </div>
          <div style={{ marginTop: 9, padding: 10, background: '#0f172a', borderRadius: 7, border: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div><div style={{ color: '#94a3b8', fontSize: 9, textTransform: 'uppercase', fontWeight: 800 }}>Total COML / L</div><div style={{ color: '#34d399', fontSize: 22, fontWeight: 900 }}>{money(total)}</div></div>
            <div style={{ color: '#64748b', fontSize: 9, textAlign: 'right' }}>Auto-sum only.<br />No live transaction linkage.</div>
          </div>
          <label style={{ display: 'block', marginTop: 9, color: '#94a3b8', fontSize: 9, textTransform: 'uppercase', fontWeight: 800 }}>Notes<textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3} style={{ ...inputStyle, marginTop: 4, resize: 'vertical' }} placeholder="Basis, TMR assumptions, management note..." /></label>
          <div style={{ marginTop: 9, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <div style={{ color: '#94a3b8', fontSize: 9 }}>{status?.has_official ? `Last updated: ${formatDate(status.record?.updated_at)} · Locked: ${formatDate(status.record?.locked_at)}` : `Valid for: ${monthLabel(selectedMonth)}`}</div>
            <button disabled={saving || Number(feedCost) < 0 || Number(opexCost) < 0 || total <= 0} onClick={() => void lock()} style={button('#059669')}><Save size={12} /> {saving ? 'Locking…' : `Lock / Save Official COML for ${monthLabel(selectedMonth)}`}</button>
          </div>
        </section>

        <section style={card}>
          <div style={sectionTitle}><span><Clock3 size={13} /> Monthly Reminder</span><span style={{ color: reminderColor(status?.reminder_status), fontSize: 9 }}>{status?.reminder_status || '—'}</span></div>
          <div style={{ color: '#cbd5e1', fontSize: 11, lineHeight: 1.5 }}>Reminder stays active until the selected month has an official locked COML.</div>
          <label style={{ marginTop: 12, display: 'block', color: '#94a3b8', fontSize: 9, textTransform: 'uppercase', fontWeight: 800 }}>Reminder Day (1–28)<input type="number" min={1} max={28} value={reminderDay} onChange={e => setReminderDay(Number(e.target.value))} style={{ ...inputStyle, marginTop: 4 }} /></label>
          <button onClick={() => void saveReminder()} style={{ ...button('#334155'), marginTop: 8 }}><Settings2 size={12} /> Save Reminder Setting</button>
          {isCurrentMonth && <div style={{ marginTop: 12, padding: 9, borderRadius: 6, background: status?.has_official ? 'rgba(52,211,153,.08)' : 'rgba(245,158,11,.08)', color: status?.has_official ? '#86efac' : '#fcd34d', fontSize: 10 }}>{status?.has_official ? `Current month is officially locked: ${status.month_label}.` : `Current month has no official COML: ${status?.month_label || monthLabel(selectedMonth)}.`}</div>}
        </section>
      </div>

      <section style={{ marginBottom: 12 }}>
        <div style={{ marginBottom: 7, color: '#38bdf8', fontSize: 13, fontWeight: 900 }}>TMR Preparation Tool</div>
        <TMRPreparationTool />
      </section>

      <section style={card}>
        <div style={sectionTitle}><span>Historical Monthly COML</span><span style={{ color: '#64748b', fontSize: 9 }}>{history.length} locked month(s)</span></div>
        <div style={{ overflowX: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}><thead><tr style={{ color: '#94a3b8', textAlign: 'left', borderBottom: '1px solid #1f2937' }}><th style={th}>Month</th><th style={th}>Feed / L</th><th style={th}>OPEX / L</th><th style={th}>Official COML / L</th><th style={th}>Last Updated</th></tr></thead><tbody>{history.map(row => <tr key={row.id} style={{ borderBottom: '1px solid #1a2234', cursor: 'pointer' }} onClick={() => setSelectedMonth(row.month_start)}><td style={td}>{row.month_label}</td><td style={td}>{money(row.feed_cost_per_liter)}</td><td style={td}>{money(row.opex_cost_per_liter)}</td><td style={{ ...td, color: '#34d399', fontWeight: 900 }}>{money(row.total_coml_per_liter)}</td><td style={td}>{formatDate(row.updated_at)}</td></tr>)}{history.length === 0 && <tr><td colSpan={5} style={{ padding: 16, color: '#64748b', textAlign: 'center' }}>No historical monthly COML records yet.</td></tr>}</tbody></table></div>
      </section>
    </div>
  );
}

const card: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 12 };
const sectionTitle: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 9, color: '#fff', fontSize: 12, fontWeight: 900 };
const inputStyle: React.CSSProperties = { background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '7px 8px', borderRadius: 5, fontSize: 10, boxSizing: 'border-box', width: '100%' };
const th: React.CSSProperties = { padding: 8, fontWeight: 800 };
const td: React.CSSProperties = { padding: 8 };
const button = (background: string): React.CSSProperties => ({ background, color: '#fff', border: 'none', borderRadius: 5, padding: '8px 10px', fontSize: 10, fontWeight: 800, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 5 });
function Metric({ label, value, accent }: { label: string; value: string; accent: string }) { return <div style={{ ...card, borderLeft: `4px solid ${accent}` }}><div style={{ color: '#94a3b8', fontSize: 9, textTransform: 'uppercase', fontWeight: 800 }}>{label}</div><div style={{ color: accent, fontSize: 18, fontWeight: 900, marginTop: 5 }}>{value}</div></div>; }
function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label style={{ color: '#94a3b8', fontSize: 9, textTransform: 'uppercase', fontWeight: 800 }}>{label}<input type="number" min="0" step="0.01" value={value} onChange={e => onChange(e.target.value)} style={{ ...inputStyle, marginTop: 4 }} placeholder="0.00" /></label>; }
function Banner({ children, tone }: { children: React.ReactNode; tone: string }) { return <div style={{ background: `${tone}12`, border: `1px solid ${tone}`, color: tone, borderRadius: 6, padding: 9, marginBottom: 10, fontSize: 10, display: 'flex', alignItems: 'center', gap: 6 }}>{children}</div>; }
function reminderColor(status?: string) { return status === 'LOCKED' ? '#34d399' : status === 'UPCOMING' ? '#38bdf8' : '#f59e0b'; }
