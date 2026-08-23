import React, { useEffect, useMemo, useState } from 'react';
import { Activity, Plus } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';
import { apiUrl } from '../config/api';

interface BreedingRecord {
  id: string;
  tag: string;
  status: 'Standing Heat' | 'Inseminated (Pending PD)' | 'Confirmed Pregnant' | 'Dry' | 'Open / Ready';
  aiDate: string;
  sireCode: string;
  semenType: 'Sexed Semen (90% Female)' | 'Conventional';
  inseminator: string;
  daysPregnant: number;
  expectedCalving: string;
  pdDueDate: string;
  notes: string;
}

interface HerdAnimal {
  id: string;
  breed: string;
  category: string;
}

interface BreedingTabProps {
  onOpenPassport?: (tag: string) => void;
  herdMasterList?: HerdAnimal[];
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(apiUrl(path));
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

async function postJson<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(apiUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const body = await response.json() as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Preserve the status when the response is not JSON.
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

function normaliseEvent(value: unknown): string {
  return String(value || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
}

function dateOnly(value: unknown): string {
  if (!value) return '-';
  const parsed = new Date(String(value));
  return Number.isNaN(parsed.getTime()) ? String(value).slice(0, 10) : parsed.toISOString().split('T')[0];
}

function addDays(value: string, days: number): string {
  if (value === '-') return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  parsed.setDate(parsed.getDate() + days);
  return parsed.toISOString().split('T')[0];
}

export default function BreedingTab({ onOpenPassport, herdMasterList = [] }: BreedingTabProps) {
  const [activeModalPassport, setActiveModalPassport] = useState<string | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [eventType, setEventType] = useState<'HEAT' | 'AI' | 'PD' | 'CALVING'>('AI');
  const [records, setRecords] = useState<BreedingRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conceptionRate, setConceptionRate] = useState<number | null>(null);

  const herdKey = herdMasterList.map(animal => animal.id).join('|');
  const eligibleFemales = useMemo(() => {
    return herdMasterList.filter(a => !a.category.includes('Male') && !a.category.includes('Bull'));
  }, [herdKey]);

  const [formTag, setFormTag] = useState('');
  const [formSire, setFormSire] = useState('');
  const [formSemenType, setFormSemenType] = useState<'Sexed Semen (90% Female)' | 'Conventional'>('Sexed Semen (90% Female)');
  const [formInseminator, setFormInseminator] = useState('Dr. Tariq Mahmood');
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0]);
  const [formPdResult, setFormPdResult] = useState<'POSITIVE' | 'NEGATIVE'>('POSITIVE');
  const [formNotes, setFormNotes] = useState('');

  useEffect(() => {
    if (eligibleFemales.length > 0 && !eligibleFemales.some(animal => animal.id === formTag)) {
      setFormTag(eligibleFemales[0].id);
    }
    if (eligibleFemales.length === 0 && formTag) setFormTag('');
  }, [herdKey, formTag]);

  const loadRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const [breeding, overview] = await Promise.all([
        getJson<any[]>('/farm/breeding'),
        getJson<any>('/farm/reproduction/overview'),
      ]);

      const mapped = breeding.map((item, index): BreedingRecord => {
        const event = normaliseEvent(item.event_type);
        const timestamp = dateOnly(item.timestamp || item.date);
        const result = String(item.result || '').toUpperCase();
        const status: BreedingRecord['status'] =
          event.includes('heat') ? 'Standing Heat' :
          event.includes('insemin') || event === 'ai' ? 'Inseminated (Pending PD)' :
          event.includes('pregnancy_confirmed') || (event.includes('pregnancy') && result.includes('POSITIVE')) ? 'Confirmed Pregnant' :
          event.includes('pregnancy_negative') || (event.includes('pregnancy') && result.includes('NEGATIVE')) ? 'Open / Ready' :
          event.includes('dry') ? 'Dry' :
          'Open / Ready';

        const aiDate = event.includes('insemin') || event === 'ai' ? timestamp : '-';
        const confirmedAt = status === 'Confirmed Pregnant' ? (item.pregnancy_confirmed_date || item.timestamp || item.date) : null;
        const confirmedMs = confirmedAt ? new Date(String(confirmedAt)).getTime() : NaN;
        const pregnantDays = Number.isNaN(confirmedMs) ? 0 : Math.max(0, Math.floor((Date.now() - confirmedMs) / 86400000));
        const semen = String(item.semen_or_bull || item.sire_code || '');
        const semenType = semen.toLowerCase().includes('sexed') ? 'Sexed Semen (90% Female)' : 'Conventional';

        return {
          id: String(item.record_id ?? item.id ?? `BRD-${index + 1}`),
          tag: String(item.animal_id || ''),
          status,
          aiDate,
          sireCode: semen || '-',
          semenType,
          inseminator: String(item.technician || item.inseminator || '-'),
          daysPregnant: pregnantDays,
          expectedCalving: aiDate === '-' ? '-' : addDays(aiDate, 280),
          pdDueDate: aiDate === '-' ? '-' : addDays(aiDate, 35),
          notes: String(item.notes || item.result || 'Reproductive event recorded.'),
        };
      });

      setRecords(mapped.sort((a, b) => b.aiDate.localeCompare(a.aiDate)));
      const rate = overview?.conception_rate_percent;
      setConceptionRate(rate === null || rate === undefined ? null : Number(rate));
    } catch (loadError) {
      setRecords([]);
      setConceptionRate(null);
      setError(loadError instanceof Error ? loadError.message : 'Unable to load persisted breeding records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRecords();
  }, [herdKey]);

  const openPassportHandler = (tag: string) => {
    if (onOpenPassport) onOpenPassport(tag);
    else setActiveModalPassport(tag);
  };

  const handleSaveEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTag) return;
    setError(null);

    try {
      let event_type = 'insemination';
      let result = 'RECORDED';
      if (eventType === 'HEAT') event_type = 'heat_detected';
      if (eventType === 'PD') {
        event_type = formPdResult === 'POSITIVE' ? 'pregnancy_confirmed' : 'pregnancy_negative';
        result = formPdResult;
      }
      if (eventType === 'CALVING') event_type = 'calving';

      await postJson('/farm/breeding', {
        animal_id: formTag,
        event_type,
        technician: formInseminator,
        result,
        semen_or_bull: eventType === 'AI' ? `${formSemenType} — ${formSire || 'Unspecified'}` : formSire || null,
        notes: formNotes || undefined,
        operator: formInseminator,
        timestamp: formDate,
      });

      setShowEventModal(false);
      setFormNotes('');
      await loadRecords();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save the breeding event.');
    }
  };

  const activeHeat = records.filter(r => r.status === 'Standing Heat').length;
  const pendingPd = records.filter(r => r.status === 'Inseminated (Pending PD)').length;
  const confirmedPregnant = records.filter(r => r.status === 'Confirmed Pregnant').length;
  const gestationDays = records.filter(r => r.status === 'Confirmed Pregnant' && r.daysPregnant > 0).map(r => r.daysPregnant);
  const averageGestation = gestationDays.length > 0 ? Math.round(gestationDays.reduce((sum, value) => sum + value, 0) / gestationDays.length) : null;

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}><div><h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#fb923c', display: 'flex', alignItems: 'center', gap: '8px' }}><Activity size={20} /> Breeding, Artificial Insemination (AI) & Gestation Ledger</h2><p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Track estrus detection, genetic sire lineage, sexed semen straws, and 280-day gestation schedules.</p></div><button onClick={() => setShowEventModal(true)} style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}><Plus size={15} /> + Record Breeding / AI Event</button></div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}><div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Active Heat Standing</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fb923c' }}>{activeHeat} Animals</div><div style={{ fontSize: '10px', color: '#fb923c' }}>AI Window: Next 12 Hours</div></div><div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #60a5fa' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Inseminated (Pending PD)</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: '#60a5fa' }}>{pendingPd} Animals</div><div style={{ fontSize: '10px', color: '#64748b' }}>PD Check Due Day 35</div></div><div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a78bfa' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Confirmed Pregnant</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: '#a78bfa' }}>{confirmedPregnant} Animals</div><div style={{ fontSize: '10px', color: '#a78bfa' }}>{averageGestation === null ? 'No confirmed pregnancy data' : `Average ${averageGestation}d Gestation`}</div></div><div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>First-Service Conception Rate</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>{conceptionRate === null ? '—' : `${conceptionRate.toFixed(1)}%`}</div><div style={{ fontSize: '10px', color: '#34d399' }}>Calculated from persisted reproductive outcomes</div></div></div>
      {error && <div style={{ marginBottom: '12px', padding: '10px 12px', borderRadius: '6px', background: 'rgba(251,146,60,0.12)', border: '1px solid #7c2d12', color: '#fdba74', fontSize: '12px' }}>{error}</div>}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}><table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}><thead><tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}><th style={{ padding: '10px 12px' }}>Animal Tag</th><th style={{ padding: '10px 12px' }}>Reproductive Status</th><th style={{ padding: '10px 12px' }}>AI Date & Sire Lineage</th><th style={{ padding: '10px 12px' }}>Semen Type</th><th style={{ padding: '10px 12px' }}>Gestation / Calving Timeline</th><th style={{ padding: '10px 12px' }}>Veterinary Clinical Notes</th></tr></thead><tbody>{loading ? null : records.map(r => <tr key={r.id} style={{ borderBottom: '1px solid #1a2234' }}><td style={{ padding: '10px 12px' }}><button onClick={() => openPassportHandler(r.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, textDecoration: 'underline', fontSize: '12px' }} title="Open Biological Passport">#{r.tag}</button><div style={{ fontSize: '10px', color: '#64748b' }}>{r.id}</div></td><td style={{ padding: '10px 12px' }}><span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold', background: r.status === 'Confirmed Pregnant' ? 'rgba(167, 139, 250, 0.2)' : r.status === 'Standing Heat' ? 'rgba(251, 146, 60, 0.2)' : r.status === 'Inseminated (Pending PD)' ? 'rgba(96, 165, 250, 0.2)' : 'rgba(52, 211, 153, 0.2)', color: r.status === 'Confirmed Pregnant' ? '#a78bfa' : r.status === 'Standing Heat' ? '#fb923c' : r.status === 'Inseminated (Pending PD)' ? '#60a5fa' : '#34d399' }}>{r.status}</span></td><td style={{ padding: '10px 12px' }}><div style={{ fontWeight: 'bold', color: '#fff' }}>{r.sireCode}</div><div style={{ fontSize: '10px', color: '#94a3b8' }}>Date: {r.aiDate} • {r.inseminator}</div></td><td style={{ padding: '10px 12px', color: '#cbd5e1' }}><span style={{ color: r.semenType.includes('Sexed') ? '#ec4899' : '#94a3b8', fontWeight: 'bold', fontSize: '11px' }}>{r.semenType}</span></td><td style={{ padding: '10px 12px' }}><div style={{ color: '#fff' }}><strong>PD:</strong> {r.pdDueDate}</div>{r.expectedCalving !== '-' && <div style={{ fontSize: '10px', color: '#34d399' }}>Calving: {r.expectedCalving} ({r.daysPregnant}d)</div>}</td><td style={{ padding: '10px 12px', color: '#94a3b8', fontSize: '11px' }}>{r.notes}</td></tr>)}</tbody></table></div>
      {showEventModal && <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}><div style={{ background: '#111827', border: '1px solid #fb923c', borderRadius: '10px', width: '480px', padding: '22px' }}><h3 style={{ margin: '0 0 14px 0', color: '#fb923c', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}><Activity size={18} /> Record Reproduction & Gestation Event</h3><div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '14px' }}><button type="button" onClick={() => setEventType('AI')} style={{ background: eventType === 'AI' ? '#fb923c' : '#1e293b', color: eventType === 'AI' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Insemination (AI)</button><button type="button" onClick={() => setEventType('HEAT')} style={{ background: eventType === 'HEAT' ? '#fb923c' : '#1e293b', color: eventType === 'HEAT' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Heat Observation</button><button type="button" onClick={() => setEventType('PD')} style={{ background: eventType === 'PD' ? '#fb923c' : '#1e293b', color: eventType === 'PD' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Pregnancy Check (PD)</button></div><form onSubmit={handleSaveEvent} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Select Animal ID</label><select value={formTag} onChange={e => setFormTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>{eligibleFemales.length > 0 ? eligibleFemales.map(a => <option key={a.id} value={a.id}>{a.id} ({a.breed})</option>) : <option value="" disabled>No eligible female animals available</option>}</select></div>{eventType === 'AI' && <><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Sire Code / Bull</label><input type="text" required value={formSire} onChange={e => setFormSire(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Semen Type</label><select value={formSemenType} onChange={e => setFormSemenType(e.target.value as 'Sexed Semen (90% Female)' | 'Conventional')} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}><option value="Sexed Semen (90% Female)">Sexed Semen (90% Female)</option><option value="Conventional">Conventional Semen</option></select></div></div><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>AI Date</label><input type="date" value={formDate} onChange={e => setFormDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Inseminator / Vet</label><input type="text" value={formInseminator} onChange={e => setFormInseminator(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div></div></>}{eventType === 'PD' && <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>PD Check Result</label><select value={formPdResult} onChange={e => setFormPdResult(e.target.value as 'POSITIVE' | 'NEGATIVE')} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}><option value="POSITIVE">Positive (Confirmed Pregnant)</option><option value="NEGATIVE">Negative (Open - Re-breed)</option></select></div><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Check Date</label><input type="date" value={formDate} onChange={e => setFormDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div></div>}<div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Clinical / Behavioral Notes</label><input type="text" placeholder="e.g., Mucus quality, straw lot number, ultrasound finding" value={formNotes} onChange={e => setFormNotes(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div><div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}><button type="button" onClick={() => setShowEventModal(false)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>Cancel</button><button type="submit" disabled={loading || !formTag} style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px' }}>Save Breeding Entry</button></div></form></div></div>}
      {activeModalPassport && <AnimalPassportModal animalId={activeModalPassport} onClose={() => setActiveModalPassport(null)} />}
    </div>
  );
}
