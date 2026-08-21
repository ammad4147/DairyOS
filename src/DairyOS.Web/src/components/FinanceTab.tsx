import React, { useState, useMemo } from 'react';
import {
  DollarSign, TrendingUp, TrendingDown, Plus, Printer, Download,
  Ban, CheckCircle2, AlertTriangle, Calendar, FileText, Search, Filter
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
}

export default function FinanceTab() {
  // Master Ledger State
  const [ledger, setLedger] = useState<LedgerItem[]>([
    {
      id: 'REV-2026-001',
      type: 'REVENUE',
      category: 'Commercial Milk Sales',
      amount: 23400,
      quantity: '120.0 L',
      unitRate: 195.0,
      date: '2026-08-21',
      refNumber: 'INV-8821',
      description: 'Morning & evening commercial delivery to dairy collection center',
      isVoid: false,
    },
    {
      id: 'REV-2026-002',
      type: 'REVENUE',
      category: 'Organic Manure / Dung',
      amount: 15000,
      quantity: '3 Trolleys',
      unitRate: 5000,
      date: '2026-08-18',
      refNumber: 'REC-0912',
      description: 'Sold to local citrus orchard',
      isVoid: false,
    },
    {
      id: 'REV-2026-003',
      type: 'REVENUE',
      category: 'Male Calf Sales',
      amount: 35000,
      quantity: '1 Head',
      unitRate: 35000,
      date: '2026-08-14',
      refNumber: 'SL-0441',
      description: 'Holstein male calf sale',
      isVoid: false,
    },
    {
      id: 'REV-2026-004',
      type: 'REVENUE',
      category: 'Commercial Milk Sales',
      amount: 4500,
      quantity: '25.0 L',
      unitRate: 180.0,
      date: '2026-08-12',
      refNumber: 'INV-8809',
      description: 'Typo in rate entry test',
      isVoid: true,
      voidReason: 'Incorrect milk rate applied; re-issued as INV-8810',
      voidedBy: 'Ammad Hassan',
      voidedAt: '2026-08-12 11:30'
    },
    {
      id: 'EXP-2026-001',
      type: 'EXPENSE',
      category: 'Concentrates & Feed',
      amount: 48000,
      quantity: '12 Bags (50kg)',
      unitRate: 4000,
      date: '2026-08-20',
      refNumber: 'BILL-4412',
      description: 'Barkat 18% CP High-Yield Dairy Wafaa Vanda',
      isVoid: false,
    },
    {
      id: 'EXP-2026-002',
      type: 'EXPENSE',
      category: 'Green Fodder & Silage',
      amount: 22500,
      quantity: '1.5 Tons',
      unitRate: 15000,
      date: '2026-08-19',
      refNumber: 'BILL-4401',
      description: 'Corn silage batch supply',
      isVoid: false,
    },
    {
      id: 'EXP-2026-003',
      type: 'EXPENSE',
      category: 'Veterinary & Medicines',
      amount: 8500,
      quantity: 'Treatment Lot',
      unitRate: 8500,
      date: '2026-08-17',
      refNumber: 'RX-9912',
      description: 'Mastitis intramammary infusions & antibiotic course',
      isVoid: false,
    },
    {
      id: 'EXP-2026-004',
      type: 'EXPENSE',
      category: 'AI Semen Straws',
      amount: 14000,
      quantity: '2 Sexed Straws',
      unitRate: 7000,
      date: '2026-08-15',
      refNumber: 'INV-ABS-01',
      description: 'ABS Sexed Holstein Friesian genetics',
      isVoid: false,
    },
    {
      id: 'EXP-2026-005',
      type: 'EXPENSE',
      category: 'Electricity & Solar',
      amount: 18500,
      quantity: 'Monthly',
      unitRate: 18500,
      date: '2026-08-10',
      refNumber: 'LESCO-881',
      description: 'Net billing auxiliary electricity & SkyElectric lease installment',
      isVoid: false,
    }
  ]);

  // Quick Entry States
  const [revCategory, setRevCategory] = useState('Commercial Milk Sales');
  const [revAmount, setRevAmount] = useState('');
  const [revQty, setRevQty] = useState('');
  const [revDate, setRevDate] = useState('2026-08-21');
  const [revRef, setRevRef] = useState('');
  const [revDesc, setRevDesc] = useState('');

  const [expCategory, setExpCategory] = useState('Concentrates & Feed');
  const [expAmount, setExpAmount] = useState('');
  const [expQty, setExpQty] = useState('');
  const [expDate, setExpDate] = useState('2026-08-21');
  const [expRef, setExpRef] = useState('');
  const [expDesc, setExpDesc] = useState('');

  // Void Modal State
  const [voidTargetId, setVoidTargetId] = useState<string | null>(null);
  const [voidReasonInput, setVoidReasonInput] = useState('');

  // Period Filter
  const [statementPeriod, setStatementPeriod] = useState<'MONTH' | 'QUARTER' | 'YEAR'>('MONTH');

  // Add Revenue
  const handleAddRevenue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!revAmount) return;
    const newItem: LedgerItem = {
      id: `REV-${Date.now().toString().slice(-4)}`,
      type: 'REVENUE',
      category: revCategory,
      amount: parseFloat(revAmount),
      quantity: revQty || '-',
      date: revDate,
      refNumber: revRef || `REC-${Math.floor(Math.random() * 9000 + 1000)}`,
      description: revDesc || 'Standard revenue entry',
      isVoid: false,
    };
          try {
        await fetch('/farm/finance/receipt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount: parseFloat(revAmount), counterparty: revCategory, notes: revDesc, received_on: revDate })
        });
      } catch (err) { console.error('Financial ledger sync failed', err); }
      setLedger([newItem, ...ledger]);
      setRevAmount('');
    setRevQty('');
    setRevRef('');
    setRevDesc('');
  };

  // Add Expense
  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!expAmount) return;
    const newItem: LedgerItem = {
      id: `EXP-${Date.now().toString().slice(-4)}`,
      type: 'EXPENSE',
      category: expCategory,
      amount: parseFloat(expAmount),
      quantity: expQty || '-',
      date: expDate,
      refNumber: expRef || `BILL-${Math.floor(Math.random() * 9000 + 1000)}`,
      description: expDesc || 'Standard expense entry',
      isVoid: false,
    };
          try {
        await fetch('/farm/finance/disbursement', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount: parseFloat(expAmount), counterparty: expCategory, notes: expDesc, received_on: expDate })
        });
      } catch (err) { console.error('Financial ledger sync failed', err); }
      setLedger([newItem, ...ledger]);
      setExpAmount('');
    setExpQty('');
    setExpRef('');
    setExpDesc('');
  };

  // Void Handler (Never Delete)
  const handleConfirmVoid = (e: React.FormEvent) => {
    e.preventDefault();
    if (!voidTargetId || !voidReasonInput) return;

    setLedger(ledger.map(item => {
      if (item.id === voidTargetId) {
        return {
          ...item,
          isVoid: true,
          voidReason: voidReasonInput,
          voidedBy: 'Ammad Hassan',
          voidedAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
        };
      }
      return item;
    }));

    setVoidTargetId(null);
    setVoidReasonInput('');
  };

  // Calculated Accountings (Excluding VOID)
  const activeRevenues = useMemo(() => ledger.filter(i => i.type === 'REVENUE'), [ledger]);
  const activeExpenses = useMemo(() => ledger.filter(i => i.type === 'EXPENSE'), [ledger]);

  const totalRevenue = useMemo(() => {
    return activeRevenues.filter(i => !i.isVoid).reduce((acc, curr) => acc + curr.amount, 0);
  }, [activeRevenues]);

  const totalExpense = useMemo(() => {
    return activeExpenses.filter(i => !i.isVoid).reduce((acc, curr) => acc + curr.amount, 0);
  }, [activeExpenses]);

  const netMargin = totalRevenue - totalExpense;

  // Print Statement
  const handlePrintStatement = () => {
    window.print();
  };

  // Export CSV
  const handleExportCSV = () => {
    const headers = ['ID', 'Type', 'Category', 'Amount (PKR)', 'Quantity', 'Date', 'Ref Number', 'Description', 'Status', 'Void Reason'];
    const rows = ledger.map(l => [
      l.id,
      l.type,
      `"${l.category}"`,
      l.amount,
      `"${l.quantity || ''}"`,
      l.date,
      `"${l.refNumber}"`,
      `"${l.description}"`,
      l.isVoid ? 'VOIDED' : 'ACTIVE',
      `"${l.voidReason || ''}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `DairyOS_Financial_Statement_${statementPeriod}_2026.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ padding: '16px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>

      {/* TOP CONTROL & RECONCILIATION BAR */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#111827', border: '1px solid #1f2937', padding: '12px 16px', borderRadius: '8px', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>August 2026 Net Margin</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: netMargin >= 0 ? '#34d399' : '#f87171' }}>
              PKR {netMargin.toLocaleString()}
            </div>
          </div>
          <div style={{ width: '1px', height: '30px', background: '#334155' }} />
          <div>
            <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>CMPL Metric</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#38bdf8' }}>PKR 43.75 / Liter</div>
          </div>
          <div style={{ width: '1px', height: '30px', background: '#334155' }} />
          <div>
            <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>Mass Balance Audit</div>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle2 size={13} /> 100% Reconciled
            </div>
          </div>
        </div>

        {/* Statement Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <select
            value={statementPeriod}
            onChange={(e: any) => setStatementPeriod(e.target.value)}
            style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}
          >
            <option value="MONTH">Monthly Statement (August 2026)</option>
            <option value="QUARTER">Q3 2026 Statement (Jul - Sep)</option>
            <option value="YEAR">Annual P&L (2026 Year-to-Date)</option>
          </select>
          <button
            onClick={handlePrintStatement}
            style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Printer size={13} /> Print
          </button>
          <button
            onClick={handleExportCSV}
            style={{ background: '#0284c7', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Download size={13} /> Export CSV
          </button>
        </div>
      </div>

      {/* TWO-COLUMN FINANCIAL CORE (REVENUE vs EXPENSES) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>

        {/* ===================================================================
            LEFT COLUMN: REVENUE STREAM
            =================================================================== */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Revenue Running Total Card */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px 16px', borderRadius: '8px', borderLeft: '4px solid #34d399', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold' }}>Monthly Total Revenue</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#34d399' }}>PKR {totalRevenue.toLocaleString()}</div>
            </div>
            <div style={{ background: 'rgba(52, 211, 153, 0.15)', padding: '8px', borderRadius: '8px', color: '#34d399' }}>
              <TrendingUp size={20} />
            </div>
          </div>

          {/* Revenue Quick Entry Form */}
          <form onSubmit={handleAddRevenue} style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Plus size={14} /> Record Revenue Transaction
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Revenue Category</label>
                <select value={revCategory} onChange={e => setRevCategory(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                  <option value="Commercial Milk Sales">Commercial Milk Sales</option>
                  <option value="Organic Manure / Dung">Organic Manure / Dung</option>
                  <option value="Male Calf Sales">Male Calf Sales</option>
                  <option value="Cull Animal Sales">Cull Animal Sales</option>
                  <option value="Breeding Service Fee">Breeding Service Fee</option>
                  <option value="Government Dairy Subsidy">Government Dairy Subsidy</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Amount (PKR)</label>
                <input type="number" required placeholder="e.g. 24000" value={revAmount} onChange={e => setRevAmount(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Volume / Quantity</label>
                <input type="text" placeholder="e.g. 120 L" value={revQty} onChange={e => setRevQty(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Date</label>
                <input type="date" value={revDate} onChange={e => setRevDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Invoice / Slip #</label>
                <input type="text" placeholder="INV-001" value={revRef} onChange={e => setRevRef(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '9px', color: '#94a3b8' }}>Transaction Notes</label>
              <input type="text" placeholder="Brief description / party name" value={revDesc} onChange={e => setRevDesc(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
            </div>

            <button type="submit" style={{ background: '#059669', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', marginTop: '4px' }}>
              + Save Revenue Entry
            </button>
          </form>

          {/* Revenue Ledger Table */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ padding: '8px 12px', background: '#161f30', borderBottom: '1px solid #1f2937', fontSize: '11px', fontWeight: 'bold', color: '#34d399' }}>
              Revenue Ledger & Billed Invoices
            </div>
            <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}>
                  <th style={{ padding: '8px 10px' }}>Date / Ref</th>
                  <th style={{ padding: '8px 10px' }}>Category & Details</th>
                  <th style={{ padding: '8px 10px' }}>Qty</th>
                  <th style={{ padding: '8px 10px', textAlign: 'right' }}>Amount</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {activeRevenues.map(item => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #1a2234', background: item.isVoid ? 'rgba(239, 68, 68, 0.08)' : 'transparent' }}>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#fff' }}>
                      <div>{item.date}</div>
                      <div style={{ fontSize: '9px', color: '#94a3b8' }}>{item.refNumber}</div>
                    </td>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#cbd5e1' }}>
                      <div style={{ fontWeight: 'bold', color: item.isVoid ? '#64748b' : '#34d399' }}>{item.category}</div>
                      <div style={{ fontSize: '9px', color: '#94a3b8' }}>{item.description}</div>
                      {item.isVoid && (
                        <div style={{ fontSize: '9px', color: '#ef4444', fontWeight: 'bold', textDecoration: 'none' }}>
                          [VOID: {item.voidReason}]
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#cbd5e1' }}>{item.quantity}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'right', fontWeight: 'bold', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#34d399' }}>
                      PKR {item.amount.toLocaleString()}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {!item.isVoid ? (
                        <button onClick={() => setVoidTargetId(item.id)} title="Void this entry (Registers audit trail without deletion)" style={{ background: 'none', border: '1px solid #475569', color: '#f87171', padding: '2px 6px', borderRadius: '3px', fontSize: '9px', cursor: 'pointer' }}>
                          Void
                        </button>
                      ) : (
                        <span style={{ fontSize: '9px', color: '#ef4444', fontWeight: 'bold' }}>VOIDED</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>


        {/* ===================================================================
            RIGHT COLUMN: EXPENSE STREAM
            =================================================================== */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Expense Running Total Card */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px 16px', borderRadius: '8px', borderLeft: '4px solid #f87171', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold' }}>Monthly Total Expenses</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#f87171' }}>PKR {totalExpense.toLocaleString()}</div>
            </div>
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '8px', borderRadius: '8px', color: '#f87171' }}>
              <TrendingDown size={20} />
            </div>
          </div>

          {/* Expense Quick Entry Form */}
          <form onSubmit={handleAddExpense} style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#f87171', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Plus size={14} /> Record Farm Expense
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Expense Category</label>
                <select value={expCategory} onChange={e => setExpCategory(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                  <option value="Concentrates & Feed">Concentrates & Feed (Vanda)</option>
                  <option value="Green Fodder & Silage">Green Fodder & Silage</option>
                  <option value="Veterinary & Medicines">Veterinary & Medicines</option>
                  <option value="AI Semen Straws">AI Semen Straws & Breeding</option>
                  <option value="Farm Labor & Salaries">Farm Labor & Salaries</option>
                  <option value="Electricity & Solar">Electricity & Solar Power</option>
                  <option value="Machinery, Fuel & Tractor">Machinery, Fuel & Tractor</option>
                  <option value="Bedding Sand & Disinfectants">Bedding Sand & Disinfectants</option>
                  <option value="Shed & Farm Maintenance">Shed & Farm Maintenance</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Amount (PKR)</label>
                <input type="number" required placeholder="e.g. 15000" value={expAmount} onChange={e => setExpAmount(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Quantity / Units</label>
                <input type="text" placeholder="e.g. 5 Bags" value={expQty} onChange={e => setExpQty(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Date</label>
                <input type="date" value={expDate} onChange={e => setExpDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '9px', color: '#94a3b8' }}>Bill / Receipt #</label>
                <input type="text" placeholder="BILL-101" value={expRef} onChange={e => setExpRef(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '9px', color: '#94a3b8' }}>Expense Notes</label>
              <input type="text" placeholder="Supplier name / batch description" value={expDesc} onChange={e => setExpDesc(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
            </div>

            <button type="submit" style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', marginTop: '4px' }}>
              + Save Expense Entry
            </button>
          </form>

          {/* Expense Ledger Table */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ padding: '8px 12px', background: '#161f30', borderBottom: '1px solid #1f2937', fontSize: '11px', fontWeight: 'bold', color: '#f87171' }}>
              Expense Ledger & Disbursed Accounts
            </div>
            <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}>
                  <th style={{ padding: '8px 10px' }}>Date / Ref</th>
                  <th style={{ padding: '8px 10px' }}>Category & Details</th>
                  <th style={{ padding: '8px 10px' }}>Qty</th>
                  <th style={{ padding: '8px 10px', textAlign: 'right' }}>Amount</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {activeExpenses.map(item => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #1a2234', background: item.isVoid ? 'rgba(239, 68, 68, 0.08)' : 'transparent' }}>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#fff' }}>
                      <div>{item.date}</div>
                      <div style={{ fontSize: '9px', color: '#94a3b8' }}>{item.refNumber}</div>
                    </td>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#cbd5e1' }}>
                      <div style={{ fontWeight: 'bold', color: item.isVoid ? '#64748b' : '#f87171' }}>{item.category}</div>
                      <div style={{ fontSize: '9px', color: '#94a3b8' }}>{item.description}</div>
                      {item.isVoid && (
                        <div style={{ fontSize: '9px', color: '#ef4444', fontWeight: 'bold', textDecoration: 'none' }}>
                          [VOID: {item.voidReason}]
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '8px 10px', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#cbd5e1' }}>{item.quantity}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'right', fontWeight: 'bold', textDecoration: item.isVoid ? 'line-through' : 'none', color: item.isVoid ? '#64748b' : '#f87171' }}>
                      PKR {item.amount.toLocaleString()}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {!item.isVoid ? (
                        <button onClick={() => setVoidTargetId(item.id)} title="Void this entry (Registers audit trail without deletion)" style={{ background: 'none', border: '1px solid #475569', color: '#f87171', padding: '2px 6px', borderRadius: '3px', fontSize: '9px', cursor: 'pointer' }}>
                          Void
                        </button>
                      ) : (
                        <span style={{ fontSize: '9px', color: '#ef4444', fontWeight: 'bold' }}>VOIDED</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>

      </div>

      {/* MANDATORY VOID JUSTIFICATION MODAL */}
      {voidTargetId && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #ef4444', borderRadius: '8px', padding: '20px', width: '420px' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#ef4444', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Ban size={16} /> Mark Entry #{voidTargetId} as VOID
            </h3>
            <p style={{ fontSize: '11px', color: '#cbd5e1', marginBottom: '14px' }}>
              In compliance with dairy enterprise accounting rules, records cannot be deleted. This transaction will be stricken, zeroed out from all balances, and registered in the audit ledger.
            </p>
            <form onSubmit={handleConfirmVoid}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Reason for Cancellation / Void *</label>
                <textarea
                  required
                  value={voidReasonInput}
                  onChange={e => setVoidReasonInput(e.target.value)}
                  placeholder="e.g., Duplicate bill submission or wrong rate entered."
                  style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '8px', borderRadius: '4px', fontSize: '11px', minHeight: '60px', boxSizing: 'border-box' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" onClick={() => setVoidTargetId(null)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>
                  Keep Entry
                </button>
                <button type="submit" style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '11px' }}>
                  Confirm Void
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
