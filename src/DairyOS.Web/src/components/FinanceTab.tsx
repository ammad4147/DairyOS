import React, { useState } from 'react';
import { DollarSign, ArrowUpCircle, ArrowDownCircle, PlusCircle, FileText, Users, ShoppingCart, CreditCard } from 'lucide-react';

interface Transaction {
  id: string;
  type: 'INCOME' | 'EXPENSE';
  category: string;
  amount: number;
  buyerOrVendor?: string;
  quantityLiters?: number;
  ratePerLiter?: number;
  paymentStatus: 'PAID' | 'CREDIT';
  operator: string;
  notes?: string;
  date: string;
}

export default function FinanceTab() {
  const [activeSubTab, setActiveSubTab] = useState<'LEDGER' | 'MILK_SALES' | 'RECEIVABLES' | 'PAYABLES'>('LEDGER');
  const [txType, setTxType] = useState<'EXPENSE' | 'INCOME'>('EXPENSE');
  const [category, setCategory] = useState('Feed Purchases (Silage, Hay, Concentrates)');
  const [amount, setAmount] = useState('');
  const [buyerOrVendor, setBuyerOrVendor] = useState('');
  const [quantityLiters, setQuantityLiters] = useState('');
  const [ratePerLiter, setRatePerLiter] = useState('');
  const [paymentStatus, setPaymentStatus] = useState<'PAID' | 'CREDIT'>('PAID');
  const [operator, setOperator] = useState('Ammad Hassan');
  const [notes, setNotes] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Initial robust transactions reflecting best commercial dairy practices
  const [transactions, setTransactions] = useState<Transaction[]>([
    { id: "TX-501", type: "INCOME", category: "Commercial Milk Sales", amount: 165000, buyerOrVendor: "Lahore Fresh Dairies", quantityLiters: 600, ratePerLiter: 275, paymentStatus: "PAID", operator: "Ammad Hassan", notes: "Morning wholesale batch", date: "2026-08-20" },
    { id: "TX-502", type: "INCOME", category: "Commercial Milk Sales", amount: 84000, buyerOrVendor: "Model Town Retail Hub", quantityLiters: 280, ratePerLiter: 300, paymentStatus: "CREDIT", operator: "Ammad Hassan", notes: "Credit delivery due Friday", date: "2026-08-20" },
    { id: "TX-503", type: "EXPENSE", category: "Feed Purchases (Silage, Hay, Concentrates)", amount: 450000, buyerOrVendor: "Punjab Feed Mills", paymentStatus: "CREDIT", operator: "Ammad Hassan", notes: "Corn silage bulk order (Invoice #902)", date: "2026-08-18" },
    { id: "TX-504", type: "EXPENSE", category: "Veterinary, Medicine & AI Services", amount: 45000, buyerOrVendor: "Dr. Aslam Veterinary Clinic", paymentStatus: "PAID", operator: "Ammad Hassan", notes: "Routine vaccination & minerals", date: "2026-08-19" },
    { id: "TX-505", type: "EXPENSE", category: "Utilities (Electricity, Water, Fuel)", amount: 110000, buyerOrVendor: "WAPDA / Diesel Supplier", paymentStatus: "PAID", operator: "Ammad Hassan", notes: "Tube well & parlor electricity", date: "2026-08-19" }
  ]);

  const expenseCategories = [
    'Feed Purchases (Silage, Hay, Concentrates)',
    'Veterinary, Medicine & AI Services',
    'Utilities (Electricity, Water, Fuel)',
    'Labor & Staff Wages',
    'Repairs & Maintenance (Equipment, Sheds)',
    'Transport & Logistics',
    'Miscellaneous Farm Overhead'
  ];

  const incomeCategories = [
    'Commercial Milk Sales',
    'Livestock Sale (Cows/Heifers)',
    'Calf / Bull Sale',
    'Manure & Organic Compost Sale',
    'Agricultural Subsidies / Grants',
    'Miscellaneous Farm Revenue'
  ];

  // Auto-calculate amount when milk sale quantity and rate are provided
  const handleQuantityChange = (val: string) => {
    setQuantityLiters(val);
    const q = parseFloat(val) || 0;
    const r = parseFloat(ratePerLiter) || 0;
    if (q > 0 && r > 0) {
      setAmount((q * r).toString());
    }
  };

  const handleRateChange = (val: string) => {
    setRatePerLiter(val);
    const q = parseFloat(quantityLiters) || 0;
    const r = parseFloat(val) || 0;
    if (q > 0 && r > 0) {
      setAmount((q * r).toString());
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsedAmount = parseFloat(amount);
    if (!parsedAmount || parsedAmount <= 0) return;

    const newTx: Transaction = {
      id: `TX-${Date.now().toString().slice(-4)}`,
      type: txType,
      category,
      amount: parsedAmount,
      buyerOrVendor,
      quantityLiters: category === 'Commercial Milk Sales' ? parseFloat(quantityLiters) || 0 : undefined,
      ratePerLiter: category === 'Commercial Milk Sales' ? parseFloat(ratePerLiter) || 0 : undefined,
      paymentStatus,
      operator,
      notes,
      date: new Date().toISOString().split('T')[0]
    };

    setTransactions([newTx, ...transactions]);
    setSuccessMsg(`Successfully posted ${txType.toLowerCase()} transaction to segregated ledger.`);
    setAmount('');
    setBuyerOrVendor('');
    setQuantityLiters('');
    setRatePerLiter('');
    setNotes('');
    setTimeout(() => setSuccessMsg(''), 4000);
  };

  // Financial calculations
  const totalRevenue = transactions.filter(t => t.type === 'INCOME').reduce((acc, t) => acc + t.amount, 0);
  const totalExpense = transactions.filter(t => t.type === 'EXPENSE').reduce((acc, t) => acc + t.amount, 0);
  const netBalance = totalRevenue - totalExpense;

  // Receivables & Payables
  const accountsReceivable = transactions.filter(t => t.type === 'INCOME' && t.paymentStatus === 'CREDIT');
  const accountsPayable = transactions.filter(t => t.type === 'EXPENSE' && t.paymentStatus === 'CREDIT');
  const totalReceivableAmount = accountsReceivable.reduce((acc, t) => acc + t.amount, 0);
  const totalPayableAmount = accountsPayable.reduce((acc, t) => acc + t.amount, 0);

  // Milk Sales Reconciliation Metrics
  const totalMilkSoldLiters = transactions
    .filter(t => t.category === 'Commercial Milk Sales')
    .reduce((acc, t) => acc + (t.quantityLiters || 0), 0);
  const farmTotalProductionLiters = 1236; // Daily baseline production
  const domesticAndCalfUsageLiters = 45;
  const reconcilableSoldPercentage = ((totalMilkSoldLiters / (farmTotalProductionLiters - domesticAndCalfUsageLiters)) * 100).toFixed(1);

  return (
    <div style={{ padding: '16px', color: '#f8fafc', height: 'calc(100vh - 100px)', overflowY: 'auto', boxSizing: 'border-box' }}>
      
      {/* Header & Financial KPI Summary Cards */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid #1e293b', paddingBottom: '12px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DollarSign size={20}/> Commercial Dairy Financial Ledger & Receivables
          </h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
            Segregated revenue and operating expenses with multi-buyer rate differentiation, milk reconciliation, and credit tracking.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <div style={{ background: '#1e293b', padding: '6px 10px', borderRadius: '6px', borderLeft: '3px solid #10b981' }}>
            <div style={{ fontSize: '9px', color: '#94a3b8' }}>Total Revenue</div>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399' }}>PKR {totalRevenue.toLocaleString()}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '6px 10px', borderRadius: '6px', borderLeft: '3px solid #ef4444' }}>
            <div style={{ fontSize: '9px', color: '#94a3b8' }}>Total Expenses</div>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#fca5a5' }}>PKR {totalExpense.toLocaleString()}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '6px 10px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
            <div style={{ fontSize: '9px', color: '#94a3b8' }}>Net Balance</div>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: netBalance >= 0 ? '#38bdf8' : '#f87171' }}>PKR {netBalance.toLocaleString()}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '6px 10px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}>
            <div style={{ fontSize: '9px', color: '#fb923c' }}>Accounts Receivable</div>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#fb923c' }}>PKR {totalReceivableAmount.toLocaleString()}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '6px 10px', borderRadius: '6px', borderLeft: '3px solid #f43f5e' }}>
            <div style={{ fontSize: '9px', color: '#f43f5e' }}>Accounts Payable</div>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#f43f5e' }}>PKR {totalPayableAmount.toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button onClick={() => setActiveSubTab('LEDGER')} style={{ background: activeSubTab === 'LEDGER' ? '#38bdf8' : '#1e293b', color: activeSubTab === 'LEDGER' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <FileText size={13}/> Segregated Ledger
        </button>
        <button onClick={() => setActiveSubTab('MILK_SALES')} style={{ background: activeSubTab === 'MILK_SALES' ? '#38bdf8' : '#1e293b', color: activeSubTab === 'MILK_SALES' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <ShoppingCart size={13}/> Milk Sales & Reconciliation ({totalMilkSoldLiters} L Sold)
        </button>
        <button onClick={() => setActiveSubTab('RECEIVABLES')} style={{ background: activeSubTab === 'RECEIVABLES' ? '#38bdf8' : '#1e293b', color: activeSubTab === 'RECEIVABLES' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Users size={13}/> Accounts Receivable ({accountsReceivable.length})
        </button>
        <button onClick={() => setActiveSubTab('PAYABLES')} style={{ background: activeSubTab === 'PAYABLES' ? '#38bdf8' : '#1e293b', color: activeSubTab === 'PAYABLES' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <CreditCard size={13}/> Accounts Payable ({accountsPayable.length})
        </button>
      </div>

      {successMsg && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '8px 12px', borderRadius: '6px', marginBottom: '14px', fontSize: '12px' }}>
          {successMsg}
        </div>
      )}

      {/* Main Content Area */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: '16px' }}>
        
        {/* Left: Transaction Posting Form */}
        <form onSubmit={handleSubmit} style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '10px', height: 'fit-content' }}>
          <h3 style={{ margin: '0 0 4px 0', fontSize: '13px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <PlusCircle size={15} color="#38bdf8"/> Post Financial Entry
          </h3>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', marginBottom: '3px' }}>Transaction Classification</label>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button type="button" onClick={() => { setTxType('EXPENSE'); setCategory(expenseCategories[0]); }} style={{ flex: 1, background: txType === 'EXPENSE' ? '#ef4444' : '#1e293b', color: '#fff', border: 'none', padding: '7px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                <ArrowDownCircle size={13}/> Operating Expense
              </button>
              <button type="button" onClick={() => { setTxType('INCOME'); setCategory(incomeCategories[0]); }} style={{ flex: 1, background: txType === 'INCOME' ? '#10b981' : '#1e293b', color: '#fff', border: 'none', padding: '7px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                <ArrowUpCircle size={13}/> Farm Revenue
              </button>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', marginBottom: '3px' }}>Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', outline: 'none' }}>
              {(txType === 'EXPENSE' ? expenseCategories : incomeCategories).map(cat => <option key={cat} value={cat}>{cat}</option>)}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', marginBottom: '3px' }}>{txType === 'INCOME' ? 'Buyer / Customer Name' : 'Supplier / Vendor Name'}</label>
            <input type="text" required value={buyerOrVendor} onChange={e => setBuyerOrVendor(e.target.value)} placeholder={txType === 'INCOME' ? 'e.g. Lahore Fresh Dairies' : 'e.g. Punjab Feed Mills'} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box', outline: 'none' }} />
          </div>

          {/* Conditional Milk Sales Quantity & Rate fields */}
          {category === 'Commercial Milk Sales' && (
            <div style={{ background: '#161f30', padding: '8px', borderRadius: '6px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ fontSize: '10px', color: '#38bdf8', fontWeight: 'bold' }}>🥛 Milk Sale Rate & Quantity Audit</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '9px', color: '#94a3b8', marginBottom: '2px' }}>Quantity (Liters)</label>
                  <input type="number" value={quantityLiters} onChange={e => handleQuantityChange(e.target.value)} placeholder="0" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '9px', color: '#94a3b8', marginBottom: '2px' }}>Rate (PKR / Liter)</label>
                  <input type="number" value={ratePerLiter} onChange={e => handleRateChange(e.target.value)} placeholder="0.00" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '6px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
                </div>
              </div>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', marginBottom: '3px' }}>Total Amount (PKR)</label>
            <input type="number" step="0.01" required value={amount} onChange={e => setAmount(e.target.value)} placeholder="0.00" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box', outline: 'none' }} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', marginBottom: '3px' }}>Payment Settlement Status</label>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button type="button" onClick={() => setPaymentStatus('PAID')} style={{ flex: 1, background: paymentStatus === 'PAID' ? '#10b981' : '#1e293b', color: '#fff', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer', fontWeight: 'bold' }}>Settled (Cash/Bank)</button>
              <button type="button" onClick={() => setPaymentStatus('CREDIT')} style={{ flex: 1, background: paymentStatus === 'CREDIT' ? '#fb923c' : '#1e293b', color: '#fff', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer', fontWeight: 'bold' }}>On Credit (Due)</button>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', marginBottom: '3px' }}>Operator</label>
            <input type="text" required value={operator} onChange={e => setOperator(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box', outline: 'none' }} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '10px', color: '#94a3b8', marginBottom: '3px' }}>Notes / Invoice Details</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Additional transaction notes..." style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', height: '50px', boxSizing: 'border-box', outline: 'none' }} />
          </div>

          <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '9px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12px' }}>
            <PlusCircle size={15}/> Post Transaction
          </button>
        </form>

        {/* Right: Dynamic Sub-Tab Viewport */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column', minHeight: '420px' }}>
          
          {activeSubTab === 'LEDGER' && (
            <>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <FileText size={15} color="#38bdf8"/> Segregated Master Financial Ledger
              </h3>
              <div style={{ flex: 1, overflowY: 'auto', maxHeight: '430px' }}>
                <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}>
                      <th style={{ padding: '6px' }}>Type</th>
                      <th style={{ padding: '6px' }}>Category & Entity</th>
                      <th style={{ padding: '6px' }}>Status</th>
                      <th style={{ padding: '6px', textAlign: 'right' }}>Amount (PKR)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map(tx => (
                      <tr key={tx.id} style={{ borderBottom: '1px solid #1a2234' }}>
                        <td style={{ padding: '8px 6px' }}>
                          <span style={{ background: tx.type === 'INCOME' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)', color: tx.type === 'INCOME' ? '#34d399' : '#fca5a5', padding: '2px 5px', borderRadius: '4px', fontSize: '9px', fontWeight: 'bold' }}>
                            {tx.type}
                          </span>
                        </td>
                        <td style={{ padding: '8px 6px', color: '#e2e8f0' }}>
                          <div style={{ fontWeight: 'bold' }}>{tx.category}</div>
                          <div style={{ fontSize: '10px', color: '#38bdf8' }}>{tx.buyerOrVendor} {tx.quantityLiters ? `(${tx.quantityLiters}L @ ${tx.ratePerLiter} PKR)` : ''}</div>
                        </td>
                        <td style={{ padding: '8px 6px' }}>
                          <span style={{ color: tx.paymentStatus === 'PAID' ? '#34d399' : '#fb923c', fontSize: '10px', fontWeight: 'bold' }}>{tx.paymentStatus}</span>
                        </td>
                        <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 'bold', color: tx.type === 'INCOME' ? '#34d399' : '#fff' }}>
                          {tx.type === 'INCOME' ? '+' : '-'}{tx.amount.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {activeSubTab === 'MILK_SALES' && (
            <>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShoppingCart size={15} color="#38bdf8"/> Milk Sales & Production Reconciliation Audit
              </h3>
              <div style={{ background: '#1e293b', padding: '12px', borderRadius: '6px', marginBottom: '14px', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Total Farm Milk Produced:</span> <strong>{farmTotalProductionLiters} Liters</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Domestic & Calf Consumption:</span> <strong>{domesticAndCalfUsageLiters} Liters</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Total Commercial Milk Sold:</span> <strong style={{ color: '#34d399' }}>{totalMilkSoldLiters} Liters</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #334155', paddingTop: '6px' }}><span style={{ color: '#38bdf8' }}>Reconciled Sales Ratio:</span> <strong style={{ color: '#38bdf8' }}>{reconcilableSoldPercentage}% of marketable yield</strong></div>
              </div>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}>
                      <th style={{ padding: '6px' }}>Buyer Name</th>
                      <th style={{ padding: '6px' }}>Quantity</th>
                      <th style={{ padding: '6px' }}>Rate/L</th>
                      <th style={{ padding: '6px', textAlign: 'right' }}>Total Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.filter(t => t.category === 'Commercial Milk Sales').map(t => (
                      <tr key={t.id} style={{ borderBottom: '1px solid #1a2234' }}>
                        <td style={{ padding: '8px 6px', color: '#e2e8f0', fontWeight: 'bold' }}>{t.buyerOrVendor}</td>
                        <td style={{ padding: '8px 6px', color: '#38bdf8' }}>{t.quantityLiters} L</td>
                        <td style={{ padding: '8px 6px', color: '#cbd5e1' }}>PKR {t.ratePerLiter}</td>
                        <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 'bold', color: '#34d399' }}>PKR {t.amount.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {activeSubTab === 'RECEIVABLES' && (
            <>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Users size={15} color="#fb923c"/> Accounts Receivable (Customer Credit Dues)
              </h3>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                {accountsReceivable.length === 0 ? (
                  <p style={{ color: '#94a3b8', fontSize: '12px' }}>No outstanding customer receivables.</p>
                ) : (
                  <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}>
                        <th style={{ padding: '6px' }}>Customer / Buyer</th>
                        <th style={{ padding: '6px' }}>Details</th>
                        <th style={{ padding: '6px', textAlign: 'right' }}>Outstanding Due (PKR)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {accountsReceivable.map(t => (
                        <tr key={t.id} style={{ borderBottom: '1px solid #1a2234' }}>
                          <td style={{ padding: '8px 6px', color: '#e2e8f0', fontWeight: 'bold' }}>{t.buyerOrVendor}</td>
                          <td style={{ padding: '8px 6px', color: '#94a3b8' }}>{t.category}</td>
                          <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 'bold', color: '#fb923c' }}>PKR {t.amount.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}

          {activeSubTab === 'PAYABLES' && (
            <>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CreditCard size={15} color="#f43f5e"/> Accounts Payable (Supplier & Vendor Liabilities)
              </h3>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                {accountsPayable.length === 0 ? (
                  <p style={{ color: '#94a3b8', fontSize: '12px' }}>No outstanding vendor payables.</p>
                ) : (
                  <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}>
                        <th style={{ padding: '6px' }}>Supplier / Vendor</th>
                        <th style={{ padding: '6px' }}>Expense Category</th>
                        <th style={{ padding: '6px', textAlign: 'right' }}>Liability Due (PKR)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {accountsPayable.map(t => (
                        <tr key={t.id} style={{ borderBottom: '1px solid #1a2234' }}>
                          <td style={{ padding: '8px 6px', color: '#e2e8f0', fontWeight: 'bold' }}>{t.buyerOrVendor}</td>
                          <td style={{ padding: '8px 6px', color: '#94a3b8' }}>{t.category}</td>
                          <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 'bold', color: '#f43f5e' }}>PKR {t.amount.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}

        </div>

      </div>
    </div>
  );
}
