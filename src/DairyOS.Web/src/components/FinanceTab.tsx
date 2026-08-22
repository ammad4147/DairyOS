import React, { useEffect, useMemo, useState } from 'react';
import { Ban, Plus, Printer, RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:8000';
type MasterCategory = 'FEED' | 'OPEX';
type LedgerFilter = 'ALL' | MasterCategory;

type TaxonomyResponse = {
  master_categories: MasterCategory[];
  taxonomies: Record<string, Record<string, string[]>>;
  items: Record<MasterCategory, string[]>;
};

type Transaction = {
  id: number;
  transaction_type: string;
  category: string;
  master_category?: MasterCategory | null;
  sub_category?: string | null;
  custom_specification?: string | null;
  amount: number;
  quantity?: number | null;
  unit?: string | null;
  unit_rate?: number | null;
  date?: string | null;
  reference?: string | null;
  payment_method?: string | null;
  counterparty?: string | null;
  vendor_name?: string | null;
  notes?: string | null;
  status?: string | null;
};

type Props = {
  onSaveSale?: (liters: number) => void;
  onUpdateReceivables?: (amount: number) => void;
};

const inputStyle: React.CSSProperties = { background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '7px 8px', borderRadius: 5, fontSize: 11, boxSizing: 'border-box', width: '100%' };
const smallButtonStyle: React.CSSProperties = { background: '#1e293b', border: '1px solid #334155', color: '#cbd5e1', padding: '4px 7px', borderRadius: 4, fontSize: 9, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 4 };
const rowStyle: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 12, padding: '9px 12px', borderBottom: '1px solid #1a2234', fontSize: 11 };
const formatPKR = (value: number) => `PKR ${value.toLocaleString('en-PK', { maximumFractionDigits: 2 })}`;
const today = () => new Date().toISOString().slice(0, 10);

export default function FinanceTab({ onSaveSale, onUpdateReceivables }: Props = {}) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [taxonomy, setTaxonomy] = useState<TaxonomyResponse | null>(null);
  const [masterCategory, setMasterCategory] = useState<MasterCategory>('FEED');
  const [subCategory, setSubCategory] = useState('');
  const [customSpecification, setCustomSpecification] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [unitRate, setUnitRate] = useState('');
  const [directAmount, setDirectAmount] = useState('');
  const [expenseDate, setExpenseDate] = useState(today());
  const [vendor, setVendor] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('BANK');
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');
  const [ledgerFilter, setLedgerFilter] = useState<LedgerFilter>('ALL');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [voidTarget, setVoidTarget] = useState<Transaction | null>(null);
  const [voidReason, setVoidReason] = useState('');
  const [revCategory, setRevCategory] = useState('Milk Sales');
  const [revAmount, setRevAmount] = useState('');
  const [revQty, setRevQty] = useState('');
  const [revDate, setRevDate] = useState(today());
  const [revRef, setRevRef] = useState('');
  const [revNotes, setRevNotes] = useState('');
  const [revStatus, setRevStatus] = useState<'RECEIVED' | 'RECEIVABLE'>('RECEIVABLE');
  const [cmpl, setCmpl] = useState<number | null>(null);

  const load = async () => {
    setLoading(true); setError('');
    try {
      const [ledgerRes, taxonomyRes, costRes] = await Promise.all([
        fetch(`${API_BASE}/farm/finance-ledger`),
        fetch(`${API_BASE}/farm/finance-ledger/taxonomy`),
        fetch(`${API_BASE}/farm/finance-ledger/cost-of-production?days=30`),
      ]);
      if (!ledgerRes.ok || !taxonomyRes.ok) throw new Error('Finance API unavailable.');
      const ledger = await ledgerRes.json();
      const tax = await taxonomyRes.json();
      setTransactions(ledger.transactions ?? []);
      setTaxonomy(tax);
      if (costRes.ok) {
        const cost = await costRes.json();
        setCmpl(cost.cmpl ?? cost.cost_per_litre ?? null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load Finance data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);
  useEffect(() => {
    const items = taxonomy?.items?.[masterCategory] ?? [];
    setSubCategory(items[0] ?? '');
    setCustomSpecification('');
  }, [masterCategory, taxonomy]);

  const expenseRows = useMemo(() => transactions.filter(t => (t.transaction_type === 'EXPENSE' || t.transaction_type === 'PAYMENT') && t.status !== 'VOID'), [transactions]);
  const revenueRows = useMemo(() => transactions.filter(t => (t.transaction_type === 'INCOME' || t.transaction_type === 'RECEIPT') && t.status !== 'VOID'), [transactions]);
  const filteredExpenses = useMemo(() => ledgerFilter === 'ALL' ? expenseRows : expenseRows.filter(t => t.master_category === ledgerFilter), [expenseRows, ledgerFilter]);
  const feedCost = expenseRows.filter(t => t.master_category === 'FEED').reduce((s, t) => s + t.amount, 0);
  const opex = expenseRows.filter(t => t.master_category === 'OPEX').reduce((s, t) => s + t.amount, 0);
  const totalExpenses = feedCost + opex;
  const cashRevenue = revenueRows.filter(t => ['RECEIVED', 'RECORDED', 'PAID'].includes(String(t.status))).reduce((s, t) => s + t.amount, 0);
  const receivables = revenueRows.filter(t => t.status === 'RECEIVABLE').reduce((s, t) => s + t.amount, 0);
  const netMargin = cashRevenue - totalExpenses;
  const calculatedAmount = quantity && unitRate ? Number(quantity) * Number(unitRate) : Number(directAmount || 0);

  useEffect(() => { onUpdateReceivables?.(receivables); }, [receivables, onUpdateReceivables]);

  const saveExpense = async (event: React.FormEvent) => {
    event.preventDefault(); setSaving(true); setError('');
    try {
      const response = await fetch(`${API_BASE}/farm/finance-ledger`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_type: 'EXPENSE', master_category: masterCategory, sub_category: subCategory,
          custom_specification: subCategory === 'Other' ? customSpecification : null,
          quantity: quantity ? Number(quantity) : null, unit: quantity ? unit : null,
          unit_rate: quantity ? Number(unitRate) : null, amount: calculatedAmount,
          transaction_date: expenseDate, payment_method: paymentMethod, counterparty: vendor || null,
          reference: reference || null, notes: notes || null, status: paymentMethod === 'CREDIT' ? 'PAYABLE' : 'PAID',
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Expense could not be saved.');
      await load(); setQuantity(''); setUnitRate(''); setDirectAmount(''); setVendor(''); setReference(''); setNotes(''); setCustomSpecification('');
    } catch (err) { setError(err instanceof Error ? err.message : 'Expense save failed.'); }
    finally { setSaving(false); }
  };

  const saveRevenue = async (event: React.FormEvent) => {
    event.preventDefault(); const amount = Number(revAmount); if (!amount || amount <= 0) return;
    setSaving(true); setError('');
    try {
      const response = await fetch(`${API_BASE}/farm/finance-ledger`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_type: revStatus === 'RECEIVED' ? 'RECEIPT' : 'INCOME', amount,
          transaction_date: revDate, payment_method: revStatus === 'RECEIVABLE' ? 'CREDIT' : 'CASH', status: revStatus,
          reference: revRef || null, notes: `${revCategory}${revNotes ? ` — ${revNotes}` : ''}`,
        }),
      });
      const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Revenue could not be saved.');
      if (revCategory === 'Milk Sales' && revQty && onSaveSale) onSaveSale(Number(revQty));
      await load(); setRevAmount(''); setRevQty(''); setRevRef(''); setRevNotes('');
    } catch (err) { setError(err instanceof Error ? err.message : 'Revenue save failed.'); }
    finally { setSaving(false); }
  };

  const updateStatus = async (transaction: Transaction, status: string, reason?: string) => {
    try {
      const response = await fetch(`${API_BASE}/farm/finance-ledger/${transaction.id}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status, reason }) });
      const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Status update failed.');
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Status update failed.'); }
    finally { setVoidTarget(null); setVoidReason(''); }
  };

  const subItems = taxonomy?.items?.[masterCategory] ?? [];

  return (
    <div style={{ padding: 16, color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 14 }}>
        <div><div style={{ fontSize: 20, fontWeight: 800 }}>Finance</div><div style={{ fontSize: 11, color: '#94a3b8' }}>One persistent ledger • Feed and OPEX analytical streams</div></div>
        <button onClick={() => void load()} style={smallButtonStyle}><RefreshCw size={13}/> Refresh</button>
      </div>
      {error && <div style={{ background: 'rgba(239,68,68,.12)', border: '1px solid #ef4444', color: '#fecaca', padding: 9, borderRadius: 6, marginBottom: 12, fontSize: 11 }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,minmax(0,1fr))', gap: 8, marginBottom: 14 }}>
        {[
          ['Cash Revenue', cashRevenue, '#34d399'], ['Feed Cost', feedCost, '#38bdf8'], ['OPEX', opex, '#f59e0b'],
          ['Total Expenses', totalExpenses, '#f87171'], ['Net Margin', netMargin, netMargin >= 0 ? '#34d399' : '#f87171'], ['CMPL', cmpl ?? 0, '#a78bfa'],
        ].map(([label, value, color]) => <div key={String(label)} style={{ background:'#111827', border:'1px solid #1f2937', borderLeft:`4px solid ${color}`, borderRadius:7, padding:'10px 12px' }}><div style={{fontSize:9,color:'#94a3b8',textTransform:'uppercase'}}>{label}</div><div style={{fontSize:17,fontWeight:800,color}}>{label === 'CMPL' ? `${formatPKR(Number(value))}/L` : formatPKR(Number(value))}</div></div>)}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          <form onSubmit={saveRevenue} style={{background:'#111827',border:'1px solid #1f2937',borderRadius:8,padding:12}}>
            <div style={{fontSize:12,fontWeight:800,color:'#34d399',marginBottom:9}}>Record Revenue</div>
            <div style={{display:'grid',gridTemplateColumns:'1.2fr 1fr 1fr',gap:7}}>
              <select value={revCategory} onChange={e=>setRevCategory(e.target.value)} style={inputStyle}><option>Milk Sales</option><option>Organic Manure / Dung</option><option>Male Calf Sales</option></select>
              <input type="number" min="0" step="0.01" required placeholder="Amount" value={revAmount} onChange={e=>setRevAmount(e.target.value)} style={inputStyle}/>
              <input type="number" min="0" step="0.01" placeholder="Qty (L)" value={revQty} onChange={e=>setRevQty(e.target.value)} style={inputStyle}/>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:7,marginTop:7}}>
              <input type="date" value={revDate} onChange={e=>setRevDate(e.target.value)} style={inputStyle}/>
              <select value={revStatus} onChange={e=>setRevStatus(e.target.value as any)} style={inputStyle}><option value="RECEIVABLE">Credit / Receivable</option><option value="RECEIVED">Cash Received</option></select>
              <input placeholder="Reference" value={revRef} onChange={e=>setRevRef(e.target.value)} style={inputStyle}/>
            </div>
            <input placeholder="Notes" value={revNotes} onChange={e=>setRevNotes(e.target.value)} style={{...inputStyle,width:'100%',marginTop:7}}/>
            <button disabled={saving} type="submit" style={buttonStyle('#059669')}>{saving?'Saving…':'Save Revenue'}</button>
          </form>
          <div style={{background:'#111827',border:'1px solid #1f2937',borderRadius:8,overflow:'hidden'}}>
            <div style={{padding:'9px 12px',fontSize:11,fontWeight:800,color:'#34d399',borderBottom:'1px solid #1f2937'}}>Revenue Ledger</div>
            {revenueRows.slice(0,30).map(row => <div key={row.id} style={rowStyle}><div style={{flex:1}}><strong>{row.notes || row.category}</strong><div style={{fontSize:9,color:'#64748b'}}>{row.date?.slice(0,10)} • {row.reference || 'No reference'}</div></div><div style={{fontWeight:800,color:row.status==='RECEIVABLE'?'#f59e0b':'#34d399'}}>{formatPKR(row.amount)}</div>{row.status==='RECEIVABLE' && <button onClick={()=>void updateStatus(row,'RECEIVED')} style={smallButtonStyle}>Paid</button>}</div>)}
            {!loading && revenueRows.length===0 && <div style={{padding:14,color:'#64748b',fontSize:11}}>No persisted revenue entries.</div>}
          </div>
        </div>

        <div style={{display:'flex',flexDirection:'column',gap:12}}>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8}}>{(['FEED','OPEX'] as MasterCategory[]).map(cat=><button key={cat} onClick={()=>setMasterCategory(cat)} style={{...modeButton,background:masterCategory===cat?'#0ea5e9':'#111827',borderColor:masterCategory===cat?'#7dd3fc':'#334155'}}>{cat==='FEED'?'Feed Cost':'OPEX'}{masterCategory===cat?' • ACTIVE':''}</button>)}</div>
          <form onSubmit={saveExpense} style={{background:'#111827',border:'1px solid #1f2937',borderRadius:8,padding:12}}>
            <div style={{fontSize:12,fontWeight:800,color:masterCategory==='FEED'?'#38bdf8':'#f59e0b',marginBottom:9}}>Record {masterCategory === 'FEED' ? 'Feed Cost' : 'OPEX'}</div>
            <div style={{display:'grid',gridTemplateColumns:'1.5fr 1fr',gap:7}}><select required value={subCategory} onChange={e=>setSubCategory(e.target.value)} style={inputStyle}>{subItems.map(item=><option key={item}>{item}</option>)}</select>{subCategory==='Other' ? <input required placeholder="Custom Specification" value={customSpecification} onChange={e=>setCustomSpecification(e.target.value)} style={inputStyle}/> : <input placeholder="Vendor / Supplier" value={vendor} onChange={e=>setVendor(e.target.value)} style={inputStyle}/>}</div>
            {subCategory==='Other' && <input placeholder="Vendor / Supplier" value={vendor} onChange={e=>setVendor(e.target.value)} style={{...inputStyle,width:'100%',marginTop:7}}/>}
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr 1fr',gap:7,marginTop:7}}><input type="number" min="0" step="0.001" placeholder="Quantity" value={quantity} onChange={e=>setQuantity(e.target.value)} style={inputStyle}/><select value={unit} onChange={e=>setUnit(e.target.value)} style={inputStyle}><option>kg</option><option>bag</option><option>ton</option><option>litre</option><option>service</option><option>head</option><option>month</option><option>bill</option><option>unit</option></select><input type="number" min="0" step="0.01" placeholder="Unit Rate" value={unitRate} onChange={e=>setUnitRate(e.target.value)} style={inputStyle} disabled={!quantity}/><input type="number" min="0" step="0.01" placeholder={quantity?'Calculated':'Amount'} value={quantity ? (calculatedAmount || '') : directAmount} onChange={e=>quantity?undefined:setDirectAmount(e.target.value)} style={{...inputStyle,background:'#0f172a',fontWeight:800}} readOnly={Boolean(quantity)}/></div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:7,marginTop:7}}><input type="date" value={expenseDate} onChange={e=>setExpenseDate(e.target.value)} style={inputStyle}/><select value={paymentMethod} onChange={e=>setPaymentMethod(e.target.value)} style={inputStyle}><option value="BANK">Bank</option><option value="CASH">Cash</option><option value="MOBILE">Mobile</option><option value="CREDIT">Credit / Payable</option></select><input placeholder="Reference" value={reference} onChange={e=>setReference(e.target.value)} style={inputStyle}/></div>
            <input placeholder="Notes" value={notes} onChange={e=>setNotes(e.target.value)} style={{...inputStyle,width:'100%',marginTop:7}}/>
            <button disabled={saving} type="submit" style={buttonStyle(masterCategory==='FEED'?'#0284c7':'#d97706')}>{saving?'Saving…':'Save Expense'}</button>
          </form>
        </div>
      </div>

      <div style={{marginTop:14,background:'#111827',border:'1px solid #1f2937',borderRadius:8,overflow:'hidden'}}>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'9px 12px',borderBottom:'1px solid #1f2937'}}><div style={{fontSize:11,fontWeight:800}}>Unified Expense Ledger</div><div style={{display:'flex',gap:6}}>{(['ALL','FEED','OPEX'] as LedgerFilter[]).map(f=><button key={f} onClick={()=>setLedgerFilter(f)} style={{...smallButtonStyle,background:ledgerFilter===f?'#0ea5e9':'#1e293b',color:'#fff'}}>{f}</button>)}<button onClick={()=>window.print()} style={smallButtonStyle}><Printer size={11}/></button></div></div>
        {loading && <div style={{padding:14,color:'#94a3b8',fontSize:11}}>Loading persistent ledger…</div>}
        {!loading && filteredExpenses.slice(0,100).map(row => <div key={row.id} style={{...rowStyle,opacity:row.status==='VOID'?.55:1}}><div style={{minWidth:110}}><div style={{fontSize:9,color:'#64748b'}}>{row.date?.slice(0,10)}</div><strong style={{color:row.master_category==='FEED'?'#38bdf8':'#f59e0b'}}>{row.master_category || 'LEGACY'}</strong></div><div style={{flex:1}}><div style={{fontWeight:700}}>{row.sub_category || row.category}{row.custom_specification ? ` — ${row.custom_specification}` : ''}</div><div style={{fontSize:9,color:'#64748b'}}>{row.vendor_name || 'No vendor'} • {row.payment_method || 'No payment'}{row.notes ? ` • ${row.notes}` : ''}</div></div><div style={{textAlign:'right',minWidth:100}}><div style={{fontWeight:800}}>{formatPKR(row.amount)}</div><div style={{fontSize:9,color:'#64748b'}}>{row.quantity ? `${row.quantity} ${row.unit || ''} @ ${row.unit_rate}` : 'Direct amount'}</div></div>{row.status !== 'VOID' && <button onClick={()=>setVoidTarget(row)} style={{...smallButtonStyle,color:'#f87171'}}><Ban size={11}/></button>}</div>)}
        {!loading && filteredExpenses.length===0 && <div style={{padding:14,color:'#64748b',fontSize:11}}>No expenses match the selected view.</div>}
      </div>

      {voidTarget && <div style={{position:'fixed',inset:0,background:'rgba(0,0,0,.72)',display:'flex',alignItems:'center',justifyContent:'center',zIndex:1000}}><div style={{background:'#111827',border:'1px solid #ef4444',borderRadius:8,padding:18,width:380}}><div style={{fontWeight:800,color:'#ef4444',marginBottom:8}}>Void Finance Entry #{voidTarget.id}</div><textarea required value={voidReason} onChange={e=>setVoidReason(e.target.value)} placeholder="Reason" style={{...inputStyle,width:'100%',minHeight:70}}/><div style={{display:'flex',justifyContent:'flex-end',gap:7,marginTop:10}}><button onClick={()=>setVoidTarget(null)} style={smallButtonStyle}>Cancel</button><button disabled={!voidReason.trim()} onClick={()=>void updateStatus(voidTarget,'VOID',voidReason)} style={buttonStyle('#dc2626')}>Confirm Void</button></div></div></div>}
    </div>
  );
}

const modeButton: React.CSSProperties = { color:'#fff', border:'1px solid #334155', padding:'10px 12px', borderRadius:7, fontSize:12, fontWeight:800, cursor:'pointer' };
const buttonStyle = (background:string): React.CSSProperties => ({ background, color:'#fff', border:'none', padding:'8px 12px', borderRadius:5, fontSize:11, fontWeight:800, cursor:'pointer', marginTop:8, width:'100%' });
