import React, { useEffect, useMemo, useState } from 'react';
import { Check, Droplets, Milk, RefreshCw, Trash2, X } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

type HerdAnimal = {
  id: string;
  breed: string;
  category: string;
  frequency?: string;
};

type ProductionRow = {
  id: number;
  animal_id: string;
  production_date: string;
  milking_session?: string | null;
  session_ledger: boolean;
  morning_yield?: number | null;
  afternoon_yield?: number | null;
  evening_yield?: number | null;
  total_yield?: number | null;
  status: string;
  notes?: string | null;
};

type DispositionRow = {
  id: number;
  production_date: string;
  disposition_type: string;
  quantity_litres: number;
  sale_id?: string | null;
  counterparty?: string | null;
  selling_price_per_litre?: number | null;
  amount_due: number;
  amount_received: number;
  receivable_outstanding: number;
  notes?: string | null;
  status: string;
};

type Reconciliation = {
  production_date: string;
  production_complete: boolean;
  produced_litres: number | null;
  accounted_litres: number;
  sold_litres: number;
  non_sale_accounted_litres: number;
  unaccounted_litres: number | null;
  over_accounted_litres: number | null;
  sale_value: number;
  cash_received: number;
  receivable_outstanding: number;
  status: string;
};

type NextSession = {
  animal_id: string;
  milking_frequency?: string;
  expected_sessions: string[];
  settled_sessions: string[];
  next_session: string | null;
  status: string;
};

type QualitySample = {
  id: number;
  quality_date: string;
  fat_pct: number;
  snf_pct: number;
  sample_type: string;
  notes?: string | null;
  recorded_by: string;
  status: string;
  recorded_at: string;
  updated_at: string;
};

type FinanceRow = {
  transaction_type: string;
  category?: string;
  amount: number;
  quantity?: number | null;
  date?: string | null;
  status?: string | null;
};

type InlineDispositionType = 'DOMESTIC_USE' | 'CALF_FEED' | 'WASTAGE';

type Props = {
  initialOpenModal?: boolean;
  onModalClose?: () => void;
  herdMasterList?: HerdAnimal[];
  onSaveYield?: (addedLiters: number) => void;
  realTimeTodaySold?: number;
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

const buttonStyle = (background: string): React.CSSProperties => ({
  background,
  color: '#fff',
  border: 'none',
  padding: '8px 11px',
  borderRadius: 5,
  fontSize: 10,
  fontWeight: 800,
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 5,
});

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

const today = () => new Date().toISOString().slice(0, 10);
const litre = (value: number | null | undefined) => `${Number(value || 0).toFixed(1)} L`;

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const body = await response.json() as { detail?: unknown };
      if (body.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // Keep HTTP status as the error detail.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

const monthBounds = (value: string) => {
  const date = new Date(`${value}T12:00:00`);
  const start = new Date(date.getFullYear(), date.getMonth(), 1);
  const end = new Date(date.getFullYear(), date.getMonth() + 1, 0);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
    label: start.toLocaleDateString('en-PK', { month: 'long', year: 'numeric' }),
  };
};

const datesBetween = (start: string, end: string) => {
  const output: string[] = [];
  const date = new Date(`${start}T12:00:00`);
  const last = new Date(`${end}T12:00:00`);
  while (date <= last) {
    output.push(date.toISOString().slice(0, 10));
    date.setDate(date.getDate() + 1);
  }
  return output;
};

export default function MilkTab({
  initialOpenModal = false,
  onModalClose,
  herdMasterList = [],
  onSaveYield,
}: Props) {
  const [date, setDate] = useState(today());
  const [monthData, setMonthData] = useState<{ production: ProductionRow[]; dispositions: DispositionRow[] }>({ production: [], dispositions: [] });
  const [productions, setProductions] = useState<ProductionRow[]>([]);
  const [dispositions, setDispositions] = useState<DispositionRow[]>([]);
  const [reconciliation, setReconciliation] = useState<Reconciliation | null>(null);
  const [dailyRecon, setDailyRecon] = useState<Reconciliation[]>([]);
  const [finance, setFinance] = useState<FinanceRow[]>([]);
  const [qualitySample, setQualitySample] = useState<QualitySample | null>(null);
  const [qualityFat, setQualityFat] = useState('');
  const [qualitySnf, setQualitySnf] = useState('');
  const [qualitySampleType, setQualitySampleType] = useState('BULK_TANK');
  const [qualityNotes, setQualityNotes] = useState('');

  const [productionAnimal, setProductionAnimal] = useState('');
  const [productionLitres, setProductionLitres] = useState('');
  const [productionNextSession, setProductionNextSession] = useState<NextSession | null>(null);
  const [productionPickerOpen, setProductionPickerOpen] = useState(initialOpenModal);
  const [inlineDisposition, setInlineDisposition] = useState<InlineDispositionType | null>(null);
  const [dispositionLitres, setDispositionLitres] = useState('');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [qualitySaving, setQualitySaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [selectedPanel, setSelectedPanel] = useState<'monthProduced' | 'monthSold' | 'monthRecon' | 'dailyProduced' | 'dailySold' | 'domestic' | 'calves' | 'wastage' | 'dailyRecon' | null>(null);

  const bounds = monthBounds(date);
  const milkingAnimals = useMemo(
    () => herdMasterList.filter((animal) => animal.category.toLowerCase().includes('milking')),
    [herdMasterList],
  );

  const closeProductionPicker = () => {
    setProductionPickerOpen(false);
    setProductionAnimal('');
    setProductionLitres('');
    setProductionNextSession(null);
    onModalClose?.();
  };

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [day, month, rec, quality, financeLedger] = await Promise.all([
        request<{ production: ProductionRow[]; dispositions: DispositionRow[] }>(`/farm/milk/ledger?start_date=${date}&end_date=${date}`),
        request<{ production: ProductionRow[]; dispositions: DispositionRow[] }>(`/farm/milk/ledger?start_date=${bounds.start}&end_date=${bounds.end}`),
        request<Reconciliation>(`/farm/milk/reconciliation?production_date=${date}`),
        request<{ sample: QualitySample | null }>(`/farm/milk/quality?quality_date=${date}`),
        request<{ transactions: FinanceRow[] }>(`/farm/finance-ledger`),
      ]);

      setProductions(day.production || []);
      setDispositions(day.dispositions || []);
      setMonthData({ production: month.production || [], dispositions: month.dispositions || [] });
      setReconciliation(rec);
      setFinance(financeLedger.transactions || []);
      setQualitySample(quality.sample || null);

      if (quality.sample) {
        setQualityFat(String(quality.sample.fat_pct));
        setQualitySnf(String(quality.sample.snf_pct));
        setQualitySampleType(quality.sample.sample_type);
        setQualityNotes(quality.sample.notes || '');
      } else {
        setQualityFat('');
        setQualitySnf('');
        setQualitySampleType('BULK_TANK');
        setQualityNotes('');
      }

      const days = datesBetween(bounds.start, bounds.end);
      const recs = await Promise.all(
        days.map((dayDate) => request<Reconciliation>(`/farm/milk/reconciliation?production_date=${dayDate}`).catch(() => null)),
      );
      setDailyRecon(recs.filter((value): value is Reconciliation => Boolean(value)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load Milk data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [date]);

  useEffect(() => {
    if (initialOpenModal) {
      setProductionPickerOpen(true);
    }
  }, [initialOpenModal]);

  const monthProduced = monthData.production
    .filter((row) => row.status !== 'VOID')
    .reduce((sum, row) => sum + Number(row.total_yield || 0), 0);

  const financeMilkSold = finance
    .filter((row) => ['INCOME', 'RECEIPT'].includes(row.transaction_type) && row.status !== 'VOID' && String(row.category || '').toUpperCase().includes('MILK'))
    .reduce((sum, row) => sum + Number(row.quantity || 0), 0);

  const monthSoldDisposition = monthData.dispositions
    .filter((row) => row.status !== 'VOID' && row.disposition_type === 'SOLD')
    .reduce((sum, row) => sum + Number(row.quantity_litres || 0), 0);

  const monthSold = financeMilkSold || monthSoldDisposition;

  const dispositionTotal = (type: string) => dispositions
    .filter((row) => row.status !== 'VOID' && row.disposition_type === type)
    .reduce((sum, row) => sum + Number(row.quantity_litres || 0), 0);

  const soldToday = finance
    .filter((row) => ['INCOME', 'RECEIPT'].includes(row.transaction_type) && row.status !== 'VOID' && String(row.category || '').toUpperCase().includes('MILK') && String(row.date || '').slice(0, 10) === date)
    .reduce((sum, row) => sum + Number(row.quantity || 0), 0) || dispositionTotal('SOLD');

  const domestic = dispositionTotal('DOMESTIC_USE');
  const calves = dispositionTotal('CALF_FEED');
  const wastage = dispositionTotal('WASTAGE');
  const dailyDifference = Number(reconciliation?.produced_litres || 0) - soldToday - domestic - calves - wastage;
  const monthRecon = monthProduced
    - monthSold
    - monthData.dispositions
      .filter((row) => row.status !== 'VOID' && ['DOMESTIC_USE', 'CALF_FEED', 'WASTAGE'].includes(row.disposition_type))
      .reduce((sum, row) => sum + Number(row.quantity_litres || 0), 0);

  const click = (panel: typeof selectedPanel) => {
    setSelectedPanel(selectedPanel === panel ? null : panel);
  };

  const selectProductionAnimal = async (animalId: string) => {
    setProductionAnimal(animalId);
    setProductionLitres('');
    setProductionNextSession(null);
    setError('');

    try {
      const next = await request<NextSession>(`/farm/milk/next-session?animal_id=${encodeURIComponent(animalId)}&operational_date=${today()}`);
      setProductionNextSession(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to resolve the next milking session.');
    }
  };

  const saveProduction = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      const litres = Number(productionLitres);
      const operationalDate = today();
      let session = productionNextSession?.next_session || productionNextSession?.expected_sessions?.[0] || '';

      if (!session && productionAnimal) {
        const next = await request<NextSession>(`/farm/milk/next-session?animal_id=${encodeURIComponent(productionAnimal)}&operational_date=${operationalDate}`);
        setProductionNextSession(next);
        session = next.next_session || next.expected_sessions?.[0] || '';
      }

      if (!(litres > 0) || !productionAnimal || !session) {
        throw new Error('Select a milking animal and enter litres; the next session must be available.');
      }

      await request('/farm/milk', {
        method: 'POST',
        body: JSON.stringify({
          animal_id: productionAnimal,
          milking_session: session,
          morning_yield: session === 'MORNING' ? litres : null,
          afternoon_yield: session === 'AFTERNOON' ? litres : null,
          evening_yield: session === 'EVENING' ? litres : null,
          production_date: operationalDate,
          notes: null,
          operator: 'WEB',
        }),
      });

      if (onSaveYield && operationalDate === today()) {
        onSaveYield(litres);
      }

      setMessage(`Milk production recorded for ${productionAnimal}.`);
      setProductionAnimal('');
      setProductionLitres('');
      setProductionNextSession(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Milk production save failed.');
    } finally {
      setSaving(false);
    }
  };

  const openInlineDisposition = (type: InlineDispositionType) => {
    setInlineDisposition(type);
    setDispositionLitres('');
    setError('');
  };

  const closeInlineDisposition = () => {
    setInlineDisposition(null);
    setDispositionLitres('');
  };

  const saveDisposition = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!inlineDisposition) return;

    setSaving(true);
    setError('');
    try {
      const litres = Number(dispositionLitres);
      if (!(litres > 0)) {
        throw new Error('Litres must be greater than zero.');
      }

      await request('/farm/milk/dispositions', {
        method: 'POST',
        body: JSON.stringify({
          production_date: date,
          disposition_type: inlineDisposition,
          quantity_litres: litres,
          sale_id: null,
          counterparty: null,
          selling_price_per_litre: null,
          notes: null,
        }),
      });

      const label = inlineDisposition === 'DOMESTIC_USE'
        ? 'Domestic use'
        : inlineDisposition === 'CALF_FEED'
          ? 'Calves feed'
          : 'Wastage';
      setMessage(`${label} milk recorded.`);
      closeInlineDisposition();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Milk disposition save failed.');
    } finally {
      setSaving(false);
    }
  };

  const saveQuality = async (event: React.FormEvent) => {
    event.preventDefault();
    setQualitySaving(true);
    setError('');
    try {
      const fat = Number(qualityFat);
      const snf = Number(qualitySnf);
      if (!(fat > 0) || !(snf > 0)) {
        throw new Error('Fat % and SNF % must be greater than zero.');
      }

      await request('/farm/milk/quality', {
        method: 'POST',
        body: JSON.stringify({
          quality_date: date,
          fat_pct: fat,
          snf_pct: snf,
          sample_type: qualitySampleType,
          notes: qualityNotes || null,
          recorded_by: 'UI Operator',
        }),
      });

      setMessage('Milk quality sample saved.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Milk quality save failed.');
    } finally {
      setQualitySaving(false);
    }
  };

  const voidProduction = async (row: ProductionRow) => {
    if (!window.confirm(`Void milk production record ${row.id}?`)) return;
    try {
      await request(`/farm/milk/production/${row.id}/void`, {
        method: 'POST',
        body: JSON.stringify({ reason: 'Operator void from Milk register' }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to void production.');
    }
  };

  const voidDisposition = async (row: DispositionRow) => {
    if (!window.confirm(`Void milk disposition ${row.id}?`)) return;
    try {
      await request(`/farm/milk/dispositions/${row.id}/void`, {
        method: 'POST',
        body: JSON.stringify({ reason: 'Operator void from Milk register' }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to void disposition.');
    }
  };

  const detail = useMemo(() => {
    if (selectedPanel === 'monthProduced') {
      return monthData.production.filter((row) => row.status !== 'VOID').sort((a, b) => a.production_date.localeCompare(b.production_date));
    }
    if (selectedPanel === 'dailyProduced') return productions.filter((row) => row.status !== 'VOID');
    if (selectedPanel === 'monthSold') return monthData.dispositions.filter((row) => row.status !== 'VOID' && row.disposition_type === 'SOLD');
    if (selectedPanel === 'dailySold') return dispositions.filter((row) => row.status !== 'VOID' && row.disposition_type === 'SOLD');
    if (selectedPanel === 'domestic') return dispositions.filter((row) => row.status !== 'VOID' && row.disposition_type === 'DOMESTIC_USE');
    if (selectedPanel === 'calves') return dispositions.filter((row) => row.status !== 'VOID' && row.disposition_type === 'CALF_FEED');
    if (selectedPanel === 'wastage') return dispositions.filter((row) => row.status !== 'VOID' && row.disposition_type === 'WASTAGE');
    return [];
  }, [selectedPanel, monthData, productions, dispositions]);

  const titleMap: Record<string, string> = {
    monthProduced: `Daily milk production — ${bounds.label}`,
    monthSold: `Milk sold — ${bounds.label}`,
    monthRecon: `Daily reconciliation — ${bounds.label}`,
    dailyProduced: `Animal milk production — ${date}`,
    dailySold: `Milk sold — ${date}`,
    domestic: `Domestic use — ${date}`,
    calves: `Calves feed — ${date}`,
    wastage: `Wastage / unusable — ${date}`,
    dailyRecon: `Daily reconciliation — ${date}`,
  };

  return (
    <div style={{ padding: 14, color: '#fff', height: '100%', overflowY: 'auto', overflowX: 'hidden', boxSizing: 'border-box', minWidth: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 10, flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 auto', minWidth: 0 }}>
          <div style={{ fontSize: 18, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 7 }}>
            <Milk size={18} color="#38bdf8" /> Milk
          </div>
          <div style={{ fontSize: 10, color: '#94a3b8' }}>Current-month production, sales and daily reconciliation.</div>
        </div>
        <button
          type="button"
          onClick={() => { setProductionPickerOpen(true); setError(''); }}
          style={{ ...buttonStyle('#0284c7'), border: '1px solid #38bdf8', boxShadow: '0 0 0 1px rgba(56,189,248,.18)', padding: '9px 13px', fontSize: 11 }}
        >
          <Droplets size={13} /> Enter Milk Production
        </button>
        <button type="button" style={smallButton} onClick={() => void load()}>
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {error && <div style={{ background: 'rgba(239,68,68,.12)', border: '1px solid #ef4444', color: '#fecaca', padding: 8, borderRadius: 6, marginBottom: 10, fontSize: 10 }}>{error}</div>}
      {message && <div style={{ background: 'rgba(52,211,153,.1)', border: '1px solid #34d399', color: '#bbf7d0', padding: 8, borderRadius: 6, marginBottom: 10, fontSize: 10 }}><Check size={12} /> {message}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 8, marginBottom: 8 }}>
        <MetricButton label={`Total Milk Produced (${bounds.label})`} value={litre(monthProduced)} color="#38bdf8" active={selectedPanel === 'monthProduced'} onClick={() => click('monthProduced')} />
        <MetricButton label="Milk Sold (month)" value={litre(monthSold)} color="#34d399" active={selectedPanel === 'monthSold'} onClick={() => click('monthSold')} />
        <MetricButton label="Overall Reconciliation" value={litre(monthRecon)} color={monthRecon === 0 ? '#34d399' : '#f59e0b'} active={selectedPanel === 'monthRecon'} onClick={() => click('monthRecon')} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,minmax(0,1fr))', gap: 7, marginBottom: 10 }}>
        <MetricButton
          label="Milk Produced"
          value={litre(reconciliation?.produced_litres)}
          color="#38bdf8"
          active={selectedPanel === 'dailyProduced'}
          onClick={() => click('dailyProduced')}
          suffix={<input type="date" value={date} onChange={(event) => { event.stopPropagation(); setDate(event.target.value); }} style={{ ...inputStyle, width: '100%', marginTop: 5, fontSize: 9 }} />}
        />
        <MetricButton label="Milk Sold" value={litre(soldToday)} color="#34d399" active={selectedPanel === 'dailySold'} onClick={() => click('dailySold')} />
        <MetricButton
          label="Domestic Use"
          value={litre(domestic)}
          color="#f59e0b"
          active={selectedPanel === 'domestic'}
          onClick={() => click('domestic')}
          suffix={inlineDisposition === 'DOMESTIC_USE' ? <InlineDispositionEditor litres={dispositionLitres} setLitres={setDispositionLitres} saving={saving} onSave={saveDisposition} onCancel={closeInlineDisposition} color="#b45309" /> : <button type="button" onClick={(event) => { event.stopPropagation(); openInlineDisposition('DOMESTIC_USE'); }} style={{ ...buttonStyle('#b45309'), width: '100%', marginTop: 5 }}>Enter Milk for Domestic Use</button>}
        />
        <MetricButton
          label="Calves Feed"
          value={litre(calves)}
          color="#a78bfa"
          active={selectedPanel === 'calves'}
          onClick={() => click('calves')}
          suffix={inlineDisposition === 'CALF_FEED' ? <InlineDispositionEditor litres={dispositionLitres} setLitres={setDispositionLitres} saving={saving} onSave={saveDisposition} onCancel={closeInlineDisposition} color="#7c3aed" /> : <button type="button" onClick={(event) => { event.stopPropagation(); openInlineDisposition('CALF_FEED'); }} style={{ ...buttonStyle('#7c3aed'), width: '100%', marginTop: 5 }}>Enter Milk for Calves</button>}
        />
        <MetricButton
          label="Wastage / Not Usable"
          value={litre(wastage)}
          color="#f87171"
          active={selectedPanel === 'wastage'}
          onClick={() => click('wastage')}
          suffix={inlineDisposition === 'WASTAGE' ? <InlineDispositionEditor litres={dispositionLitres} setLitres={setDispositionLitres} saving={saving} onSave={saveDisposition} onCancel={closeInlineDisposition} color="#dc2626" /> : <button type="button" onClick={(event) => { event.stopPropagation(); openInlineDisposition('WASTAGE'); }} style={{ ...buttonStyle('#dc2626'), width: '100%', marginTop: 5 }}>Enter Wastage / Unusable</button>}
        />
        <MetricButton label="Reconciliation" value={litre(dailyDifference)} color={Math.abs(dailyDifference) < 0.05 ? '#34d399' : '#f59e0b'} active={selectedPanel === 'dailyRecon'} onClick={() => click('dailyRecon')} />
      </div>

      {selectedPanel && (
        <section style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 10, marginBottom: 10, overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <strong style={{ fontSize: 12 }}>{titleMap[selectedPanel]}</strong>
            <button style={smallButton} onClick={() => setSelectedPanel(null)}><X size={11} /> Close</button>
          </div>
          {selectedPanel === 'monthRecon' || selectedPanel === 'dailyRecon' ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={tableStyle}>
                <thead><tr><th>Date</th><th>Produced</th><th>Sold</th><th>Non-sale</th><th>Unaccounted</th><th>Status</th></tr></thead>
                <tbody>{(selectedPanel === 'monthRecon' ? dailyRecon : reconciliation ? [reconciliation] : []).map((row) => (
                  <tr key={row.production_date}>
                    <td>{row.production_date}</td><td>{litre(row.produced_litres)}</td><td>{litre(row.sold_litres)}</td><td>{litre(row.non_sale_accounted_litres)}</td><td>{litre(row.unaccounted_litres)}</td><td>{row.status}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          ) : <DetailTable rows={detail} kind={selectedPanel} />}
        </section>
      )}

      <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(260px,.5fr)', gap: 10, alignItems: 'start' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '9px 11px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: 12 }}>Daily Milk Register — {date}</strong>
            <span style={{ fontSize: 9, color: '#64748b' }}>{loading ? 'Loading…' : `${productions.length + dispositions.length} records`}</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', minWidth: 720, borderCollapse: 'collapse', fontSize: 10 }}>
              <thead>
                <tr style={{ background: '#161f30', color: '#94a3b8', textAlign: 'left' }}>
                  <th style={{ padding: 8 }}>Date</th><th>Type / Animal</th><th>Quantity</th><th>Status</th><th>Notes</th><th style={{ textAlign: 'right', padding: 8 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ...productions.map((row) => ({ kind: 'PRODUCTION' as const, id: row.id, label: `${row.animal_id} • ${row.milking_session || 'LEGACY'}`, qty: litre(row.total_yield), status: row.status, notes: row.notes, row })),
                  ...dispositions.map((row) => ({ kind: 'DISPOSITION' as const, id: row.id, label: `${row.disposition_type}${row.sale_id ? ` • ${row.sale_id}` : ''}`, qty: litre(row.quantity_litres), status: row.status, notes: row.notes, row })),
                ].map((entry) => {
                  const isVoid = entry.status === 'VOID';
                  return (
                    <tr
                      key={`${entry.kind}-${entry.id}`}
                      style={{ borderTop: '1px solid #1a2234', color: isVoid ? '#f87171' : undefined, textDecoration: isVoid ? 'line-through' : 'none' }}
                    >
                      <td style={{ padding: 8 }}>{entry.kind === 'PRODUCTION' ? (entry.row as ProductionRow).production_date.slice(0, 10) : (entry.row as DispositionRow).production_date.slice(0, 10)}</td>
                      <td>{entry.label}</td>
                      <td>{entry.qty}</td>
                      <td style={{ fontWeight: isVoid ? 800 : 400 }}>{entry.status}</td>
                      <td style={{ color: isVoid ? '#f87171' : '#94a3b8' }}>{entry.notes || '—'}</td>
                      <td style={{ padding: 8, textAlign: 'right' }}>
                        {!isVoid && (
                          <span style={{ display: 'inline-flex', gap: 5 }}>
                            {entry.kind === 'PRODUCTION'
                              ? <button style={{ ...smallButton, borderColor: '#7f1d1d', color: '#fecaca' }} onClick={() => voidProduction(entry.row as ProductionRow)}><Trash2 size={10} /> Void</button>
                              : <button style={{ ...smallButton, borderColor: '#7f1d1d', color: '#fecaca' }} onClick={() => voidDisposition(entry.row as DispositionRow)}><Trash2 size={10} /> Void</button>}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div />
      </section>

      <section style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 10, marginTop: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 7 }}>
          <div>
            <strong style={{ fontSize: 11, color: '#a78bfa' }}>Milk Quality — Daily Sample</strong>
            <div style={{ fontSize: 9, color: '#64748b' }}>Persisted Fat % and SNF %.</div>
          </div>
          <span style={{ fontSize: 9, color: qualitySample ? '#34d399' : '#64748b' }}>{qualitySample ? 'SAVED' : 'NOT RECORDED'}</span>
        </div>
        <form onSubmit={saveQuality}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 6 }}>
            <input type="number" min="0.001" max="15" step="0.001" value={qualityFat} onChange={(event) => setQualityFat(event.target.value)} style={inputStyle} placeholder="Fat %" required />
            <input type="number" min="0.001" max="15" step="0.001" value={qualitySnf} onChange={(event) => setQualitySnf(event.target.value)} style={inputStyle} placeholder="SNF %" required />
            <select value={qualitySampleType} onChange={(event) => setQualitySampleType(event.target.value)} style={inputStyle}>
              <option>BULK_TANK</option><option>COLLECTION</option><option>PROCESSOR</option><option>OTHER</option>
            </select>
          </div>
          <input value={qualityNotes} onChange={(event) => setQualityNotes(event.target.value)} style={{ ...inputStyle, marginTop: 6 }} placeholder="Quality notes" />
          <button disabled={qualitySaving} type="submit" style={{ ...buttonStyle('#7c3aed'), marginTop: 6 }}>{qualitySaving ? 'Saving…' : qualitySample ? 'Update Quality Sample' : 'Save Quality Sample'}</button>
        </form>
      </section>

      {productionPickerOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(2,6,23,.72)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 18, zIndex: 200 }}>
          <div style={{ width: 'min(760px, 100%)', maxHeight: '80vh', overflowY: 'auto', background: '#0f172a', border: '1px solid #334155', borderRadius: 10, boxShadow: '0 25px 50px -12px rgba(0,0,0,.75)' }}>
            <div style={{ padding: 12, borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 900, color: '#fff' }}>Enter Milk Production</div>
                <div style={{ fontSize: 9, color: '#94a3b8' }}>Select a milking animal. Session and date/time are resolved automatically.</div>
              </div>
              <button style={smallButton} onClick={closeProductionPicker}><X size={12} /> Close</button>
            </div>

            <div style={{ padding: 10, display: 'grid', gap: 6 }}>
              {milkingAnimals.length === 0 ? (
                <div style={{ padding: 14, color: '#94a3b8', fontSize: 10, textAlign: 'center' }}>No milking animals are currently available.</div>
              ) : milkingAnimals.map((animal) => {
                const selected = productionAnimal === animal.id;
                return (
                  <div key={animal.id} style={{ background: selected ? '#16253a' : '#111827', border: `1px solid ${selected ? '#38bdf8' : '#1f2937'}`, borderRadius: 7 }}>
                    <button
                      type="button"
                      onClick={() => { void selectProductionAnimal(animal.id); }}
                      style={{ width: '100%', background: 'transparent', border: 'none', color: '#fff', padding: '9px 10px', display: 'grid', gridTemplateColumns: '1fr 1.5fr .8fr auto', gap: 8, alignItems: 'center', textAlign: 'left', cursor: 'pointer', fontFamily: 'inherit' }}
                    >
                      <span style={{ color: '#38bdf8', fontWeight: 800, fontSize: 10 }}>{animal.id}</span>
                      <span style={{ fontSize: 10 }}>{animal.category} / {animal.breed || 'Unknown'}</span>
                      <span style={{ color: '#cbd5e1', fontSize: 10 }}>{animal.frequency || 'AUTO'}</span>
                      <span style={{ color: selected ? '#38bdf8' : '#64748b', fontSize: 9 }}>{selected ? 'Selected' : 'Enter'}</span>
                    </button>

                    {selected && (
                      <form onSubmit={saveProduction} style={{ borderTop: '1px solid #1f2937', padding: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <input
                          autoFocus
                          type="number"
                          min="0.001"
                          step="0.001"
                          value={productionLitres}
                          onChange={(event) => setProductionLitres(event.target.value)}
                          style={{ ...inputStyle, width: 150 }}
                          placeholder="Quantity (L)"
                          required
                        />
                        <button disabled={saving} type="submit" style={{ ...buttonStyle('#0284c7'), minWidth: 74 }}>{saving ? 'Saving…' : 'Save'}</button>
                        <button type="button" onClick={(event) => { event.stopPropagation(); setProductionAnimal(''); setProductionLitres(''); setProductionNextSession(null); }} style={{ ...smallButton, marginLeft: 'auto' }}><X size={11} /> Cancel</button>
                      </form>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function InlineDispositionEditor({
  litres,
  setLitres,
  saving,
  onSave,
  onCancel,
  color,
}: {
  litres: string;
  setLitres: (value: string) => void;
  saving: boolean;
  onSave: (event: React.FormEvent) => void;
  onCancel: () => void;
  color: string;
}) {
  return (
    <form
      onSubmit={onSave}
      onClick={(event) => event.stopPropagation()}
      style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 4, marginTop: 5 }}
    >
      <input autoFocus type="number" min="0.001" step="0.001" value={litres} onChange={(event) => setLitres(event.target.value)} style={{ ...inputStyle, fontSize: 10, padding: '6px 7px' }} placeholder="Litres" required />
      <button disabled={saving} type="submit" style={{ ...buttonStyle(color), padding: '6px 8px', fontSize: 9 }}>{saving ? '…' : 'Save'}</button>
      <button type="button" onClick={(event) => { event.stopPropagation(); onCancel(); }} style={{ ...smallButton, padding: '5px 6px' }}><X size={10} /></button>
    </form>
  );
}

function MetricButton({
  label,
  value,
  color,
  active,
  onClick,
  suffix,
}: {
  label: string;
  value: string;
  color: string;
  active: boolean;
  onClick: () => void;
  suffix?: React.ReactNode;
}) {
  return (
    <div
      onClick={onClick}
      style={{ textAlign: 'left', background: active ? '#16253a' : '#111827', border: `1px solid ${active ? color : '#1f2937'}`, borderLeft: `4px solid ${color}`, borderRadius: 7, padding: '9px 10px', color: '#fff', cursor: 'pointer', minWidth: 0, fontFamily: 'inherit' }}
    >
      <div style={{ fontSize: 8, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800, lineHeight: 1.25 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 900, color, marginTop: 3 }}>{value}</div>
      {suffix}
    </div>
  );
}

function DetailTable({ rows, kind }: { rows: (ProductionRow | DispositionRow)[]; kind: string }) {
  const isProduction = kind === 'monthProduced' || kind === 'dailyProduced';

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10, minWidth: 620 }}>
        <thead>
          <tr style={{ color: '#94a3b8', textAlign: 'left', borderBottom: '1px solid #1f2937' }}>
            {isProduction ? <><th style={{ padding: 7 }}>Date</th><th style={{ padding: 7 }}>Animal ID</th><th style={{ padding: 7 }}>Session</th><th style={{ padding: 7 }}>Milk</th><th style={{ padding: 7 }}>Status</th></> : <><th style={{ padding: 7 }}>Date</th><th style={{ padding: 7 }}>Disposition</th><th style={{ padding: 7 }}>Litres</th><th style={{ padding: 7 }}>Destination / Customer</th><th style={{ padding: 7 }}>Status</th></>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => isProduction ? (
            <tr key={row.id} style={{ borderBottom: '1px solid #1a2234' }}>
              <td style={{ padding: 7 }}>{row.production_date.slice(0, 10)}</td>
              <td style={{ padding: 7, color: '#38bdf8', fontWeight: 700 }}>{(row as ProductionRow).animal_id}</td>
              <td style={{ padding: 7 }}>{(row as ProductionRow).milking_session || '—'}</td>
              <td style={{ padding: 7 }}>{litre((row as ProductionRow).total_yield)}</td>
              <td style={{ padding: 7 }}>{row.status}</td>
            </tr>
          ) : (
            <tr key={row.id} style={{ borderBottom: '1px solid #1a2234' }}>
              <td style={{ padding: 7 }}>{row.production_date.slice(0, 10)}</td>
              <td style={{ padding: 7 }}>{(row as DispositionRow).disposition_type}</td>
              <td style={{ padding: 7 }}>{litre((row as DispositionRow).quantity_litres)}</td>
              <td style={{ padding: 7 }}>{(row as DispositionRow).counterparty || '—'}</td>
              <td style={{ padding: 7 }}>{row.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: 10,
};
