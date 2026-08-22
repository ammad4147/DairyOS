import React, { useEffect, useState } from 'react';
import { Check, Milk, RefreshCw, Save, Trash2 } from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const input: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', color: '#fff', border: '1px solid #334155', borderRadius: 5, padding: '7px 8px', fontSize: 10 };
const panel: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 10, minWidth: 0, boxSizing: 'border-box', overflow: 'hidden' };
const btn = (bg: string): React.CSSProperties => ({ background: bg, color: '#fff', border: 0, borderRadius: 5, padding: '7px 9px', fontSize: 9, fontWeight: 800, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 5 });

type HerdAnimal = { id: string; category: string; frequency?: string };
type Production = { id: number; animal_id: string; production_date: string; milking_session?: string | null; total_yield?: number | null; status: string; notes?: string | null };
type Disposition = { id: number; production_date: string; disposition_type: string; quantity_litres: number; amount_due: number; amount_received: number; receivable_outstanding: number; status: string };
type Reconciliation = { produced_litres: number | null; sold_litres: number; non_sale_accounted_litres: number; unaccounted_litres: number | null; over_accounted_litres: number | null; status: string };
type Quality = { id: number; quality_date: string; fat_pct: number; snf_pct: number; sample_type: string; notes?: string | null };
type Props = { initialOpenModal?: boolean; onModalClose?: () => void; herdMasterList?: HerdAnimal[]; onSaveYield?: (litres: number) => void };

async function api<T>(url: string, init?: RequestInit): Promise<T> { const r = await fetch(`${API_BASE}${url}`, { headers: { 'Content-Type': 'application/json' }, ...init }); const body = await r.json().catch(() => null); if (!r.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : 'Request failed.'); return body as T; }
const today = () => new Date().toISOString().slice(0, 10);

export default function MilkTabClean({ initialOpenModal = false, onModalClose, herdMasterList = [], onSaveYield }: Props) {
  const [date, setDate] = useState(today());
  const [animal, setAnimal] = useState(herdMasterList[0]?.id || '');
  const [session, setSession] = useState('');
  const [litres, setLitres] = useState('');
  const [note, setNote] = useState('');
  const [production, setProduction] = useState<Production[]>([]);
  const [sales, setSales] = useState<Disposition[]>([]);
  const [recon, setRecon] = useState<Reconciliation | null>(null);
  const [quality, setQuality] = useState<Quality | null>(null);
  const [fat, setFat] = useState('');
  const [snf, setSnf] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showQuality, setShowQuality] = useState(false);
  const [showSales, setShowSales] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const load = async () => {
    setError('');
    try {
      const [ledger, reconciliation, qualityResult] = await Promise.all([
        api<{ production: Production[]; dispositions: Disposition[] }>(`/farm/milk/ledger?start_date=${date}&end_date=${date}`),
        api<Reconciliation>(`/farm/milk/reconciliation?production_date=${date}`),
        api<{ sample: Quality | null }>(`/farm/milk/quality?quality_date=${date}`),
      ]);
      setProduction(ledger.production || []); setSales(ledger.dispositions || []); setRecon(reconciliation); setQuality(qualityResult.sample || null);
      if (qualityResult.sample) { setFat(String(qualityResult.sample.fat_pct)); setSnf(String(qualityResult.sample.snf_pct)); }
      if (!animal && herdMasterList[0]) setAnimal(herdMasterList[0].id);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load Milk data.'); }
  };

  useEffect(() => { void load(); }, [date]);
  useEffect(() => { if (initialOpenModal) onModalClose?.(); }, [initialOpenModal, onModalClose]);

  const recordProduction = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError(''); setMessage('');
    try {
      const quantity = Number(litres); if (!animal || !session || !(quantity > 0)) throw new Error('Select animal, session, and a positive milk quantity.');
      await api('/farm/milk', { method: 'POST', body: JSON.stringify({ animal_id: animal, milking_session: session, production_date: date, morning_yield: session === 'MORNING' ? quantity : null, afternoon_yield: session === 'AFTERNOON' ? quantity : null, evening_yield: session === 'EVENING' ? quantity : null, notes: note || null, operator: 'WEB' }) });
      if (onSaveYield && date === today()) onSaveYield(quantity);
      setLitres(''); setNote(''); setMessage('Milk production recorded.'); await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Milk production save failed.'); }
    finally { setBusy(false); }
  };

  const saveQuality = async (e: React.FormEvent) => { e.preventDefault(); setBusy(true); setError(''); try { const f = Number(fat), s = Number(snf); if (!(f > 0) || !(s > 0)) throw new Error('Enter positive Fat % and SNF %.'); await api('/farm/milk/quality', { method: 'POST', body: JSON.stringify({ quality_date: date, fat_pct: f, snf_pct: s, sample_type: 'BULK_TANK', recorded_by: 'WEB' }) }); setMessage('Milk quality saved.'); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Milk quality save failed.'); } finally { setBusy(false); } };

  const sessionOptions = animal ? ['MORNING', 'AFTERNOON', 'EVENING'] : [];
  const activeSessions = herdMasterList.find(row => row.id === animal)?.frequency || 'NONE';

  return <div style={{ height: '100%', overflowY: 'auto', overflowX: 'hidden', padding: 14, boxSizing: 'border-box', color: '#fff' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}><div><div style={{ fontSize: 18, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 6 }}><Milk size={18} color="#38bdf8" /> Milk Production</div><div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>Compact operational view. Animal Passport frequency remains authoritative.</div></div><button onClick={() => void load()} style={btn('#1e293b')}><RefreshCw size={11}/> Refresh</button></div>
    {error && <div style={{ ...panel, borderColor: '#ef4444', color: '#fecaca', marginBottom: 8, fontSize: 10 }}>{error}</div>}
    {message && <div style={{ ...panel, borderColor: '#34d399', color: '#bbf7d0', marginBottom: 8, fontSize: 10, display: 'flex', alignItems: 'center', gap: 5 }}><Check size={11}/>{message}</div>}

    <div style={{ display: 'grid', gridTemplateColumns: '160px minmax(0,1fr)', gap: 8, marginBottom: 8 }}>
      <section style={panel}><label style={{ ...labelStyle }}>Operational date<input type="date" value={date} onChange={e => setDate(e.target.value)} style={{ ...input, marginTop: 4 }}/></label></section>
      <section style={panel}><div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr 120px 1fr auto', gap: 6, alignItems: 'end' }}><label style={labelStyle}>Animal<select value={animal} onChange={e => setAnimal(e.target.value)} style={{ ...input, marginTop: 4 }}>{herdMasterList.filter(a => a.category.includes('Milking')).map(a => <option key={a.id} value={a.id}>{a.id}</option>)}</select></label><label style={labelStyle}>Frequency<div style={{ ...input, marginTop: 4, color: '#38bdf8' }}>{activeSessions}</div></label><label style={labelStyle}>Session<select value={session} onChange={e => setSession(e.target.value)} style={{ ...input, marginTop: 4 }}>{sessionOptions.map(option => <option key={option}>{option}</option>)}</select></label><label style={labelStyle}>Milk (L)<input type="number" min="0.1" step="0.1" value={litres} onChange={e => setLitres(e.target.value)} style={{ ...input, marginTop: 4 }} /></label><button type="button" onClick={() => void recordProduction(new Event('submit') as any)} style={btn('#0284c7')}>Save</button></div><div style={{ marginTop: 6 }}><input placeholder="Optional note" value={note} onChange={e => setNote(e.target.value)} style={input}/></div></section>
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,minmax(0,1fr))', gap: 7, marginBottom: 8 }}><Stat label="Produced" value={`${recon?.produced_litres ?? 0} L`} accent="#38bdf8"/><Stat label="Sold" value={`${recon?.sold_litres ?? 0} L`} accent="#34d399"/><Stat label="Non-sale" value={`${recon?.non_sale_accounted_litres ?? 0} L`} accent="#f59e0b"/><Stat label="Unaccounted" value={`${recon?.unaccounted_litres ?? 0} L`} accent="#f87171"/><Stat label="Status" value={recon?.status || '—'} accent="#a78bfa"/></div>

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 8 }}>
      <section style={panel}><div style={sectionHead}><span>Today’s Milk Records</span><button onClick={() => setShowHistory(v => !v)} style={btn('#1e293b')}>{showHistory ? 'Compact' : 'View all'}</button></div><div style={{ display: 'grid', gap: 4, marginTop: 7 }}>{(showHistory ? production : production.slice(0, 5)).map(row => <div key={row.id} style={recordRow}><span><strong>{row.animal_id}</strong> • {row.milking_session || 'Legacy'}</span><span style={{ color: row.status === 'VOID' ? '#94a3b8' : '#38bdf8' }}>{Number(row.total_yield || 0).toFixed(1)} L</span></div>)}{production.length === 0 && <div style={muted}>No production recorded for this date.</div>}</div></section>
      <section style={panel}><div style={sectionHead}><span>Quality & Sales</span><div style={{ display: 'flex', gap: 5 }}><button onClick={() => setShowQuality(v => !v)} style={btn('#1e293b')}>Quality</button><button onClick={() => setShowSales(v => !v)} style={btn('#1e293b')}>Sales</button></div></div>{showQuality && <form onSubmit={saveQuality} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 6, marginTop: 7 }}><input type="number" min="0.001" max="15" step="0.001" placeholder="Fat %" value={fat} onChange={e => setFat(e.target.value)} style={input} required/><input type="number" min="0.001" max="15" step="0.001" placeholder="SNF %" value={snf} onChange={e => setSnf(e.target.value)} style={input} required/><button disabled={busy} style={btn('#7c3aed')}><Save size={11}/> {quality ? 'Update' : 'Save'}</button></form>}{quality && <div style={{ ...muted, marginTop: 6 }}>Recorded quality: Fat {quality.fat_pct}% · SNF {quality.snf_pct}%</div>}{showSales && <div style={{ marginTop: 8, display: 'grid', gap: 4 }}>{sales.slice(0, 8).map(row => <div key={row.id} style={recordRow}><span>{row.disposition_type}</span><span style={{ color: '#34d399' }}>{row.quantity_litres.toFixed(1)} L</span></div>)}{sales.length === 0 && <div style={muted}>No sales/dispositions recorded for this date.</div>}</div>}</section>
    </div>
  </div>;
}

const labelStyle: React.CSSProperties = { fontSize: 9, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800 };
const label = <T extends string>(x: T) => x;
const muted: React.CSSProperties = { fontSize: 9, color: '#64748b' };
const recordRow: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, padding: '6px 7px', background: '#1e293b', borderRadius: 5, fontSize: 9, minWidth: 0 };
const sectionHead: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11, fontWeight: 800 };
function Stat({ label: l, value, accent }: { label: string; value: string; accent: string }) { return <div style={{ ...panel, borderLeft: `4px solid ${accent}` }}><div style={{ fontSize: 8, color: '#94a3b8', textTransform: 'uppercase' }}>{l}</div><div style={{ fontSize: 13, fontWeight: 800, color: accent, marginTop: 2 }}>{value}</div></div>; }
