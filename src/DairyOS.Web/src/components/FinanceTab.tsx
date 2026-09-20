import React, { useEffect, useMemo, useState } from 'react';
import { Ban, Edit3, Search, WalletCards } from 'lucide-react';
import { API_BASE_URL } from '../config/api';
import { farmToday } from '../utils/farmDate';
import { useFarmDateField } from '../utils/farmDate';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';
const DEFAULT_ANIMAL_PURCHASE_CATEGORIES = [
  { value: 'Milking', label: 'Milking Cows' },
  { value: 'Dry', label: 'Dry Cows' },
  { value: 'Heifer', label: 'Heifers' },
  { value: 'Female Calf', label: 'Female Calves' },
  { value: 'Male Calf', label: 'Male Calves' },
  { value: 'Bull', label: 'Bulls' },
] as const;

type MasterCategory = 'FEED' | 'OPEX' | 'NON_OPEX';
type LedgerFilter = 'ALL' | MasterCategory | 'NON_OPEX';
type ExploreView = 'COMBINED' | 'REVENUE' | 'EXPENSES';
type PeriodMode = 'MONTH' | 'CUSTOM';
type RevenueStatus = 'RECEIVED' | 'RECEIVABLE';

type RevenueFieldName = 'animalId' | 'amount' | 'quantity' | 'rate';

type FinanceFieldContract = {
  visible: readonly RevenueFieldName[];
  required: readonly RevenueFieldName[];
  clearsOnExit: readonly RevenueFieldName[];
};

type ExpenseFormBehavior = 'immediate' | 'defined_period' | 'estimated_consumption' | 'authoritative_consumption' | 'non_opex';

const REVENUE_FIELD_CONTRACTS: Record<string, FinanceFieldContract> = {
  'Milk Sales': { visible: ['quantity', 'rate', 'amount'], required: ['quantity', 'rate'], clearsOnExit: ['animalId', 'amount'] },
  'Milking Animal Sale': { visible: ['animalId', 'amount'], required: ['animalId', 'amount'], clearsOnExit: ['quantity', 'rate'] },
  'Dry Animal Sale': { visible: ['animalId', 'amount'], required: ['animalId', 'amount'], clearsOnExit: ['quantity', 'rate'] },
  'Heifer Sale': { visible: ['animalId', 'amount'], required: ['animalId', 'amount'], clearsOnExit: ['quantity', 'rate'] },
  'Female Calf Sale': { visible: ['animalId', 'amount'], required: ['animalId', 'amount'], clearsOnExit: ['quantity', 'rate'] },
  'Male Calf Sale': { visible: ['animalId', 'amount'], required: ['animalId', 'amount'], clearsOnExit: ['quantity', 'rate'] },
  'Bull Sale': { visible: ['animalId', 'amount'], required: ['animalId', 'amount'], clearsOnExit: ['quantity', 'rate'] },
  'Organic Manure / Dung': { visible: ['amount'], required: ['amount'], clearsOnExit: ['animalId', 'quantity', 'rate'] },
  'Owner Investment / Add Money': { visible: ['amount'], required: ['amount'], clearsOnExit: ['animalId', 'quantity', 'rate'] },
  'Owner Draw / Withdraw Money': { visible: ['amount'], required: ['amount'], clearsOnExit: ['animalId', 'quantity', 'rate'] },
};

type TaxonomyResponse = {
  master_categories: MasterCategory[];
  taxonomies: Record<MasterCategory, Record<string, string[]>>;
  items: Record<MasterCategory, string[]>;
  animal_purchase_categories?: Array<{ value: string; label: string }>;
  cop_governance?: {
    defaults?: Record<string, { classification?: string | null; attribution_method?: string | null }>;
  };
};

type Transaction = {
  id: number;
  transaction_type: string;
  category?: string | null;
  master_category?: MasterCategory | null;
  sub_category?: string | null;
  custom_specification?: string | null;
  animal_category?: string | null;
  animal_id?: string | null;
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
  currency?: string | null;
  due_date?: string | null;
  settled_date?: string | null;
  cop_classification?: string | null;
  cop_attribution_method?: string | null;
  cop_service_date?: string | null;
  cop_coverage_start?: string | null;
  cop_coverage_end?: string | null;
  semen_lot_code?: string | null;
  semen_type?: string | null;
  sire_code?: string | null;
  bull_name?: string | null;
  semen_breed?: string | null;
  semen_batch_number?: string | null;
  semen_expiry_date?: string | null;
  semen_storage_location?: string | null;
  semen_country_source?: string | null;
  semen_purchased_quantity?: number | null;
  semen_unit_cost?: number | null;
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
  onOpenAnimalRegistration?: (request: AnimalPurchaseRegistrationRequest) => void;
};

export type AnimalPurchaseRegistrationRequest = {
  purchaseTransactionId: number;
  category: string;
  acquisitionDate: string;
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

const today = () => farmToday();
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
const isCapitalInflow = (t: Transaction) =>
  t.transaction_type === 'OWNER_INVESTMENT';
const isOwnerWithdrawal = (t: Transaction) =>
  t.transaction_type === 'OWNER_WITHDRAWAL';

const isRevenueSide = (t: Transaction) => isRevenue(t) || isCapitalInflow(t);
const isExpense = (t: Transaction) =>
  t.transaction_type === 'EXPENSE' || t.transaction_type === 'PAYMENT';
const activeAmount = (t: Transaction) =>
  String(t.status || '').toUpperCase() === 'VOID' ? 0 : Number(t.amount || 0);

const money = (value: number) =>
  `PKR ${Number(value || 0).toLocaleString('en-PK', { maximumFractionDigits: 2 })}`;

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
  onOpenAnimalRegistration,
}: Props = {}) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [taxonomy, setTaxonomy] = useState<TaxonomyResponse | null>(null);
  const [masterCategory, setMasterCategory] = useState<MasterCategory>('FEED');
  const [expenseGroup, setExpenseGroup] = useState('');
  const [subCategory, setSubCategory] = useState('');
  const [customSpecification, setCustomSpecification] = useState('');
  const [animalPurchaseCategory, setAnimalPurchaseCategory] = useState('Milking');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [unitRate, setUnitRate] = useState('');
  const [directAmount, setDirectAmount] = useState('');
  const [expenseDate, setExpenseDate, resetExpenseDateToToday] = useFarmDateField();
  const [vendor, setVendor] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('CASH');
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [copClassification, setCopClassification] = useState('OPEX');
  const [copAttributionMethod, setCopAttributionMethod] = useState('');
  const [copServiceDate, setCopServiceDate] = useState('');
  const [copCoverageStart, setCopCoverageStart] = useState('');
  const [copCoverageEnd, setCopCoverageEnd] = useState('');
  const [semenType, setSemenType] = useState<'SEXED'|'CONVENTIONAL'|''>('');
  const [semenSireCode, setSemenSireCode] = useState('');
  const [semenBullName, setSemenBullName] = useState('');
  const [semenBreed, setSemenBreed] = useState('');
  const [semenBatch, setSemenBatch] = useState('');
  const [semenExpiry, setSemenExpiry] = useState('');
  const [semenStorage, setSemenStorage] = useState('');
  const [semenCountry, setSemenCountry] = useState('');
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
  const [revRate, setRevRate] = useState('');
  const [revDate, setRevDate, resetRevDateToToday] = useFarmDateField();
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
  const [editStatus, setEditStatus] = useState('');
  const [editCopClassification, setEditCopClassification] = useState('');
  const [editCopAttributionMethod, setEditCopAttributionMethod] = useState('');

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

  useEffect(() => {
    if (masterCategory !== 'OPEX') return;
    const defaults = taxonomy?.cop_governance?.defaults?.[subCategory];
    setCopClassification(defaults?.classification || '');
    setCopAttributionMethod(defaults?.attribution_method || '');
    setCopServiceDate(expenseDate);
    setCopCoverageStart('');
    setCopCoverageEnd('');
  }, [masterCategory, subCategory, taxonomy, expenseDate]);

  useEffect(() => {
    // A direct amount belongs to the current expense intent.  Clear it when
    // the operator changes category so a hidden Animal Purchase amount cannot
    // become the amount of a different expense after the controls change.
    setDirectAmount('');
  }, [masterCategory, subCategory]);

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
  const revenueSideRows = useMemo(
    () => transactions.filter(isRevenueSide),
    [transactions],
  );
  const activeRevenueRows = useMemo(
    () => revenueSideRows.filter(t => t.status !== 'VOID'),
    [revenueSideRows],
  );

  const currentMonthStart = monthStartFor(today());
  const currentMonthEnd = monthEndFor(today());
  const currentMonthExpenseRows = useMemo(
    () => expenseRows.filter(t => inRange(t.date, currentMonthStart, currentMonthEnd)),
    [expenseRows, currentMonthStart, currentMonthEnd],
  );
  const currentMonthRevenueRows = useMemo(
    () => revenueSideRows.filter(t => inRange(t.date, currentMonthStart, currentMonthEnd)),
    [revenueSideRows, currentMonthStart, currentMonthEnd],
  );

  const filteredExpenses = useMemo(() => {
    const q = search.trim().toLowerCase();
    const base = ledgerFilter === 'ALL'
      ? currentMonthExpenseRows
      : ledgerFilter === 'NON_OPEX'
        ? currentMonthExpenseRows.filter(t => String(t.cop_classification || '').toUpperCase() === 'NON_OPEX')
        : currentMonthExpenseRows.filter(t => t.master_category === ledgerFilter && (ledgerFilter !== 'OPEX' || String(t.cop_classification || '').toUpperCase() !== 'NON_OPEX'));
    return base.filter(t => !q || [
      t.id,
      t.master_category,
      t.sub_category,
      t.custom_specification,
      t.vendor_name,
      t.counterparty,
      t.payment_method,
      t.reference,
      t.notes,
      t.status,
      t.due_date,
      t.settled_date,
      t.animal_category,
      t.animal_id,
      t.semen_lot_code,
      t.semen_type,
      t.sire_code,
      t.bull_name,
      t.semen_breed,
      t.semen_batch_number,
      t.semen_storage_location,
      t.semen_country_source,
      t.cop_classification,
      t.cop_attribution_method,
    ].some(v => String(v ?? '').toLowerCase().includes(q)));
  }, [currentMonthExpenseRows, ledgerFilter, search]);

  const cashRevenue = activeRevenueRows
    .filter(isRevenue)
    .filter(t => ['RECEIVED', 'RECORDED', 'PAID'].includes(String(t.status)))
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const receivables = activeRevenueRows
    .filter(isRevenue)
    .filter(t => t.status === 'RECEIVABLE')
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const capitalAdded = activeRevenueRows
    .filter(isCapitalInflow)
    .filter(t => ['RECEIVED', 'RECORDED', 'PAID'].includes(String(t.status)))
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const totalExpenses = activeExpenseRows.reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const payableTotal = activeExpenseRows
    .filter(t => t.status === 'PAYABLE')
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const ownerWithdrawals = transactions
    .filter(isOwnerWithdrawal)
    .reduce((sum, t) => sum + activeAmount(t), 0);
  const netCash = cashRevenue + capitalAdded - totalExpenses - ownerWithdrawals;


  const exploreBounds = useMemo(
    () => explorePeriodMode === 'MONTH'
      ? { start: `${exploreMonth}-01`, end: monthEndFor(`${exploreMonth}-01`) }
      : { start: exploreStart, end: exploreEnd },
    [explorePeriodMode, exploreMonth, exploreStart, exploreEnd],
  );

  const exploredRows = useMemo(() => transactions.filter(t => {
    if (!inRange(t.date, exploreBounds.start, exploreBounds.end)) return false;
    if (exploreView === 'REVENUE' && !isRevenueSide(t)) return false;
    if (exploreView === 'EXPENSES' && !isExpense(t)) return false;
    if (isExpense(t) && exploreExpenseFilter !== 'ALL') {
      const master = String(t.master_category || '').toUpperCase();
      const copClassification = String(t.cop_classification || '').toUpperCase();

      if (
        exploreExpenseFilter === 'NON_OPEX' &&
        master !== 'NON_OPEX' &&
        copClassification !== 'NON_OPEX'
      ) return false;

      if (
        exploreExpenseFilter === 'OPEX' &&
        (master !== 'OPEX' || copClassification === 'NON_OPEX')
      ) return false;

      if (
        exploreExpenseFilter === 'FEED' &&
        master !== 'FEED'
      ) return false;
    }
    return isRevenueSide(t) || isExpense(t) || isOwnerWithdrawal(t);
  }).sort((a, b) => String(a.date || '').localeCompare(String(b.date || '')) || a.id - b.id), [transactions, exploreBounds, exploreView, exploreExpenseFilter]);

  const carriedForward = useMemo(
    () => transactions
      .filter(t => String(t.date || '').slice(0, 10) < exploreBounds.start)
      .reduce((sum, t) => sum + (
        isRevenueSide(t)
          ? activeAmount(t)
          : isExpense(t) || isOwnerWithdrawal(t)
            ? -activeAmount(t)
            : 0
      ), 0),
    [transactions, exploreBounds.start],
  );
  const periodRevenue = useMemo(
    () => exploredRows.filter(isRevenue).reduce((sum, t) => sum + activeAmount(t), 0),
    [exploredRows],
  );
  const periodCapitalInflow = useMemo(
    () => exploredRows.filter(isCapitalInflow).reduce((sum, t) => sum + activeAmount(t), 0),
    [exploredRows],
  );
  const periodExpenses = useMemo(
    () => exploredRows.filter(isExpense).reduce((sum, t) => sum + activeAmount(t), 0),
    [exploredRows],
  );
  const periodOwnerWithdrawals = useMemo(
    () => exploredRows.filter(isOwnerWithdrawal).reduce((sum, t) => sum + activeAmount(t), 0),
    [exploredRows],
  );
  const periodOperatingNet = periodRevenue - periodExpenses;
  const periodNet =
    periodRevenue +
    periodCapitalInflow -
    periodExpenses -
    periodOwnerWithdrawals;
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
  const statusCapitalInflow = useMemo(
    () => statusRows.filter(isCapitalInflow).reduce((sum, t) => sum + activeAmount(t), 0),
    [statusRows],
  );
  const statusExpenses = useMemo(
    () => statusRows.filter(isExpense).reduce((sum, t) => sum + activeAmount(t), 0),
    [statusRows],
  );
  const statusOwnerWithdrawals = useMemo(
    () => statusRows.filter(isOwnerWithdrawal).reduce((sum, t) => sum + activeAmount(t), 0),
    [statusRows],
  );
  const statusBalance =
    statusRevenue +
    statusCapitalInflow -
    statusExpenses -
    statusOwnerWithdrawals;
  const graphMax = Math.max(
    statusRevenue + statusCapitalInflow,
    statusExpenses + statusOwnerWithdrawals,
    1,
  );

  const calculatedAmount = quantity && unitRate
    ? Number(quantity) * Number(unitRate)
    : Number(directAmount || 0);

  const requiresCustomSpecification=subCategory==='Other'||subCategory==='Equipment Purchase';
  const isSemenPurchase = masterCategory === 'OPEX' && subCategory === 'Semen Straws (Sexed / Conventional)';
  const isAnimalPurchase = masterCategory === 'NON_OPEX' && subCategory === 'Animal Purchase';
  const selectedExpenseDefault = taxonomy?.cop_governance?.defaults?.[subCategory];
  const expenseFormBehavior: ExpenseFormBehavior = masterCategory === 'NON_OPEX' ? 'non_opex' : masterCategory === 'FEED' ? 'authoritative_consumption' : selectedExpenseDefault?.attribution_method === 'DIRECT' || (!selectedExpenseDefault?.attribution_method && copAttributionMethod === 'DIRECT') ? 'immediate' : selectedExpenseDefault?.attribution_method === 'PERIODIC' || (!selectedExpenseDefault?.attribution_method && copAttributionMethod === 'PERIODIC') ? 'defined_period' : 'estimated_consumption';
  const requiresOperatorAttribution = masterCategory === 'OPEX' && !selectedExpenseDefault?.attribution_method;
  const showExpenseQuantity = masterCategory === 'FEED' || isSemenPurchase || expenseFormBehavior === 'estimated_consumption';
  const animalPurchaseCategories = taxonomy?.animal_purchase_categories ?? DEFAULT_ANIMAL_PURCHASE_CATEGORIES;

  useEffect(() => {
    if (!isAnimalPurchase) return;
    setQuantity('');
    setUnitRate('');
    setUnit('head');
    setCustomSpecification('');
    if (!animalPurchaseCategories.some(option => option.value === animalPurchaseCategory)) {
      setAnimalPurchaseCategory(animalPurchaseCategories[0]?.value ?? 'Milking');
    }
  }, [isAnimalPurchase, animalPurchaseCategories, animalPurchaseCategory]);

  useEffect(() => {
    if (isSemenPurchase) return;
    setSemenType('');
    setSemenSireCode('');
    setSemenBullName('');
    setSemenBreed('');
    setSemenBatch('');
    setSemenExpiry('');
    setSemenStorage('');
    setSemenCountry('');
  }, [isSemenPurchase]);

  const ledgerParticulars = (t: Transaction) => {
    const base = t.sub_category || t.category || '—';
    const specification = String(t.custom_specification || '').trim();
    return specification ? `${base} — ${specification}` : base;
  };
  const ledgerCounterparty = (t: Transaction) => t.counterparty || t.vendor_name || '—';
  const ledgerReference = (t: Transaction) => t.reference || '—';
  const ledgerStatus = (t: Transaction) => t.status || 'RECORDED';
  const ledgerDate = (t: Transaction) => String(t.date || t.transaction_date || '').slice(0, 10) || '—';
  const ledgerType = (t: Transaction) => isCapitalInflow(t)
    ? 'Capital Inflow'
    : isOwnerWithdrawal(t)
      ? 'Owner Draw'
      : isRevenue(t)
        ? 'Revenue'
        : 'Expense';
  const ledgerQuantityValue = (t: Transaction) => {
    const qty = Number(t.quantity || 0);
    return qty > 0 ? qty.toLocaleString('en-PK', { maximumFractionDigits: 3 }) : '—';
  };
  const ledgerUnit = (t: Transaction) => {
    const recordedUnit = String(t.unit || '').trim();
    if (recordedUnit) return recordedUnit;
    return String(t.category || '').toUpperCase() === 'MILK_SALES' && Number(t.quantity || 0) > 0
      ? 'litres'
      : '—';
  };
  const ledgerRateValue = (t: Transaction) => {
    const rate = Number(t.unit_rate || 0);
    return rate > 0 ? rate.toFixed(6).replace(/0+$/, '').replace(/\.$/, '') : '';
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
    OWNER_INVESTMENT: 'Owner Investment / Add Money',
    OTHER_REVENUE: 'Other Revenue',
    OWNER_WITHDRAWAL: 'Owner Draw / Withdraw Money',
  };

  const revenueParticulars = (t: Transaction) => {
    const category = String(t.category || 'OTHER_REVENUE').toUpperCase();
    return revenueCategoryLabels[category] || ledgerParticulars(t);
  };

  const ledgerItem = (t: Transaction) => isRevenue(t) || isCapitalInflow(t) || isOwnerWithdrawal(t)
    ? revenueParticulars(t)
    : ledgerParticulars(t);

  const revenueAnimalId= (t: Transaction) => {
    if (t.animal_id) return String(t.animal_id);
    const match = String(t.notes || '').match(/\bAnimal\s+([A-Za-z0-9_-]+)/i);
    return match?.[1] || '';
  };

  const ledgerPayment = (t: Transaction) => {
    const method = String(t.payment_method || '').trim().toUpperCase();
    const labels: Record<string, string> = {
      CASH: 'Cash',
      BANK: 'Bank',
      MOBILE: 'Mobile',
      CREDIT: 'Credit',
    };
    return labels[method] || (method ? groupLabel(method) : '—');
  };
  const ledgerDueDate = (t: Transaction) => t.due_date || '—';
  const ledgerSettledDate = (t: Transaction) => t.settled_date || '—';
  const ledgerCop = (t: Transaction) => {
    const classification = String(t.cop_classification || '').trim().toUpperCase();
    const classificationLabel = classification === 'NON_OPEX'
      ? 'Non-OPEX'
      : classification === 'OPEX'
        ? 'OPEX'
        : '';
    const method = t.cop_attribution_method ? groupLabel(t.cop_attribution_method) : '';
    return [classificationLabel, method].filter(Boolean).join(' · ') || '—';
  };
  const ledgerDomainDetails = (t: Transaction) => {
    const details: string[] = [];
    const animalId = revenueAnimalId(t);
    if (t.animal_category) details.push(`Animal category: ${t.animal_category}`);
    if (animalId) details.push(`Animal: ${animalId}`);
    if (t.semen_lot_code) details.push(`Semen lot: ${t.semen_lot_code}`);
    if (t.semen_type) details.push(`Semen type: ${t.semen_type}`);
    if (t.sire_code) details.push(`Sire: ${t.sire_code}`);
    if (t.bull_name) details.push(`Bull: ${t.bull_name}`);
    if (t.semen_breed) details.push(`Breed: ${t.semen_breed}`);
    if (t.semen_batch_number) details.push(`Batch: ${t.semen_batch_number}`);
    if (t.semen_expiry_date) details.push(`Expiry: ${t.semen_expiry_date}`);
    if (t.semen_storage_location) details.push(`Storage: ${t.semen_storage_location}`);
    if (t.semen_country_source) details.push(`Source: ${t.semen_country_source}`);
    if (t.cop_service_date) details.push(`Service: ${t.cop_service_date}`);
    if (t.cop_coverage_start || t.cop_coverage_end) {
      details.push(`Coverage: ${t.cop_coverage_start || '—'} → ${t.cop_coverage_end || '—'}`);
    }
    return details.join(' · ') || '—';
  };
  const ledgerNotes = (t: Transaction) => String(t.notes || '').trim() || '—';

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
          animal_category: isAnimalPurchase ? animalPurchaseCategory : null,
          quantity: isAnimalPurchase ? null : (quantity ? Number(quantity) : null),
          unit: isAnimalPurchase ? null : (quantity ? (isSemenPurchase ? 'straw' : unit) : null),
          unit_rate: isAnimalPurchase ? null : (quantity ? Number(unitRate) : null),
          amount: isAnimalPurchase ? Number(directAmount) : calculatedAmount,
          transaction_date: expenseDate,
          payment_method: paymentMethod,
          counterparty: vendor || null,
          reference: reference || null,
          notes: notes || null,
          status,
          due_date: status === 'PAYABLE' ? dueDate : null,
          semen_type: isSemenPurchase ? semenType : null,
          sire_code: isSemenPurchase ? semenSireCode : null,
          bull_name: isSemenPurchase ? semenBullName || null : null,
          semen_breed: isSemenPurchase ? semenBreed || null : null,
          semen_batch_number: isSemenPurchase ? semenBatch : null,
          semen_expiry_date: isSemenPurchase ? semenExpiry || null : null,
          semen_storage_location: isSemenPurchase ? semenStorage || null : null,
          semen_country_source: isSemenPurchase ? semenCountry || null : null,
          cop_classification: masterCategory === 'NON_OPEX' ? 'NON_OPEX' : masterCategory === 'OPEX' ? copClassification : null,
          cop_attribution_method: masterCategory === 'OPEX' && copClassification === 'OPEX' ? (copAttributionMethod || null) : null,
          cop_service_date: masterCategory === 'OPEX' && copClassification === 'OPEX' && copAttributionMethod === 'DIRECT' ? (copServiceDate || null) : null,
          cop_coverage_start: masterCategory === 'OPEX' && copClassification === 'OPEX' && ['PERIODIC','ALLOCATED'].includes(copAttributionMethod) ? (copCoverageStart || null) : null,
          cop_coverage_end: masterCategory === 'OPEX' && copClassification === 'OPEX' && ['PERIODIC','ALLOCATED'].includes(copAttributionMethod) ? (copCoverageEnd || null) : null,
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
      resetExpenseDateToToday();
      await load();
      if (isAnimalPurchase && onOpenAnimalRegistration && body.id) {
        onOpenAnimalRegistration({
          purchaseTransactionId: Number(body.id),
          category: animalPurchaseCategory,
          acquisitionDate: String(body.transaction_date || body.date || expenseDate).slice(0, 10),
        });
      }
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
  const isOwnerInvestment = revCategory === 'Owner Investment / Add Money';
  const isOwnerWithdrawalEntry = revCategory === 'Owner Draw / Withdraw Money';
  const isOwnerFinancing = isOwnerInvestment || isOwnerWithdrawalEntry;

  useEffect(() => {
    if (isOwnerFinancing) setRevStatus('RECEIVED');
  }, [isOwnerFinancing]);

  const isMilkSale = revCategory === 'Milk Sales';
  const calculatedMilkSaleAmount = isMilkSale && revQty && revRate
    ? Number(revQty) * Number(revRate)
    : 0;
  const isAnimalSale = Boolean(animalSaleCategories[revCategory]);
  const revenueContract = REVENUE_FIELD_CONTRACTS[revCategory] ?? REVENUE_FIELD_CONTRACTS['Organic Manure / Dung'];
  const hasRevenueField = (field: RevenueFieldName) => revenueContract.visible.includes(field);
  const requiresRevenueField = (field: RevenueFieldName) => revenueContract.required.includes(field);

  // A hidden field is not merely invisible: leaving its state populated would
  // allow an old intent to leak into a later canonical payload.
  useEffect(() => {
    const clears = new Set(revenueContract.clearsOnExit);
    if (clears.has('animalId')) setRevAnimalId('');
    if (clears.has('quantity')) setRevQty('');
    if (clears.has('rate')) setRevRate('');
    if (clears.has('amount')) setRevAmount('');
  }, [revCategory]);

  const saleEligibleAnimals = useMemo(() => {
    if (!isAnimalSale) return [];
    const wantedCategory: Record<string, string> = {
      'Milking Animal Sale': 'MILKING',
      'Dry Animal Sale': 'DRY',
      'Heifer Sale': 'HEIFER',
      'Female Calf Sale': 'FEMALE_CALF',
      'Male Calf Sale': 'MALE_CALF',
      'Bull Sale': 'BULL',
    };
    const expectedCategory = wantedCategory[revCategory] || '';
    const normalizeCategory = (value: string) =>
      String(value || '')
        .trim()
        .toUpperCase()
        .replace(/[\s-]+/g, '_');
    return herdMasterList.filter(
      animal => normalizeCategory(animal.category) === expectedCategory,
    );
  }, [herdMasterList, isAnimalSale, revCategory]);

  useEffect(() => {
    if (!isAnimalSale) {
      setRevAnimalId('');
      return;
    }
    setRevQty('1');
    if (revAnimalId && !saleEligibleAnimals.some(a => a.id === revAnimalId)) {
      setRevAnimalId('');
    }
  }, [isAnimalSale, revAnimalId, saleEligibleAnimals]);

  const saveRevenue = async (e: React.FormEvent) => {
    e.preventDefault();
    const amount = isMilkSale
      ? calculatedMilkSaleAmount
      : Number(revAmount);
    if (isOwnerFinancing && revStatus !== 'RECEIVED') {
      setError(
        isOwnerInvestment
          ? 'Owner investment must be recorded as cash received.'
          : 'Owner withdrawal must be recorded as an immediate cash movement.',
      );
      return;
    }
    if (requiresRevenueField('quantity') && !(Number(revQty) > 0)) {
      setError('This revenue type requires a positive quantity.');
      return;
    }
    if (requiresRevenueField('rate') && !(Number(revRate) > 0)) {
      setError('Milk Sale requires a positive rate per litre.');
      return;
    }
    if (requiresRevenueField('amount') && !(amount > 0)) {
      setError('Enter a positive revenue amount.');
      return;
    }
    if (requiresRevenueField('animalId') && !revAnimalId) {
      setError('Select the Animal ID being sold.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const categoryMap: Record<string, string> = {
        'Milk Sales': 'MILK_SALES',
        'Organic Manure / Dung': 'MANURE_SALES',
        'Owner Investment / Add Money': 'OWNER_INVESTMENT',
        'Owner Draw / Withdraw Money': 'OWNER_WITHDRAWAL',
        ...animalSaleCategories,
      };
      const response = await fetch(`${API_BASE}/farm/finance-ledger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_type: isOwnerInvestment
            ? 'OWNER_INVESTMENT'
            : isOwnerWithdrawalEntry
              ? 'OWNER_WITHDRAWAL'
              : revStatus === 'RECEIVED' ? 'RECEIPT' : 'INCOME',
          category: categoryMap[revCategory] ?? 'OTHER_REVENUE',
          amount: isMilkSale ? undefined : amount,
          quantity: isAnimalSale ? 1 : hasRevenueField('quantity') && revQty ? Number(revQty) : null,
          unit: isAnimalSale ? 'head' : hasRevenueField('quantity') && revQty && isMilkSale ? 'litres' : null,
          unit_rate: hasRevenueField('rate') && revRate ? Number(revRate) : null,
          transaction_date: revDate,
          payment_method: isOwnerFinancing || revStatus === 'RECEIVED' ? 'CASH' : 'CREDIT',
          counterparty: revCounterparty || null,
          status: isOwnerFinancing ? 'RECEIVED' : revStatus,
          due_date: isOwnerFinancing || revStatus !== 'RECEIVABLE' ? null : revDueDate,
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
      setRevRate('');
      setRevRef('');
      setRevCounterparty('');
      setRevNotes('');
      setRevDueDate('');
      resetRevDateToToday();
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

  const openEditTarget = (target: Transaction) => {
    setEditTarget(target);
    setEditStatus(String(target.status || 'RECORDED').toUpperCase());
    setEditCopClassification(String(target.cop_classification || '').toUpperCase());
    setEditCopAttributionMethod(String(target.cop_attribution_method || '').toUpperCase());
  };

  const editIsAnimalPurchase = editTarget?.sub_category === 'Animal Purchase';
  const editIsSemenPurchase = editTarget?.sub_category === 'Semen Straws (Sexed / Conventional)';
  const editRequiresCustomSpecification = editTarget?.sub_category === 'Other' || editTarget?.sub_category === 'Equipment Purchase';
  const editCopEnabled = editTarget?.master_category === 'OPEX' && !editIsAnimalPurchase;
  const editStatusChoices = editTarget
    ? String(editTarget.status || 'RECORDED').toUpperCase() === 'PAYABLE'
      ? ['PAYABLE', 'PAID']
      : String(editTarget.status || 'RECORDED').toUpperCase() === 'RECEIVABLE'
        ? ['RECEIVABLE', 'RECEIVED']
        : ['RECORDED', 'PAYABLE', 'RECEIVABLE']
    : [];

  const saveEdit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editTarget) return;
    setEditSaving(true);
    setError('');
    try {
      const form = new FormData(e.currentTarget);
      const qty = editIsAnimalPurchase ? 0 : Number(form.get('quantity') || 0);
      const rate = editIsAnimalPurchase ? 0 : Number(form.get('unit_rate') || 0);
      const amount = editIsAnimalPurchase ? Number(form.get('amount') || 0) : qty > 0 ? qty * rate : Number(form.get('amount') || 0);
      const response = await fetch(`${API_BASE}/farm/finance-ledger/${editTarget.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          master_category: form.get('master_category'),
          sub_category: form.get('sub_category'),
          custom_specification: form.get('custom_specification') || null,
          animal_category: form.get('animal_category') || null,
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
          cop_classification: form.get('cop_classification') || null,
          cop_attribution_method: form.get('cop_attribution_method') || null,
          cop_service_date: form.get('cop_service_date') || null,
          cop_coverage_start: form.get('cop_coverage_start') || null,
          cop_coverage_end: form.get('cop_coverage_end') || null,
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
    ['Capital Added', capitalAdded, '#2dd4bf'],
    ['Receivables', receivables, '#f59e0b'],
    ['Payables',payableTotal,'#fb7185'],
    ['Total Expenses', totalExpenses, '#f87171'],
    ['Net Cash Position', netCash, '#38bdf8'],
  ];

  const renderExpenseLedgerRow = (r: Transaction) => {
    const isVoid = String(r.status || '').toUpperCase() === 'VOID';
    const reason = isVoid ? voidReasonFromNotes(r.notes) : '';
    const editable = !['VOID', 'PAID', 'RECEIVED'].includes(String(r.status));
    const particulars = ledgerParticulars(r);
    const details = ledgerDomainDetails(r);
    return (
      <div
        key={r.id}
        style={{
          ...row,
          minWidth: 2100,
          color: isVoid ? '#f87171' : '#fff',
          background: isVoid ? 'rgba(239,68,68,.06)' : 'transparent',
          borderLeft: isVoid ? '2px solid #ef4444' : undefined,
        }}
      >
        <div style={{ ...ledgerLine, alignItems: 'flex-start', textDecoration:isVoid?'line-through':'none' }}>
          <span style={{ width: 62, flex: '0 0 62px', fontWeight: 800 }}>#{r.id}</span>
          <span style={{ width: 88, flex: '0 0 88px' }}>{ledgerDate(r)}</span>
          <span title={particulars} style={{ ...ledgerEllipsis, flexBasis: 210 }}>
            <span>{particulars}</span>
          </span>
          <span style={{ width: 86, flex: '0 0 86px' }}>{r.master_category || '—'}</span>
          <span style={{ width: 78, flex: '0 0 78px' }}>{ledgerQuantityValue(r)}</span>
          <span style={{ width: 70, flex: '0 0 70px' }}>{ledgerUnit(r)}</span>
          <span style={{ width: 105, flex: '0 0 105px', textAlign: 'right' }}>{ledgerRateValue(r) ? money(Number(ledgerRateValue(r))) : '—'}</span>
          <strong style={{ width: 125, flex: '0 0 125px', textAlign: 'right' }}>{money(Number(r.amount || 0))}</strong>
          <span title={ledgerCounterparty(r)} style={{ ...ledgerEllipsis, flexBasis: 135 }}>{ledgerCounterparty(r)}</span>
          <span style={{ width: 95, flex: '0 0 95px' }}>{ledgerPayment(r)}</span>
          <span title={ledgerReference(r)} style={{ ...ledgerEllipsis, flexBasis: 120 }}>{ledgerReference(r)}</span>
          <span style={{ width: 94, flex: '0 0 94px', fontWeight: 800 }}>{ledgerStatus(r)}</span>
          <span style={{ width: 95, flex: '0 0 95px' }}>{ledgerDueDate(r)}</span>
          <span style={{ width: 95, flex: '0 0 95px' }}>{ledgerSettledDate(r)}</span>
          <span title={ledgerCop(r)} style={{ ...ledgerEllipsis, flexBasis: 135 }}>{ledgerCop(r)}</span>
          <span title={details} style={{ ...ledgerEllipsis, flexBasis: 250 }}>{details}</span>
          <span title={ledgerNotes(r)} style={{ ...ledgerEllipsis, flexBasis: 210 }}>{ledgerNotes(r)}</span>
          <span style={{ width: 130, flex: '0 0 130px', display: 'flex', justifyContent: 'flex-end', gap: 4, textDecoration: 'none' }}>
            {isVoid ? <span style={{ color: '#f87171', fontSize: 9, fontWeight: 800 }}>Voided</span> : (
              <>
                {editable && <button type="button" onClick={() => openEditTarget(r)} style={smallButton}><Edit3 size={10} /></button>}
                <button type="button" onClick={() => setVoidTarget(r)} style={{ ...smallButton, color: '#f87171' }}><Ban size={10} /></button>
              </>
            )}
          </span>
        </div>
        {isVoid && <span title={reason || 'Reason recorded in audit trail'} style={{ ...voidReasonStyle, maxWidth: 500 }}>VOID: {reason||'See audit trail'}</span>}
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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,minmax(0,1fr))', gap: 7, marginBottom: 10 }}>
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
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
              {(['COMBINED', 'REVENUE', 'EXPENSES'] as ExploreView[]).map(value => (
                <button type="button" key={value} onClick={() => setExploreView(value)} style={{ ...smallButton, background: exploreView === value ? '#7c3aed' : '#1e293b', color: '#fff' }}>{value === 'COMBINED' ? 'Combined' : value === 'REVENUE' ? 'Revenue' : 'Expenses'}</button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              {(['ALL', 'FEED', 'OPEX', 'NON_OPEX'] as LedgerFilter[]).map(value => (
                <button type="button" key={value} onClick={() => setExploreExpenseFilter(value)} disabled={exploreView === 'REVENUE'} style={{ ...smallButton, opacity: exploreView === 'REVENUE' ? .45 : 1, background: exploreExpenseFilter === value ? '#0369a1' : '#1e293b', color: '#fff' }}>{value === 'ALL' ? 'All Expenses' : value === 'FEED' ? 'Feed-only' : value === 'OPEX' ? 'OPEX-only' : 'Non-OPEX'}</button>
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
            {/* Contract: the explorer keeps Owner Draw separate from expenses. */}
            {/* 'Owner Draw': periodOwnerWithdrawals */}
            {/* 'Operating Net': periodOperatingNet */}
            {/* 'Cash Movement': periodNet */}
            {[
              ['Carried Forward', carriedForward, '#94a3b8'],
              ['Period Revenue', periodRevenue, '#34d399'],
              ['Capital Added', periodCapitalInflow, '#2dd4bf'],
              ['Period Expenses', periodExpenses, '#f87171'],
              ['Owner Draw', periodOwnerWithdrawals, '#f59e0b'],
              ['Cash Movement', periodNet, periodNet >= 0 ? '#38bdf8' : '#f87171'],
              ['Closing Balance', closingBalance, closingBalance >= 0 ? '#a78bfa' : '#f87171'],
            ].map(([cardLabel, value, color]) => (
              <div key={String(cardLabel)} style={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: 6, padding: 8 }}>
                <div style={{ fontSize: 8, color: '#64748b', textTransform: 'uppercase', fontWeight: 800 }}>{String(cardLabel)}</div>
                <div style={{ fontSize: 12, color: String(color), fontWeight: 900, marginTop: 2 }}>{money(Number(value))}</div>
              </div>
            ))}
          </div>
          <div style={{ overflowX: 'auto' }}>
            <div style={{ minWidth: 2100 }}>
              <div style={{ ...ledgerLine, color: '#64748b', fontSize: 8, fontWeight: 800, textTransform: 'uppercase', borderBottom: '1px solid #1f2937', padding: '0 8px 5px', alignItems: 'flex-start' }}>
                <span style={{ width: 62, flex: '0 0 62px' }}>Transaction #</span><span style={{ width: 88, flex: '0 0 88px' }}>Date</span><span style={{ width: 90, flex: '0 0 90px' }}>Type</span><span style={{ ...ledgerEllipsis, flexBasis: 210 }}>Item / Specification</span><span style={{ width: 86, flex: '0 0 86px' }}>Master Category</span><span style={{ width: 78, flex: '0 0 78px' }}>Quantity</span><span style={{ width: 70, flex: '0 0 70px' }}>Unit</span><span style={{ width: 105, flex: '0 0 105px', textAlign: 'right' }}>Unit Rate</span><span style={{ width: 125, flex: '0 0 125px', textAlign: 'right' }}>Amount</span><span style={{ ...ledgerEllipsis, flexBasis: 135 }}>Counterparty</span><span style={{ width: 95, flex: '0 0 95px' }}>Payment Method</span><span style={{ ...ledgerEllipsis, flexBasis: 120 }}>Reference</span><span style={{ width: 94, flex: '0 0 94px' }}>Status</span><span style={{ width: 95, flex: '0 0 95px' }}>Due Date</span><span style={{ width: 95, flex: '0 0 95px' }}>Settled Date</span><span style={{ ...ledgerEllipsis, flexBasis: 135 }}>COP / Attribution</span><span style={{ ...ledgerEllipsis, flexBasis: 250 }}>Animal / Other Details</span><span style={{ ...ledgerEllipsis, flexBasis: 210 }}>Notes</span>
              </div>
              <div style={{ maxHeight: 310, overflowY: 'auto' }}>
                {exploredRows.map(r => {
                  const isVoid = String(r.status || '').toUpperCase() === 'VOID';
                  const reason = isVoid ? voidReasonFromNotes(r.notes) : '';
                  const details = ledgerDomainDetails(r);
                  return (
                    <div key={`${isRevenueSide(r) ? 'R' : 'E'}-${r.id}`} style={{ ...row, minWidth: 2100, color: isVoid ? '#f87171' : '#fff', background: isVoid ? 'rgba(239,68,68,.06)' : 'transparent' }}>
                      <div style={{ ...ledgerLine, alignItems: 'flex-start', textDecoration:isVoid?'line-through':'none' }}>
                        <span style={{ width: 62, flex: '0 0 62px', fontWeight: 800 }}>#{r.id}</span>
                        <span style={{ width: 88, flex: '0 0 88px' }}>{ledgerDate(r)}</span>
                        <span style={{ width: 90, flex: '0 0 90px', fontWeight: 800, color: isRevenueSide(r) ? '#34d399' : '#f59e0b' }}>{ledgerType(r)}</span>
                        <span title={ledgerItem(r)} style={{ ...ledgerEllipsis, flexBasis: 210 }}>{ledgerItem(r)}</span>
                        <span style={{ width: 86, flex: '0 0 86px' }}>{r.master_category || '—'}</span>
                        <span style={{ width: 78, flex: '0 0 78px' }}>{ledgerQuantityValue(r)}</span>
                        <span style={{ width: 70, flex: '0 0 70px' }}>{ledgerUnit(r)}</span>
                        <span style={{ width: 105, flex: '0 0 105px', textAlign: 'right' }}>{ledgerRateValue(r) ? money(Number(ledgerRateValue(r))) : '—'}</span>
                        <strong style={{ width: 125, flex: '0 0 125px', textAlign: 'right' }}>{money(Number(r.amount || 0))}</strong>
                        <span title={ledgerCounterparty(r)} style={{ ...ledgerEllipsis, flexBasis: 135 }}>{ledgerCounterparty(r)}</span>
                        <span style={{ width: 95, flex: '0 0 95px' }}>{ledgerPayment(r)}</span>
                        <span title={ledgerReference(r)} style={{ ...ledgerEllipsis, flexBasis: 120 }}>{ledgerReference(r)}</span>
                        <span style={{ width: 94, flex: '0 0 94px', fontWeight: 800 }}>{ledgerStatus(r)}</span>
                        <span style={{ width: 95, flex: '0 0 95px' }}>{ledgerDueDate(r)}</span>
                        <span style={{ width: 95, flex: '0 0 95px' }}>{ledgerSettledDate(r)}</span>
                        <span title={ledgerCop(r)} style={{ ...ledgerEllipsis, flexBasis: 135 }}>{ledgerCop(r)}</span>
                        <span title={details} style={{ ...ledgerEllipsis, flexBasis: 250 }}>{details}</span>
                        <span title={ledgerNotes(r)} style={{ ...ledgerEllipsis, flexBasis: 210 }}>{ledgerNotes(r)}</span>
                      </div>
                      {isVoid && <span style={{ ...voidReasonStyle, maxWidth: 500 }}>VOID: {reason||'See audit trail'}</span>}
                    </div>
                  );
                })}
                {exploredRows.length === 0 && <div style={empty}>No ledger entries in this period/view.</div>}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap', paddingTop: 8, borderTop: '1px solid #1f2937', fontSize: 10 }}>
            <strong>Period Aggregate: Revenue {money(periodRevenue)} · Capital {money(periodCapitalInflow)} · Expenses {money(periodExpenses)} · Owner Draw {money(periodOwnerWithdrawals)} · Cash Movement {money(periodNet)}</strong>
            <strong style={{ color: closingBalance >= 0 ? '#a78bfa' : '#f87171' }}>Closing: {money(closingBalance)}</strong>
          </div>
        </section>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: 10, alignItems: 'start' }}>
        <div style={{ display: 'grid', gap: 10 }}>
          <form onSubmit={saveRevenue} style={card}>
            <div style={sectionTitle}>{isOwnerInvestment ? 'Add Investment / Money' : isOwnerWithdrawalEntry ? 'Owner Draw / Withdrawal' : 'Record Revenue'}</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 6 }}>
              <select value={revCategory} onChange={event => setRevCategory(event.target.value)} style={inputStyle}>
                <option>Milk Sales</option><option>Organic Manure / Dung</option><option>Milking Animal Sale</option><option>Dry Animal Sale</option><option>Heifer Sale</option><option>Female Calf Sale</option><option>Male Calf Sale</option><option>Bull Sale</option><option>Owner Investment / Add Money</option><option>Owner Draw / Withdraw Money</option>
              </select>
              {hasRevenueField('quantity') && isMilkSale
                ? <input required={requiresRevenueField('quantity')} type="number" min="0" step="0.01" value={revQty} onChange={event => setRevQty(event.target.value)} style={inputStyle} placeholder="Quantity (Litres)" />
                : hasRevenueField('amount')
                  ? <input required={requiresRevenueField('amount')} type="number" min="0" step="0.01" value={revAmount} onChange={event => setRevAmount(event.target.value)} style={inputStyle} placeholder="Amount" />
                  : null}
              {hasRevenueField('rate')
                ? <input required={requiresRevenueField('rate')} type="number" min="0" step="0.01" value={revRate} onChange={event => setRevRate(event.target.value)} style={inputStyle} placeholder="Rate / Litre" />
                : isOwnerFinancing
                  ? <input
                      value={isOwnerInvestment ? 'Cash contribution' : 'Owner withdrawal'}
                      readOnly
                      disabled
                      style={inputStyle}
                      aria-label="Financing type"
                    />
                  : hasRevenueField('quantity')
                    ? <input required={requiresRevenueField('quantity')} type="number" min="0" step="0.01" value={revQty} onChange={event => setRevQty(event.target.value)} style={inputStyle} placeholder="Quantity" />
                    : null}
            </div>
            {isMilkSale && <input readOnly value={calculatedMilkSaleAmount > 0 ? calculatedMilkSaleAmount.toFixed(2) : ''} style={{ ...inputStyle, marginTop: 6, color: '#34d399', fontWeight: 800 }} placeholder="Amount — auto calculated from Quantity × Rate" />}
            {isOwnerInvestment && (
              <div style={{ marginTop: 6, padding: 8, border: '1px solid #065f46', borderRadius: 6, background: '#052e2b', color: '#a7f3d0', fontSize: 9 }}>
                Owner Investment / Add Money is recorded as a financing cash inflow. It increases cash position but is excluded from operating revenue, farm expense, OPEX, CAPEX and Estimated COP.
              </div>
            )}
            {isOwnerWithdrawalEntry && (
              <div style={{ marginTop: 6, padding: 8, border: '1px solid #92400e', borderRadius: 6, background: '#451a03', color: '#fde68a', fontSize: 9 }}>
                Owner Draw / Withdrawal is a financing cash outflow. It reduces cash position but is excluded from revenue, farm expense, OPEX, CAPEX and Estimated COP.
              </div>
            )}
            {isAnimalSale && (
              <div style={{ marginTop: 6 }}>
                <select required={requiresRevenueField('animalId')} value={revAnimalId} onChange={event => setRevAnimalId(event.target.value)} style={inputStyle}>
                  <option value="">Select Animal ID being sold</option>
                  {saleEligibleAnimals.map(animal => <option key={animal.id} value={animal.id}>{animal.id} · {animal.category} · {animal.breed}</option>)}
                </select>
                <div style={{ fontSize: 9, color: '#fbbf24', marginTop: 3 }}>Saving this revenue permanently marks the selected animal SOLD, removes it from active herd strength, and retains its Passport / Final Disposal history.</div>
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginTop: 6 }}>
              <input type="date" value={revDate} onChange={event => setRevDate(event.target.value)} style={inputStyle} />
              {isOwnerFinancing
                ? <select value="RECEIVED" disabled style={{ ...inputStyle, opacity: .8 }} aria-label="Financing status">
                    <option value="RECEIVED">{isOwnerInvestment ? 'Cash Received' : 'Cash Withdrawn'}</option>
                  </select>
                : <select value={revStatus} onChange={event => setRevStatus(event.target.value as RevenueStatus)} style={inputStyle}>
                    <option value="RECEIVABLE">Credit / Receivable</option><option value="RECEIVED">Cash Received</option>
                  </select>}
              {!isOwnerFinancing && revStatus === 'RECEIVABLE'
                ? <input required type="date" value={revDueDate} onChange={event => setRevDueDate(event.target.value)} style={inputStyle} />
                : <input value={revRef} onChange={event => setRevRef(event.target.value)} style={inputStyle} placeholder="Reference" />}
            </div>
            {!isOwnerFinancing && revStatus === 'RECEIVABLE' && <input value={revRef} onChange={event => setRevRef(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Reference" />}
            <input
              value={revCounterparty}
              onChange={event => setRevCounterparty(event.target.value)}
              style={{ ...inputStyle, marginTop: 6 }}
              placeholder={
                isOwnerInvestment
                  ? 'Investor / Source (optional)'
                  : isOwnerWithdrawalEntry
                    ? 'Owner / Recipient (optional)'
                    : 'Customer / Buyer'
              }
            />
            <input value={revNotes} onChange={event => setRevNotes(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Notes" />
            <button disabled={saving} type="submit" style={{ ...button(isOwnerWithdrawalEntry ? '#d97706' : '#059669'), width: '100%', marginTop: 6 }}>
              {saving
                ? 'Saving…'
                : isOwnerInvestment
                  ? 'Add Money to Finance'
                  : isOwnerWithdrawalEntry
                    ? 'Record Owner Draw'
                    : 'Save Revenue'}
            </button>
          </form>

          <section style={card}>
            <div style={{ ...sectionTitle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span>Revenue Ledger</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 8, color: '#64748b' }}>Current month: {currentMonthStart} → {currentMonthEnd}</span>
              </div>
            </div>
            <div style={{ overflowX: 'auto', border: '1px solid #1f2937', borderRadius: 6, background: '#0b1120' }}>
              <table style={{ width: '100%', minWidth: 1950, borderCollapse: 'collapse', tableLayout: 'fixed', fontSize: 10 }}>
                <colgroup><col style={{ width: 62 }} /><col style={{ width: 88 }} /><col style={{ width: 190 }} /><col style={{ width: 78 }} /><col style={{ width: 70 }} /><col style={{ width: 105 }} /><col style={{ width: 125 }} /><col style={{ width: 140 }} /><col style={{ width: 95 }} /><col style={{ width: 120 }} /><col style={{ width: 94 }} /><col style={{ width: 95 }} /><col style={{ width: 95 }} /><col style={{ width: 240 }} /><col style={{ width: 210 }} /><col style={{ width: 130 }} /></colgroup>
                <thead><tr><th style={revenueHeaderCell}>Transaction #</th><th style={revenueHeaderCell}>Date</th><th style={revenueHeaderCell}>Item / Category</th><th style={{ ...revenueHeaderCell, textAlign: 'right' }}>Quantity</th><th style={revenueHeaderCell}>Unit</th><th style={{ ...revenueHeaderCell, textAlign: 'right' }}>Unit Rate</th><th style={{ ...revenueHeaderCell, textAlign: 'right' }}>Amount</th><th style={revenueHeaderCell}>Buyer / Customer</th><th style={revenueHeaderCell}>Payment Method</th><th style={revenueHeaderCell}>Reference</th><th style={revenueHeaderCell}>Status</th><th style={revenueHeaderCell}>Due Date</th><th style={revenueHeaderCell}>Settled Date</th><th style={revenueHeaderCell}>Animal / Other Details</th><th style={revenueHeaderCell}>Notes</th><th style={{ ...revenueHeaderCell, textAlign: 'right' }}>Actions</th></tr></thead>
                <tbody>
                  {currentMonthRevenueRows.slice(0, 50).map(r => {
                    const isVoid = String(r.status || '').toUpperCase() === 'VOID';
                    const reason = isVoid ? voidReasonFromNotes(r.notes) : '';
                    const animalId = revenueAnimalId(r);
                    return (
                      <React.Fragment key={r.id}>
                        <tr style={{ color: isVoid ? '#f87171' : '#fff', background: isVoid ? 'rgba(239,68,68,.06)' : 'transparent', textDecoration:isVoid?'line-through':'none' }}>
                          <td style={{ ...revenueCell, fontWeight: 800 }}>#{r.id}</td>
                          <td style={revenueCell}>{ledgerDate(r)}</td>
                          <td style={revenueCell} title={ledgerItem(r)}>
                            <div style={{ fontWeight: 800, color: isVoid ? '#f87171' : '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis' }}>{revenueParticulars(r)}</div>
                            {animalId && <div style={{ marginTop: 2, color: '#38bdf8', fontSize: 9, fontWeight: 700 }}>Animal #{animalId}</div>}
                          </td>
                          <td style={{ ...revenueCell, textAlign: 'right', fontWeight: 800, color: String(r.category || '').toUpperCase() === 'MILK_SALES' ? '#38bdf8' : '#cbd5e1' }}>{ledgerQuantityValue(r)}</td>
                          <td style={revenueCell}>{ledgerUnit(r)}</td>
                          <td style={{ ...revenueCell, textAlign: 'right', fontWeight: 800 }}>{ledgerRateValue(r) ? money(Number(ledgerRateValue(r))) : '—'}</td>
                          <td style={{ ...revenueCell, textAlign: 'right', fontWeight: 900 }}>{money(Number(r.amount || 0))}</td>
                          <td style={revenueCell} title={r.counterparty || ''}>{ledgerCounterparty(r)}</td>
                          <td style={revenueCell}>{ledgerPayment(r)}</td>
                          <td style={revenueCell} title={r.reference || ''}>{ledgerReference(r)}</td>
                          <td style={{ ...revenueCell, fontWeight: 800, color: isVoid ? '#f87171' : r.status === 'RECEIVABLE' ? '#f59e0b' : '#34d399' }}>{ledgerStatus(r)}</td>
                          <td style={revenueCell}>{ledgerDueDate(r)}</td>
                          <td style={revenueCell}>{ledgerSettledDate(r)}</td>
                          <td style={revenueCell} title={ledgerDomainDetails(r)}>{ledgerDomainDetails(r)}</td>
                          <td style={revenueCell} title={ledgerNotes(r)}>{ledgerNotes(r)}</td>
                          <td style={{ ...revenueCell, textAlign: 'right', textDecoration: 'none' }}>
                            {isVoid ? <span style={{ color: '#f87171', fontSize: 9, fontWeight: 800 }}>Voided</span> : (
                              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 4 }}>
                                {r.status === 'RECEIVABLE' && <button type="button" onClick={() => void updateStatus(r, 'RECEIVED')} style={smallButton}>Received</button>}
                                <button type="button" onClick={() => setVoidTarget(r)} style={{ ...smallButton, color: '#f87171' }}><Ban size={10} />Void</button>
                              </div>
                            )}
                          </td>
                        </tr>
                        {isVoid && <tr><td colSpan={16} style={{ padding: '3px 8px 7px', borderBottom: '1px solid #1a2234', color: '#fca5a5', fontSize: 8, fontWeight: 800 }}>VOID: {reason||'See audit trail'}</td></tr>}
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
            <div style={{ fontSize: 9, color: '#64748b', marginBottom: 7 }}>Feed purchases are entered here and automatically appear in the Feed tab. Farm expenses are classified here as OPEX or Non-OPEX for Estimated COP.</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              <button type="button" onClick={() => setMasterCategory('FEED')} style={{ background: masterCategory === 'FEED' ? '#0369a1' : '#1e293b', border: '1px solid', borderColor: masterCategory === 'FEED' ? '#38bdf8' : '#334155', color: '#fff', padding: '10px 10px', borderRadius: 5, fontSize: 11, fontWeight: 800, cursor: 'pointer' }}>Feed Expenses</button>
              <button type="button" onClick={() => setMasterCategory('OPEX')} style={{ background: masterCategory === 'OPEX' ? '#92400e' : '#1e293b', border: '1px solid', borderColor: masterCategory === 'OPEX' ? '#f59e0b' : '#334155', color: '#fff', padding: '10px 10px', borderRadius: 5, fontSize: 11, fontWeight: 800, cursor: 'pointer' }}>Farm Expenses</button>
              <button type="button" onClick={() => setMasterCategory('NON_OPEX')} style={{ background: masterCategory === 'NON_OPEX' ? '#475569' : '#1e293b', border: '1px solid', borderColor: masterCategory === 'NON_OPEX' ? '#94a3b8' : '#334155', color: '#fff', padding: '10px 10px', borderRadius: 5, fontSize: 11, fontWeight: 800, cursor: 'pointer' }}>Non-OPEX</button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: 6, marginTop: 6 }}>
              <select aria-label="Expense category group" required value={expenseGroup} onChange={event => selectExpenseGroup(event.target.value)} style={inputStyle}>
                {expenseGroups.map(group => <option key={group} value={group}>{groupLabel(group)}</option>)}
              </select>
              <select aria-label="Expense list item" required value={subCategory} onChange={event => { setSubCategory(event.target.value); setCustomSpecification(''); }} style={inputStyle}>
                {expenseItems.map(item => <option key={item} value={item}>{item}</option>)}
              </select>
            </div>
            {isAnimalPurchase && <div style={{ marginTop: 6, padding: 8, border: '1px solid #92400e', borderRadius: 6, background: '#1c1917' }}><div style={{ fontSize: 10, fontWeight: 900, color: '#fbbf24', marginBottom: 5 }}>Animal Purchase — Standard Category</div><select required aria-label="Animal purchase standard category" value={animalPurchaseCategory} onChange={event => setAnimalPurchaseCategory(event.target.value)} style={inputStyle}>{animalPurchaseCategories.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select><div style={{ fontSize: 8, color: '#d6d3d1', marginTop: 5 }}>After this expense is endorsed, DairyOS will open the detailed Register Animal / Passport form with this category preselected.</div></div>}
            {isSemenPurchase && <div style={{ marginTop:6, padding:8, border:'1px solid #7c2d12', borderRadius:6, background:'#1c1917' }}><div style={{fontSize:10,fontWeight:900,color:'#fbbf24',marginBottom:6}}>Semen Purchase Details</div><div style={{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:6}}><select required value={semenType} onChange={e=>setSemenType(e.target.value as typeof semenType)} style={inputStyle}><option value="">Semen type</option><option value="SEXED">Sexed</option><option value="CONVENTIONAL">Conventional</option></select><input required value={semenSireCode} onChange={e=>setSemenSireCode(e.target.value)} style={inputStyle} placeholder="Sire / Bull Code" /><input value={semenBullName} onChange={e=>setSemenBullName(e.target.value)} style={inputStyle} placeholder="Bull Name" /><input value={semenBreed} onChange={e=>setSemenBreed(e.target.value)} style={inputStyle} placeholder="Breed" /><input required value={semenBatch} onChange={e=>setSemenBatch(e.target.value)} style={inputStyle} placeholder="Batch / Lot Number" /><label style={{fontSize:8,color:'#94a3b8'}}>Expiry Date<input aria-label="Expiry Date" type="date" value={semenExpiry} onChange={e=>setSemenExpiry(e.target.value)} style={{...inputStyle,marginTop:3}} /></label><input value={semenStorage} onChange={e=>setSemenStorage(e.target.value)} style={inputStyle} placeholder="Storage Tank / Location" /><input value={semenCountry} onChange={e=>setSemenCountry(e.target.value)} style={inputStyle} placeholder="Country / Source" /></div><div style={{fontSize:8,color:'#a8a29e',marginTop:5}}>Quantity below = straws purchased. Unit rate = cost per straw. Supplier is the Vendor / Supplier field.</div></div>}
            {requiresCustomSpecification && <input required value={customSpecification} onChange={event => setCustomSpecification(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder={subCategory === 'Equipment Purchase' ? 'Equipment name' : 'Specification'} />}
            <input value={vendor} onChange={event => setVendor(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Vendor / Supplier" />
            {isAnimalPurchase ? <input required type="number" min="0.01" step="0.01" value={directAmount} onChange={event => setDirectAmount(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Purchase amount (PKR)" /> : !showExpenseQuantity ? <input required type="number" min="0.01" step="0.01" value={directAmount} onChange={event => setDirectAmount(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Amount (PKR)" /> : <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 6, marginTop: 6 }}>
              <input type="number" min="0" step="0.001" value={quantity} onChange={event => setQuantity(event.target.value)} style={inputStyle} placeholder="Quantity" />
              <select value={isSemenPurchase ? 'straw' : unit} onChange={event => setUnit(event.target.value)} disabled={isSemenPurchase} style={inputStyle}><option>straw</option><option>kg</option><option>bag</option><option>ton</option><option>litre</option><option>service</option><option>head</option><option>unit</option></select>
              <input type="number" min="0" step="0.01" value={unitRate} onChange={event => setUnitRate(event.target.value)} style={inputStyle} placeholder="Unit rate" disabled={!quantity} />
              <input type="number" min="0" step="0.01" value={quantity ? calculatedAmount : directAmount} onChange={event => quantity ? undefined : setDirectAmount(event.target.value)} style={inputStyle} placeholder="Amount" readOnly={Boolean(quantity)} />
            </div>}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginTop: 6 }}>
              <input type="date" value={expenseDate} onChange={event => setExpenseDate(event.target.value)} style={inputStyle} />
              <select value={paymentMethod} onChange={event => setPaymentMethod(event.target.value)} style={inputStyle}><option>BANK</option><option>CASH</option><option>MOBILE</option><option value="CREDIT">Credit / Payable</option></select>
              {paymentMethod === 'CREDIT' ? <input required type="date" value={dueDate} onChange={event => setDueDate(event.target.value)} style={inputStyle} /> : <input value={reference} onChange={event => setReference(event.target.value)} style={inputStyle} placeholder="Reference" />}
            </div>
            {paymentMethod === 'CREDIT' && <input value={reference} onChange={event => setReference(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Reference" />}
            {masterCategory === 'OPEX' && !isAnimalPurchase && expenseFormBehavior !== 'non_opex' && (
              <div style={{ marginTop: 6, padding: 8, border: '1px solid #334155', borderRadius: 6, background: '#0f172a' }}>
                <div style={{ fontSize: 9, fontWeight: 900, color: '#cbd5e1', marginBottom: 6 }}>Expense facts</div>
                {requiresOperatorAttribution && <select aria-label="Attribution method for conditional expense" required value={copAttributionMethod} onChange={event => setCopAttributionMethod(event.target.value)} style={inputStyle}><option value="">Select how this expense is used</option><option value="DIRECT">Immediate service/use</option><option value="PERIODIC">Defined coverage period</option><option value="ALLOCATED">Estimated consumption period</option></select>}
                {expenseFormBehavior === 'immediate' && (
                  <label style={{ display:'block', marginTop:6, fontSize:8, color:'#94a3b8' }}>Service / Incurred Date
                    <input aria-label="COP service date" type="date" value={copServiceDate} onChange={event => setCopServiceDate(event.target.value)} style={{ ...inputStyle, marginTop: 3 }} />
                  </label>
                )}
                {['defined_period', 'estimated_consumption'].includes(expenseFormBehavior) && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 6 }}>
                    <label style={{ fontSize:8, color:'#94a3b8' }}>Coverage Start<input aria-label="COP coverage start" type="date" value={copCoverageStart} onChange={event => setCopCoverageStart(event.target.value)} style={{...inputStyle,marginTop:3}} /></label>
                    <label style={{ fontSize:8, color:'#94a3b8' }}>Coverage End<input aria-label="COP coverage end" type="date" value={copCoverageEnd} onChange={event => setCopCoverageEnd(event.target.value)} style={{...inputStyle,marginTop:3}} /></label>
                  </div>
                )}
                {expenseFormBehavior === 'authoritative_consumption' && <div style={{ marginTop: 6, fontSize: 8, color: '#fbbf24' }}>Consumption recognition follows the governed domain authority; no operator allocation is required.</div>}
              </div>
            )}
            {isAnimalPurchase && <div style={{ marginTop: 6, padding: 8, border: '1px solid #334155', borderRadius: 6, background: '#0f172a', color: '#cbd5e1', fontSize: 8 }}>Animal Purchase is capital/non-OPEX and is excluded from Estimated COP. Its standard category is retained until the Passport record is completed.</div>}
            <input value={notes} onChange={event => setNotes(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Notes" />
            <button disabled={saving} type="submit" style={{ ...button('#0284c7'), width: '100%', marginTop: 6 }}>{saving ? 'Saving…' : isAnimalPurchase ? 'Endorse Animal Purchase' : 'Save Expense'}</button>
          </form>

          <section style={card}>
            <div style={{ ...sectionTitle, display: 'flex', justifyContent: 'space-between', gap: 6 }}><span>Accounting Expense Ledger</span><span style={{ fontSize: 8, color: '#64748b' }}>Current month · {currentMonthStart} → {currentMonthEnd}</span></div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 7 }}>
              {(['ALL', 'FEED', 'OPEX', 'NON_OPEX'] as LedgerFilter[]).map(value => <button key={value} type="button" onClick={() => setLedgerFilter(value)} style={{ ...smallButton, background: ledgerFilter === value ? '#0ea5e9' : '#1e293b', color: '#fff' }}>{value === 'NON_OPEX' ? 'Non-OPEX' : value}</button>)}
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, flex: 1, minWidth: 150, background: '#1e293b', border: '1px solid #334155', padding: '4px 6px', borderRadius: 4 }}><Search size={11} color="#94a3b8" /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search ledger…" style={{ ...inputStyle, border: 0, padding: 0, background: 'transparent' }} /></div>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <div style={{ ...ledgerLine, minWidth: 2100, color: '#64748b', fontSize: 8, fontWeight: 800, textTransform: 'uppercase', borderBottom: '1px solid #1f2937', padding: '0 8px 5px', alignItems: 'flex-start' }}><span style={{ width: 62, flex: '0 0 62px' }}>Transaction #</span><span style={{ width: 88, flex: '0 0 88px' }}>Date</span><span style={{ ...ledgerEllipsis, flexBasis: 210 }}>Item / Specification</span><span style={{ width: 86, flex: '0 0 86px' }}>Master Category</span><span style={{ width: 78, flex: '0 0 78px' }}>Quantity</span><span style={{ width: 70, flex: '0 0 70px' }}>Unit</span><span style={{ width: 105, flex: '0 0 105px', textAlign: 'right' }}>Unit Rate</span><span style={{ width: 125, flex: '0 0 125px', textAlign: 'right' }}>Amount</span><span style={{ ...ledgerEllipsis, flexBasis: 135 }}>Counterparty</span><span style={{ width: 95, flex: '0 0 95px' }}>Payment Method</span><span style={{ ...ledgerEllipsis, flexBasis: 120 }}>Reference</span><span style={{ width: 94, flex: '0 0 94px' }}>Status</span><span style={{ width: 95, flex: '0 0 95px' }}>Due Date</span><span style={{ width: 95, flex: '0 0 95px' }}>Settled Date</span><span style={{ ...ledgerEllipsis, flexBasis: 135 }}>COP / Attribution</span><span style={{ ...ledgerEllipsis, flexBasis: 250 }}>Animal / Other Details</span><span style={{ ...ledgerEllipsis, flexBasis: 210 }}>Notes</span><span style={{ width: 130, flex: '0 0 130px', textAlign: 'right' }}>Actions</span></div>
              {loading ? <div style={empty}>Loading persistent ledger…</div> : filteredExpenses.slice(0, 100).map(renderExpenseLedgerRow)}
              {!loading && filteredExpenses.length === 0 && <div style={empty}>No expenses match this view.</div>}
            </div>
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 7, marginBottom: 10 }}>
          {[
            ['Revenues', statusRevenue, '#34d399'],
            ['Capital Added', statusCapitalInflow, '#2dd4bf'],
            ['Expenses', statusExpenses, '#f87171'],
            ['Balance', statusBalance, statusBalance >= 0 ? '#38bdf8' : '#f87171'],
          ].map(([cardLabel, value, color]) => <div key={String(cardLabel)} style={{ background: '#0f172a', border: '1px solid #1f2937', borderLeft: `4px solid ${String(color)}`, borderRadius: 7, padding: '9px 10px' }}><div style={{ fontSize: 8, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800 }}>{String(cardLabel)}</div><div style={{ fontSize: 15, fontWeight: 900, color: String(color), marginTop: 3 }}>{money(Number(value))}</div></div>)}
        </div>
        <div style={{ fontSize: 10, fontWeight: 800, marginBottom: 6 }}>Cash Inflows vs Expense</div>
        <div style={{ display: 'grid', gridTemplateColumns: '88px 1fr 120px', gap: 8, alignItems: 'center', fontSize: 9 }}>
          <span style={{ color: '#34d399', fontWeight: 800 }}>Revenue + capital</span><div style={{ height: 16, background: '#0f172a', border: '1px solid #1f2937', borderRadius: 4, overflow: 'hidden' }}><div style={{ height: '100%', width: `${((statusRevenue + statusCapitalInflow) / graphMax) * 100}%`, background: '#059669' }} /></div><strong style={{ textAlign: 'right' }}>{money(statusRevenue + statusCapitalInflow)}</strong>
          <span style={{ color: '#f87171', fontWeight: 800 }}>Expenses</span><div style={{ height: 16, background: '#0f172a', border: '1px solid #1f2937', borderRadius: 4, overflow: 'hidden' }}><div style={{ height: '100%', width: `${(statusExpenses / graphMax) * 100}%`, background: '#dc2626' }} /></div><strong style={{ textAlign: 'right' }}>{money(statusExpenses)}</strong>
        </div>
      </section>

      {editTarget && (
        <div style={modalBackdrop}>
          <form onSubmit={saveEdit} style={modalCard}>
            <strong style={{ fontSize: 13 }}>Edit Finance Entry #{editTarget.id}</strong>
            <div style={{ marginTop: 5, fontSize: 9, color: '#94a3b8' }}>The authoritative expense category is fixed for this edit. Use a governed correction entry when the transaction intent itself was recorded incorrectly.</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 8 }}>
              <input name="transaction_date" type="date" defaultValue={editTarget.date?.slice(0, 10)} style={inputStyle} />
              <input name="master_category" value={editTarget.master_category || '—'} readOnly style={{ ...inputStyle, opacity: .8 }} aria-label="Master category" />
              <input name="sub_category" value={editTarget.sub_category || editTarget.category || '—'} readOnly style={{ ...inputStyle, opacity: .8 }} aria-label="Expense item" />
              {editRequiresCustomSpecification && <input required name="custom_specification" defaultValue={editTarget.custom_specification || ''} style={inputStyle} placeholder={editTarget.sub_category === 'Equipment Purchase' ? 'Equipment name' : 'Specification'} />}
              {editIsAnimalPurchase ? <>
                <input name="animal_category" value={editTarget.animal_category || ''} readOnly style={{ ...inputStyle, opacity: .8 }} placeholder="Animal category" aria-label="Animal purchase category" />
                <input required name="amount" type="number" min="0.01" step="0.01" defaultValue={editTarget.amount} style={inputStyle} placeholder="Purchase amount (PKR)" />
              </> : <>
                <input name="quantity" type="number" step="0.001" defaultValue={editTarget.quantity ?? ''} style={inputStyle} placeholder="Quantity" />
                <input name="unit" defaultValue={editTarget.unit || 'kg'} style={inputStyle} placeholder="Unit" />
                <input name="unit_rate" type="number" step="0.01" defaultValue={editTarget.unit_rate ?? ''} style={inputStyle} placeholder="Unit rate" />
                <input name="amount" type="number" step="0.01" defaultValue={editTarget.amount} style={inputStyle} placeholder="Amount" />
              </>}
              {editIsSemenPurchase && <div style={{ gridColumn: '1 / -1', padding: 8, border: '1px solid #7c2d12', borderRadius: 6, background: '#1c1917', color: '#fed7aa', fontSize: 9 }}>
                <strong>Semen Purchase details (read-only)</strong>
                <div style={{ marginTop: 4 }}>Lot {editTarget.semen_lot_code || '—'} · {editTarget.semen_type || '—'} · Sire {editTarget.sire_code || '—'} · Batch {editTarget.semen_batch_number || '—'} · {editTarget.semen_purchased_quantity ?? editTarget.quantity ?? '—'} straws at PKR {editTarget.semen_unit_cost ?? editTarget.unit_rate ?? '—'}.</div>
              </div>}
              <input name="counterparty" defaultValue={editTarget.vendor_name || editTarget.counterparty || ''} style={inputStyle} placeholder="Vendor" />
              <input name="reference" defaultValue={editTarget.reference || ''} style={inputStyle} placeholder="Reference" />
              <select name="payment_method" defaultValue={editTarget.payment_method || 'CASH'} style={inputStyle}><option>BANK</option><option>CASH</option><option>MOBILE</option><option>CREDIT</option></select>
              <select required name="status" value={editStatus || String(editTarget.status || 'RECORDED').toUpperCase()} onChange={event => setEditStatus(event.target.value)} style={inputStyle}>{editStatusChoices.map(value => <option key={value}>{value}</option>)}</select>
              {['PAYABLE', 'RECEIVABLE'].includes(editStatus || String(editTarget.status || '').toUpperCase()) && <input required name="due_date" type="date" defaultValue={editTarget.due_date || ''} style={inputStyle} placeholder="Due date" />}
              {editCopEnabled && <select name="cop_classification" value={editCopClassification} onChange={event => { setEditCopClassification(event.target.value); if (event.target.value !== 'OPEX') setEditCopAttributionMethod(''); }} style={inputStyle}><option value="">COP classification unresolved</option><option value="OPEX">OPEX</option><option value="NON_OPEX">NON-OPEX</option></select>}
              {editCopEnabled && editCopClassification === 'OPEX' && <select name="cop_attribution_method" value={editCopAttributionMethod} onChange={event => setEditCopAttributionMethod(event.target.value)} style={inputStyle}><option value="">Attribution unresolved</option><option value="DIRECT">DIRECT</option><option value="PERIODIC">PERIODIC</option><option value="CONSUMPTION">CONSUMPTION</option><option value="ALLOCATED">ALLOCATED</option></select>}
              {editCopEnabled && editCopClassification === 'OPEX' && editCopAttributionMethod === 'DIRECT' && <input name="cop_service_date" type="date" defaultValue={editTarget.cop_service_date || ''} style={inputStyle} title="COP service/incurred date" />}
              {editCopEnabled && editCopClassification === 'OPEX' && ['PERIODIC', 'ALLOCATED'].includes(editCopAttributionMethod) && <>
                <input name="cop_coverage_start" type="date" defaultValue={editTarget.cop_coverage_start || ''} style={inputStyle} title="COP coverage start" />
                <input name="cop_coverage_end" type="date" defaultValue={editTarget.cop_coverage_end || ''} style={inputStyle} title="COP coverage end" />
              </>}
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
