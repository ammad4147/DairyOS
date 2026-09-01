import React, { useEffect, useMemo, useState } from 'react';
import { Activity, Plus } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';
import { apiUrl } from '../config/api';

interface BreedingRecord {
  id: string;
  tag: string;
  status: 'Inseminated (Pending PD)' | 'Confirmed Pregnant' | 'Dry' | 'Open / Ready' | 'Lactating / Waiting';
  aiDate: string;
  pregnancyDate: string;
  sireCode: string;
  semenType: 'Sexed Semen (90% Female)' | 'Conventional' | 'Not recorded';
  inseminator: string;
  daysPregnant: number;
  expectedCalving: string;
  pdDueDate: string;
  notes: string;
  daysAfterCalving: number | null;
  eligibleToBreed: boolean;
}

interface CurrentReproductiveState {
  animal_id: string;
  state: string;
  reproductive_status: string;
  pregnancy_status: string;
  pregnancy_confirmed_date?: string | null;
  expected_calving?: string | null;
  last_insemination?: string | null;
  last_calving?: string | null;
  days_in_milk?: number | null;
  eligible_to_breed?: boolean;
  data_status: string;
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

function normaliseState(value: unknown): string {
  return String(value || '').trim().toUpperCase();
}

function uiStatusFromState(value: string): BreedingRecord['status'] {
  switch (normaliseState(value)) {
    case 'INSEMINATED':
    case 'BRED':
      return 'Inseminated (Pending PD)';
    case 'PREGNANT':
      return 'Confirmed Pregnant';
    case 'OPEN':
      return 'Open / Ready';
    case 'CALVED':
      return 'Open / Ready';
    case 'DRY_OFF':
      return 'Dry';
    case 'LACTATING':
      return 'Lactating / Waiting';
    default:
      return 'Open / Ready';
  }
}

function statusOptionsForState(
  value: string,
): Array<{
  value: string;
  label: BreedingRecord['status'];
}> {
  switch (normaliseState(value)) {
    case 'INSEMINATED':
    case 'BRED':
      return [
        { value: 'PREGNANT', label: 'Confirmed Pregnant' },
        { value: 'OPEN', label: 'Open / Ready' },
      ];
    case 'PREGNANT':
      return [
        { value: 'CALVED', label: 'Open / Ready' },
      ];
    default:
      return [];
  }
}

export default function BreedingTab({ onOpenPassport, herdMasterList = [] }: BreedingTabProps) {
  const [activeModalPassport, setActiveModalPassport] = useState<string | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [eventType, setEventType] = useState<'AI' | 'PD' | 'CALVING'>('AI');
  const [records, setRecords] = useState<BreedingRecord[]>([]);
  const [currentStates, setCurrentStates] = useState<CurrentReproductiveState[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conceptionRate, setConceptionRate] = useState<number | null>(null);
  const [attemptSuccess, setAttemptSuccess] = useState({
    first: null as number | null,
    second: null as number | null,
    third: null as number | null,
  });

  const herdKey = herdMasterList.map(animal => animal.id).join('|');
  const eligibleFemales = useMemo(() => {
    return herdMasterList.filter(a => !a.category.includes('Male') && !a.category.includes('Bull'));
  }, [herdKey]);

  const [formTag, setFormTag] = useState('');
  const [formSire, setFormSire] = useState('');
  const [formSemenType, setFormSemenType] = useState<'Sexed Semen (90% Female)' | 'Conventional' | ''>('');
  const [formInseminator, setFormInseminator] = useState('');
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0]);
  const [formPdResult, setFormPdResult] = useState<'POSITIVE' | 'NEGATIVE' | ''>('');
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
      const [breeding, overview, states] = await Promise.all([
        getJson<any[]>('/farm/breeding'),
        getJson<any>('/farm/reproduction/overview'),
        Promise.all(
          eligibleFemales.map(animal =>
            getJson<CurrentReproductiveState>(
              `/farm/animals/${encodeURIComponent(animal.id)}/reproduction`,
            ),
          ),
        ),
      ]);

      const liveStates = states.filter(
        state => state.data_status === 'LIVE_PERSISTED_DATA',
      );

      setCurrentStates(liveStates);

      // The table is a CURRENT breeding ledger: one row per animal.
      // Historical events remain in the Animal Passport.
      const latestByAnimal = new Map<string, any>();

      for (const item of breeding) {
        const animalId = String(item.animal_id || '');

        if (!animalId) continue;

        const timestamp = new Date(
          String(item.timestamp || item.date || ''),
        ).getTime();

        const existing = latestByAnimal.get(animalId);
        const existingTimestamp = existing
          ? new Date(
              String(existing.timestamp || existing.date || ''),
            ).getTime()
          : -Infinity;

        if (!existing || timestamp >= existingTimestamp) {
          latestByAnimal.set(animalId, item);
        }
      }

      const mapped = Array.from(latestByAnimal.entries())
        .map(([animalId, item], index): BreedingRecord => {
          const animalEvents = breeding
            .filter(record => String(record.animal_id || '') === animalId)
            .sort((a, b) => new Date(String(a.timestamp || a.date || '')).getTime() - new Date(String(b.timestamp || b.date || '')).getTime());
          const lastMatching = (predicate: (eventName: string, result: string) => boolean) =>
            [...animalEvents].reverse().find(record => predicate(normaliseEvent(record.event_type), String(record.result || '').toUpperCase()));
          const aiRecord = lastMatching(eventName => eventName.includes('insemin') || eventName === 'ai');
          const pregnancyRecord = lastMatching((eventName, eventResult) => eventName.includes('pregnancy') && (eventName.includes('confirmed') || eventResult.includes('POSITIVE') || eventName.includes('negative') || eventResult.includes('NEGATIVE')));
          const animalState = liveStates.find(
            state => state.animal_id === animalId,
          );

          const event = normaliseEvent(item.event_type);
          const eventTimestamp = item.timestamp || item.date;
          const eventDate = dateOnly(eventTimestamp);
          const result = String(item.result || '').toUpperCase();

          const status = animalState
            ? uiStatusFromState(animalState.state)
            : (
                event.includes('insemin') || event === 'ai'
                    ? 'Inseminated (Pending PD)'
                    : event.includes('pregnancy_confirmed')
                      || (
                        event.includes('pregnancy')
                        && result.includes('POSITIVE')
                      )
                      ? 'Confirmed Pregnant'
                      : event.includes('pregnancy_negative')
                        || (
                          event.includes('pregnancy')
                          && result.includes('NEGATIVE')
                        )
                          ? 'Open / Ready'
                          : event.includes('dry')
                            ? 'Dry'
                            : 'Open / Ready'
              );

          const aiDate = animalState?.last_insemination
            ? dateOnly(animalState.last_insemination)
            : aiRecord ? dateOnly(aiRecord.timestamp || aiRecord.date) : '-';

          const confirmedAt = (
            status === 'Confirmed Pregnant'
            && (
              animalState?.pregnancy_confirmed_date
              || eventTimestamp
            )
          )
            ? (
                animalState?.pregnancy_confirmed_date
                || eventTimestamp
              )
            : null;

          const confirmedMs = confirmedAt
            ? new Date(String(confirmedAt)).getTime()
            : NaN;

          const pregnantDays = Number.isNaN(confirmedMs)
            ? 0
            : Math.max(
                0,
                Math.floor(
                  (Date.now() - confirmedMs) / 86400000,
                ),
              );

          const semen = String(
            aiRecord?.semen_or_bull
            || aiRecord?.sire_code
            || '',
          );

          const semenType = semen
            .toLowerCase()
            .includes('sexed')
            ? 'Sexed Semen (90% Female)'
            : semen
              ? 'Conventional'
              : 'Not recorded';

          return {
            id: String(
              item.record_id
              || item.id
              || `BRD-${index + 1}`,
            ),
            tag: animalId,
            status,
            aiDate,
            pregnancyDate: pregnancyRecord ? dateOnly(pregnancyRecord.timestamp || pregnancyRecord.date) : '-',
            sireCode: semen || '-',
            semenType,
            inseminator: String(
              aiRecord?.technician
              || aiRecord?.inseminator
              || '-',
            ),
            daysPregnant: pregnantDays,
            expectedCalving:
              aiDate === '-'
                ? '-'
                : addDays(aiDate, 283),
            pdDueDate:
              aiDate === '-'
                ? '-'
                : addDays(aiDate, 35),
            notes: String(
              pregnancyRecord?.notes
              || pregnancyRecord?.result
              || item.notes
              || item.result
              || 'Reproductive event recorded.',
            ),
            daysAfterCalving:
              animalState?.days_in_milk === null || animalState?.days_in_milk === undefined
                ? null
                : Number(animalState.days_in_milk),
            eligibleToBreed: Boolean(animalState?.eligible_to_breed),
          };
        })
        .sort((a, b) => b.aiDate.localeCompare(a.aiDate));

      setRecords(mapped);

      const rate = overview?.conception_rate_percent;

      setConceptionRate(
        rate === null || rate === undefined
          ? null
          : Number(rate),
      );
      setAttemptSuccess({
        first: overview?.first_attempt_success_ratio_percent == null ? null : Number(overview.first_attempt_success_ratio_percent),
        second: overview?.second_attempt_success_ratio_percent == null ? null : Number(overview.second_attempt_success_ratio_percent),
        third: overview?.third_attempt_success_ratio_percent == null ? null : Number(overview.third_attempt_success_ratio_percent),
      });
    } catch (loadError) {
      setRecords([]);
      setCurrentStates([]);
      setConceptionRate(null);
      setAttemptSuccess({ first: null, second: null, third: null });
      setError(
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load persisted breeding records.',
      );
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

  const handleStatusChange = async (
    animalId: string,
    nextStatus: string,
  ) => {
    const state = currentStates.find(
      value => value.animal_id === animalId,
    );

    if (!state || !nextStatus) return;

    const options = statusOptionsForState(state.state);
    const selected = options.find(
      option => option.value === nextStatus,
    );

    if (!selected) {
      setError(
        `Invalid reproductive status transition from ${state.state}.`,
      );
      return;
    }

    let eventType: string;
    let result: string;

    switch (nextStatus) {
      case 'INSEMINATED':
        eventType = 'insemination';
        result = 'COMPLETED';
        break;

      case 'PREGNANT':
        eventType = 'pregnancy_confirmed';
        result = 'CONFIRMED';
        break;

      case 'OPEN':
        eventType = 'pregnancy_negative';
        result = 'NEGATIVE';
        break;

      case 'CALVED':
        eventType = 'calving';
        result = 'COMPLETED';
        break;


      default:
        setError(
          `Unsupported reproductive status: ${nextStatus}.`,
        );
        return;
    }

    setError(null);

    try {
      await postJson('/farm/breeding', {
        animal_id: animalId,
        event_type: eventType,
        technician: formInseminator.trim() || 'WEB',
        result,
        operator: formInseminator.trim() || 'WEB',
        notes:
          `Status transition: ${state.state} -> ${nextStatus}`,
      });

      await loadRecords();
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : 'Unable to change the breeding status.',
      );
    }
  };
  const handleSaveEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTag) return;
    setError(null);

    try {
      let event_type = 'insemination';
      let result = 'RECORDED';
      if (eventType === 'PD') {
        if (!formPdResult) throw new Error('Select the actual pregnancy-diagnosis result.');
        event_type = formPdResult === 'POSITIVE' ? 'pregnancy_confirmed' : 'pregnancy_negative';
        result = formPdResult;
      }
      if (eventType === 'CALVING') event_type = 'calving';
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
      await loadRecords();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save the breeding event.');
    }
  };

  const pendingPd = currentStates.filter(state => state.state === 'INSEMINATED' || state.state === 'BRED').length;
  const confirmedPregnantStates = currentStates.filter(state => state.state === 'PREGNANT');
  const confirmedPregnant = confirmedPregnantStates.length;
  const inseminatedCycle = currentStates.filter(
    state => state.state === 'INSEMINATED' || state.state === 'BRED' || state.state === 'PREGNANT',
  ).length;
  const pregnancyRatio = inseminatedCycle > 0 ? (confirmedPregnant / inseminatedCycle) * 100 : 0;
  const eligibleToBreed = currentStates.filter(
    state => Boolean(state.eligible_to_breed) && state.state !== 'PREGNANT',
  ).length;
  const gestationDays = confirmedPregnantStates
    .map(state => state.pregnancy_confirmed_date)
    .filter((value): value is string => Boolean(value))
    .map(value => Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 86400000)));
  const averageGestation = gestationDays.length > 0
    ? Math.round(gestationDays.reduce((sum, value) => sum + value, 0) / gestationDays.length)
    : null;

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}><div><h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#fb923c', display: 'flex', alignItems: 'center', gap: '8px' }}><Activity size={20} /> Breeding, Artificial Insemination (AI) & Gestation Ledger</h2><p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Manage insemination timing using days after calving, breeding readiness, sire lineage, pregnancy diagnosis, and 283-day gestation schedules.</p></div><button onClick={() => setShowEventModal(true)} style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}><Plus size={15} /> + Record Breeding / AI Event</button></div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(170px,1fr))', gap: '12px', marginBottom: '16px' }}><div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Eligible to Breed</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fb923c' }}>{eligibleToBreed} Animals</div><div style={{ fontSize: '10px', color: '#fb923c' }}>Based on post-calving waiting period and pregnancy state</div></div><div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #60a5fa' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Inseminated (Pending PD)</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: '#60a5fa' }}>{pendingPd} Animals</div><div style={{ fontSize: '10px', color: '#64748b' }}>PD Check Due Day 35</div></div><div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a78bfa' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Confirmed Pregnant</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: '#a78bfa' }}>{confirmedPregnant} Animals</div><div style={{ fontSize: '10px', color: '#a78bfa' }}>{averageGestation === null ? 'No confirmed pregnancy data' : `Average ${averageGestation}d Gestation`}</div></div><div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Pregnancy Ratio</div><div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>{pregnancyRatio.toFixed(1)}%</div><div style={{ fontSize: '10px', color: '#34d399' }}>Pregnant / inseminated reproductive cycle</div></div></div>
      {error && <div style={{ marginBottom: '12px', padding: '10px 12px', borderRadius: '6px', background: 'rgba(251,146,60,0.12)', border: '1px solid #7c2d12', color: '#fdba74', fontSize: '12px' }}>{error}</div>}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflowX: 'auto' }}><table style={{ width: '100%', minWidth: 980, fontSize: '12px', borderCollapse: 'collapse' }}><thead><tr style={{ color: '#cbd5e1', borderBottom: '1px solid #334155', textAlign: 'left', background: '#161f30' }}><th style={{ padding: '10px 12px' }}>Animal &amp; Breeding Readiness</th><th style={{ padding: '10px 12px' }}>Current Stage</th><th style={{ padding: '10px 12px' }}>Insemination Date &amp; Sire</th><th style={{ padding: '10px 12px' }}>Semen Type</th><th style={{ padding: '10px 12px' }}>Pregnancy &amp; Calving Timeline</th><th style={{ padding: '10px 12px' }}>Clinical Notes</th></tr></thead><tbody>{loading ? null : records.map(r => <tr key={r.id} style={{ borderBottom: '1px solid #1a2234' }}><td style={{ padding: '10px 12px' }}><button onClick={() => openPassportHandler(r.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, textDecoration: 'underline', fontSize: '12px' }} title="Open Biological Passport">#{r.tag}</button><div style={{ fontSize: '10px', color: r.eligibleToBreed ? '#34d399' : '#94a3b8', marginTop:3 }}>{r.daysAfterCalving === null ? 'No calving date' : `${r.daysAfterCalving} days after calving`} · {r.eligibleToBreed ? 'Eligible to breed' : 'Not yet eligible'}</div></td><td style={{ padding: '10px 12px' }}>
  {(() => {
    const state = currentStates.find(
      value => value.animal_id === r.tag,
    );

    const options = state
      ? statusOptionsForState(state.state)
      : [];

    const isConfirmed =
      r.status === 'Confirmed Pregnant';
    const isPending =
      r.status === 'Inseminated (Pending PD)';

    const background = isConfirmed
      ? 'rgba(167, 139, 250, 0.2)'
      : isPending
        ? 'rgba(96, 165, 250, 0.2)'
        : 'rgba(52, 211, 153, 0.2)';

    const color = isConfirmed
      ? '#a78bfa'
      : isPending
        ? '#60a5fa'
        : '#34d399';

    return (
      <select
        value={r.status}
        onChange={event => {
          void handleStatusChange(
            r.tag,
            event.target.value,
          );
        }}
        title="Change current reproductive status. Previous events remain in the Animal Passport."
        style={{
          padding: '3px 8px',
          borderRadius: '4px',
          fontSize: '10px',
          fontWeight: 'bold',
          background,
          color,
          border: `1px solid ${color}`,
          cursor: options.length
            ? 'pointer'
            : 'default',
          maxWidth: '190px',
        }}
        disabled={options.length === 0}
      >
        <option value={r.status}>
          {r.status}
        </option>

        {options
          .filter(
            option => option.label !== r.status,
          )
          .map(option => (
            <option
              key={option.value}
              value={option.value}
            >
              {option.label}
            </option>
          ))}
      </select>
    );
  })()}
</td><td style={{ padding: '10px 12px' }}><div style={{ fontWeight: 'bold', color: '#fff' }}>{r.sireCode}</div><div style={{ fontSize: '10px', color: '#94a3b8' }}>AI: {r.aiDate} • {r.inseminator}</div></td><td style={{ padding: '10px 12px', color: '#cbd5e1' }}><span style={{ color: r.semenType.includes('Sexed') ? '#f472b6' : '#cbd5e1', fontWeight: 'bold', fontSize: '11px' }}>{r.semenType}</span></td><td style={{ padding: '10px 12px' }}><div style={{ color: r.pregnancyDate==='-'?'#94a3b8':'#a78bfa' }}><strong>Pregnancy check:</strong> {r.pregnancyDate}</div><div style={{ color: '#cbd5e1', fontSize: '10px', marginTop:3 }}><strong>PD due:</strong> {r.pdDueDate}</div>{r.expectedCalving !== '-' && <div style={{ fontSize: '10px', color: '#34d399', marginTop:3 }}>Expected calving: {r.expectedCalving} ({r.daysPregnant}d)</div>}</td><td style={{ padding: '10px 12px', color: '#cbd5e1', fontSize: '11px' }}>{r.notes}</td></tr>)}</tbody></table></div>
      <div style={{ background:'#111827', border:'1px solid #1f2937', borderRadius:'8px', padding:'12px', marginTop:'12px' }}><div style={{ fontWeight:800, color:'#fb923c', fontSize:'12px', marginBottom:'10px' }}>Insemination Success Analytics</div><div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))', gap:'8px' }}>{[['1st Attempt',attemptSuccess.first],['2nd Attempt',attemptSuccess.second],['3rd Attempt',attemptSuccess.third]].map(([label,value])=><div key={String(label)} style={{ background:'#0f172a', border:'1px solid #334155', borderRadius:'6px', padding:'10px' }}><div style={{ fontSize:'10px', color:'#94a3b8' }}>{String(label)} Insemination Success Ratio</div><div style={{ fontSize:'20px', fontWeight:900, color:'#34d399', marginTop:'4px' }}>{value===null?'No documented outcome':`${Number(value).toFixed(1)}%`}</div><div style={{ fontSize:'9px', color:'#64748b', marginTop:'3px' }}>Confirmed pregnancies / services with documented pregnancy outcome</div></div>)}</div></div>
      {showEventModal && <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}><div style={{ background: '#111827', border: '1px solid #fb923c', borderRadius: '10px', width: '480px', padding: '22px' }}><h3 style={{ margin: '0 0 14px 0', color: '#fb923c', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}><Activity size={18} /> Record Reproduction & Gestation Event</h3><div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '14px' }}><button type="button" onClick={() => setEventType('AI')} style={{ background: eventType === 'AI' ? '#fb923c' : '#1e293b', color: eventType === 'AI' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Insemination (AI)</button><button type="button" onClick={() => setEventType('PD')} style={{ background: eventType === 'PD' ? '#fb923c' : '#1e293b', color: eventType === 'PD' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Pregnancy Check (PD)</button><button type="button" onClick={() => setEventType('CALVING')} style={{ background: eventType === 'CALVING' ? '#fb923c' : '#1e293b', color: eventType === 'CALVING' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Calving</button></div><form onSubmit={handleSaveEvent} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Select Animal ID</label><select value={formTag} onChange={e => setFormTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>{eligibleFemales.length > 0 ? eligibleFemales.map(a => <option key={a.id} value={a.id}>{a.id} ({a.breed})</option>) : <option value="" disabled>No eligible female animals available</option>}</select></div>{eventType === 'AI' && <><div style={{ background:'#0f172a', border:'1px solid #334155', padding:'8px', borderRadius:'4px', fontSize:'10px', color:'#cbd5e1' }}>{(() => { const state=currentStates.find(x=>x.animal_id===formTag); const days=state?.days_in_milk; return `Breeding readiness: ${days===null||days===undefined?'No calving date':`${days} days after calving`} · ${state?.eligible_to_breed?'Eligible by waiting-period rule':'Review condition / waiting period before service'}`; })()}</div><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Sire Code / Bull</label><input type="text" required value={formSire} onChange={e => setFormSire(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Semen Type</label><select required value={formSemenType} onChange={e => setFormSemenType(e.target.value as 'Sexed Semen (90% Female)' | 'Conventional' | '')} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}><option value="">Select actual semen type</option><option value="Sexed Semen (90% Female)">Sexed Semen (90% Female)</option><option value="Conventional">Conventional Semen</option></select></div></div><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>AI Date</label><input type="date" required value={formDate} onChange={e => setFormDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Inseminator / Vet</label><input type="text" value={formInseminator} onChange={e => setFormInseminator(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div></div></>}{eventType === 'PD' && <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>PD Check Result</label><select required value={formPdResult} onChange={e => setFormPdResult(e.target.value as 'POSITIVE' | 'NEGATIVE' | '')} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}><option value="">Select actual result</option><option value="POSITIVE">Positive (Confirmed Pregnant)</option><option value="NEGATIVE">Negative (Open - Re-breed)</option></select></div><div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Check Date</label><input type="date" required value={formDate} onChange={e => setFormDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div></div>}{eventType === 'CALVING' && <div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Calving Date</label><input type="date" required value={formDate} onChange={e => setFormDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} /></div>}<div><label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Reproductive / Clinical Notes</label><input type="text" placeholder="e.g., body condition, uterine recovery, straw lot, ultrasound finding" value={formNotes} onChange={e => setFormNotes(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }} /></div><div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}><button type="button" onClick={() => setShowEventModal(false)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>Cancel</button><button type="submit" disabled={loading || !formTag} style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px' }}>Save Breeding Entry</button></div></form></div></div>}
      {activeModalPassport && <AnimalPassportModal animalId={activeModalPassport} onClose={() => setActiveModalPassport(null)} />}
    </div>
  );
}
