import React, { useEffect, useMemo, useState } from 'react';
import { Calculator, CheckCircle2, X } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';
const inputStyle: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: 5, fontSize: 11 };
const button: React.CSSProperties = { background: '#38bdf8', color: '#082f49', border: 0, borderRadius: 5, padding: '8px 12px', fontWeight: 800, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 5 };
const money = (value: string | number) => `PKR ${Number(value || 0).toLocaleString('en-PK', { maximumFractionDigits: 2 })}`;
const today = () => new Date().toISOString().slice(0, 10);

type PayrollRow = { id: number; employee_name: string; employee_role: string; period_start: string; period_end: string; worked_days: string; base_pay: string; overtime_hours: string; overtime_rate: string; overtime_pay: string; allowances: string; advances: string; deductions: string; gross_pay: string; net_pay: string; status: string; payment_date?: string | null };

export default function PayrollWindow() {
  const [rows, setRows] = useState<PayrollRow[]>([]);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ employee_name: '', employee_role: '', period_start: today().slice(0, 8) + '01', period_end: today(), worked_days: '0', base_pay: '', overtime_hours: '0', overtime_rate: '0', allowances: '0', advances: '0', deductions: '0', notes: '' });

  const load = async () => {
    setError('');
    try {
      const response = await fetch(`${API_BASE}/farm/payroll`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Payroll API unavailable.');
      setRows(data.records || []);
    } catch (exc) { setError(exc instanceof Error ? exc.message : 'Unable to load payroll.'); }
  };

  useEffect(() => { void load(); }, []);

  const preview = useMemo(() => {
    const base = Number(form.base_pay || 0), overtime = Number(form.overtime_hours || 0) * Number(form.overtime_rate || 0), allowances = Number(form.allowances || 0), advances = Number(form.advances || 0), deductions = Number(form.deductions || 0);
    return { overtime, gross: base + overtime + allowances, net: base + overtime + allowances - advances - deductions };
  }, [form]);

  const update = (key: keyof typeof form, value: string) => setForm(current => ({ ...current, [key]: value }));

  const save = async (event: React.FormEvent) => {
    event.preventDefault(); setSaving(true); setError('');
    try {
      const response = await fetch(`${API_BASE}/farm/payroll`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...form, worked_days: Number(form.worked_days || 0), base_pay: Number(form.base_pay || 0), overtime_hours: Number(form.overtime_hours || 0), overtime_rate: Number(form.overtime_rate || 0), allowances: Number(form.allowances || 0), advances: Number(form.advances || 0), deductions: Number(form.deductions || 0) }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Payroll record could not be saved.');
      setForm({ employee_name: '', employee_role: '', period_start: today().slice(0, 8) + '01', period_end: today(), worked_days: '0', base_pay: '', overtime_hours: '0', overtime_rate: '0', allowances: '0', advances: '0', deductions: '0', notes: '' });
      await load();
    } catch (exc) { setError(exc instanceof Error ? exc.message : 'Payroll save failed.'); }
    finally { setSaving(false); }
  };

  const markPaid = async (id: number) => {
    setError('');
    try {
      const response = await fetch(`${API_BASE}/farm/payroll/${id}/pay`, { method: 'POST' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Payroll payment failed.');
      await load();
    } catch (exc) { setError(exc instanceof Error ? exc.message : 'Payroll payment failed.'); }
  };

  return <div style={{ minHeight: '100vh', background: '#0b0f19', color: '#f8fafc', padding: 18, boxSizing: 'border-box', fontFamily: 'sans-serif' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 14 }}>
      <div><div style={{ color: '#38bdf8', fontSize: 10, fontWeight: 800, textTransform: 'uppercase' }}>Finance</div><h1 style={{ margin: 0, fontSize: 20 }}>Payroll</h1><div style={{ color: '#94a3b8', fontSize: 10 }}>Employee pay periods, overtime, allowances, advances, deductions and settlement.</div></div>
      <div style={{ display: 'flex', gap: 6 }}><button style={{ ...button, background: '#1e293b', color: '#cbd5e1' }} onClick={() => window.close()}><X size={13}/>Close</button></div>
    </div>
    {error && <div style={{ background: '#450a0a', border: '1px solid #7f1d1d', color: '#fecaca', padding: 9, borderRadius: 6, marginBottom: 12, fontSize: 10 }}>{error}</div>}
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 340px', gap: 12, alignItems: 'start' }}>
      <form onSubmit={save} style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 14 }}>
        <h2 style={{ margin: '0 0 12px', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}><Calculator size={14}/>Create Payroll Record</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr 1fr 1fr', gap: 7 }}>
          <input required placeholder="Employee name" value={form.employee_name} onChange={e => update('employee_name', e.target.value)} style={inputStyle}/>
          <input required placeholder="Role" value={form.employee_role} onChange={e => update('employee_role', e.target.value)} style={inputStyle}/>
          <input required type="date" value={form.period_start} onChange={e => update('period_start', e.target.value)} style={inputStyle}/>
          <input required type="date" value={form.period_end} onChange={e => update('period_end', e.target.value)} style={inputStyle}/>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 7, marginTop: 7 }}>
          <input type="number" min="0" step="0.01" placeholder="Worked days" value={form.worked_days} onChange={e => update('worked_days', e.target.value)} style={inputStyle}/>
          <input required type="number" min="0" step="0.01" placeholder="Base pay" value={form.base_pay} onChange={e => update('base_pay', e.target.value)} style={inputStyle}/>
          <input type="number" min="0" step="0.01" placeholder="Overtime hours" value={form.overtime_hours} onChange={e => update('overtime_hours', e.target.value)} style={inputStyle}/>
          <input type="number" min="0" step="0.01" placeholder="Overtime rate" value={form.overtime_rate} onChange={e => update('overtime_rate', e.target.value)} style={inputStyle}/>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 7, marginTop: 7 }}>
          <input type="number" min="0" step="0.01" placeholder="Allowances" value={form.allowances} onChange={e => update('allowances', e.target.value)} style={inputStyle}/>
          <input type="number" min="0" step="0.01" placeholder="Advances" value={form.advances} onChange={e => update('advances', e.target.value)} style={inputStyle}/>
          <input type="number" min="0" step="0.01" placeholder="Deductions" value={form.deductions} onChange={e => update('deductions', e.target.value)} style={inputStyle}/>
          <input placeholder="Notes" value={form.notes} onChange={e => update('notes', e.target.value)} style={inputStyle}/>
        </div>
        <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 7 }}>
          <div style={summary}>Overtime: <strong>{money(preview.overtime)}</strong></div><div style={summary}>Gross: <strong>{money(preview.gross)}</strong></div><div style={summary}>Net: <strong>{money(preview.net)}</strong></div>
        </div>
        <button disabled={saving} type="submit" style={{ ...button, width: '100%', justifyContent: 'center', marginTop: 10 }}>{saving ? 'Saving…' : 'Save Payroll Record'}</button>
      </form>
      <section style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 14 }}><h2 style={{ margin: '0 0 12px', fontSize: 13 }}>Payroll Register</h2>{rows.map(row => <div key={row.id} style={{ borderBottom: '1px solid #1f2937', paddingBottom: 9, marginBottom: 9 }}><div style={{ fontWeight: 800, fontSize: 11 }}>{row.employee_name}</div><div style={{ color: '#94a3b8', fontSize: 9 }}>{row.employee_role} • {row.period_start} → {row.period_end}</div><div style={{ marginTop: 5, fontSize: 11 }}>Net: <strong>{money(row.net_pay)}</strong></div><div style={{ marginTop: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><span style={{ color: row.status === 'PAID' ? '#86efac' : '#fbbf24', fontSize: 9, fontWeight: 800 }}>{row.status}</span>{row.status !== 'PAID' && <button style={{ ...button, padding: '5px 8px', fontSize: 9 }} onClick={() => void markPaid(row.id)}><CheckCircle2 size={11}/>Mark Paid</button>}</div></div>)}{rows.length===0&&<div style={{ color: '#64748b', fontSize: 10 }}>No payroll records.</div>}</section>
    </div>
  </div>;
}

const summary: React.CSSProperties = { background: '#0f172a', border: '1px solid #1f2937', borderRadius: 5, padding: 8, fontSize: 10, color: '#94a3b8' };
