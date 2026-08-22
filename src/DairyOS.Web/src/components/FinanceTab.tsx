import React, { useState, useMemo, useEffect } from 'react';
import {
  DollarSign, TrendingUp, TrendingDown, Plus, Printer, Download,
  Ban, CheckCircle2, AlertTriangle, Calendar, FileText, Search, Filter, Clock
} from 'lucide-react';

interface LedgerItem {
  id: string;
  type: 'REVENUE' | 'EXPENSE';
  category: string;
  amount: number;
  quantity?: string;
  unitRate?: number;
  date: string;
  refNumber: string;
  description: string;
  isVoid: boolean;
  voidReason?: string;
  voidedBy?: string;
  voidedAt?: string;
  paymentStatus?: 'RECEIVED' | 'RECEIVABLE' | 'PAID'; 
}

interface FinanceTabProps {
  onSaveSale?: (liters: number) => void;
  onUpdateReceivables?: (amount: number) => void;
}

export default function FinanceTab({ onSaveSale, onUpdateReceivables }: FinanceTabProps = {}) {
  const [ledger, setLedger] = useState<LedgerItem[]>([
    { id: 'REV-2026-001', type: 'REVENUE', category: 'Milk Sales', amount: 23400, quantity: '120.0 L', unitRate: 195.0, date: '2026-08-21', refNumber: 'INV-8821', description: 'Commercial delivery to dairy collection center', isVoid: false, paymentStatus: 'RECEIVABLE' },
    { id: 'REV-2026-002', type: 'REVENUE', category: 'Organic Manure / Dung', amount: 15000, quantity: '3 Trolleys', unitRate: 5000, date: '2026-08-18', refNumber: 'REC-0912', description: 'Sold to local citrus orchard', isVoid: false, paymentStatus: 'RECEIVED' },
    { id: 'REV-2026-003', type: 'REVENUE', category: 'Male Calf Sales', amount: 35000, quantity: '1 Head', unitRate: 35000, date: '2026-08-14', refNumber: 'SL-0441', description: 'Holstein male calf sale', isVoid: false, paymentStatus: 'RECEIVED' },
    { id: 'REV-2026-004', type: 'REVENUE', category: 'Milk Sales', amount: 4500, quantity: '25.0 L', unitRate: 180.0, date: '2026-08-12', refNumber: 'INV-8809', description: 'Typo in rate entry test', isVoid: true, voidReason: 'Incorrect milk rate applied', voidedBy: 'Ammad Hassan', voidedAt: '2026-08-12 11:30' },
    { id: 'EXP-2026-001', type: 'EXPENSE', category: 'Concentrates & Feed', amount: 48000, quantity: '12 Bags (50kg)', unitRate: 4000, date: '2026-08-20', refNumber: 'BILL-4412', description: 'Barkat 18% CP High-Yield Dairy Wafaa Vanda', isVoid: false, paymentStatus: 'PAID' },
    { id: 'EXP-2026-002', type: 'EXPENSE', category: 'Green Fodder & Silage', amount: 22500, quantity: '1.5 Tons', unitRate: 15000, date: '2026-08-19', refNumber: 'BILL-4401', description: 'Corn silage batch supply', isVoid: false, paymentStatus: 'PAID' },
  ]);

  const [revCategory, setRevCategory] = useState('Milk Sales');
  const [customRevCategory, setCustomRevCategory] = useState('');
  const [revAmount, setRevAmount] = useState('');
  const [revQty, setRevQty] = useState('');
  const [revDate, setRevDate] = useState(new Date().toISOString().split('T')[0]);
  const [revRef, setRevRef] = useState('');
  const [revDesc, setRevDesc] = useState('');
  const [revStatus, setRevStatus] = useState<'RECEIVED' | 'RECEIVABLE'>('RECEIVABLE');

  const [expCategory, setExpCategory] = useState('Concentrates & Feed');
  const [customExpCategory, setCustomExpCategory] = useState('');
  const [expAmount, setExpAmount] = useState('');
  const [expQty, setExpQty] = useState('');
  const [expDate, setExpDate] = useState(new Date().toISOString().split('T')[0]);
  const [expRef, setExpRef] = useState('');
  const [expDesc, setExpDesc] = useState('');

  const [voidTargetId, setVoidTargetId] = useState<string | null>(null);
  const [voidReasonInput, setVoidReasonInput] = useState('');
  const [statementPeriod, setStatementPeriod] = useState<'MONTH' | 'QUARTER' | 'YEAR'>('MONTH');

  const activeRevenues = useMemo(() => ledger.filter(i => i.type === 'REVENUE'), [ledger]);
  const activeExpenses = useMemo(() => ledger.filter(i => i.type === 'EXPENSE'), [ledger]);
  
  const totalCashRevenue = useMemo(() => activeRevenues.filter(i => !i.isVoid && i.paymentStatus === 'RECEIVED').reduce((acc, curr) => acc + curr.amount, 0), [activeRevenues]);
  const totalReceivables = useMemo(() => activeRevenues.filter(i => !i.isVoid && i.paymentStatus === 'RECEIVABLE').reduce((acc, curr) => acc + curr.amount, 0), [activeRevenues]);
  
  const totalExpense = useMemo(() => activeExpenses.filter(i => !i.isVoid).reduce((acc, curr) => acc + curr.amount, 0), [activeExpenses]);
  const netMargin = totalCashRevenue - totalExpense;

  useEffect(() => {
    if (onUpdateReceivables) {
      onUpdateReceivables(totalReceivables);
    }
  }, [totalReceivables, onUpdateReceivables]);

  const handleAddRevenue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!revAmount) return;
    const finalCategory = revCategory === 'Others' && customRevCategory ? customRevCategory : revCategory;
    const newItem: LedgerItem = {
      id: 'REV-' + Date.now().toString().slice(-4),
      type: 'REVENUE',
      category: finalCategory,
      amount: parseFloat(revAmount),
      quantity: revQty || '-',
      date: revDate,
      refNumber: revRef || 'REC-' + Math.floor(Math.random() * 9000 + 1000),
      description: revDesc || 'Standard revenue entry',
      isVoid: false,
      paymentStatus: revStatus
    };
    
    if (finalCategory === 'Milk Sales' && onSaveSale) {
      const parsedLiters = parseFloat(revQty);
      if (!isNaN(parsedLiters) && parsedLiters > 0) {
        onSaveSale(parsedLiters);
      }
    }

    setLedger([newItem, ...ledger]);
    setRevAmount(''); setRevQty(''); setRevRef(''); setRevDesc(''); setCustomRevCategory('');
  };

  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!expAmount) return;
    const finalCategory = expCategory === 'Others' && customExpCategory ? customExpCategory : expCategory;
    const newItem: LedgerItem = {
      id: 'EXP-' + Date.now().toString().slice(-4),
      type: 'EXPENSE',
      category: finalCategory,
      amount: parseFloat(expAmount),
      quantity: expQty || '-',
      date: expDate,
      refNumber: expRef || 'BILL-' + Math.floor(Math.random() * 9000 + 1000),
      description: expDesc || 'Standard expense entry',
      isVoid: false,
      paymentStatus: 'PAID'
    };
    setLedger([newItem, ...ledger]);
    setExpAmount(''); setExpQty(''); setExpRef(''); setExpDesc(''); setCustomExpCategory('');
  };

  const handleMarkPaid = (id: string) => {
    setLedger(ledger.map(item => {
      if (item.id === id && item.paymentStatus === 'RECEIVABLE') {
        return { ...item, paymentStatus: 'RECEIVED' };
      }
      return item;
    }));
  };

  const handleConfirmVoid = (e: React.FormEvent) => {
    e.preventDefault();
    if (!voidTargetId || !voidReasonInput) return;
    setLedger(ledger.map(item => {
      if (item.id === voidTargetId) {
        return { ...item, isVoid: true, voidReason: voidReasonInput, voidedBy: 'Ammad Hassan', voidedAt: new Date().toISOString().replace('T', ' ').slice(0, 16) };
      }
      return item;
    }));
    setVoidTargetId(null); setVoidReasonInput('');
  };

  const handlePrintStatement = () => window.print();

  return (
    <div style={{ padding: '16px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      
      {/* Top Bar */}
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', background: '#111827', border: '1px solid #1f2937', padding: '12px 16px', borderRadius: '8px', marginBottom: '14px', gap: '10px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '16px', flex: 1 }}>
          <div>
            <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>Cash Margin (Bank)</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: netMargin >= 0 ? '#34d399' : '#f87171' }}>PKR {netMargin.toLocaleString()}</div>
          </div>
          <div style={{ width: '1px', height: '30px', background: '#334155' }} />
          <div>
            <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}><Clock size={10} color="#f59e0b"/> Accounts Receivable</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#f59e0b' }}>PKR {totalReceivables.toLocaleString()}</div>
          </div>
          <div style={{ width: '1px', height: '30px', background: '#334155' }} />
          <div>
            <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>CMPL Metric</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#38bdf8' }}>PKR 43.75 / Liter</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <select value={statementPeriod} onChange={(e: any) => setStatementPeriod(e.target.value)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>
            <option value="MONTH">Monthly Statement</option>
            <option value="QUARTER">Q3 2026 Statement</option>
          </select>
          <button onClick={handlePrintStatement} style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}><Printer size={13} /> Print</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        
        {/* REVENUE SECTION */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px 16px', borderRadius: '8px', borderLeft: '4px solid #34d399', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div><div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold' }}>Total Cash Revenue</div><div style={{ fontSize: '20px', fontWeight: 'bold', color: '#34d399' }}>PKR {totalCashRevenue.toLocaleString()}</div></div>
            <div style={{ background: 'rgba(52, 211, 153, 0.15)', padding: '8px', borderRadius: '8px', color: '#34d399' }}><TrendingUp size={20} /></div>
          </div>
          <form onSubmit={handleAddRevenue} style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}><Plus size={14} /> Record Revenue</div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Revenue Category</label>
                <select value={revCategory} onChange={e => setRevCategory(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                  <option value="Milk Sales">Milk Sales</option>
                  <option value="Organic Manure / Dung">Organic Manure / Dung</option>
                  <option value="Male Calf Sales">Male Calf Sales</option>
                </select>
              </div>
              <div><label style={{ fontSize: '9px', color: '#94a3b8' }}>Amount (PKR)</label><input type="number" required placeholder="e.g. 24000" value={revAmount} onChange={e => setRevAmount(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
              <div><label style={{ fontSize: '9px', color: '#94a3b8' }}>Qty (e.g. 120.5 L)</label><input type="text" placeholder="120 L" value={revQty} onChange={e => setRevQty(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
              <div>
                <label style={{ fontSize: '9px', color: '#f59e0b' }}>Payment Status</label>
                <select value={revStatus} onChange={e => setRevStatus(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: revStatus === 'RECEIVABLE' ? '#f59e0b' : '#34d399', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>
                  <option value="RECEIVABLE">Credit (A/R)</option>
                  <option value="RECEIVED">Cash Received</option>
                </select>
              </div>
              <div><label style={{ fontSize: '9px', color: '#94a3b8' }}>Ref #</label><input type="text" placeholder="INV-001" value={revRef} onChange={e => setRevRef(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            </div>

            <button type="submit" style={{ background: '#059669', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', marginTop: '4px' }}>+ Save Revenue Entry</button>
          </form>

          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ padding: '8px 12px', background: '#161f30', borderBottom: '1px solid #1f2937', fontSize: '11px', fontWeight: 'bold', color: '#34d399' }}>Revenue Ledger</div>
            <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
              <thead><tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}><th style={{ padding: '8px 10px' }}>Date</th><th style={{ padding: '8px 10px' }}>Details</th><th style={{ padding: '8px 10px', textAlign: 'right' }}>Amount</th><th style={{ padding: '8px 10px', textAlign: 'center' }}>Action</th></tr></thead>
              <tbody>
                {activeRevenues.map(item => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #1a2234', background: item.isVoid ? 'rgba(239, 68, 68, 0.08)' : (item.paymentStatus === 'RECEIVABLE' ? 'rgba(245, 158, 11, 0.05)' : 'transparent') }}>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#fff' }}>{item.date}</td>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#cbd5e1' }}>
                      <div style={{ fontWeight: 'bold', color: item.isVoid ? '#64748b' : '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        {item.category}
                        {!item.isVoid && item.paymentStatus === 'RECEIVABLE' && <span style={{ background: '#f59e0b', color: '#111827', padding: '1px 4px', borderRadius: '3px', fontSize: '8px' }}>PENDING</span>}
                      </div>
                      <div style={{ fontSize: '9px', color: '#94a3b8' }}>{item.description}</div>
                      {item.isVoid && item.voidReason && <div style={{ fontSize: '9px', color: '#ef4444', fontWeight: 'bold', marginTop: '2px' }}>[VOID: {item.voidReason}]</div>}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right', fontWeight: 'bold', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : (item.paymentStatus === 'RECEIVABLE' ? '#f59e0b' : '#34d399') }}>PKR {item.amount.toLocaleString()}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'center', display: 'flex', gap: '4px', justifyContent: 'center' }}>
                      {!item.isVoid && item.paymentStatus === 'RECEIVABLE' && (
                         <button onClick={() => handleMarkPaid(item.id)} style={{ background: '#34d399', border: 'none', color: '#0f172a', padding: '2px 6px', borderRadius: '3px', fontSize: '9px', cursor: 'pointer', fontWeight: 'bold' }}>Paid</button>
                      )}
                      {item.isVoid && <span style={{ fontSize: '9px', color: '#ef4444', fontWeight: 'bold' }}>VOIDED</span>}
                      {!item.isVoid && <button onClick={() => setVoidTargetId(item.id)} style={{ background: 'none', border: '1px solid #475569', color: '#f87171', padding: '2px 6px', borderRadius: '3px', fontSize: '9px', cursor: 'pointer' }}>Void</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* EXPENSES SECTION */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px 16px', borderRadius: '8px', borderLeft: '4px solid #f87171', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div><div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold' }}>Monthly Total Expenses</div><div style={{ fontSize: '20px', fontWeight: 'bold', color: '#f87171' }}>PKR {totalExpense.toLocaleString()}</div></div>
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '8px', borderRadius: '8px', color: '#f87171' }}><TrendingDown size={20} /></div>
          </div>
          <form onSubmit={handleAddExpense} style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#f87171', display: 'flex', alignItems: 'center', gap: '6px' }}><Plus size={14} /> Record Expense</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Expense Category</label>
                <select value={expCategory} onChange={e => setExpCategory(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                  <option value="Concentrates & Feed">Concentrates & Feed</option>
                  <option value="Green Fodder & Silage">Green Fodder & Silage</option>
                  <option value="Veterinary & Medicines">Veterinary & Medicines</option>
                </select>
              </div>
              <div><label style={{ fontSize: '9px', color: '#94a3b8' }}>Amount (PKR)</label><input type="number" required placeholder="e.g. 15000" value={expAmount} onChange={e => setExpAmount(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
              <div><label style={{ fontSize: '9px', color: '#94a3b8' }}>Qty</label><input type="text" placeholder="120 L" value={expQty} onChange={e => setExpQty(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
              <div><label style={{ fontSize: '9px', color: '#94a3b8' }}>Date</label><input type="date" value={expDate} onChange={e => setExpDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
              <div><label style={{ fontSize: '9px', color: '#94a3b8' }}>Ref #</label><input type="text" placeholder="INV-001" value={expRef} onChange={e => setExpRef(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            </div>
            <div><label style={{ fontSize: '9px', color: '#94a3b8' }}>Notes</label><input type="text" placeholder="Description" value={expDesc} onChange={e => setExpDesc(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>

            <button type="submit" style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', marginTop: '4px' }}>+ Save Expense Entry</button>
          </form>

          {/* Corrected Expense Ledger Table */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ padding: '8px 12px', background: '#161f30', borderBottom: '1px solid #1f2937', fontSize: '11px', fontWeight: 'bold', color: '#f87171' }}>Expense Ledger</div>
            <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
              <thead><tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}><th style={{ padding: '8px 10px' }}>Date</th><th style={{ padding: '8px 10px' }}>Details</th><th style={{ padding: '8px 10px', textAlign: 'right' }}>Amount</th><th style={{ padding: '8px 10px', textAlign: 'center' }}>Action</th></tr></thead>
              <tbody>
                {activeExpenses.map(item => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #1a2234', background: item.isVoid ? 'rgba(239, 68, 68, 0.08)' : 'transparent' }}>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#fff' }}>{item.date}</td>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#cbd5e1' }}>
                      <div style={{ fontWeight: 'bold', color: item.isVoid ? '#64748b' : '#f87171' }}>{item.category}</div>
                      <div style={{ fontSize: '9px', color: '#94a3b8' }}>{item.description}</div>
                      {item.isVoid && item.voidReason && <div style={{ fontSize: '9px', color: '#ef4444', fontWeight: 'bold', marginTop: '2px' }}>[VOID: {item.voidReason}]</div>}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right', fontWeight: 'bold', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#f87171' }}>PKR {item.amount.toLocaleString()}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {item.isVoid && <span style={{ fontSize: '9px', color: '#ef4444', fontWeight: 'bold' }}>VOIDED</span>}
                      {!item.isVoid && <button onClick={() => setVoidTargetId(item.id)} style={{ background: 'none', border: '1px solid #475569', color: '#f87171', padding: '2px 6px', borderRadius: '3px', fontSize: '9px', cursor: 'pointer' }}>Void</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {voidTargetId && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #ef4444', borderRadius: '8px', padding: '20px', width: '420px' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#ef4444', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '6px' }}><Ban size={16} /> Mark Entry #{voidTargetId} as VOID</h3>
            <form onSubmit={handleConfirmVoid}>
              <textarea required value={voidReasonInput} onChange={e => setVoidReasonInput(e.target.value)} placeholder="Reason for Cancellation" style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '8px', borderRadius: '4px', fontSize: '11px', minHeight: '60px', boxSizing: 'border-box', marginBottom: '14px' }} />
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" onClick={() => setVoidTargetId(null)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>Cancel</button>
                <button type="submit" style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '11px' }}>Confirm Void</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

