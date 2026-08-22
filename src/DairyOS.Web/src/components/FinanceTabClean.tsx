import React, { useEffect, useMemo, useState } from 'react';
import { Ban, Edit3, Printer, RefreshCw, Search } from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const input: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', color: '#fff', border: '1px solid #334155', borderRadius: 5, padding: '7px 8px', fontSize: 10 };
const panel: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 10, minWidth: 0, boxSizing: 'border-box', overflow: 'hidden' };
const small = (active = false): React.CSSProperties => ({ background: active ? '#0ea5e9' : '#1e293b', border: '1px solid #334155', color: '#fff', borderRadius: 5, padding: '6px 8px', fontSize: 9, fontWeight: 800, cursor: 'pointer' });
const button = (bg: string): React.CSSProperties => ({ background: bg, color: '#fff', border: 0, borderRadius: 5, padding: '7px 9px', fontSize: 9, fontWeight: 800, cursor: 'pointer' });

type MasterCategory = 'FEED' | 'OPEX';
type Transaction = { id: number; transaction_type: string; category: string; master_category?: MasterCategory | null; sub_category?: string | null; custom_specification?: string | null; amount: number; quantity?: number | null; unit?: string | null; unit_rate?: number | null; date?: string | null; reference?: string | null; payment_method?: string | null; vendor_name?: string | null; counterparty?: string | null; notes?: string | null; status?: string | null; due_date?: string | null; settled_date?: string | null };
type Taxonomy = { items: Record<MasterCategory, string[]> };
type Payables = { outstanding_total: number; overdue_total: number; count: number; ageing_buckets: Record<string, number>; supplier_rollup: { supplier: string; outstanding: number }[]; transactions: (Transaction & { days_overdue: number | null })[] };

const money = (n: number) => `PKR ${Number(n || 0).toLocaleString('en-PK', { maximumFractionDigits: 2 })}`;
const today = () => new Date().toISOString().slice(0, 10);
async function api<T>(url: string, init?: RequestInit): Promise<T> { const r = await fetch(`${API_BASE}${url}`, { headers: { 'Content-Type': 'application/json' }, ...init }); const b = await r.json().catch(() => null); if (!r.ok) throw new Error(typeof b?.detail === 'string' ? b.detail : 'Finance request failed.'); return b as T; }

export default function FinanceTabClean() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null);
  const [payables, setPayables] = useState<Payables | null>(null);
  const [master, setMaster] = useState<MasterCategory>('FEED');
  const [sub, setSub] = useState('');
  const [custom, setCustom] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [rate, setRate] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(today());
  const [vendor, setVendor] = useState('');
  const [payment, setPayment] = useState('BANK');
  const [dueDate, setDueDate] = useState('');
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');
  const [revenueCategory, setRevenueCategory] = useState('Milk Sales');
  const [revenueAmount, setRevenueAmount] = useState('');
  const [revenueDate, setRevenueDate] = useState(today());
  const [revenueStatus, setRevenueStatus] = useState<'RECEIVED' | 'RECEIVABLE'>('RECEIVABLE');
  const [revenueDue, setRevenueDue] = useState('');
  const [ledgerFilter, setLedgerFilter] = useState<'ALL' | MasterCategory>('ALL');
  const [search, setSearch] = useState('');
  const [editTarget, setEditTarget] = useState<Transaction | null>(null);
  const [voidTarget, setVoidTarget] = useState<Transaction | null>(null);
  const [voidReason, setVoidReason] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = async () => { setLoading(true); setError(''); try { const [ledger, tax, debt] = await Promise.all([api<{ transactions: Transaction[] }>('/farm/finance-ledger'), api<Taxonomy>('/farm/finance-ledger/taxonomy'), api<Payables>('/farm/finance-ledger/payables')]); setTransactions(ledger.transactions || []); setTaxonomy(tax); setPayables(debt); } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load Finance.'); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, []);
  useEffect(() => { setSub(taxonomy?.items?.[master]?.[0] || ''); setCustom(''); }, [master, taxonomy]);

  const revenueRows = useMemo(() => transactions.filter(t => ['INCOME', 'RECEIPT'].includes(t.transaction_type) && t.status !== 'VOID'), [transactions]);
  const expenseRows = useMemo(() => transactions.filter(t => ['EXPENSE', 'PAYMENT'].includes(t.transaction_type) && t.status !== 'VOID'), [transactions]);
  const receivables = revenueRows.filter(t => t.status === 'RECEIVABLE').reduce((s, t) => s + t.amount, 0);
  const cashReceived = revenueRows.filter(t => ['RECEIVED', 'PAID', 'RECORDED'].includes(String(t.status))).reduce((s, t) => s + t.amount, 0);
  const filtered = useMemo(() => { const q = search.toLowerCase().trim(); return expenseRows.filter(t => (ledgerFilter === 'ALL' || t.master_category === ledgerFilter) && (!q || [t.sub_category, t.custom_specification, t.vendor_name, t.reference, t.notes].some(v => String(v || '').toLowerCase().includes(q)))); }, [expenseRows, ledgerFilter, search]);
  const calcAmount = quantity && rate ? Number(quantity) * Number(rate) : Number(amount || 0);

  const saveExpense = async (e: React.FormEvent) => { e.preventDefault(); setBusy(true); setError(''); try { await api('/farm/finance-ledger', { method: 'POST', body: JSON.stringify({ transaction_type: 'EXPENSE', master_category: master, sub_category: sub, custom_specification: sub === 'Other' ? custom : null, quantity: quantity ? Number(quantity) : null, unit: quantity ? unit : null, unit_rate: quantity ? Number(rate) : null, amount: calcAmount, transaction_date: date, payment_method: payment, counterparty: vendor || null, reference: reference || null, notes: notes || null, status: payment === 'CREDIT' ? 'PAYABLE' : 'PAID', due_date: payment === 'CREDIT' ? dueDate : null }) }); setQuantity(''); setRate(''); setAmount(''); setVendor(''); setReference(''); setNotes(''); setDueDate(''); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Expense save failed.'); } finally { setBusy(false); } };

  const saveRevenue = async (e: React.FormEvent) => { e.preventDefault(); setBusy(true); setError(''); try { const map: Record<string, string> = { 'Milk Sales': 'MILK_SALES', 'Organic Manure / Dung': 'MANURE_SALES', 'Male Calf Sales': 'MALE_CALF_SALES' }; await api('/farm/finance-ledger', { method: 'POST', body: JSON.stringify({ transaction_type: revenueStatus === 'RECEIVED' ? 'RECEIPT' : 'INCOME', category: map[revenueCategory] || 'OTHER_REVENUE', amount: Number(revenueAmount), transaction_date: revenueDate, payment_method: revenueStatus === 'RECEIVED' ? 'CASH' : 'CREDIT', status: revenueStatus, due_date: revenueStatus === 'RECEIVABLE' ? revenueDue : null }) }); setRevenueAmount(''); setRevenueDue(''); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Revenue save failed.'); } finally { setBusy(false); } };

  const setStatus = async (row: Transaction, status: string, reason?: string) => { try { await api(`/farm/finance-ledger/${row.id}/status`, { method: 'POST', body: JSON.stringify({ status, reason }) }); setVoidTarget(null); setVoidReason(''); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Status update failed.'); } };

  return <div style={{ height: '100%', overflowY: 'auto', overflowX: 'hidden', padding: 14, color: '#fff', boxSizing: 'border-box' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}><div><div style={{ fontSize: 18, fontWeight: 800 }}>Finance & Accounting</div><div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>Revenue, expenses, receivables, payables and the unified accounting ledger.</div></div><button onClick={() => void load()} style={small()}><RefreshCw size={11}/> Refresh</button></div>
    {error && <div style={{ ...panel, borderColor: '#ef4444', color: '#fecaca', marginBottom: 8, fontSize: 10 }}>{error}</div>}

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 7, marginBottom: 8 }}><Kpi label="Cash Received" value={money(cashReceived)} accent="#34d399"/><Kpi label="Receivables" value={money(receivables)} accent="#f59e0b"/><Kpi label="Payables" value={money(payables?.outstanding_total || 0)} accent="#f87171"/><Kpi label="Open Bills" value={String(payables?.count || 0)} accent="#a78bfa"/></div>

    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: 8, alignItems: 'start' }}>
      <form onSubmit={saveRevenue} style={panel}><div style={sectionTitle}>Record Revenue</div><div style={grid3}><select value={revenueCategory} onChange={e => setRevenueCategory(e.target.value)} style={input}><option>Milk Sales</option><option>Organic Manure / Dung</option><option>Male Calf Sales</option></select><input required type="number" min="0.01" step="0.01" placeholder="Amount" value={revenueAmount} onChange={e => setRevenueAmount(e.target.value)} style={input}/><input type="date" value={revenueDate} onChange={e => setRevenueDate(e.target.value)} style={input}/></div><div style={{ ...grid3, marginTop: 6 }}><select value={revenueStatus} onChange={e => setRevenueStatus(e.target.value as any)} style={input}><option value="RECEIVABLE">Receivable</option><option value="RECEIVED">Received</option></select>{revenueStatus === 'RECEIVABLE' ? <input required type="date" value={revenueDue} onChange={e => setRevenueDue(e.target.value)} style={input}/> : <div/>}<div/></div><button disabled={busy} style={{ ...button('#059669'), marginTop: 7 }}>{busy ? 'Saving…' : 'Save Revenue'}</button></form>

      <form onSubmit={saveExpense} style={panel}><div style={sectionTitle}>Record Expense</div><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5, marginBottom: 6 }}><button type="button" onClick={() => setMaster('FEED')} style={small(master === 'FEED')}>Feed</button><button type="button" onClick={() => setMaster('OPEX')} style={small(master === 'OPEX')}>OPEX</button></div><div style={grid2}><select value={sub} onChange={e => setSub(e.target.value)} style={input}>{(taxonomy?.items?.[master] || []).map(item => <option key={item}>{item}</option>)}</select>{sub === 'Other' ? <input required placeholder="Custom specification" value={custom} onChange={e => setCustom(e.target.value)} style={input}/> : <input placeholder="Vendor / Supplier" value={vendor} onChange={e => setVendor(e.target.value)} style={input}/>}</div>{sub === 'Other' && <input placeholder="Vendor / Supplier" value={vendor} onChange={e => setVendor(e.target.value)} style={{ ...input, marginTop: 6 }}/>}<div style={{ ...grid4, marginTop: 6 }}><input type="number" min="0" step="0.001" placeholder="Qty" value={quantity} onChange={e => setQuantity(e.target.value)} style={input}/><select value={unit} onChange={e => setUnit(e.target.value)} style={input}><option>kg</option><option>bag</option><option>ton</option><option>litre</option><option>service</option><option>head</option><option>month</option><option>bill</option><option>unit</option></select><input type="number" min="0" step="0.01" placeholder="Rate" value={rate} onChange={e => setRate(e.target.value)} style={input}/><input type="number" min="0" step="0.01" placeholder="Amount" value={quantity ? calcAmount : amount} onChange={e => !quantity && setAmount(e.target.value)} style={input} readOnly={Boolean(quantity)}/></div><div style={{ ...grid3, marginTop: 6 }}><input type="date" value={date} onChange={e => setDate(e.target.value)} style={input}/><select value={payment} onChange={e => setPayment(e.target.value)} style={input}><option value="BANK">Bank</option><option value="CASH">Cash</option><option value="MOBILE">Mobile</option><option value="CREDIT">Credit / Payable</option></select>{payment === 'CREDIT' ? <input required type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} style={input}/> : <input placeholder="Reference" value={reference} onChange={e => setReference(e.target.value)} style={input}/>}</div><button disabled={busy} style={{ ...button(master === 'FEED' ? '#0284c7' : '#d97706'), marginTop: 7 }}>{busy ? 'Saving…' : 'Save Expense'}</button></form>
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.15fr) minmax(280px,.85fr)', gap: 8, marginTop: 8, alignItems: 'start' }}>
      <section style={panel}><div style={sectionTitle}>Unified Expense Ledger</div><div style={{ display: 'flex', gap: 5, alignItems: 'center', flexWrap: 'wrap', marginBottom: 6 }}>{(['ALL','FEED','OPEX'] as const).map(f => <button key={f} onClick={() => setLedgerFilter(f)} style={small(ledgerFilter === f)}>{f}</button>)}<div style={{ display: 'flex', gap: 4, alignItems: 'center', marginLeft: 'auto', minWidth: 150 }}><Search size={11} color="#64748b"/><input placeholder="Search" value={search} onChange={e => setSearch(e.target.value)} style={{ ...input, padding: '5px 6px' }}/></div><button onClick={() => window.print()} style={small()}><Printer size={11}/></button></div>{loading ? <div style={muted}>Loading ledger…</div> : <div style={{ maxHeight: 360, overflowY: 'auto', overflowX: 'hidden' }}>{filtered.slice(0, 100).map(row => <div key={row.id} style={rowRow}><div style={{ minWidth: 92 }}><div style={muted}>{row.date?.slice(0,10)}</div><strong>{row.master_category || 'LEGACY'}</strong></div><div style={{ flex: 1, minWidth: 0 }}><div style={{ fontSize: 10, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.sub_category || row.category}{row.custom_specification ? ` — ${row.custom_specification}` : ''}</div><div style={muted}>{row.vendor_name || row.counterparty || 'No counterparty'}{row.due_date ? ` · Due ${row.due_date}` : ''}</div></div><div style={{ textAlign: 'right' }}><strong>{money(row.amount)}</strong><div style={{ ...muted, color: row.status === 'PAYABLE' ? '#f59e0b' : '#64748b' }}>{row.status}</div></div><button onClick={() => setVoidTarget(row)} style={{ ...small(), color: '#f87171' }}><Ban size={10}/></button></div>)}</div>}</section>

      <section style={panel}><div style={sectionTitle}>Payables Ageing</div>{payables && <><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 6 }}><Kpi label="Outstanding" value={money(payables.outstanding_total)} accent="#f87171"/><Kpi label="Overdue" value={money(payables.overdue_total)} accent="#f59e0b"/></div>{payables.transactions.slice(0, 12).map(row => <div key={row.id} style={rowRow}><div style={{ flex: 1, minWidth: 0 }}><div style={{ fontSize: 10, fontWeight: 700 }}>{row.vendor_name || 'Supplier'}</div><div style={muted}>{row.sub_category || row.category} · Due {row.due_date || '—'}</div></div><div style={{ textAlign: 'right' }}><strong>{money(row.amount)}</strong><div style={{ ...muted, color: row.days_overdue && row.days_overdue > 0 ? '#f87171' : '#34d399' }}>{row.days_overdue && row.days_overdue > 0 ? `${row.days_overdue}d overdue` : 'Current'}</div></div><button onClick={() => void setStatus(row, 'PAID')} style={small()}>Paid</button></div>)}</>}</section>
    </div>

    {voidTarget && <div style={overlay}><div style={modal}><div style={{ fontSize: 12, fontWeight: 800, color: '#f87171' }}>Void Finance Entry #{voidTarget.id}</div><textarea value={voidReason} onChange={e => setVoidReason(e.target.value)} required placeholder="Reason" style={{ ...input, marginTop: 8, minHeight: 70 }}/><div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 8 }}><button onClick={() => setVoidTarget(null)} style={small()}>Cancel</button><button disabled={!voidReason.trim()} onClick={() => void setStatus(voidTarget, 'VOID', voidReason)} style={button('#dc2626')}>Confirm Void</button></div></div></div>}
    {editTarget && <EditModal target={editTarget} onClose={() => setEditTarget(null)} onSaved={() => { setEditTarget(null); void load(); }}/>} 
  </div>;
}

function EditModal({ target, onClose, onSaved }: { target: Transaction; onClose: () => void; onSaved: () => void }) {
  const [saving, setSaving] = useState(false);
  const submit = async (e: React.FormEvent<HTMLFormElement>) => { e.preventDefault(); setSaving(true); try { const f = new FormData(e.currentTarget); const qty = Number(f.get('quantity') || 0); const rate = Number(f.get('unit_rate') || 0); await api(`/farm/finance-ledger/${target.id}`, { method: 'PATCH', body: JSON.stringify({ transaction_date: f.get('date'), master_category: f.get('master'), sub_category: f.get('sub'), quantity: qty || null, unit: qty ? f.get('unit') : null, unit_rate: qty ? rate : null, amount: qty ? qty * rate : Number(f.get('amount') || 0), payment_method: f.get('payment'), counterparty: f.get('vendor'), reference: f.get('reference'), notes: f.get('notes'), status: f.get('status'), due_date: f.get('due') || null }) }); onSaved(); } catch { /* parent reload reports errors */ } finally { setSaving(false); } };
  return <div style={overlay}><form onSubmit={submit} style={modal}><div style={{ fontSize: 12, fontWeight: 800 }}>Edit Finance Entry #{target.id}</div><div style={{ ...grid2, marginTop: 8 }}><input name="date" type="date" defaultValue={target.date?.slice(0,10)} style={input}/><select name="master" defaultValue={target.master_category || 'FEED'} style={input}><option value="FEED">Feed</option><option value="OPEX">OPEX</option></select><input name="sub" defaultValue={target.sub_category || ''} style={input}/><input name="quantity" type="number" step="0.001" defaultValue={target.quantity ?? ''} style={input}/><select name="unit" defaultValue={target.unit || 'kg'} style={input}><option>kg</option><option>bag</option><option>ton</option><option>litre</option><option>service</option><option>head</option><option>month</option><option>bill</option><option>unit</option></select><input name="unit_rate" type="number" step="0.01" defaultValue={target.unit_rate ?? ''} style={input}/><input name="amount" type="number" step="0.01" defaultValue={target.amount} style={input}/><input name="vendor" defaultValue={target.vendor_name || target.counterparty || ''} style={input}/><input name="payment" defaultValue={target.payment_method || 'BANK'} style={input}/><select name="status" defaultValue={target.status === 'PAYABLE' ? 'PAYABLE' : 'PAID'} style={input}><option value="PAID">Paid</option><option value="PAYABLE">Payable</option></select><input name="due" type="date" defaultValue={target.due_date || ''} style={input}/><input name="reference" defaultValue={target.reference || ''} style={input}/><input name="notes" defaultValue={target.notes || ''} style={input}/></div><div style={{ display:'flex',justifyContent:'flex-end',gap:6,marginTop:8 }}><button type="button" onClick={onClose} style={small()}>Cancel</button><button disabled={saving} style={button('#0284c7')}>{saving ? 'Saving…' : 'Save'}</button></div></form></div>;
}

const sectionTitle: React.CSSProperties = { fontSize: 11, fontWeight: 800, color: '#e2e8f0', marginBottom: 7 };
const grid2: React.CSSProperties = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5 };
const grid3: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 5 };
const grid4: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 5 };
const rowRow: React.CSSProperties = { display:'flex',alignItems:'center',gap:7,padding:'6px 0',borderBottom:'1px solid #1a2234',fontSize:9,minWidth:0 };
const muted: React.CSSProperties = { fontSize:8,color:'#64748b',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis' };
const overlay: React.CSSProperties = { position:'fixed',inset:0,background:'rgba(0,0,0,.72)',display:'flex',alignItems:'center',justifyContent:'center',zIndex:1000,padding:12 };
const modal: React.CSSProperties = { width:'min(680px,100%)',maxHeight:'90vh',overflowY:'auto',background:'#111827',border:'1px solid #334155',borderRadius:8,padding:14 };
function Kpi({ label, value, accent }: { label: string; value: string; accent: string }) { return <div style={{ ...panel, borderLeft:`4px solid ${accent}` }}><div style={muted}>{label}</div><div style={{ fontSize:13,fontWeight:800,color:accent,marginTop:2 }}>{value}</div></div>; }
