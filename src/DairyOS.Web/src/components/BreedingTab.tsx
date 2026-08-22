import React, { useState, useMemo } from 'react';
import {
  Activity, Plus, Calendar, CheckCircle2, Heart, Sparkles,
  AlertTriangle, Filter, Search, ShieldCheck, ChevronRight
} from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';

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

export default function BreedingTab({ onOpenPassport, herdMasterList = [] }: BreedingTabProps) {
  const [activeModalPassport, setActiveModalPassport] = useState<string | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [eventType, setEventType] = useState<'HEAT' | 'AI' | 'PD' | 'CALVING'>('AI');

  const [records, setRecords] = useState<BreedingRecord[]>([
    {
      id: 'BRD-2026-01', tag: 'TD-001', status: 'Confirmed Pregnant', aiDate: '2026-03-28',
      sireCode: 'ABS-SUPERIOR-991', semenType: 'Sexed Semen (90% Female)', inseminator: 'Dr. Tariq Mahmood',
      daysPregnant: 146, expectedCalving: '2027-01-02', pdDueDate: '2026-05-02 (Confirmed +)', notes: 'Strong fetal heartbeat detected at 60d ultrasound.'
    },
    {
      id: 'BRD-2026-02', tag: 'TD-002', status: 'Inseminated (Pending PD)', aiDate: '2026-08-06',
      sireCode: 'WWS-SAHIWAL-STAR', semenType: 'Conventional', inseminator: 'Dr. Tariq Mahmood',
      daysPregnant: 15, expectedCalving: '2027-05-13', pdDueDate: '2026-09-10 (Day 35)', notes: 'Natural standing heat observed morning milking.'
    },
    {
      id: 'BRD-2026-03', tag: 'TD-003', status: 'Standing Heat', aiDate: '-',
      sireCode: 'Assigned: US-HO-882', semenType: 'Sexed Semen (90% Female)', inseminator: '-',
      daysPregnant: 0, expectedCalving: '-', pdDueDate: '-', notes: 'Clear mucus discharge & standing heat at 06:00 AM.'
    },
    {
      id: 'BRD-2026-04', tag: 'TD-005', status: 'Open / Ready', aiDate: '-',
      sireCode: 'Candidate: ABS-EASY-CALV', semenType: 'Sexed Semen (90% Female)', inseminator: '-',
      daysPregnant: 0, expectedCalving: '-', pdDueDate: '-', notes: 'Virgin Heifer (18 months, 345 kg BW) ready for 1st service.'
    },
  ]);

  // Default select to first available female if array exists
  const eligibleFemales = useMemo(() => {
    return herdMasterList.filter(a => !a.category.includes('Male') && !a.category.includes('Bull'));
  }, [herdMasterList]);

  const [formTag, setFormTag] = useState(eligibleFemales.length > 0 ? eligibleFemales[0].id : 'TD-003');
  const [formSire, setFormSire] = useState('ABS-SUPERIOR-991');
  const [formSemenType, setFormSemenType] = useState<'Sexed Semen (90% Female)' | 'Conventional'>('Sexed Semen (90% Female)');
  const [formInseminator, setFormInseminator] = useState('Dr. Tariq Mahmood');
  const [formDate, setFormDate] = useState('2026-08-21');
  const [formPdResult, setFormPdResult] = useState<'POSITIVE' | 'NEGATIVE'>('POSITIVE');
  const [formNotes, setFormNotes] = useState('');

  const openPassportHandler = (tag: string) => {
    if (onOpenPassport) onOpenPassport(tag);
    else setActiveModalPassport(tag);
  };

  const handleSaveEvent = (e: React.FormEvent) => {
    e.preventDefault();
    if (eventType === 'AI') {
      const aiDateTime = new Date(formDate);
      const pdDate = new Date(aiDateTime);
      pdDate.setDate(pdDate.getDate() + 35);
      const calvingDate = new Date(aiDateTime);
      calvingDate.setDate(calvingDate.getDate() + 280);

      const newRecord: BreedingRecord = {
        id: `BRD-2026-${(records.length + 1).toString().padStart(2, '0')}`,
        tag: formTag, status: 'Inseminated (Pending PD)', aiDate: formDate, sireCode: formSire,
        semenType: formSemenType, inseminator: formInseminator, daysPregnant: 0,
        expectedCalving: calvingDate.toISOString().split('T')[0],
        pdDueDate: `${pdDate.toISOString().split('T')[0]} (Day 35)`,
        notes: formNotes || 'AI Straw thawed at 37°C for 45s.'
      };
      setRecords([newRecord, ...records.filter(r => r.tag !== formTag)]);
    } else if (eventType === 'HEAT') {
      const newRecord: BreedingRecord = {
        id: `BRD-2026-${(records.length + 1).toString().padStart(2, '0')}`,
        tag: formTag, status: 'Standing Heat', aiDate: '-', sireCode: formSire,
        semenType: formSemenType, inseminator: '-', daysPregnant: 0, expectedCalving: '-', pdDueDate: '-',
        notes: formNotes || 'Standing heat confirmed. Optimal AI window: 12 hrs.'
      };
      setRecords([newRecord, ...records.filter(r => r.tag !== formTag)]);
    } else if (eventType === 'PD') {
      setRecords(records.map(r => {
        if (r.tag === formTag) {
          return {
            ...r,
            status: formPdResult === 'POSITIVE' ? 'Confirmed Pregnant' : 'Open / Ready',
            daysPregnant: formPdResult === 'POSITIVE' && r.aiDate !== '-' 
              ? Math.max(0, Math.floor((new Date('2026-08-22').getTime() - new Date(r.aiDate).getTime()) / (1000 * 60 * 60 * 24))) 
              : 0,
            pdDueDate: formPdResult === 'POSITIVE' ? `${formDate} (Confirmed +)` : `${formDate} (Open - Reheat due)`,
            notes: formNotes || (formPdResult === 'POSITIVE' ? 'Fetus detected healthy via rectal palpation.' : 'Open cow returned to AI breeding pool.')
          };
        }
        return r;
      }));
    }
    setShowEventModal(false);
    setFormNotes('');
  };

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#fb923c', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} /> Breeding, Artificial Insemination (AI) & Gestation Ledger
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Track estrus detection, genetic sire lineage, sexed semen straws, and 280-day gestation schedules.
          </p>
        </div>
        <button onClick={() => setShowEventModal(true)} style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
          <Plus size={15} /> + Record Breeding / AI Event
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Active Heat Standing</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fb923c' }}>{records.filter(r => r.status === 'Standing Heat').length} Animals</div>
          <div style={{ fontSize: '10px', color: '#fb923c' }}>AI Window: Next 12 Hours</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #60a5fa' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Inseminated (Pending PD)</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#60a5fa' }}>{records.filter(r => r.status === 'Inseminated (Pending PD)').length} Animals</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>PD Check Due Day 35</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a78bfa' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Confirmed Pregnant</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#a78bfa' }}>{records.filter(r => r.status === 'Confirmed Pregnant').length} Animals</div>
          <div style={{ fontSize: '10px', color: '#a78bfa' }}>Average 146d Gestation</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>First-Service Conception Rate</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>68.5%</div>
          <div style={{ fontSize: '10px', color: '#34d399' }}>Sexed Semen Target Met</div>
        </div>
      </div>

      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
              <th style={{ padding: '10px 12px' }}>Animal Tag</th>
              <th style={{ padding: '10px 12px' }}>Reproductive Status</th>
              <th style={{ padding: '10px 12px' }}>AI Date & Sire Lineage</th>
              <th style={{ padding: '10px 12px' }}>Semen Type</th>
              <th style={{ padding: '10px 12px' }}>Gestation / Calving Timeline</th>
              <th style={{ padding: '10px 12px' }}>Veterinary Clinical Notes</th>
            </tr>
          </thead>
          <tbody>
            {records.map(r => (
              <tr key={r.id} style={{ borderBottom: '1px solid #1a2234' }}>
                <td style={{ padding: '10px 12px' }}>
                  <button onClick={() => openPassportHandler(r.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, textDecoration: 'underline', fontSize: '12px' }} title="Open Biological Passport">#{r.tag}</button>
                  <div style={{ fontSize: '10px', color: '#64748b' }}>{r.id}</div>
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold', background: r.status === 'Confirmed Pregnant' ? 'rgba(167, 139, 250, 0.2)' : r.status === 'Standing Heat' ? 'rgba(251, 146, 60, 0.2)' : r.status === 'Inseminated (Pending PD)' ? 'rgba(96, 165, 250, 0.2)' : 'rgba(52, 211, 153, 0.2)', color: r.status === 'Confirmed Pregnant' ? '#a78bfa' : r.status === 'Standing Heat' ? '#fb923c' : r.status === 'Inseminated (Pending PD)' ? '#60a5fa' : '#34d399' }}>{r.status}</span>
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <div style={{ fontWeight: 'bold', color: '#fff' }}>{r.sireCode}</div>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Date: {r.aiDate} • {r.inseminator}</div>
                </td>
                <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>
                  <span style={{ color: r.semenType.includes('Sexed') ? '#ec4899' : '#94a3b8', fontWeight: 'bold', fontSize: '11px' }}>{r.semenType}</span>
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <div style={{ color: '#fff' }}><strong>PD:</strong> {r.pdDueDate}</div>
                  {r.expectedCalving !== '-' && <div style={{ fontSize: '10px', color: '#34d399' }}>Calving: {r.expectedCalving} ({r.daysPregnant}d)</div>}
                </td>
                <td style={{ padding: '10px 12px', color: '#94a3b8', fontSize: '11px' }}>{r.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showEventModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #fb923c', borderRadius: '10px', width: '480px', padding: '22px' }}>
            <h3 style={{ margin: '0 0 14px 0', color: '#fb923c', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={18} /> Record Reproduction & Gestation Event
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '14px' }}>
              <button type="button" onClick={() => setEventType('AI')} style={{ background: eventType === 'AI' ? '#fb923c' : '#1e293b', color: eventType === 'AI' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Insemination (AI)</button>
              <button type="button" onClick={() => setEventType('HEAT')} style={{ background: eventType === 'HEAT' ? '#fb923c' : '#1e293b', color: eventType === 'HEAT' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Heat Observation</button>
              <button type="button" onClick={() => setEventType('PD')} style={{ background: eventType === 'PD' ? '#fb923c' : '#1e293b', color: eventType === 'PD' ? '#0f172a' : '#cbd5e1', border: 'none', padding: '6px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}>Pregnancy Check (PD)</button>
            </div>

            <form onSubmit={handleSaveEvent} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Select Animal ID</label>
                <select value={formTag} onChange={e => setFormTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
                  {eligibleFemales.length > 0 ? (
                    eligibleFemales.map(a => (
                      <option key={a.id} value={a.id}>{a.id} ({a.breed})</option>
                    ))
                  ) : (
                    <option value="TD-003">TD-003 (Fallback Cow)</option>
                  )}
                </select>
              </div>

              {eventType === 'AI' && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div>
                      <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Sire Code / Bull</label>
                      <input type="text" required value={formSire} onChange={e => setFormSire(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                    <div>
                      <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Semen Type</label>
                      <select value={formSemenType} onChange={(e: any) => setFormSemenType(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
                        <option value="Sexed Semen (90% Female)">Sexed Semen (90% Female)</option>
                        <option value="Conventional">Conventional Semen</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div>
                      <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>AI Date</label>
                      <input type="date" value={formDate} onChange={e => setFormDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                    <div>
                      <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Inseminator / Vet</label>
                      <input type="text" value={formInseminator} onChange={e => setFormInseminator(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                  </div>
                </>
              )}

              {eventType === 'PD' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div>
                    <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>PD Check Result</label>
                    <select value={formPdResult} onChange={(e: any) => setFormPdResult(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
                      <option value="POSITIVE">Positive (Confirmed Pregnant)</option>
                      <option value="NEGATIVE">Negative (Open - Re-breed)</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Check Date</label>
                    <input type="date" value={formDate} onChange={e => setFormDate(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                </div>
              )}

              <div>
                <label style={{ fontSize: '10px', color: '#94a3b8', display: 'block', marginBottom: '3px' }}>Clinical / Behavioral Notes</label>
                <input type="text" placeholder="e.g., Mucus quality, straw lot number, ultrasound finding" value={formNotes} onChange={e => setFormNotes(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
                <button type="button" onClick={() => setShowEventModal(false)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>Cancel</button>
                <button type="submit" style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px' }}>Save Breeding Entry</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {activeModalPassport && <AnimalPassportModal animalId={activeModalPassport} onClose={() => setActiveModalPassport(null)} />}
    </div>
  );
}

