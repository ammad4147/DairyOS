import React, { useEffect, useMemo, useState } from 'react';
import { Activity, Plus } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';
import { apiUrl } from '../config/api';

type Stage =
  | 'Inseminated (Pending PD)'
  | 'Confirmed Pregnant'
  | 'Dry'
  | 'Open / Manual Entry'
  | 'Lactating / Waiting';
type EventMode = 'AI' | 'PD' | 'CALVING' | 'LOSS';
type LossOutcome = 'MISCARRIAGE' | 'ABORTION' | '';
interface HerdAnimal { id: string; breed: string; category: string }
interface State {
  animal_id: string;
  state: string;
  reproductive_status?: string;
  pregnancy_status?: string;
  pregnancy_confirmed_date?: string | null;
  expected_calving?: string | null;
  expected_calving_date?: string | null;
  last_insemination?: string | null;
  last_insemination_date?: string | null;
  days_in_milk?: number | null;
  eligible_to_breed?: boolean;
  data_status?: string;
}
interface Row {
  id: string;
  tag: string;
  status: Stage;
  aiDate: string;
  pregnancyDate: string;
  sireCode: string;
  semenType: string;
  inseminator: string;
  daysPregnant: number;
  expectedCalving: string;
  pdDueDate: string;
  notes: string;
  daysAfterCalving: number | null;
  manualAiCandidate: boolean;
}
interface Props { onOpenPassport?: (tag: string) => void; herdMasterList?: HerdAnimal[]; onChanged?: () => void | Promise<void> }

async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(apiUrl(path));
  if (!r.ok) throw new Error(`Request failed: ${r.status}`);
  return r.json() as Promise<T>;
}
async function postJson<T>(path: string, payload: unknown): Promise<T> {
  const r = await fetch(apiUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    let detail = `Request failed: ${r.status}`;
    try {
      const b = await r.json() as { detail?: string };
      if (b.detail) detail = b.detail;
    } catch {}
    throw new Error(detail);
  }
  return r.json() as Promise<T>;
}
const norm = (v: unknown) => String(v || '').trim().toUpperCase();
const ev = (v: unknown) => String(v || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
const categoryKey = (v: unknown) => String(v || '').trim().toLowerCase().replace(/[_-]+/g, ' ').replace(/\s+/g, ' ');
const dateOnly = (v: unknown) => {
  if (!v) return '-';
  const d = new Date(String(v));
  return Number.isNaN(d.getTime()) ? String(v).slice(0, 10) : d.toISOString().split('T')[0];
};
const addDays = (v: string, n: number) => {
  if (v === '-') return '-';
  const d = new Date(`${v}T00:00:00`);
  if (Number.isNaN(d.getTime())) return '-';
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
};
const aiSelectableCategory = (c: string) => [
  'milking',
  'milking cow',
  'milking cows',
  'dry',
  'dry cow',
  'dry cows',
  'heifer',
  'heifers',
].includes(categoryKey(c));
const stage = (v: unknown): Stage => {
  switch (norm(v)) {
    case 'INSEMINATED':
    case 'BRED':
      return 'Inseminated (Pending PD)';
    case 'PREGNANT':
      return 'Confirmed Pregnant';
    case 'DRY_OFF':
      return 'Dry';
    case 'LACTATING':
      return 'Lactating / Waiting';
    default:
      return 'Open / Manual Entry';
  }
};
const inputStyle: React.CSSProperties = {
  width: '100%',
  background: '#1e293b',
  color: '#fff',
  border: '1px solid #334155',
  padding: '8px',
  borderRadius: '4px',
  fontSize: '12px',
  boxSizing: 'border-box',
};
const labelStyle: React.CSSProperties = {
  fontSize: '10px',
  color: '#94a3b8',
  display: 'block',
  marginBottom: '3px',
};

export default function BreedingTab({ onOpenPassport, herdMasterList = [], onChanged }: Props) {
  const [activeModalPassport, setActiveModalPassport] = useState<string | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [eventType, setEventType] = useState<EventMode>('AI');
  const [rows, setRows] = useState<Row[]>([]);
  const [states, setStates] = useState<State[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState({ first: null as number | null, second: null as number | null, third: null as number | null });
  const [outcomes, setOutcomes] = useState({ confirmed: 0, negative: 0, calvings: 0, miscarriages: 0, abortions: 0 });
  const [formTag, setFormTag] = useState('');
  const [formSire, setFormSire] = useState('');
  const [formSemenType, setFormSemenType] = useState<'Sexed Semen (90% Female)' | 'Conventional' | ''>('');
  const [formInseminator, setFormInseminator] = useState('');
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0]);
  const [formPdResult, setFormPdResult] = useState<'POSITIVE' | 'NEGATIVE' | ''>('');
  const [formLossOutcome, setFormLossOutcome] = useState<LossOutcome>('');
  const [formNotes, setFormNotes] = useState('');

  const herdKey = herdMasterList.map(a => `${a.id}:${a.category}`).join('|');
  const manualAiAnimals = useMemo(
    () => herdMasterList.filter(a => aiSelectableCategory(a.category)),
    [herdKey],
  );

  const loadRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const [breeding, overview, current] = await Promise.all([
        getJson<any[]>('/farm/breeding'),
        getJson<any>('/farm/reproduction/overview'),
        Promise.all(manualAiAnimals.map(a => getJson<State>(`/farm/animals/${encodeURIComponent(a.id)}/reproduction`))),
      ]);
      const live = current.filter(s => {
        const d = norm(s.data_status);
        return !!s.animal_id && (!d || d === 'LIVE_PERSISTED_DATA' || d === 'LIVE_PERSISTED');
      });
      setStates(live);

      const latest = new Map<string, any>();
      for (const item of breeding) {
        const id = String(item.animal_id || '');
        if (!id) continue;
        const t = new Date(String(item.timestamp || item.date || '')).getTime();
        const old = latest.get(id);
        const ot = old ? new Date(String(old.timestamp || old.date || '')).getTime() : -Infinity;
        if (!old || Number.isNaN(ot) || (!Number.isNaN(t) && t >= ot)) latest.set(id, item);
      }

      const selectableIds = new Set(manualAiAnimals.map(animal => animal.id));
      const mapped = Array.from(latest.entries()).map(([id, item], i): Row => {
        const events = breeding
          .filter(x => String(x.animal_id || '') === id)
          .sort((a, b) => new Date(String(a.timestamp || a.date || '')).getTime() - new Date(String(b.timestamp || b.date || '')).getTime());
        const last = (p: (e: string, r: string) => boolean) => [...events].reverse().find(x => p(ev(x.event_type), norm(x.result)));
        const ai = last(e => e.includes('insemin') || e === 'ai');
        const pd = last((e, r) => e.includes('pregnancy') && (e.includes('confirmed') || e.includes('negative') || r.includes('POSITIVE') || r.includes('NEGATIVE')));
        const s = live.find(x => x.animal_id === id);
        const st = stage(s?.state);
        const aiDate = dateOnly(s?.last_insemination || s?.last_insemination_date || ai?.timestamp || ai?.date);
        const semen = String(ai?.semen_or_bull || ai?.sire_code || '');
        const gestationStartMs =
          st === 'Confirmed Pregnant' && aiDate !== '-'
            ? new Date(`${aiDate}T00:00:00`).getTime()
            : NaN;
        return {
          id: String(item.record_id || item.id || `BRD-${i + 1}`),
          tag: id,
          status: st,
          aiDate,
          pregnancyDate: pd ? dateOnly(pd.timestamp || pd.date) : '-',
          sireCode: semen || '-',
          semenType: semen.toLowerCase().includes('sexed') ? 'Sexed Semen (90% Female)' : semen ? 'Conventional' : 'Not recorded',
          inseminator: String(ai?.technician || ai?.inseminator || '-'),
          daysPregnant: Number.isNaN(gestationStartMs) ? 0 : Math.max(0, Math.floor((Date.now() - gestationStartMs) / 86400000)),
          expectedCalving: st === 'Confirmed Pregnant' ? dateOnly(s?.expected_calving || s?.expected_calving_date) : '-',
          pdDueDate: st === 'Inseminated (Pending PD)' ? addDays(aiDate, 35) : '-',
          notes: String(item.notes || item.result || pd?.notes || pd?.result || 'Reproductive event recorded.'),
          daysAfterCalving: s?.days_in_milk == null ? null : Number(s.days_in_milk),
          manualAiCandidate: selectableIds.has(id) && !['Inseminated (Pending PD)', 'Confirmed Pregnant'].includes(st),
        };
      }).sort((a, b) => b.aiDate.localeCompare(a.aiDate));
      setRows(mapped);

      setAttempt({
        first: overview?.first_attempt_success_ratio_percent == null ? null : Number(overview.first_attempt_success_ratio_percent),
        second: overview?.second_attempt_success_ratio_percent == null ? null : Number(overview.second_attempt_success_ratio_percent),
        third: overview?.third_attempt_success_ratio_percent == null ? null : Number(overview.third_attempt_success_ratio_percent),
      });
      const confirmedCount = breeding.filter(x => {
        const t = ev(x.event_type), r = norm(x.result);
        return t === 'pregnancy_confirmed' || ((t === 'pregnancy_diagnosis' || t === 'pregnancy_check') && ['POSITIVE', 'PREGNANT', 'CONFIRMED'].includes(r));
      }).length;
      const negativeCount = breeding.filter(x => {
        const t = ev(x.event_type), r = norm(x.result);
        return t === 'pregnancy_negative' || ((t === 'pregnancy_diagnosis' || t === 'pregnancy_check') && ['NEGATIVE', 'OPEN', 'NOT_PREGNANT', 'NOT PREGNANT'].includes(r));
      }).length;
      const miscarriageCount = breeding.filter(x => ev(x.event_type) === 'pregnancy_lost' || norm(x.result) === 'MISCARRIAGE').length;
      const abortionCount = breeding.filter(x => ev(x.event_type) === 'abortion' || ['ABORTED', 'ABORTION'].includes(norm(x.result))).length;
      const calvingCount = breeding.filter(x => ['calving', 'calved', 'parturition'].includes(ev(x.event_type))).length;
      setOutcomes({ confirmed: confirmedCount, negative: negativeCount, calvings: calvingCount, miscarriages: miscarriageCount, abortions: abortionCount });
    } catch (e) {
      setRows([]);
      setStates([]);
      setError(e instanceof Error ? e.message : 'Unable to load persisted breeding records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadRecords(); }, [herdKey]);
  const byId = useMemo(() => new Map(states.map(s => [s.animal_id, s])), [states]);
  const aiCandidates = useMemo(
    () => manualAiAnimals.filter(a => {
      const x = norm(byId.get(a.id)?.state);
      return !['INSEMINATED', 'BRED', 'PREGNANT'].includes(x);
    }),
    [manualAiAnimals, byId],
  );
  const candidates = useMemo(
    () => eventType === 'AI'
      ? aiCandidates
      : eventType === 'PD'
        ? manualAiAnimals.filter(a => ['INSEMINATED', 'BRED', 'PREGNANT'].includes(norm(byId.get(a.id)?.state)))
        : (eventType === 'CALVING' || eventType === 'LOSS')
          ? manualAiAnimals.filter(a => norm(byId.get(a.id)?.state) === 'PREGNANT')
          : [],
    [eventType, manualAiAnimals, aiCandidates, byId],
  );
  useEffect(() => {
    if (candidates.length && !candidates.some(a => a.id === formTag)) setFormTag(candidates[0].id);
    if (!candidates.length && formTag) setFormTag('');
  }, [candidates, formTag]);

  const pending = states.filter(s => ['INSEMINATED', 'BRED'].includes(norm(s.state))).length;
  const pregStates = states.filter(s => norm(s.state) === 'PREGNANT');
  const pregnant = pregStates.length;
  const cycle = pending + pregnant;
  const ratio = cycle ? pregnant / cycle * 100 : 0;
  const availableForManualAi = aiCandidates.length;
  const gest = pregStates
    .map(s => s.pregnancy_confirmed_date)
    .filter((x): x is string => Boolean(x))
    .map(x => Math.max(0, Math.floor((Date.now() - new Date(x).getTime()) / 86400000)));
  const avg = gest.length ? Math.round(gest.reduce((a, b) => a + b, 0) / gest.length) : null;
  const pregnancyLosses = outcomes.miscarriages + outcomes.abortions;
  const lossRate = outcomes.confirmed ? pregnancyLosses / outcomes.confirmed * 100 : null;

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTag) return;
    setError(null);
    try {
      let event_type = 'insemination', result = 'RECORDED';
      if (eventType === 'PD') {
        if (!formPdResult) throw new Error('Select the actual pregnancy-diagnosis result.');
        event_type = formPdResult === 'POSITIVE' ? 'pregnancy_confirmed' : 'pregnancy_negative';
        result = formPdResult;
      }
      if (eventType === 'CALVING') event_type = 'calving';
      if (eventType === 'LOSS') {
        if (!formLossOutcome) throw new Error('Select whether the confirmed pregnancy ended in miscarriage or abortion.');
        event_type = formLossOutcome === 'MISCARRIAGE' ? 'pregnancy_lost' : 'abortion';
        result = formLossOutcome === 'MISCARRIAGE' ? 'MISCARRIAGE' : 'ABORTED';
      }
      if (eventType === 'AI') {
        if (!formSire.trim()) throw new Error('Enter the actual sire code / bull used.');
        if (!formSemenType) throw new Error('Select the actual semen type used.');
      }
      await postJson('/farm/breeding', {
        animal_id: formTag,
        event_type,
        technician: formInseminator.trim() || null,
        result,
        semen_or_bull: eventType === 'AI' ? `${formSemenType} — ${formSire.trim()}` : formSire.trim() || null,
        notes: formNotes || undefined,
        operator: formInseminator.trim() || 'WEB',
        timestamp: formDate,
      });
      setShowEventModal(false);
      setFormNotes('');
      setFormSire('');
      setFormSemenType('');
      setFormInseminator('');
      setFormPdResult('');
      setFormLossOutcome('');
      await loadRecords();
      await onChanged?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to save the breeding event.');
    }
  };

  const selected = byId.get(formTag);
  const empty = eventType === 'AI'
    ? 'No Milking, Dry, or Heifer animals available for manual insemination'
    : eventType === 'PD'
      ? 'No inseminated or confirmed-pregnant animals currently available for pregnancy diagnosis/review'
      : eventType === 'CALVING'
        ? 'No confirmed pregnant animals currently awaiting calving'
        : 'No confirmed pregnant animals currently available for pregnancy-loss entry';
  const summaryCards: Array<[string, string | number, string]> = [
    ['Manual AI Candidates', availableForManualAi, '#fb923c'],
    ['Inseminated (Pending PD)', pending, '#60a5fa'],
    ['Confirmed Pregnant', pregnant, '#a78bfa'],
    ['Pregnancy Ratio', `${ratio.toFixed(1)}%`, '#34d399'],
  ];

  return <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}><div><h2 style={{ margin: '0 0 4px', fontSize: '18px', color: '#fb923c', display: 'flex', alignItems: 'center', gap: '8px' }}><Activity size={20} /> Breeding, Artificial Insemination (AI) & Gestation Ledger</h2><p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Manage operator-entered breeding events as authoritative Passport records. Biological clocks provide reminders and guidance only; lifecycle changes occur only through recorded manual breeding events.</p></div><button onClick={() => setShowEventModal(true)} style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', gap: '6px', fontSize: '12px' }}><Plus size={15} /> + Record Breeding / AI Event</button></div>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(170px,1fr))', gap: '12px', marginBottom: '16px' }}>{summaryCards.map(([l, v, c]) => <div key={String(l)} style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: `3px solid ${c}` }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>{l}</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: String(c) }}>{typeof v === 'number' ? `${v} Animals` : v}</div><div style={{ fontSize: '10px', color: '#64748b' }}>{l === 'Manual AI Candidates' ? 'Milking, Dry and Heifer only; active cycles excluded' : l === 'Inseminated (Pending PD)' ? 'PD Check Due Day 35' : l === 'Confirmed Pregnant' ? (avg == null ? 'No confirmed pregnancy data' : `Average ${avg}d Gestation`) : 'Pregnant / active reproductive cycle'}</div></div>)}</div>
    {error && <div style={{ marginBottom: '12px', padding: '10px 12px', borderRadius: '6px', background: 'rgba(251,146,60,.12)', border: '1px solid #7c2d12', color: '#fdba74', fontSize: '12px' }}>{error}</div>}
    <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflowX: 'auto' }}><table style={{ width: '100%', minWidth: 980, fontSize: '12px', borderCollapse: 'collapse' }}><thead><tr style={{ color: '#cbd5e1', borderBottom: '1px solid #334155', textAlign: 'left', background: '#161f30' }}>{['Animal & Manual AI Status', 'Insemination Date & Sire', 'Semen Type', 'Pregnancy & Calving Timeline', 'Clinical Notes'].map(h => <th key={h} style={{ padding: '10px 12px' }}>{h}</th>)}</tr></thead><tbody>{loading ? null : rows.map(r => <tr key={r.id} style={{ borderBottom: '1px solid #1a2234' }}><td style={{ padding: '10px 12px' }}><button onClick={() => onOpenPassport ? onOpenPassport(r.tag) : setActiveModalPassport(r.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}>#{r.tag}</button><div style={{ fontSize: '10px', color: r.manualAiCandidate ? '#34d399' : '#94a3b8' }}>{r.daysAfterCalving == null ? 'No calving date / maiden animal' : `${r.daysAfterCalving} days after calving`} · {r.manualAiCandidate ? 'Manual AI entry available' : 'Active cycle or review state'}</div></td><td style={{ padding: '10px 12px' }}><div style={{ fontWeight: 'bold' }}>{r.sireCode}</div><div style={{ fontSize: '10px', color: '#94a3b8' }}>AI: {r.aiDate} • {r.inseminator}</div></td><td style={{ padding: '10px 12px' }}>{r.semenType}</td><td style={{ padding: '10px 12px' }}><div><strong>Pregnancy check:</strong> {r.pregnancyDate}</div><div style={{ fontSize: '10px' }}><strong>PD due:</strong> {r.pdDueDate}</div>{r.expectedCalving !== '-' && <div style={{ fontSize: '10px', color: '#34d399' }}>Expected calving: {r.expectedCalving} ({r.daysPregnant}d)</div>}</td><td style={{ padding: '10px 12px' }}>{r.notes}</td></tr>)}</tbody></table></div>
    <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '12px', marginTop: '12px' }}><div style={{ fontWeight: 800, color: '#fb923c', fontSize: '12px', marginBottom: '10px' }}>Insemination Success Analytics</div><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: '8px' }}>{[['1st Attempt', attempt.first], ['2nd Attempt', attempt.second], ['3rd Attempt', attempt.third]].map(([l, v]) => <div key={String(l)} style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', padding: '10px' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>{String(l)} Insemination Success Ratio</div><div style={{ fontSize: '20px', fontWeight: 900, color: '#34d399' }}>{v == null ? 'No documented outcome' : `${Number(v).toFixed(1)}%`}</div></div>)}</div></div>
    <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '12px', marginTop: '12px' }}><div style={{ fontWeight: 800, color: '#fb923c', fontSize: '12px', marginBottom: '10px' }}>Pregnancy Outcome Analytics</div><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: '8px' }}>{[['Confirmed Pregnancies', outcomes.confirmed], ['Negative PD Results', outcomes.negative], ['Calvings', outcomes.calvings], ['Miscarriages', outcomes.miscarriages], ['Abortions', outcomes.abortions], ['Pregnancy Loss Rate', lossRate == null ? 'No documented pregnancy' : `${lossRate.toFixed(1)}%`]].map(([l, v]) => <div key={String(l)} style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', padding: '10px' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>{String(l)}</div><div style={{ fontSize: '18px', fontWeight: 900, color: '#cbd5e1' }}>{v}</div></div>)}</div></div>
    {showEventModal && <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}><div style={{ background: '#111827', border: '1px solid #fb923c', borderRadius: '10px', width: '480px', padding: '22px' }}><h3 style={{ margin: '0 0 14px', color: '#fb923c', fontSize: '16px' }}><Activity size={18} /> Record Reproduction & Gestation Event</h3><div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '6px', marginBottom: '14px' }}>{(['AI', 'PD', 'CALVING', 'LOSS'] as EventMode[]).map(m => <button key={m} type="button" onClick={() => setEventType(m)} style={{ background: eventType === m ? '#fb923c' : '#1e293b', color: eventType === m ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>{m === 'AI' ? 'Insemination (AI)' : m === 'PD' ? 'Pregnancy Check / Review (PD)' : m === 'CALVING' ? 'Calving' : 'Pregnancy Loss'}</button>)}</div><form onSubmit={save} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}><div><label style={labelStyle}>Select Animal ID</label><select value={formTag} onChange={e => setFormTag(e.target.value)} disabled={!candidates.length} style={inputStyle}>{candidates.length ? candidates.map(a => <option key={a.id} value={a.id}>{a.id} ({a.breed})</option>) : <option value="">{empty}</option>}</select></div>{eventType === 'AI' && <><div style={{ background: '#0f172a', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '10px', color: '#cbd5e1' }}>Manual AI authority: Milking, Dry and Heifer animals are selectable. Advisory clock: {selected?.days_in_milk == null ? 'no calving date / maiden heifer' : `${selected.days_in_milk} days after calving`} · waiting-period guidance {selected?.eligible_to_breed ? 'passed' : 'not passed'}; operator entry remains authoritative.</div><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div><label style={labelStyle}>Sire Code / Bull</label><input required value={formSire} onChange={e => setFormSire(e.target.value)} style={inputStyle} /></div><div><label style={labelStyle}>Semen Type</label><select required value={formSemenType} onChange={e => setFormSemenType(e.target.value as typeof formSemenType)} style={inputStyle}><option value="">Select actual semen type</option><option value="Sexed Semen (90% Female)">Sexed Semen (90% Female)</option><option value="Conventional">Conventional Semen</option></select></div></div></>}{eventType === 'PD' && <div><label style={labelStyle}>PD Check / Review Result</label><select required value={formPdResult} onChange={e => setFormPdResult(e.target.value as typeof formPdResult)} style={inputStyle}><option value="">Select actual result</option><option value="POSITIVE">Positive (Confirmed Pregnant)</option><option value="NEGATIVE">Negative (Revise to Not Pregnant / Open)</option></select></div>}{eventType === 'LOSS' && <div><label style={labelStyle}>Pregnancy Loss Outcome</label><select required value={formLossOutcome} onChange={e => setFormLossOutcome(e.target.value as LossOutcome)} style={inputStyle}><option value="">Select actual outcome</option><option value="MISCARRIAGE">Miscarriage</option><option value="ABORTION">Aborted Pregnancy</option></select></div>}<div><label style={labelStyle}>{eventType === 'AI' ? 'AI Date' : eventType === 'PD' ? 'Check / Review Date' : eventType === 'CALVING' ? 'Calving Date' : 'Pregnancy Loss Date'}</label><input type="date" required value={formDate} onChange={e => setFormDate(e.target.value)} style={inputStyle} /></div>{eventType === 'AI' && <div><label style={labelStyle}>Inseminator / Vet</label><input value={formInseminator} onChange={e => setFormInseminator(e.target.value)} style={inputStyle} /></div>}<div><label style={labelStyle}>Reproductive / Clinical Notes</label><input value={formNotes} onChange={e => setFormNotes(e.target.value)} style={inputStyle} /></div><div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}><button type="button" onClick={() => setShowEventModal(false)}>Cancel</button><button type="submit" disabled={loading || !formTag || !candidates.length}>Save Breeding Entry</button></div></form></div></div>}
    {activeModalPassport && <AnimalPassportModal animalId={activeModalPassport} onClose={() => setActiveModalPassport(null)} />}
  </div>;
}
