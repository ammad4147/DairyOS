import React, { useEffect, useMemo, useState } from 'react';
import { Ban, Edit3, Printer, Search, WalletCards } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

type MasterCategory = 'FEED' | 'OPEX';
type LedgerFilter = 'ALL' | MasterCategory;
type ExploreView = 'COMBINED' | 'REVENUE' | 'EXPENSES';
type PeriodMode = 'MONTH' | 'CUSTOM';
type RevenueStatus = 'RECEIVED' | 'RECEIVABLE';

type TaxonomyResponse = {
  master_categories: MasterCategory[];
  taxonomies: Record<MasterCategory, Record<string, string[]>>;
  items: Record<MasterCategory, string[]>;
};

type Transaction = {
  id: number;
  transaction_type: string;
  category?: string | null;
  master_category?: MasterCategory | null;
  sub_category?: string | null;
  custom_specification?: string | null;
  amount: number;
  quantity?: number | null;
  unit?: string | null;
  unit_rate?: number | null;
  date?: string | null;
  transaction_date?: string | null;
  reference?: string | null;
  payment_method?: string | null;
  counterparty?: string | null;
  vendor_name?: string | null;
  notes?: string | null;
  status?: string | null;
  due_date?: string | null;
  settled_date?: string | null;
};

type HerdAnimal = {
  id: string;
  breed: string;
  category: string;
  status: string;
};

type Props = {
  herdMasterList?: HerdAnimal[];
  onAnimalChanged?: () => void | Promise<void>;
  onOpenPayroll?: () => void;
};

const inputStyle: React.CSSProperties = {
  background: '#1e293b',
  color: '#fff',
  border: '1px solid #334155',
  padding: '7px 8px',
  borderRadius: 5,
  fontSize: 11,
  boxSizing: 'border-box',
  width: '100%',
};

const smallButton: React.CSSProperties = {
  background: '#1e293b',
  border: '1px solid #334155',
  color: '#cbd5e1',
  padding: '4px 7px',
  borderRadius: 4,
  fontSize: 9,
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 4,
};

const button = (bg: string): React.CSSProperties => ({
  background: bg,
  color: '#fff',
  border: 0,
  borderRadius: 5,
  padding: '8px 12px',
  fontSize: 10,
  fontWeight: 800,
  cursor: 'pointer',
});

const card: React.CSSProperties = {
  background: '#111827',
  border: '1px solid #1f2937',
  borderRadius: 8,
  padding: 10,
  minWidth: 0,
};

const sectionTitle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 800,
  marginBottom: 7,
};

const row: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  padding: '7px 8px',
  borderBottom: '1px solid #1a2234',
  fontSize: 10,
  minWidth: 0,
};

const ledgerLine: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  flex: 1,
  minWidth: 0,
  whiteSpace: 'nowrap',
};

const ledgerEllipsis: React.CSSProperties = {
  flex: '1 1 0',
  minWidth: 0,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
};

const voidReasonStyle: React.CSSProperties = {
  fontSize: 8,
  color: '#fca5a5',
  fontWeight: 800,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
};

const empty: React.CSSProperties = {
  padding: 14,
  color: '#64748b',
  fontSize: 10,
  textAlign: 'center',
};

const modalBackdrop: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0,0,0,.72)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: 16,
};

const modalCard: React.CSSProperties = {
  background: '#111827',
  border: '1px solid #334155',
  borderRadius: 8,
  padding: 16,
  width: 'min(720px,100%)',
  maxHeight: '90vh',
  overflowY: 'auto',
};

const revenueHeaderCell: React.CSSProperties = {
  padding: '6px 8px',
  color: '#94a3b8',
  fontSize: 8,
  fontWeight: 800,
  textTransform: 'uppercase',
  textAlign: 'left',
  borderBottom: '1px solid #334155',
  whiteSpace: 'nowrap',
};

const revenueCell: React.CSSProperties = {
  padding: '7px 8px',
  borderBottom: '1px solid #1a2234',
  verticalAlign: 'middle',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
};

const pakistanDateFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Karachi',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

const today = () => pakistanDateFormatter.format(new Date());
const monthStartFor = (iso: string) => `${iso.slice(0, 7)}-01`;
const monthEndFor = (iso: string) => {
  const [year, month] = iso.slice(0, 7).split('-').map(Number);
  return new Date(Date.UTC(year, month, 0)).toISOString().slice(0, 10);
};

const inRange = (value: string | undefined | null, start: string, end: string) => {
  const d = String(value || '').slice(0, 10);
  return Boolean(d && d >= start && d <= end);
};

const isRevenue = (t: Transaction) =>
  t.transaction_type === 'INCOME' || t.transaction_type === 'RECEIPT';
const isExpense = (t: Transaction) =>
  t.transaction_type === 'EXPENSE' || t.transaction_type === 'PAYMENT';
const activeAmount = (t: Transaction) =>
  String(t.status || '').toUpperCase() === 'VOID' ? 0 : Number(t.amount || 0);

const money = (value: number) =>
  `PKR ${Number(value || 0).toLocaleString('en-PK', { maximumFractionDigits: 2 })}`;

const csvCell = (value: unknown) =>
  `"${String(value ?? '').replace(/"/g, '""')}"`;

const voidReasonFromNotes = (notes?: string | null) => {
  const matches = Array.from(String(notes ?? '').matchAll(/REASON=([^\n\r]*)/g));
  return matches.length ? matches[matches.length - 1][1].trim() : '';
};

const groupLabel = (value: string) =>
  value
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, letter => letter.toUpperCase());

export default function FinanceTab({
  herdMasterList = [],
  onAnimalChanged,
  onOpenPayroll,
}: Props = {}) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [taxonomy, setTaxonomy] = useState<TaxonomyResponse | null>(null);
  const [masterCategory, setMasterCategory] = useState<MasterCategory>('FEED');
  const [expenseGroup, setExpenseGroup] = useState('');
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
  const [dueDate, setDueDate] = useState('');
  const [ledgerFilter, setLedgerFilter] = useState<LedgerFilter>('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [voidTarget, setVoidTarget] = useState<Transaction | null>(null);
  const [voidReason, setVoidReason] = useState('');
  const [editTarget, setEditTarget] = useState<Transaction | null>(null);
  const [editSaving, setEditSaving] = useState(false);
  const [revCategory, setRevCategory] = useState('Milk Sales');
  const [revAnimalId, setRevAnimalId] = useState('');
  const [revAmount, setRevAmount] = useState('');
  const [revQty, setRevQty] = useState('');
  const [revDate, setRevDate] = useState(today());
  const [revRef, setRevRef] = useState('');
  const [revCounterparty, setRevCounterparty] = useState('');
  const [revNotes, setRevNotes] = useState('');
  const [revStatus, setRevStatus] = useState<RevenueStatus>('RECEIVABLE');
  const [revDueDate, setRevDueDate] = useState('');
  const [exploreOpen, setExploreOpen] = useState(false);
  const [exploreView, setExploreView] = useState<ExploreView>('COMBINED');
  const [exploreExpenseFilter, setExploreExpenseFilter] = useState<LedgerFilter>('ALL');
  const [explorePeriodMode, setExplorePeriodMode] = useState<PeriodMode>('MONTH');
  const [exploreMonth, setExploreMonth] = useState(today().slice(0, 7));
  const [exploreStart, setExploreStart] = useState(monthStartFor(today()));
  const [exploreEnd, setExploreEnd] = useState(today());
  const [statusPeriodMode, setStatusPeriodMode] = useState<'ALL' | 'MONTH' | 'CUSTOM'>('ALL');
  const [statusMonth, setStatusMonth] = useState(today().slice(0, 7));
  const [statusStart, setStatusStart] = useState(monthStartFor(today()));
  const [statusEnd, setStatusEnd] = useState(today());

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [ledgerRes, taxRes] = await Promise.all([
        fetch(`${API_BASE}/farm/finance-ledger`),
        fetch(`${API_BASE}/farm/finance-ledger/taxonomy`),
      ]);
      if (!ledgerRes.ok || !taxRes.ok) {
        throw new Error('Finance API unavailable.');
      }
      const ledger = await ledgerRes.json();
      const tax = await taxRes.json();
      setTransactions(ledger.transactions ?? []);
      setTaxonomy(tax);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load Finance data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    const groups = Object.keys(taxonomy?.taxonomies?.[masterCategory] ?? {});
    const firstGroup = groups[0] ?? '';
    const firstItem = firstGroup
      ? (taxonomy?.taxonomies?.[masterCategory]?.[firstGroup]?.[0] ?? '')
      : '';
    setExpenseGroup(firstGroup);
    setSubCategory(firstItem);
    setCustomSpecification('');
  }, [masterCategory, taxonomy]);

  const currentTaxonomy = taxonomy?.taxonomies?.[masterCategory] ?? {};
  const groupedTaxonomyEntries = Object.entries(taxonomy?.taxonomies?.[masterCategory] ?? {}) as [string, string[]][];
  const expenseGroups = groupedTaxonomyEntries.map(([group]) => group);
  const expenseItems = expenseGroup ? (currentTaxonomy[expenseGroup] ?? []) : [];

  const selectExpenseGroup = (nextGroup: string) => {
    setExpenseGroup(nextGroup);
    setSubCategory(currentTaxonomy[nextGroup]?.[0] ?? '');
    setCustomSpecification('');
  };

  const expenseRows = useMemo(() => transactions.filter(isExpense), [transactions]);
  const activeExpenseRows = useMemo(
    () => expenseRows.filter(t => t.status !== 'VOID'),
    [expenseRows],
  );
  const revenueRows = useMemo(() => transactions.filter(isRevenue), [transactions]);
  const activeRevenueRows = useMemo(
    () => revenueRows.filter(t => t.status !== 'VOID'),
    [revenueRows],
  );

  const currentMonthStart = monthStartFor(today());
  const currentMonthEnd = monthEndFor(today());
  const currentMonthExpenseRows = useMemo(
    () => expenseRows.filter(t => inRange(t.date, currentMonthStart, currentMonthEnd)),
    [expenseRows, currentMonthStart, currentMonthEnd],
  );
  const currentMonthRevenueRows = useMemo(
    () => revenueRows.filter(t => inRange(t.date, currentMonthStart, currentMonthEnd)),
    [revenueRows, currentMonthStart, currentMonthEnd],
  );

  const filteredExpenses = useMemo(() => {
    const q = search.trim().toLowerCase();
    const base = ledgerFilter === 'ALL'
      ? currentMonthExpenseRows
      : currentMonthExpenseRows.filter(t => t.master_category === ledgerFilter);
    return base.filter(t => !q || [
      t.sub_category,
      t.custom_specification,
      t.vendor_name,
      t.counterparty,
      t.reference,
      t.notes,
      t.status,
    ].some(v => String(v ?? '').toLowerCase().includes(q)));
  }, [currentMonthExpenseRows, ledgerFilter, search]);

  const cashRevenue = activeRevenueRows
    .filter(t => ['RECEIVED', 'RECORDED', 'PAID'].includes(String(t.status)))
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const receivables = activeRevenueRows
    .filter(t => t.status === 'RECEIVABLE')
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const totalExpenses = activeExpenseRows.reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const payableTotal = activeExpenseRows
    .filter(t => t.status === 'PAYABLE')
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const netCash = cashRevenue - totalExpenses;


  const exploreBounds = useMemo(
    () => explorePeriodMode === 'MONTH'
      ? { start: `${exploreMonth}-01`, end: monthEndFor(`${exploreMonth}-01`) }
      : { start: exploreStart, end: exploreEnd },
    [explorePeriodMode, exploreMonth, exploreStart, exploreEnd],
  );

  const exploredRows = useMemo(() => transactions.filter(t => {
    if (!inRange(t.date, exploreBounds.start, exploreBounds.end)) return false;
    if (exploreView === 'REVENUE' && !isRevenue(t)) return false;
    if (exploreView === 'EXPENSES' && !isExpense(t)) return false;
    if (isExpense(t) && exploreExpenseFilter !== 'ALL' && t.master_category !== exploreExpenseFilter) return false;
    return isRevenue(t) || isExpense(t);
  }).sort((a, b) => String(a.date || '').localeCompare(String(b.date || '')) || a.id - b.id), [transactions, exploreBounds, exploreView, exploreExpenseFilter]);

  const carriedForward = useMemo(
    () => transactions
      .filter(t => String(t.date || '').slice(0, 10) < exploreBounds.start)
      .reduce((sum, t) => sum + (isRevenue(t) ? activeAmount(t) : isExpense(t) ? -activeAmount(t) : 0), 0),
    [transactions, exploreBounds.start],
  );
  const periodRevenue = useMemo(
    () => exploredRows.filter(isRevenue).reduce((sum, t) => sum + activeAmount(t), 0),
    [exploredRows],
  );
  const periodExpenses = useMemo(
    () => exploredRows.filter(isExpense).reduce((sum, t) => sum + activeAmount(t), 0),
    [exploredRows],
  );
  const periodNet = periodRevenue - periodExpenses;
  const closingBalance = carriedForward + periodNet;

  const statusBounds = useMemo(() => {
    if (statusPeriodMode === 'MONTH') return { start: `${statusMonth}-01`, end: monthEndFor(`${statusMonth}-01`) };
    if (statusPeriodMode === 'CUSTOM') return { start: statusStart, end: statusEnd };
    return { start: '0001-01-01', end: today() };
  }, [statusPeriodMode, statusMonth, statusStart, statusEnd]);
  const statusRows = useMemo(
    () => transactions.filter(t => inRange(t.date, statusBounds.start, statusBounds.end)),
    [transactions, statusBounds],
  );
  const statusRevenue = useMemo(
    () => statusRows.filter(isRevenue).reduce((sum, t) => sum + activeAmount(t), 0),
    [statusRows],
  );
  const statusExpenses = useMemo(
    () => statusRows.filter(isExpense).reduce((sum, t) => sum + activeAmount(t), 0),
    [statusRows],
  );
  const statusBalance = statusRevenue - statusExpenses;
  const graphMax = Math.max(statusRevenue, statusExpenses, 1);

  const calculatedAmount = quantity && unitRate
    ? Number(quantity) * Number(unitRate)
    : Number(directAmount || 0);

  const requiresCustomSpecification=subCategory==='Other'||subCategory==='Equipment Purchase';

  const ledgerParticulars = (t: Transaction) => t.sub_category || t.category || '—';
  const ledgerCounterparty = (t: Transaction) => t.counterparty || t.vendor_name || '—';
  const ledgerReference = (t: Transaction) => t.reference || '—';
  const ledgerStatus = (t: Transaction) => t.status || 'RECORDED';
  const ledgerQuantity= (t: Transaction) => {
    const qty = Number(t.quantity || 0);
    if (!(qty > 0)) return '—';
    const formatted = qty.toLocaleString('en-PK', { maximumFractionDigits: 2 });
    if (String(t.category || '').toUpperCase() === 'MILK_SALES') {
      return `${formatted} L`;
    }
    const recordedUnit = String(t.unit || '').trim();
    return recordedUnit ? `${formatted} ${recordedUnit}` : formatted;
  };

  const revenueCategoryLabels: Record<string, string> = {
    MILK_SALES:'Milk Sales',
    MANURE_SALES: 'Organic Manure / Dung',
    MILKING_ANIMAL_SALE: 'Milking Animal Sale',
    DRY_ANIMAL_SALE: 'Dry Animal Sale',
    HEIFER_SALE: 'Heifer Sale',
    FEMALE_CALF_SALE: 'Female Calf Sale',
    MALE_CALF_SALE:'Male Calf Sale',
    BULL_SALE: 'Bull Sale',
    OTHER_REVENUE: 'Other Revenue',
  };

  const revenueParticulars = (t: Transaction) => {
    const category = String(t.category || 'OTHER_REVENUE').toUpperCase();
    return revenueCategoryLabels[category] || ledgerParticulars(t);
  };

  const revenueAnimalId= (t: Transaction) => {
    const match = String(t.notes || '').match(/\bAnimal\s+([A-Za-z0-9_-]+)/i);
    return match?.[1] || '';
  };

  const saveRevenueLedgerCsv=(
    rows: Transaction[],
    start: string,
    end: string,
    summary: Record<string, number> = {},
  ) => {
    const header = ['Date', 'Particulars', 'Quantity', 'Buyer / Customer', 'Reference', 'Status', 'Amount'];
    const detailRows = rows.map(t => {
      const animalId = revenueAnimalId(t);
      const particulars = animalId
        ? `${revenueParticulars(t)} — Animal ${animalId}`
        : revenueParticulars(t);

      return [
        String(t.date || '').slice(0, 10),
        particulars,
        ledgerQuantity(t),
        ledgerCounterparty(t),
        ledgerReference(t),
        ledgerStatus(t),
        Number(t.amount || 0).toFixed(2),
      ];
    });
    const summaryRows = [
      [],
      ...Object.entries(summary).map(([labelText, value]) => [
        labelText,
        '',
        '',
        '',
        '',
        '',
        Number(value || 0).toFixed(2),
      ]),
    ];
    const csv = [
      ['DairyOS — Revenue Ledger'],
      ['Reporting Period', `${start} to ${end}`],
      [],
      header,
      ...detailRows,
      ...summaryRows,
    ]
      .map(line => line.map(csvCell).join(','))
      .join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `DairyOS-Revenue-Ledger-${start}-to-${end}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const saveLedgerCsv=(
    title: string,
    rows: Transaction[],
    start: string,
    end: string,
    summary: Record<string, number> = {},
  ) => {
    const header = ['Date', 'Type', 'Particulars', 'Master Category', 'Counterparty', 'Reference', 'Status', 'Amount'];
    const detailRows = rows.map(t => [
      String(t.date || '').slice(0, 10),
      isRevenue(t) ? 'Revenue' : 'Expense',
      ledgerParticulars(t),
      t.master_category || '',
      ledgerCounterparty(t),
      ledgerReference(t),
      ledgerStatus(t),
      Number(t.amount || 0).toFixed(2),
    ]);
    const summaryRows = [
      [],
      ...Object.entries(summary).map(([labelText, value]) => [
        labelText,
        '',
        '',
        '',
        '',
        '',
        '',
        Number(value || 0).toFixed(2),
      ]),
    ];
    const csv = [
      [title],
      ['Reporting Period', `${start} to ${end}`],
      [],
      header,
      ...detailRows,
      ...summaryRows,
    ]
      .map(line => line.map(csvCell).join(','))
      .join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const safeTitle = title.replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');
    link.href = url;
    link.download = `DairyOS-${safeTitle}-${start}-to-${end}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const saveExploredLedger = () => {
    saveLedgerCsv('Finance Ledger Explorer', exploredRows, exploreBounds.start, exploreBounds.end, {
      'Carried Forward': carriedForward,
      'Period Revenue': periodRevenue,
      'Period Expenses': periodExpenses,
      'Period Net': periodNet,
      'Closing Balance': closingBalance,
    });
  };


  const printRevenueLedger=(
    rows: Transaction[],
    start: string,
    end: string,
    summary: Record<string, number> = {},
  ) => {
    const popup = window.open('', '_blank', 'width=1100,height=800');
    if (!popup) {
      setError('The Revenue Ledger print window was blocked. Allow pop-ups for DairyOS and try again.');
      return;
    }
    const esc = (value: unknown) => String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    } as Record<string, string>)[ch] || ch);
    const tableRows = rows.map(t => {
      const isVoid = String(t.status || '').toUpperCase() === 'VOID';
      const reason = isVoid ? voidReasonFromNotes(t.notes) : '';
      const animalId = revenueAnimalId(t);
      const particulars = animalId
        ? `${revenueParticulars(t)} — Animal ${animalId}`
        : revenueParticulars(t);

      return `
        <tr class="${isVoid ? 'void' : ''}">
          <td>${esc(String(t.date || '').slice(0, 10) || '—')}</td>
          <td>${esc(particulars)}${reason ? `<div class="void-reason">VOID: ${esc(reason)}</div>` : ''}</td>
          <td class="quantity">${esc(ledgerQuantity(t))}</td>
          <td>${esc(ledgerCounterparty(t))}</td>
          <td>${esc(ledgerReference(t))}</td>
          <td>${esc(ledgerStatus(t))}</td>
          <td class="amount">${esc(money(Number(t.amount || 0)))}</td>
        </tr>`;
    }).join('');
    const summaryHtml = Object.keys(summary).length
      ? `<div class="summary">${Object.entries(summary).map(([labelText, value]) => `
          <div class="summary-row"><span>${esc(labelText)}</span><strong>${esc(money(Number(value || 0)))}</strong></div>`).join('')}</div>`
      : '';

    popup.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>DairyOS — Revenue Ledger</title><style>
      @page{size:A4 landscape;margin:12mm}*{box-sizing:border-box}body{margin:0;color:#111827;font-family:Arial,Helvetica,sans-serif;font-size:11px}h1{margin:0 0 4px;font-size:18px}.period{margin-bottom:14px;color:#475569}table{width:100%;border-collapse:collapse}th,td{padding:7px 8px;border-bottom:1px solid #cbd5e1;text-align:left;vertical-align:top}th{background:#f1f5f9;font-size:9px;text-transform:uppercase}.quantity,.amount{text-align:right;white-space:nowrap}tr.void td{color:#b91c1c;background:#fef2f2;text-decoration:line-through}tr.void .void-reason{text-decoration:none}.void-reason{margin-top:3px;color:#b91c1c;font-size:9px;font-weight:bold}.summary{width:380px;margin-top:16px;margin-left:auto;border-top:2px solid #334155}.summary-row{display:flex;justify-content:space-between;gap:20px;padding:5px 2px;border-bottom:1px solid #e2e8f0}.footer{margin-top:14px;color:#64748b;font-size:9px}
    </style></head><body><h1>DairyOS — Revenue Ledger</h1><div class="period">Reporting period: ${esc(start)} to ${esc(end)}</div><table><thead><tr><th>Date</th><th>Particulars</th><th style="text-align:right">Quantity</th><th>Buyer / Customer</th><th>Reference</th><th>Status</th><th style="text-align:right">Amount</th></tr></thead><tbody>${tableRows || '<tr><td colspan="7">No revenue entries in this period.</td></tr>'}</tbody></table>${summaryHtml}<div class="footer">Generated from the DairyOS Revenue Ledger. VOID transactions remain visible for audit history and are excluded from active totals.</div></body></html>`);
    popup.document.close();
    popup.focus();
    window.setTimeout(() => popup.print(), 250);
  };

  const printLedger=(
    title: string,
    rows: Transaction[],
    start: string,
    end: string,
    summary: Record<string, number> = {},
  ) => {
    const popup = window.open('', '_blank', 'width=1100,height=800');
    if (!popup) {
      setError('The ledger print window was blocked. Allow pop-ups for DairyOS and try again.');
      return;
    }
    const esc = (value: unknown) => String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    } as Record<string, string>)[ch] || ch);
    const tableRows = rows.map(t => {
      const isVoid = String(t.status || '').toUpperCase() === 'VOID';
      const reason = isVoid ? voidReasonFromNotes(t.notes) : '';
      return `
        <tr class="${isVoid ? 'void' : ''}">
          <td>${esc(String(t.date || '').slice(0, 10) || '—')}</td>
          <td>${esc(isRevenue(t) ? 'Revenue' : 'Expense')}</td>
          <td>${esc(ledgerParticulars(t))}${reason ? `<div class="void-reason">VOID: ${esc(reason)}</div>` : ''}</td>
          <td>${esc(t.master_category || '—')}</td>
          <td>${esc(ledgerCounterparty(t))}</td>
          <td>${esc(ledgerReference(t))}</td>
          <td>${esc(ledgerStatus(t))}</td>
          <td class="amount">${esc(money(Number(t.amount || 0)))}</td>
        </tr>`;
    }).join('');
    const summaryHtml = Object.keys(summary).length
      ? `<div class="summary">${Object.entries(summary).map(([labelText, value]) => `
          <div class="summary-row"><span>${esc(labelText)}</span><strong>${esc(money(Number(value || 0)))}</strong></div>`).join('')}</div>`
      : '';
    popup.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${esc(title)}</title><style>
      @page{size:A4 landscape;margin:12mm}*{box-sizing:border-box}body{margin:0;color:#111827;font-family:Arial,Helvetica,sans-serif;font-size:11px}h1{margin:0 0 4px;font-size:18px}.period{margin-bottom:14px;color:#475569}table{width:100%;border-collapse:collapse}th,td{padding:6px 7px;border-bottom:1px solid #cbd5e1;text-align:left;vertical-align:top}th{background:#f1f5f9;font-size:9px;text-transform:uppercase}.amount{text-align:right;white-space:nowrap}tr.void td{color:#b91c1c;background:#fef2f2;text-decoration:line-through}tr.void .void-reason{text-decoration:none}.void-reason{margin-top:3px;color:#b91c1c;font-size:9px;font-weight:bold}.summary{width:380px;margin-top:16px;margin-left:auto;border-top:2px solid #334155}.summary-row{display:flex;justify-content:space-between;gap:20px;padding:5px 2px;border-bottom:1px solid #e2e8f0}.footer{margin-top:14px;color:#64748b;font-size:9px}
    </style></head><body><h1>DairyOS — ${esc(title)}</h1><div class="period">Reporting period: ${esc(start)} to ${esc(end)}</div><table><thead><tr><th>Date</th><th>Type</th><th>Particulars</th><th>Master Category</th><th>Counterparty</th><th>Reference</th><th>Status</th><th style="text-align:right">Amount</th></tr></thead><tbody>${tableRows || '<tr><td colspan="8">No ledger entries in this selected view.</td></tr>'}</tbody></table>${summaryHtml}<div class="footer">Generated from the selected DairyOS ledger only. VOID transactions remain visible for audit history and are excluded from active totals.</div></body></html>`);
    popup.document.close();
    popup.focus();
    window.setTimeout(() => popup.print(), 250);
  };


  const saveExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const status = paymentMethod === 'CREDIT' ? 'PAYABLE' : 'PAID';
      const response = await fetch(`${API_BASE}/farm/finance-ledger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_type: 'EXPENSE',
          master_category: masterCategory,
          sub_category: subCategory,
          custom_specification:requiresCustomSpecification?customSpecification:null,
          quantity: quantity ? Number(quantity) : null,
          unit: quantity ? unit : null,
          unit_rate: quantity ? Number(unitRate) : null,
          amount: calculatedAmount,
          transaction_date: expenseDate,
          payment_method: paymentMethod,
          counterparty: vendor || null,
          reference: reference || null,
          notes: notes || null,
          status,
          due_date: status === 'PAYABLE' ? dueDate : null,
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Expense could not be saved.');
      setQuantity('');
      setUnitRate('');
      setDirectAmount('');
      setVendor('');
      setReference('');
      setNotes('');
      setCustomSpecification('');
      setDueDate('');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Expense save failed.');
    } finally {
      setSaving(false);
    }
  };

  const animalSaleCategories: Record<string, string> = {
    'Milking Animal Sale': 'MILKING_ANIMAL_SALE',
    'Dry Animal Sale': 'DRY_ANIMAL_SALE',
    'Heifer Sale': 'HEIFER_SALE',
    'Female Calf Sale': 'FEMALE_CALF_SALE',
    'Male Calf Sale': 'MALE_CALF_SALE',
    'Bull Sale': 'BULL_SALE',
  };
  const isAnimalSale = Boolean(animalSaleCategories[revCategory]);
  const saleEligibleAnimals = useMemo(() => {
    if (!isAnimalSale) return [];
    const wanted: Record<string, string[]> = {
      'Milking Animal Sale': ['milking'],
      'Dry Animal Sale': ['dry'],
      'Heifer Sale': ['heifer'],
      'Female Calf Sale': ['female', 'calf'],
      'Male Calf Sale': ['male', 'calf'],
      'Bull Sale': ['bull'],
    };
    const tokens = wanted[revCategory] || [];
    return herdMasterList.filter(a => {
      const hay = `${a.category} ${a.status}`.toLowerCase();
      return tokens.every(token => hay.includes(token));
    });
  }, [herdMasterList, isAnimalSale, revCategory]);

  useEffect(() => {
    if (!isAnimalSale) {
      setRevAnimalId('');
      return;
    }
    if (revAnimalId && !saleEligibleAnimals.some(a => a.id === revAnimalId)) {
      setRevAnimalId('');
    }
  }, [isAnimalSale, revAnimalId, saleEligibleAnimals]);

  const saveRevenue = async (e: React.FormEvent) => {
    e.preventDefault();
    const amount = Number(revAmount);
    if (!(amount > 0)) return;
    if (isAnimalSale && !revAnimalId) {
      setError('Select the Animal ID being sold.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const categoryMap: Record<string, string> = {
        'Milk Sales': 'MILK_SALES',
        'Organic Manure / Dung': 'MANURE_SALES',
        ...animalSaleCategories,
      };
      const response = await fetch(`${API_BASE}/farm/finance-ledger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_type: revStatus === 'RECEIVED' ? 'RECEIPT' : 'INCOME',
          category: categoryMap[revCategory] ?? 'OTHER_REVENUE',
          amount,
          quantity: revQty ? Number(revQty) : null,
          unit: revCategory === 'Milk Sales' && revQty ? 'litres' : null,
          transaction_date: revDate,
          payment_method: revStatus === 'RECEIVABLE' ? 'CREDIT' : 'CASH',
          counterparty: revCounterparty || null,
          status: revStatus,
          due_date: revStatus === 'RECEIVABLE' ? revDueDate : null,
          reference: revRef || null,
          notes: isAnimalSale
            ? `${revCategory} — Animal ${revAnimalId}${revNotes ? ` — ${revNotes}` : ''}`
            : (revNotes || null),
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Revenue could not be saved.');

      if (isAnimalSale) {
        const disposition = await fetch(`${API_BASE}/farm/animals/${encodeURIComponent(revAnimalId)}/disposition`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            disposition: 'SOLD',
            effective_date: revDate,
            reason: `Recorded through Finance: ${revCategory}`,
            buyer_or_counterparty:revCounterparty||null,
            amount,
            reference: revRef || `FIN-${body.id || 'SALE'}`,
            notes: revNotes || null,
            operator: 'Finance UI',
          }),
        });
        if (!disposition.ok) {
          try {
            await fetch(`${API_BASE}/farm/finance-ledger/${body.id}/status`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                status:'VOID',
                reason: 'Animal sale disposition failed; Finance row automatically revoked for reconciliation.',
              }),
            });
          } catch {}
          throw new Error((await disposition.text()) || 'Animal sale could not be linked to the Animal Passport. Finance row was revoked.');
        }
        try {
          await onAnimalChanged?.();
        } catch {}
      }
      setRevAnimalId('');
      setRevAmount('');
      setRevQty('');
      setRevRef('');
      setRevCounterparty('');
      setRevNotes('');
      setRevDueDate('');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Revenue save failed.');
    } finally {
      setSaving(false);
    }
  };

  const updateStatus = async (t: Transaction, status: string, reason?: string) => {
    try {
      const response = await fetch(`${API_BASE}/farm/finance-ledger/${t.id}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, reason }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Status update failed.');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Status update failed.');
    } finally {
      setVoidTarget(null);
      setVoidReason('');
    }
  };

  const saveEdit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editTarget) return;
    setEditSaving(true);
    setError('');
    try {
      const form = new FormData(e.currentTarget);
      const qty = Number(form.get('quantity') || 0);
      const rate = Number(form.get('unit_rate') || 0);
      const amount = qty > 0 ? qty * rate : Number(form.get('amount') || 0);
      const response = await fetch(`${API_BASE}/farm/finance-ledger/${editTarget.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          master_category: form.get('master_category'),
          sub_category: form.get('sub_category'),
          custom_specification: form.get('custom_specification') || null,
          quantity: qty > 0 ? qty : null,
          unit: qty > 0 ? String(form.get('unit') || 'kg') : null,
          unit_rate: qty > 0 ? rate : null,
          amount,
          transaction_date: form.get('transaction_date'),
          payment_method: form.get('payment_method'),
          counterparty: form.get('counterparty'),
          reference: form.get('reference'),
          notes: form.get('notes'),
          status: form.get('status'),
          due_date: form.get('due_date') || null,
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'Finance entry could not be edited.');
      setEditTarget(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Finance edit failed.');
    } finally {
      setEditSaving(false);
    }
  };

  const financialCards: Array<[string, number, string]> = [
    ['Cash Revenue', cashRevenue, '#34d399'],
    ['Receivables', receivables, '#f59e0b'],
    ['Payables',payableTotal,'#fb7185'],
    ['Total Expenses', totalExpenses, '#f87171'],
    ['Net Cash Position', netCash, '#38bdf8'],
  ];

  const renderExpenseLedgerRow = (r: Transaction) => {
    const isVoid = String(r.status || '').toUpperCase() === 'VOID';
    const reason = isVoid ? voidReasonFromNotes(r.notes) : '';
    const editable = !['VOID', 'PAID', 'RECEIVED'].includes(String(r.status));
    const particulars = `${r.sub_category || r.category || '—'}${r.custom_specification ? ` — ${r.custom_specification}` : ''}`;
    return (
      <div
        key={r.id}
        style={{
          ...row,
          color: isVoid ? '#f87171' : '#fff',
          background: isVoid ? 'rgba(239,68,68,.06)' : 'transparent',
          borderLeft: isVoid ? '2px solid #ef4444' : undefined,
        }}
      >
        <div style={{ ...ledgerLine, textDecoration:isVoid?'line-through':'none' }}>
          <span style={{ width: 76, flex: '0 0 76px' }}>{r.date?.slice(0, 10) || '—'}</span>
          <span title={particulars} style={ledgerEllipsis}>{particulars}</span>
          <span title={r.vendor_name || r.counterparty || ''} style={{ ...ledgerEllipsis, flexBasis: 100 }}>{r.vendor_name || r.counterparty || '—'}</span>
          <span title={r.reference || ''} style={{ ...ledgerEllipsis, flexBasis: 100 }}>{r.reference || '—'}</span>
          <span style={{ width: 70, flex: '0 0 70px', fontWeight: 800 }}>{r.status || 'RECORDED'}</span>
          <strong style={{ width: 118, flex: '0 0 118px', textAlign: 'right' }}>{money(Number(r.amount || 0))}</strong>
        </div>
        {isVoid ? (
          <span title={reason || 'Reason recorded in audit trail'} style={{ ...voidReasonStyle, maxWidth: 190 }}>
            VOID: {reason||'See audit trail'}
          </span>
        ) : (
          <>
            {editable && <button type="button" onClick={() => setEditTarget(r)} style={smallButton}><Edit3 size={10} /></button>}
            <button type="button" onClick={() => setVoidTarget(r)} style={{ ...smallButton, color: '#f87171' }}><Ban size={10} /></button>
          </>
        )}
      </div>
    );
  };

  return (
    <div style={{ padding: 14, color: '#fff', height: '100%', overflowY: 'auto', overflowX: 'hidden', boxSizing: 'border-box', minWidth: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800 }}>Finance & Accounting</div>
          <div style={{ fontSize: 10, color: '#94a3b8' }}>Revenue, receivables, expenses, payables and the persistent accounting ledger.</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onOpenPayroll}
            title="Open Finance Payroll"
            disabled={!onOpenPayroll}
            style={{
              ...button('#0f766e'),
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
              opacity: onOpenPayroll ? 1 : 0.55,
              cursor: onOpenPayroll ? 'pointer' : 'not-allowed',
            }}
          >
            <WalletCards size={11} />Payroll
          </button>
          <button type="button" onClick={() => setExploreOpen(value => !value)} style={{ ...button(exploreOpen ? '#475569' : '#7c3aed'), display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <Search size={11} />{exploreOpen ? 'Close Explorer' : 'Explore Ledgers'}
          </button>
        </div>
      </div>

      {error && <div style={{ background: 'rgba(239,68,68,.12)', border: '1px solid #ef4444', color: '#fecaca', padding: 8, borderRadius: 6, marginBottom: 10, fontSize: 10 }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,minmax(0,1fr))', gap: 7, marginBottom: 10 }}>
        {financialCards.map(([cardLabel, value, color]) => (
          <div key={cardLabel} style={{ background: '#111827', border: '1px solid #1f2937', borderLeft: `4px solid ${color}`, borderRadius: 7, padding: '9px 10px', minWidth: 0 }}>
            <div style={{ fontSize: 8, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800 }}>{cardLabel}</div>
            <div style={{ fontSize: 15, fontWeight: 900, color, marginTop: 3 }}>{money(value)}</div>
          </div>
        ))}
      </div>

      {exploreOpen && (
        <section style={{ ...card, marginBottom: 10, borderColor: '#7c3aed' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 900, color: '#c4b5fd' }}>Ledger Explorer</div>
              <div style={{ fontSize: 9, color: '#94a3b8' }}>Historical accounting view. VOID rows remain visible but are excluded from balances.</div>
            </div>
            <div style={{ display: 'flex', gap: 5 }}>
              <button type="button" onClick={saveExploredLedger} style={smallButton}>Save CSV</button>
              <button type="button" onClick={() => printLedger('Finance Ledger Explorer', exploredRows, exploreBounds.start, exploreBounds.end, { 'Carried Forward': carriedForward, 'Period Revenue': periodRevenue, 'Period Expenses': periodExpenses, 'Period Net': periodNet, 'Closing Balance': closingBalance })} style={smallButton}><Printer size={11} /> Print</button>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
              {(['COMBINED', 'REVENUE', 'EXPENSES'] as ExploreView[]).map(value => (
                <button type="button" key={value} onClick={() => setExploreView(value)} style={{ ...smallButton, background: exploreView === value ? '#7c3aed' : '#1e293b', color: '#fff' }}>{value === 'COMBINED' ? 'Combined' : value === 'REVENUE' ? 'Revenue' : 'Expenses'}</button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              {(['ALL', 'FEED', 'OPEX'] as LedgerFilter[]).map(value => (
                <button type="button" key={value} onClick={() => setExploreExpenseFilter(value)} disabled={exploreView === 'REVENUE'} style={{ ...smallButton, opacity: exploreView === 'REVENUE' ? .45 : 1, background: exploreExpenseFilter === value ? '#0369a1' : '#1e293b', color: '#fff' }}>{value === 'ALL' ? 'All Expenses' : value === 'FEED' ? 'Feed-only' : 'OPEX-only'}</button>
              ))}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
            <button type="button" onClick={() => setExplorePeriodMode('MONTH')} style={{ ...smallButton, background: explorePeriodMode === 'MONTH' ? '#0f766e' : '#1e293b', color: '#fff' }}>Month</button>
            <button type="button" onClick={() => setExplorePeriodMode('CUSTOM')} style={{ ...smallButton, background: explorePeriodMode === 'CUSTOM' ? '#0f766e' : '#1e293b', color: '#fff' }}>Custom Date Range</button>
            {explorePeriodMode === 'MONTH' ? (
              <input type="month" value={exploreMonth} onChange={event => setExploreMonth(event.target.value)} style={{ ...inputStyle, width: 155 }} />
            ) : (
              <>
                <input type="date" value={exploreStart} onChange={event => setExploreStart(event.target.value)} style={{ ...inputStyle, width: 150 }} />
                <span style={{ fontSize: 9, color: '#64748b' }}>to</span>
                <input type="date" value={exploreEnd} onChange={event => setExploreEnd(event.target.value)} style={{ ...inputStyle, width: 150 }} />
              </>
            )}
            <span style={{ fontSize: 9, color: '#94a3b8' }}>{exploreBounds.start} → {exploreBounds.end}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,minmax(0,1fr))', gap: 6, marginBottom: 8 }}>
            {[
              ['Carried Forward', carriedForward, '#94a3b8'],
              ['Period Revenue', periodRevenue, '#34d399'],
              ['Period Expenses', periodExpenses, '#f87171'],
              ['Period Net', periodNet, periodNet >= 0 ? '#38bdf8' : '#f87171'],
              ['Closing Balance', closingBalance, closingBalance >= 0 ? '#a78bfa' : '#f87171'],
            ].map(([cardLabel, value, color]) => (
              <div key={String(cardLabel)} style={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: 6, padding: 8 }}>
                <div style={{ fontSize: 8, color: '#64748b', textTransform: 'uppercase', fontWeight: 800 }}>{String(cardLabel)}</div>
                <div style={{ fontSize: 12, color: String(color), fontWeight: 900, marginTop: 2 }}>{money(Number(value))}</div>
              </div>
            ))}
          </div>
          <div style={{ ...ledgerLine, color: '#64748b', fontSize: 8, fontWeight: 800, textTransform: 'uppercase', borderBottom: '1px solid #1f2937', padding: '0 8px 5px' }}>
            <span style={{ width: 76, flex: '0 0 76px' }}>Date</span><span style={{ width: 64, flex: '0 0 64px' }}>Type</span><span style={ledgerEllipsis}>Particulars</span><span style={{ ...ledgerEllipsis, flexBasis: 92 }}>Counterparty</span><span style={{ width: 76, flex: '0 0 76px' }}>Status</span><span style={{ width: 118, flex: '0 0 118px', textAlign: 'right' }}>Amount</span>
          </div>
          <div style={{ maxHeight: 310, overflowY: 'auto' }}>
            {exploredRows.map(r => {
              const isVoid = String(r.status || '').toUpperCase() === 'VOID';
              const reason = isVoid ? voidReasonFromNotes(r.notes) : '';
              return (
                <div key={`${isRevenue(r) ? 'R' : 'E'}-${r.id}`} style={{ ...row, color: isVoid ? '#f87171' : '#fff', background: isVoid ? 'rgba(239,68,68,.06)' : 'transparent' }}>
                  <div style={{ ...ledgerLine, textDecoration:isVoid?'line-through':'none' }}>
                    <span style={{ width: 76, flex: '0 0 76px' }}>{String(r.date || '').slice(0, 10) || '—'}</span>
                    <span style={{ width: 64, flex: '0 0 64px', fontWeight: 800, color: isRevenue(r) ? '#34d399' : '#f59e0b' }}>{isRevenue(r) ? 'REV' : 'EXP'}</span>
                    <span style={ledgerEllipsis}>{r.sub_category || r.category || '—'}</span>
                    <span style={{ ...ledgerEllipsis, flexBasis: 92 }}>{r.counterparty || r.vendor_name || '—'}</span>
                    <span style={{ width: 76, flex: '0 0 76px', fontWeight: 800 }}>{r.status || 'RECORDED'}</span>
                    <strong style={{ width: 118, flex: '0 0 118px', textAlign: 'right' }}>{money(Number(r.amount || 0))}</strong>
                  </div>
                  {isVoid && <span style={{ ...voidReasonStyle, maxWidth: 220 }}>VOID: {reason||'See audit trail'}</span>}
                </div>
              );
            })}
            {exploredRows.length === 0 && <div style={empty}>No ledger entries in this period/view.</div>}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', paddingTop: 8, borderTop: '1px solid #1f2937', fontSize: 10 }}>
            <strong>Period Aggregate: Revenue {money(periodRevenue)} · Expenses {money(periodExpenses)} · Net {money(periodNet)}</strong>
            <strong style={{ color: closingBalance >= 0 ? '#a78bfa' : '#f87171' }}>Closing: {money(closingBalance)}</strong>
          </div>
        </section>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: 10, alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 10 }}>
          <form onSubmit={saveRevenue} style={card}>
            <div style={sectionTitle}>Record Revenue</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 6 }}>
              <select value={revCategory} onChange={event => setRevCategory(event.target.value)} style={inputStyle}>
                <option>Milk Sales</option><option>Organic Manure / Dung</option><option>Milking Animal Sale</option><option>Dry Animal Sale</option><option>Heifer Sale</option><option>Female Calf Sale</option><option>Male Calf Sale</option><option>Bull Sale</option>
              </select>
              <input required type="number" min="0" step="0.01" value={revAmount} onChange={event => setRevAmount(event.target.value)} style={inputStyle} placeholder="Amount" />
              <input type="number" min="0" step="0.01" value={revQty} onChange={event => setRevQty(event.target.value)} style={inputStyle} placeholder="Quantity" />
            </div>
            {isAnimalSale && (
              <div style={{ marginTop: 6 }}>
                <select required value={revAnimalId} onChange={event => setRevAnimalId(event.target.value)} style={inputStyle}>
                  <option value="">Select Animal ID being sold</option>
                  {saleEligibleAnimals.map(animal => <option key={animal.id} value={animal.id}>{animal.id} · {animal.category} · {animal.breed}</option>)}
                </select>
                <div style={{ fontSize: 9, color: '#fbbf24', marginTop: 3 }}>Saving this revenue permanently marks the selected animal SOLD, removes it from active herd strength, and retains its Passport / Final Disposal history.</div>
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginTop: 6 }}>
              <input type="date" value={revDate} onChange={event => setRevDate(event.target.value)} style={inputStyle} />
              <select value={revStatus} onChange={event => setRevStatus(event.target.value as RevenueStatus)} style={inputStyle}>
                <option value="RECEIVABLE">Credit / Receivable</option><option value="RECEIVED">Cash Received</option>
              </select>
              {revStatus === 'RECEIVABLE'
                ? <input required type="date" value={revDueDate} onChange={event => setRevDueDate(event.target.value)} style={inputStyle} />
                : <input value={revRef} onChange={event => setRevRef(event.target.value)} style={inputStyle} placeholder="Reference" />}
            </div>
            {revStatus === 'RECEIVABLE' && <input value={revRef} onChange={event => setRevRef(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Reference" />}
            <input value={revCounterparty} onChange={event => setRevCounterparty(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Customer / Buyer" />
            <input value={revNotes} onChange={event => setRevNotes(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Notes" />
            <button disabled={saving} type="submit" style={{ ...button('#059669'), width: '100%', marginTop: 6 }}>{saving ? 'Saving…' : 'Save Revenue'}</button>
          </form>

          <section style={card}>
            <div style={{ ...sectionTitle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span>Revenue Ledger</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 8, color: '#64748b' }}>Current month: {currentMonthStart} → {currentMonthEnd}</span>
                <button type="button" onClick={() => saveRevenueLedgerCsv(currentMonthRevenueRows, currentMonthStart, currentMonthEnd, { 'Active Revenue Total': currentMonthRevenueRows.reduce((sum, t) => sum + activeAmount(t), 0) })} style={smallButton}>Save CSV</button>
                <button type="button" onClick={() => printRevenueLedger(currentMonthRevenueRows, currentMonthStart, currentMonthEnd, { 'Active Revenue Total': currentMonthRevenueRows.reduce((sum, t) => sum + activeAmount(t), 0) })} style={smallButton}><Printer size={11} /> Print</button>
              </div>
            </div>
            <div style={{ overflowX: 'auto', border: '1px solid #1f2937', borderRadius: 6, background: '#0b1120' }}>
              <table style={{ width: '100%', minWidth: 820, borderCollapse: 'collapse', tableLayout: 'fixed', fontSize: 10 }}>
                <colgroup><col style={{ width: 88 }} /><col style={{ width: 190 }} /><col style={{ width: 82 }} /><col style={{ width: 140 }} /><col style={{ width: 120 }} /><col style={{ width: 94 }} /><col style={{ width: 124 }} /><col style={{ width: 120 }} /></colgroup>
                <thead><tr><th style={revenueHeaderCell}>Date</th><th style={revenueHeaderCell}>Particulars</th><th style={{ ...revenueHeaderCell, textAlign: 'right' }}>Quantity</th><th style={revenueHeaderCell}>Buyer / Customer</th><th style={revenueHeaderCell}>Reference</th><th style={revenueHeaderCell}>Status</th><th style={{ ...revenueHeaderCell, textAlign: 'right' }}>Amount</th><th style={{ ...revenueHeaderCell, textAlign: 'right' }}>Actions</th></tr></thead>
                <tbody>
                  {currentMonthRevenueRows.slice(0, 50).map(r => {
                    const isVoid = String(r.status || '').toUpperCase() === 'VOID';
                    const reason = isVoid ? voidReasonFromNotes(r.notes) : '';
                    const animalId = revenueAnimalId(r);
                    return (
                      <React.Fragment key={r.id}>
                        <tr style={{ color: isVoid ? '#f87171' : '#fff', background: isVoid ? 'rgba(239,68,68,.06)' : 'transparent', textDecoration:isVoid?'line-through':'none' }}>
                          <td style={revenueCell}>{r.date?.slice(0, 10) || '—'}</td>
                          <td style={revenueCell} title={r.notes || r.category || ''}>
                            <div style={{ fontWeight: 800, color: isVoid ? '#f87171' : '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis' }}>{revenueParticulars(r)}</div>
                            {animalId && <div style={{ marginTop: 2, color: '#38bdf8', fontSize: 9, fontWeight: 700 }}>Animal #{animalId}</div>}
                          </td>
                          <td style={{ ...revenueCell, textAlign: 'right', fontWeight: 800, color: String(r.category || '').toUpperCase() === 'MILK_SALES' ? '#38bdf8' : '#cbd5e1' }}>{ledgerQuantity(r)}</td>
                          <td style={revenueCell} title={r.counterparty || ''}>{r.counterparty || '—'}</td>
                          <td style={revenueCell} title={r.reference || ''}>{r.reference || '—'}</td>
                          <td style={{ ...revenueCell, fontWeight: 800, color: isVoid ? '#f87171' : r.status === 'RECEIVABLE' ? '#f59e0b' : '#34d399' }}>{r.status || 'RECORDED'}</td>
                          <td style={{ ...revenueCell, textAlign: 'right', fontWeight: 900 }}>{money(Number(r.amount || 0))}</td>
                          <td style={{ ...revenueCell, textAlign: 'right', textDecoration: 'none' }}>
                            {isVoid ? <span style={{ color: '#f87171', fontSize: 9, fontWeight: 800 }}>Voided</span> : (
                              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 4 }}>
                                {r.status === 'RECEIVABLE' && <button type="button" onClick={() => void updateStatus(r, 'RECEIVED')} style={smallButton}>Received</button>}
                                <button type="button" onClick={() => setVoidTarget(r)} style={{ ...smallButton, color: '#f87171' }}><Ban size={10} />Void</button>
                              </div>
                            )}
                          </td>
                        </tr>
                        {isVoid && <tr><td colSpan={8} style={{ padding: '3px 8px 7px', borderBottom: '1px solid #1a2234', color: '#fca5a5', fontSize: 8, fontWeight: 800 }}>VOID: {reason||'See audit trail'}</td></tr>}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {!loading && currentMonthRevenueRows.length === 0 && <div style={empty}>No revenue entries in the current calendar month.</div>}
          </section>
        </div>

        <div style={{ display: 'grid', gap: 10 }}>
          <form onSubmit={saveExpense} style={card}>
            <div style={sectionTitle}>Record Expense</div>
            <div style={{ fontSize: 9, color: '#64748b', marginBottom: 7 }}>Feed purchases are entered here and automatically appear in the Feed tab. Other operating expenses remain accounting entries here.</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              <button type="button" onClick={() => setMasterCategory('FEED')} style={{ background: masterCategory === 'FEED' ? '#0369a1' : '#1e293b', border: '1px solid', borderColor: masterCategory === 'FEED' ? '#38bdf8' : '#334155', color: '#fff', padding: '10px 10px', borderRadius: 5, fontSize: 11, fontWeight: 800, cursor: 'pointer' }}>Feed Expenses</button>
              <button type="button" onClick={() => setMasterCategory('OPEX')} style={{ background: masterCategory === 'OPEX' ? '#92400e' : '#1e293b', border: '1px solid', borderColor: masterCategory === 'OPEX' ? '#f59e0b' : '#334155', color: '#fff', padding: '10px 10px', borderRadius: 5, fontSize: 11, fontWeight: 800, cursor: 'pointer' }}>OPEX</button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: 6, marginTop: 6 }}>
              <select aria-label="Expense category group" required value={expenseGroup} onChange={event => selectExpenseGroup(event.target.value)} style={inputStyle}>
                {expenseGroups.map(group => <option key={group} value={group}>{groupLabel(group)}</option>)}
              </select>
              <select aria-label="Expense list item" required value={subCategory} onChange={event => { setSubCategory(event.target.value); setCustomSpecification(''); }} style={inputStyle}>
                {expenseItems.map(item => <option key={item} value={item}>{item}</option>)}
              </select>
            </div>
            {requiresCustomSpecification && <input required value={customSpecification} onChange={event => setCustomSpecification(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder={subCategory === 'Equipment Purchase' ? 'Equipment name' : 'Specification'} />}
            <input value={vendor} onChange={event => setVendor(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Vendor / Supplier" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 6, marginTop: 6 }}>
              <input type="number" min="0" step="0.001" value={quantity} onChange={event => setQuantity(event.target.value)} style={inputStyle} placeholder="Quantity" />
              <select value={unit} onChange={event => setUnit(event.target.value)} style={inputStyle}><option>kg</option><option>bag</option><option>ton</option><option>litre</option><option>service</option><option>head</option><option>unit</option></select>
              <input type="number" min="0" step="0.01" value={unitRate} onChange={event => setUnitRate(event.target.value)} style={inputStyle} placeholder="Unit rate" disabled={!quantity} />
              <input type="number" min="0" step="0.01" value={quantity ? calculatedAmount : directAmount} onChange={event => quantity ? undefined : setDirectAmount(event.target.value)} style={inputStyle} placeholder="Amount" readOnly={Boolean(quantity)} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginTop: 6 }}>
              <input type="date" value={expenseDate} onChange={event => setExpenseDate(event.target.value)} style={inputStyle} />
              <select value={paymentMethod} onChange={event => setPaymentMethod(event.target.value)} style={inputStyle}><option>BANK</option><option>CASH</option><option>MOBILE</option><option value="CREDIT">Credit / Payable</option></select>
              {paymentMethod === 'CREDIT' ? <input required type="date" value={dueDate} onChange={event => setDueDate(event.target.value)} style={inputStyle} /> : <input value={reference} onChange={event => setReference(event.target.value)} style={inputStyle} placeholder="Reference" />}
            </div>
            {paymentMethod === 'CREDIT' && <input value={reference} onChange={event => setReference(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Reference" />}
            <input value={notes} onChange={event => setNotes(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Notes" />
            <button disabled={saving} type="submit" style={{ ...button('#0284c7'), width: '100%', marginTop: 6 }}>{saving ? 'Saving…' : 'Save Expense'}</button>
          </form>

          <section style={card}>
            <div style={{ ...sectionTitle, display: 'flex', justifyContent: 'space-between', gap: 6 }}><span>Accounting Expense Ledger</span><span style={{ fontSize: 8, color: '#64748b' }}>Current month · {currentMonthStart} → {currentMonthEnd}</span></div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 7 }}>
              {(['ALL', 'FEED', 'OPEX'] as LedgerFilter[]).map(value => <button key={value} type="button" onClick={() => setLedgerFilter(value)} style={{ ...smallButton, background: ledgerFilter === value ? '#0ea5e9' : '#1e293b', color: '#fff' }}>{value}</button>)}
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, flex: 1, minWidth: 150, background: '#1e293b', border: '1px solid #334155', padding: '4px 6px', borderRadius: 4 }}><Search size={11} color="#94a3b8" /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search ledger…" style={{ ...inputStyle, border: 0, padding: 0, background: 'transparent' }} /></div>
              <button type="button" onClick={() => saveLedgerCsv(`Accounting Expense Ledger — ${ledgerFilter}`, filteredExpenses, currentMonthStart, currentMonthEnd, { 'Active Expense Total': filteredExpenses.reduce((sum, t) => sum + activeAmount(t), 0) })} style={smallButton}>Save CSV</button>
              <button type="button" onClick={() => printLedger(`Accounting Expense Ledger — ${ledgerFilter}`, filteredExpenses, currentMonthStart, currentMonthEnd, { 'Active Expense Total': filteredExpenses.reduce((sum, t) => sum + activeAmount(t), 0) })} style={smallButton}><Printer size={11} /> Print</button>
            </div>
            <div style={{ ...ledgerLine, color: '#64748b', fontSize: 8, fontWeight: 800, textTransform: 'uppercase', borderBottom: '1px solid #1f2937', padding: '0 8px 5px' }}><span style={{ width: 76, flex: '0 0 76px' }}>Date</span><span style={ledgerEllipsis}>Particulars</span><span style={{ ...ledgerEllipsis, flexBasis: 100 }}>Counterparty</span><span style={{ ...ledgerEllipsis, flexBasis: 100 }}>Reference</span><span style={{ width: 76, flex: '0 0 76px' }}>Status</span><span style={{ width: 118, flex: '0 0 118px', textAlign: 'right' }}>Amount</span></div>
            {loading ? <div style={empty}>Loading persistent ledger…</div> : filteredExpenses.slice(0, 100).map(renderExpenseLedgerRow)}
            {!loading && filteredExpenses.length === 0 && <div style={empty}>No expenses match this view.</div>}
          </section>
        </div>
      </div>

      <section style={{ ...card, marginTop: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
          <div><div style={{ fontSize: 12, fontWeight: 900 }}>Financial Running Status</div><div style={{ fontSize: 9, color: '#64748b' }}>Default: beginning of farm operations through today. VOID entries remain visible in ledgers but are excluded here.</div></div>
          <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>{(['ALL', 'MONTH', 'CUSTOM'] as const).map(value => <button type="button" key={value} onClick={() => setStatusPeriodMode(value)} style={{ ...smallButton, background: statusPeriodMode === value ? '#334155' : '#1e293b', color: '#fff' }}>{value === 'ALL' ? 'Operations to Date' : value === 'MONTH' ? 'Month' : 'Custom'}</button>)}</div>
        </div>
        {statusPeriodMode === 'MONTH' && <div style={{ marginBottom: 8 }}><input type="month" value={statusMonth} onChange={event => setStatusMonth(event.target.value)} style={{ ...inputStyle, width: 160 }} /></div>}
        {statusPeriodMode === 'CUSTOM' && <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}><input type="date" value={statusStart} onChange={event => setStatusStart(event.target.value)} style={{ ...inputStyle, width: 150 }} /><span style={{ fontSize: 9, color: '#64748b' }}>to</span><input type="date" value={statusEnd} onChange={event => setStatusEnd(event.target.value)} style={{ ...inputStyle, width: 150 }} /></div>}
        <div style={{ fontSize: 9, color: '#94a3b8', marginBottom: 7 }}>Period: {statusBounds.start === '0001-01-01' ? 'Farm inception' : statusBounds.start} → {statusBounds.end}</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 7, marginBottom: 10 }}>
          {[
            ['Revenues', statusRevenue, '#34d399'],
            ['Expenses', statusExpenses, '#f87171'],
            ['Balance', statusBalance, statusBalance >= 0 ? '#38bdf8' : '#f87171'],
          ].map(([cardLabel, value, color]) => <div key={String(cardLabel)} style={{ background: '#0f172a', border: '1px solid #1f2937', borderLeft: `4px solid ${String(color)}`, borderRadius: 7, padding: '9px 10px' }}><div style={{ fontSize: 8, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800 }}>{String(cardLabel)}</div><div style={{ fontSize: 15, fontWeight: 900, color: String(color), marginTop: 3 }}>{money(Number(value))}</div></div>)}
        </div>
        <div style={{ fontSize: 10, fontWeight: 800, marginBottom: 6 }}>Revenue vs Expense</div>
        <div style={{ display: 'grid', gridTemplateColumns: '88px 1fr 120px', gap: 8, alignItems: 'center', fontSize: 9 }}>
          <span style={{ color: '#34d399', fontWeight: 800 }}>Revenue</span><div style={{ height: 16, background: '#0f172a', border: '1px solid #1f2937', borderRadius: 4, overflow: 'hidden' }}><div style={{ height: '100%', width: `${(statusRevenue / graphMax) * 100}%`, background: '#059669' }} /></div><strong style={{ textAlign: 'right' }}>{money(statusRevenue)}</strong>
          <span style={{ color: '#f87171', fontWeight: 800 }}>Expenses</span><div style={{ height: 16, background: '#0f172a', border: '1px solid #1f2937', borderRadius: 4, overflow: 'hidden' }}><div style={{ height: '100%', width: `${(statusExpenses / graphMax) * 100}%`, background: '#dc2626' }} /></div><strong style={{ textAlign: 'right' }}>{money(statusExpenses)}</strong>
        </div>
      </section>

      {editTarget && (
        <div style={modalBackdrop}>
          <form onSubmit={saveEdit} style={modalCard}>
            <strong style={{ fontSize: 13 }}>Edit Finance Entry #{editTarget.id}</strong>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 8 }}>
              <input name="transaction_date" type="date" defaultValue={editTarget.date?.slice(0, 10)} style={inputStyle} />
              <select name="master_category" defaultValue={editTarget.master_category || 'FEED'} style={inputStyle}><option>FEED</option><option>OPEX</option></select>
              <input name="sub_category" defaultValue={editTarget.sub_category || ''} style={inputStyle} />
              <input name="custom_specification" defaultValue={editTarget.custom_specification || ''} style={inputStyle} />
              <input name="quantity" type="number" step="0.001" defaultValue={editTarget.quantity ?? ''} style={inputStyle} />
              <input name="unit" defaultValue={editTarget.unit || 'kg'} style={inputStyle} />
              <input name="unit_rate" type="number" step="0.01" defaultValue={editTarget.unit_rate ?? ''} style={inputStyle} />
              <input name="amount" type="number" step="0.01" defaultValue={editTarget.amount} style={inputStyle} />
              <input name="counterparty" defaultValue={editTarget.vendor_name || editTarget.counterparty || ''} style={inputStyle} placeholder="Vendor" />
              <input name="reference" defaultValue={editTarget.reference || ''} style={inputStyle} placeholder="Reference" />
              <select name="payment_method" defaultValue={editTarget.payment_method || 'BANK'} style={inputStyle}><option>BANK</option><option>CASH</option><option>MOBILE</option><option>CREDIT</option></select>
              <select name="status" defaultValue={editTarget.status === 'PAYABLE' ? 'PAYABLE' : 'PAID'} style={inputStyle}><option>PAID</option><option>PAYABLE</option></select>
              <input name="due_date" type="date" defaultValue={editTarget.due_date || ''} style={inputStyle} />
              <input name="notes" defaultValue={editTarget.notes || ''} style={inputStyle} placeholder="Notes" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 8 }}><button type="button" onClick={() => setEditTarget(null)} style={smallButton}>Cancel</button><button disabled={editSaving} type="submit" style={button('#0284c7')}>{editSaving ? 'Saving…' : 'Save Changes'}</button></div>
          </form>
        </div>
      )}

      {voidTarget && (
        <div style={modalBackdrop}>
          <div style={modalCard}>
            <strong style={{ color: '#ef4444' }}>Void Finance Entry #{voidTarget.id}</strong>
            <textarea required value={voidReason} onChange={event => setVoidReason(event.target.value)} placeholder="Reason" style={{ ...inputStyle, minHeight: 70, marginTop: 8 }} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 8 }}><button type="button" onClick={() => setVoidTarget(null)} style={smallButton}>Cancel</button><button type="button" disabled={!voidReason.trim()} onClick={() => void updateStatus(voidTarget, 'VOID', voidReason)} style={button('#dc2626')}>Confirm Void</button></div>
          </div>
        </div>
      )}
    </div>
  );
}

