import React, { useEffect, useState } from 'react';
import { HeartPulse, Plus, X, Syringe, AlertTriangle, ShieldCheck, FileText } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';
import { apiUrl } from '../config/api';

interface HerdAnimal {
  id: string;
  breed: string;
  category: string;
  status: string;
}

interface HealthRecord {
  id: string;
  tag: string;
  date: string;
  type: 'Treatment' | 'Vaccination' | 'Checkup';
  condition: string;
  medication: string;
  veterinarian: string;
  withdrawalDays: number;
  status: 'Active' | 'Logged' | 'Resolved' | 'Preventative';
  cost: number;
}

interface HealthTabProps {
  onOpenPassport?: (tag: string) => void;
  herdMasterList?: HerdAnimal[];
}

function normaliseDate(value: unknown): string {
  if (!value) return '';
  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) return String(value).slice(0, 10);
  return parsed.toISOString().split('T')[0];
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
      // Keep the HTTP status when the response is not JSON.
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export default function HealthTab({ onOpenPassport, herdMasterList = [] }: HealthTabProps) {
  const [showEventModal, setShowEventModal] = useState(false);
  const [activeModalPassport, setActiveModalPassport] = useState<string | null>(null);
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [vetExpenses30Day, setVetExpenses30Day] = useState(0);
  const [vaccinationCoverage, setVaccinationCoverage] = useState(0);

  const [formTag, setFormTag] = useState(herdMasterList.length > 0 ? herdMasterList[0].id : '');
  const [formType, setFormType] = useState<'Treatment' | 'Vaccination' | 'Checkup'>('Treatment');
  const [formCondition, setFormCondition] = useState('');
  const [formMedication, setFormMedication] = useState('');
  const [formVet, setFormVet] = useState('Dr. Tariq Mahmood');
  const [formWithdrawal, setFormWithdrawal] = useState('0');
  const [formCost, setFormCost] = useState('0');
  const [formDose, setFormDose] = useState('');
  const [formRoute, setFormRoute] = useState('');
  const [formBatch, setFormBatch] = useState('');
  const [formNextDue, setFormNextDue] = useState('');
  const [formSeverity, setFormSeverity] = useState('NORMAL');
  const [formFollowUp, setFormFollowUp] = useState('');

  useEffect(() => {
    if (herdMasterList.length > 0 && !herdMasterList.some(animal => animal.id === formTag)) {
      setFormTag(herdMasterList[0].id);
    }
  }, [herdMasterList, formTag]);

  const loadRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const [observations, treatments, activeWithdrawals, financeLedger, healthCases] = await Promise.all([
        getJson<any[]>('/farm/health-observations'),
        getJson<any[]>('/farm/treatments'),
        getJson<any[]>('/farm/withdrawals/active'),
        getJson<{ transactions?: any[] }>('/farm/finance-ledger'),
        getJson<{ cases?: any[] }>('/farm/health-cases'),
      ]);

      const vaccinationLists = await Promise.all(
        herdMasterList.map(async animal => {
          try {
            return await getJson<any[]>(`/farm/animals/${encodeURIComponent(animal.id)}/vaccinations`);
          } catch {
            return [];
          }
        }),
      );

      const withdrawalIds = new Set(activeWithdrawals.map(item => String(item.treatment_id)));
      const openCases = (healthCases.cases || []).filter(
        item => String(item.status || '').toUpperCase() !== 'RESOLVED',
      );
      const openCaseAnimals = new Set(openCases.map(item => String(item.animal_id || '')));
      const transactions = Array.isArray(financeLedger?.transactions) ? financeLedger.transactions : [];
      const veterinarySubCategories = [
        'Routine Vet Fees / Consultation',
        'Vaccinations (FMD, HS, LSD, Anthrax)',
        'Dewormers & Parasiticides',
        'Mastitis Injectables & Intramammary Tubes',
        'Antibiotics & General Medications',
        'Calving & OB Supplies',
      ];

      const recentVetExpenses = transactions
        .filter(item => {
          if (String(item.master_category || '').toUpperCase() !== 'OPEX') return false;
          if (String(item.status || '').toUpperCase() === 'VOID') return false;
          if (!veterinarySubCategories.includes(String(item.sub_category || ''))) return false;
          const parsed = new Date(String(item.transaction_date || item.date || ''));
          if (Number.isNaN(parsed.getTime())) return false;
          const start = new Date();
          start.setHours(0, 0, 0, 0);
          start.setDate(start.getDate() - 30);
          return parsed >= start;
        })
        .reduce((sum, item) => sum + Number(item.amount || 0), 0);

      const vaccinations = vaccinationLists.flat();
      const vaccinatedAnimals = new Set(
        vaccinations.map(item => String(item.animal_id || '')).filter(Boolean),
      );
      const coverage = herdMasterList.length > 0
        ? Math.round((vaccinatedAnimals.size / herdMasterList.length) * 100)
        : 0;

      const observationRecords: HealthRecord[] = observations.map((item, index) => ({
        id: `OBS-${item.id ?? index}`,
        tag: String(item.animal_id || ''),
        date: normaliseDate(item.timestamp || item.observed_at || item.date),
        type: 'Checkup',
        condition: String(item.observation || item.symptom || 'Health observation'),
        medication: '—',
        veterinarian: String(item.reported_by || item.operator || 'API'),
        withdrawalDays: 0,
        status: openCaseAnimals.has(String(item.animal_id || '')) ? 'Active' : 'Logged',
        cost: 0,
      }));

      const treatmentRecords: HealthRecord[] = treatments.map((item, index) => ({
        id: `TRT-${item.treatment_id ?? item.id ?? index}`,
        tag: String(item.animal_id || ''),
        date: normaliseDate(item.treated_at || item.timestamp || item.date),
        type: 'Treatment',
        condition: String(item.diagnosis || item.medicine || 'Treatment'),
        medication: String(item.medicine || '—'),
        veterinarian: String(item.treated_by || item.operator || 'API'),
        withdrawalDays: Number(item.milk_withdrawal_days || 0),
        status: (
          withdrawalIds.has(String(item.treatment_id ?? item.id))
          || openCaseAnimals.has(String(item.animal_id || ''))
        ) ? 'Active' : 'Resolved',
        cost: 0,
      }));

      const vaccinationRecords: HealthRecord[] = vaccinations.map((item, index) => ({
        id: `VAX-${item.animal_id || 'ANIMAL'}-${item.administered_date || index}-${index}`,
        tag: String(item.animal_id || ''),
        date: normaliseDate(item.administered_date),
        type: 'Vaccination',
        condition: String(item.vaccine || item.vaccination || 'Vaccination'),
        medication: String(item.dose || item.vaccine || '—'),
        veterinarian: String(item.veterinarian || item.operator || 'API'),
        withdrawalDays: 0,
        status: 'Preventative',
        cost: 0,
      }));

      setRecords([...observationRecords, ...treatmentRecords, ...vaccinationRecords].sort((a, b) => b.date.localeCompare(a.date)));
      setVetExpenses30Day(recentVetExpenses);
      setVaccinationCoverage(coverage);
    } catch (loadError) {
      setRecords([]);
      setVetExpenses30Day(0);
      setVaccinationCoverage(0);
      setError(loadError instanceof Error ? loadError.message : 'Unable to load persisted health records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRecords();
  }, [herdMasterList]);

  const openPassportHandler = (tag: string) => {
    if (onOpenPassport) onOpenPassport(tag);
    else setActiveModalPassport(tag);
  };

  const handleSaveEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTag) return;
    setError(null);

    try {
      const cost = parseFloat(formCost) || 0;
      const today = new Date().toISOString().split('T')[0];

      if (formType === 'Treatment') {
        const healthCase = await postJson<any>('/farm/health-cases', {
          animal_id: formTag,
          severity: formSeverity,
          diagnosis: formCondition,
          notes: formCondition,
          follow_up_due_at: formFollowUp || null,
          operator: formVet,
        });
        const saved = await postJson<any>('/farm/treatments', {
          animal_id: formTag,
          medicine: formMedication,
          diagnosis: formCondition,
          treated_by: formVet,
          milk_withdrawal_days: parseFloat(formWithdrawal) || 0,
          notes: formCondition,
          operator: formVet,
          dose: [formDose, formRoute].filter(Boolean).join(' / ') || null,
          health_case_id: healthCase.id,
        });
        if (cost > 0) {
          await postJson('/farm/finance-ledger', {
            transaction_type: 'EXPENSE',
            master_category: 'OPEX',
            sub_category: 'Routine Vet Fees / Consultation',
            amount: cost,
            transaction_date: today,
            reference: `HEALTH-TREATMENT-${saved.treatment_id}`,
            counterparty: formVet,
            notes: `${formCondition || 'Veterinary treatment'} — ${formTag}`,
            status: 'RECORDED',
          });
        }
      } else if (formType === 'Vaccination') {
        await postJson(`/farm/animals/${encodeURIComponent(formTag)}/vaccinations`, {
          vaccine: formMedication || formCondition,
          dose: formDose || formMedication,
          administered_date: today,
          veterinarian: formVet,
          notes: formCondition,
          operator: formVet,
          batch_number: formBatch || null,
          next_due_date: formNextDue || null,
        });
        if (cost > 0) {
          await postJson('/farm/finance-ledger', {
            transaction_type: 'EXPENSE',
            master_category: 'OPEX',
            sub_category: 'Vaccinations (FMD, HS, LSD, Anthrax)',
            amount: cost,
            transaction_date: today,
            reference: `HEALTH-VACCINATION-${formTag}-${today}`,
            counterparty: formVet,
            notes: `${formCondition || 'Vaccination'} — ${formTag}`,
            status: 'RECORDED',
          });
        }
      } else {
        const healthCase = await postJson<any>('/farm/health-cases', {
          animal_id: formTag,
          severity: formSeverity,
          diagnosis: formCondition,
          notes: formCondition,
          follow_up_due_at: formFollowUp || null,
          operator: formVet,
        });
        await postJson('/farm/health-observations', {
          animal_id: formTag,
          observation: formCondition,
          symptom: formCondition,
          severity: formSeverity,
          health_case_id: healthCase.id,
          operator: formVet,
        });
        if (cost > 0) {
          await postJson('/farm/finance-ledger', {
            transaction_type: 'EXPENSE',
            master_category: 'OPEX',
            sub_category: 'Routine Vet Fees / Consultation',
            amount: cost,
            transaction_date: today,
            reference: `HEALTH-CHECKUP-${formTag}-${today}`,
            counterparty: formVet,
            notes: `${formCondition || 'Veterinary checkup'} — ${formTag}`,
            status: 'RECORDED',
          });
        }
      }

      setShowEventModal(false);
      setFormCondition('');
      setFormMedication('');
      setFormWithdrawal('0');
      setFormCost('0');
      setFormDose('');
      setFormRoute('');
      setFormBatch('');
      setFormNextDue('');
      setFormSeverity('NORMAL');
      setFormFollowUp('');
      await loadRecords();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save the health event.');
    }
  };

  const activeTreatments = records.filter(r => r.status === 'Active');
  const withdrawalCount = activeTreatments.filter(r => r.withdrawalDays > 0).length;
  const totalMonthlyCost = vetExpenses30Day;

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}><HeartPulse size={20} /> Animal Health Register</h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Chronological clinical observations, treatments and vaccinations, with withdrawal status linked to each Animal ID.</p>
        </div>
        <button onClick={() => setShowEventModal(true)} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.3)' }}><Plus size={16} /> Record Health Event</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #ef4444' }}><div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Active Treatments</div><div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>{activeTreatments.length}</div></div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #f59e0b' }}><div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>In Withdrawal Period</div><div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>{withdrawalCount}</div></div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #34d399' }}><div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Vaccination Compliance</div><div style={{ fontSize: '24px', fontWeight: 'bold', color: '#34d399' }}>{vaccinationCoverage}%</div></div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #38bdf8' }}><div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>30-Day Vet Expenses</div><div style={{ fontSize: '24px', fontWeight: 'bold', color: '#38bdf8' }}>Rs. {totalMonthlyCost.toLocaleString()}</div></div>
      </div>

      {error && <div style={{ marginBottom: '12px', padding: '10px 12px', borderRadius: '6px', background: 'rgba(239,68,68,0.12)', border: '1px solid #7f1d1d', color: '#fca5a5', fontSize: '12px' }}>{error}</div>}

      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflowX: 'auto' }}>
        <table style={{ width: '100%', minWidth: 920, fontSize: '12px', borderCollapse: 'collapse' }}><thead><tr style={{ background: '#161f30', color: '#cbd5e1', borderBottom: '1px solid #334155', textAlign: 'left' }}><th style={{ padding: '10px 12px' }}>Date</th><th style={{ padding: '10px 12px' }}>Animal ID</th><th style={{ padding: '10px 12px' }}>Event</th><th style={{ padding: '10px 12px' }}>Clinical Detail</th><th style={{ padding: '10px 12px' }}>Medicine / Vaccine</th><th style={{ padding: '10px 12px' }}>Veterinarian</th><th style={{ padding: '10px 12px' }}>Withdrawal</th><th style={{ padding: '10px 12px', textAlign: 'right' }}>Status</th></tr></thead><tbody>
          {loading ? null : records.map(r => <tr key={r.id} style={{ borderBottom: '1px solid #1a2234' }}><td style={{ padding: '10px 12px', color: '#94a3b8' }}>{r.date}</td><td style={{ padding: '10px 12px' }}><button onClick={() => openPassportHandler(r.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, textDecoration: 'underline', fontSize: '12px' }}>#{r.tag}</button></td><td style={{ padding: '10px 12px' }}><div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight:800, color:r.type==='Vaccination'?'#6ee7b7':r.type==='Treatment'?'#fca5a5':'#7dd3fc' }}>{r.type === 'Vaccination' ? <ShieldCheck size={14} /> : r.type === 'Treatment' ? <Syringe size={14} /> : <FileText size={14} />}{r.type}</div></td><td style={{ padding: '10px 12px', color:'#e2e8f0', fontWeight:700 }}>{r.condition}</td><td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{r.medication}</td><td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{r.veterinarian}</td><td style={{ padding: '10px 12px' }}>{r.withdrawalDays > 0 ? <span style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fcd34d', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><AlertTriangle size={12} /> {r.withdrawalDays} Days</span> : <span style={{ color: '#94a3b8', fontSize: '11px' }}>None</span>}</td><td style={{ padding: '10px 12px', textAlign: 'right' }}><span style={{ background: r.status === 'Active' ? 'rgba(239, 68, 68, 0.2)' : r.status === 'Resolved' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(52, 211, 153, 0.2)', color: r.status === 'Active' ? '#fca5a5' : r.status === 'Resolved' ? '#7dd3fc' : '#6ee7b7', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>{r.status}</span></td></tr>)}
        </tbody></table>
      </div>

      {showEventModal && <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '16px', boxSizing: 'border-box', overflowY: 'auto' }}><div style={{ background: '#111827', border: '1px solid #ef4444', borderRadius: '10px', width: 'min(500px,100%)', maxHeight: 'calc(100vh - 32px)', overflowY: 'auto', padding: '24px', boxSizing: 'border-box', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.7)' }}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', position: 'sticky', top: -24, background: '#111827', paddingTop: 4, paddingBottom: 8, zIndex: 2 }}><h3 style={{ margin: 0, color: '#ef4444', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}><Syringe size={18} /> Record Clinical Event</h3><button onClick={() => setShowEventModal(false)} style={{ background: 'none', border: 'none', color: '#e2e8f0', cursor: 'pointer' }}><X size={18}/></button></div>
        <form onSubmit={handleSaveEvent} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}><div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>{['Treatment', 'Vaccination', 'Checkup'].map(type => <button key={type} type="button" onClick={() => setFormType(type as 'Treatment' | 'Vaccination' | 'Checkup')} style={{ background: formType === type ? '#ef4444' : '#1e293b', color: formType === type ? '#fff' : '#cbd5e1', border: 'none', padding: '8px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>{type}</button>)}</div>
          <div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Patient / Animal ID</label><select value={formTag} onChange={e => setFormTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px' }}>{herdMasterList.length > 0 ? herdMasterList.map(a => <option key={a.id} value={a.id}>{a.id} ({a.breed} - {a.status})</option>) : <option value="" disabled>No registered animals available</option>}</select></div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>{formType === 'Vaccination' ? 'Disease / Vaccine Purpose' : formType === 'Checkup' ? 'Reason / Clinical Finding' : 'Diagnosis / Condition'}</label><input type="text" required value={formCondition} onChange={e => setFormCondition(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} /></div><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>{formType === 'Vaccination' ? 'Administrator / Veterinarian' : 'Veterinarian / Examiner'}</label><input type="text" required value={formVet} onChange={e => setFormVet(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} /></div></div>
          {formType !== 'Checkup' && <div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>{formType === 'Vaccination' ? 'Vaccine' : 'Medication Administered'}</label><input type="text" required value={formMedication} onChange={e => setFormMedication(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} /></div>}
          {formType === 'Treatment' && <><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Dose / Frequency</label><input value={formDose} onChange={e => setFormDose(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', boxSizing: 'border-box' }} /></div><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Route</label><input value={formRoute} onChange={e => setFormRoute(e.target.value)} placeholder="IM, IV, oral, intramammary" style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', boxSizing: 'border-box' }} /></div></div><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Milk Withdrawal (Days — use 0 only when none applies)</label><input type="number" min="0" required value={formWithdrawal} onChange={e => setFormWithdrawal(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#f59e0b', border: '1px solid #334155', padding: '10px', borderRadius: '6px', boxSizing: 'border-box' }} /></div></>}
          {formType === 'Vaccination' && <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Batch / Lot</label><input value={formBatch} onChange={e => setFormBatch(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', boxSizing: 'border-box' }} /></div><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Next Due Date</label><input type="date" value={formNextDue} onChange={e => setFormNextDue(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', boxSizing: 'border-box' }} /></div></div>}
          {formType !== 'Vaccination' && <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Severity</label><select value={formSeverity} onChange={e => setFormSeverity(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px' }}><option value="NORMAL">Normal</option><option value="LOW">Low</option><option value="MODERATE">Moderate</option><option value="SEVERE">Severe</option><option value="CRITICAL">Critical</option></select></div><div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Follow-up Due</label><input type="datetime-local" value={formFollowUp} onChange={e => setFormFollowUp(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', boxSizing: 'border-box' }} /></div></div>}
          <div><label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>{formType === 'Vaccination' ? 'Vaccination Cost (Rs)' : formType === 'Checkup' ? 'Consultation Cost (Rs)' : 'Treatment Cost (Rs)'}</label><input type="number" min="0" required value={formCost} onChange={e => setFormCost(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#34d399', border: '1px solid #334155', padding: '10px', borderRadius: '6px', boxSizing: 'border-box' }} /></div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}><button type="button" onClick={() => setShowEventModal(false)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}>Cancel</button><button type="submit" disabled={loading || !formTag} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}><Plus size={16} /> Save Record</button></div>
        </form></div></div>}

      {activeModalPassport && <AnimalPassportModal animalId={activeModalPassport} onClose={() => setActiveModalPassport(null)} />}
    </div>
  );
}
