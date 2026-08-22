import React, { useState } from 'react';
import { HeartPulse, Plus, X, Syringe, AlertTriangle, ShieldCheck, FileText } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';

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
  status: 'Active' | 'Resolved' | 'Preventative';
  cost: number;
}

interface HealthTabProps {
  onOpenPassport?: (tag: string) => void;
  herdMasterList?: HerdAnimal[];
}

export default function HealthTab({ onOpenPassport, herdMasterList = [] }: HealthTabProps) {
  const [showEventModal, setShowEventModal] = useState(false);
  const [activeModalPassport, setActiveModalPassport] = useState<string | null>(null);
  
  const [records, setRecords] = useState<HealthRecord[]>([
    { id: 'HLT-001', tag: 'TD-004', date: '2026-08-20', type: 'Treatment', condition: 'Clinical Mastitis (RF Quarter)', medication: 'Ceftiofur 50mg/mL', veterinarian: 'Dr. Tariq', withdrawalDays: 5, status: 'Active', cost: 4500 },
    { id: 'HLT-002', tag: 'TD-002', date: '2026-08-15', type: 'Checkup', condition: 'Post-Calving Review', medication: 'Calcium Borogluconate', veterinarian: 'Dr. Tariq', withdrawalDays: 0, status: 'Resolved', cost: 1200 },
    { id: 'HLT-003', tag: 'TD-005', date: '2026-08-10', type: 'Vaccination', condition: 'Routine FMD Booster', medication: 'FMD-Vac (Trivalent)', veterinarian: 'Farm Staff', withdrawalDays: 0, status: 'Preventative', cost: 500 },
    { id: 'HLT-004', tag: 'TD-014', date: '2026-08-05', type: 'Treatment', condition: 'Lameness (Hind Left)', medication: 'Flunixin Meglumine', veterinarian: 'Dr. Tariq', withdrawalDays: 3, status: 'Resolved', cost: 2800 }
  ]);

  const [formTag, setFormTag] = useState(herdMasterList.length > 0 ? herdMasterList[0].id : 'TD-001');
  const [formType, setFormType] = useState<'Treatment' | 'Vaccination' | 'Checkup'>('Treatment');
  const [formCondition, setFormCondition] = useState('');
  const [formMedication, setFormMedication] = useState('');
  const [formVet, setFormVet] = useState('Dr. Tariq Mahmood');
  const [formWithdrawal, setFormWithdrawal] = useState('0');
  const [formCost, setFormCost] = useState('0');

  const openPassportHandler = (tag: string) => {
    if (onOpenPassport) onOpenPassport(tag);
    else setActiveModalPassport(tag);
  };

  const handleSaveEvent = (e: React.FormEvent) => {
    e.preventDefault();
    const newRecord: HealthRecord = {
      id: `HLT-${Date.now().toString().slice(-4)}`,
      tag: formTag,
      date: new Date().toISOString().split('T')[0],
      type: formType,
      condition: formCondition,
      medication: formMedication,
      veterinarian: formVet,
      withdrawalDays: parseInt(formWithdrawal) || 0,
      status: formType === 'Treatment' ? 'Active' : (formType === 'Vaccination' ? 'Preventative' : 'Resolved'),
      cost: parseFloat(formCost) || 0
    };
    
    setRecords([newRecord, ...records]);
    setShowEventModal(false);
    
    // Reset form
    setFormCondition('');
    setFormMedication('');
    setFormWithdrawal('0');
    setFormCost('0');
  };

  const getRemainingWithdrawal = (recordDate: string, prescribedDays: number) => {
    if (prescribedDays <= 0) return 0;
    const today = new Date('2026-08-22').getTime();
    const treatDate = new Date(recordDate).getTime();
    const daysElapsed = Math.floor((today - treatDate) / (1000 * 60 * 60 * 24));
    const remaining = prescribedDays - daysElapsed;
    return remaining > 0 ? remaining : 0;
  };

  const activeTreatments = records.filter(r => r.status === 'Active');
  const totalMonthlyCost = records.reduce((sum, r) => sum + r.cost, 0);

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <HeartPulse size={20} /> Veterinary Health & Medical Ledger
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Track treatments, vaccinations, and manage milk withdrawal periods for food safety compliance.
          </p>
        </div>
        <button onClick={() => setShowEventModal(true)} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.3)' }}>
          <Plus size={16} /> Record Health Event
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #ef4444' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Active Treatments</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>{activeTreatments.length}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #f59e0b' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>In Withdrawal Period</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>
             {records.filter(r => r.status === 'Active' && r.withdrawalDays > 0).length}
          </div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #34d399' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Vaccination Compliance</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#34d399' }}>95%</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #38bdf8' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>30-Day Vet Expenses</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#38bdf8' }}>Rs. {totalMonthlyCost.toLocaleString()}</div>
        </div>
      </div>

      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#161f30', color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}>
              <th style={{ padding: '12px 16px' }}>Date</th>
              <th style={{ padding: '12px 16px' }}>Animal ID</th>
              <th style={{ padding: '12px 16px' }}>Type & Condition</th>
              <th style={{ padding: '12px 16px' }}>Treatment / Medication</th>
              <th style={{ padding: '12px 16px' }}>Withdrawal</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id} style={{ borderBottom: '1px solid #1a2234' }}>
                <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{r.date}</td>
                <td style={{ padding: '12px 16px' }}>
                  <button onClick={() => openPassportHandler(r.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, textDecoration: 'underline', fontSize: '13px' }}>
                    #{r.tag}
                  </button>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {r.type === 'Vaccination' ? <ShieldCheck size={14} color="#34d399" /> : r.type === 'Treatment' ? <Syringe size={14} color="#ef4444" /> : <FileText size={14} color="#38bdf8" />}
                    <span style={{ color: '#e2e8f0', fontWeight: 'bold' }}>{r.condition}</span>
                  </div>
                </td>
                <td style={{ padding: '12px 16px', color: '#cbd5e1' }}>{r.medication}</td>
                <td style={{ padding: '12px 16px' }}>
                  {r.withdrawalDays > 0 ? (
                     <span style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fcd34d', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                       <AlertTriangle size={12} /> {r.withdrawalDays} Days
                     </span>
                  ) : (
                    <span style={{ color: '#64748b', fontSize: '11px' }}>Clear</span>
                  )}
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                  <span style={{ background: r.status === 'Active' ? 'rgba(239, 68, 68, 0.2)' : r.status === 'Resolved' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(52, 211, 153, 0.2)', color: r.status === 'Active' ? '#fca5a5' : r.status === 'Resolved' ? '#7dd3fc' : '#6ee7b7', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>
                    {r.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showEventModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #ef4444', borderRadius: '10px', width: '500px', padding: '24px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.7)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, color: '#ef4444', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Syringe size={18} /> Record Clinical Event
              </h3>
              <button onClick={() => setShowEventModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={18}/></button>
            </div>

            <form onSubmit={handleSaveEvent} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                {['Treatment', 'Vaccination', 'Checkup'].map(type => (
                  <button key={type} type="button" onClick={() => setFormType(type as any)} style={{ background: formType === type ? '#ef4444' : '#1e293b', color: formType === type ? '#fff' : '#cbd5e1', border: 'none', padding: '8px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
                    {type}
                  </button>
                ))}
              </div>

              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Patient / Animal ID</label>
                <select value={formTag} onChange={e => setFormTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px' }}>
                  {herdMasterList.length > 0 ? (
                    herdMasterList.map(a => <option key={a.id} value={a.id}>{a.id} ({a.breed} - {a.status})</option>)
                  ) : (
                    <option value="TD-001">TD-001 (Fallback)</option>
                  )}
                </select>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Diagnosis / Condition</label>
                  <input type="text" required placeholder="e.g., Mastitis, FMD Booster" value={formCondition} onChange={e => setFormCondition(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} />
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Veterinarian</label>
                  <input type="text" required value={formVet} onChange={e => setFormVet(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Medication Administered</label>
                <input type="text" required placeholder="e.g., Ceftiofur 50mg" value={formMedication} onChange={e => setFormMedication(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} />
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Milk/Meat Withdrawal (Days)</label>
                  <input type="number" min="0" required value={formWithdrawal} onChange={e => setFormWithdrawal(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#f59e0b', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px', fontWeight: 'bold', boxSizing: 'border-box' }} />
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Cost of Treatment (Rs)</label>
                  <input type="number" min="0" required value={formCost} onChange={e => setFormCost(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#34d399', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px', fontWeight: 'bold', boxSizing: 'border-box' }} />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setShowEventModal(false)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}>Cancel</button>
                <button type="submit" style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Plus size={16} /> Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {activeModalPassport && <AnimalPassportModal animalId={activeModalPassport} onClose={() => setActiveModalPassport(null)} />}
    </div>
  );
}

