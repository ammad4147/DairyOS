import React, { useEffect, useState } from 'react';
import { X, Save, Activity, Milk, HeartPulse, DollarSign, Database, ArchiveRestore } from 'lucide-react';

interface AnimalData {
  id: string;
  category: string;
  breed: string;
  age: string;
  status: string;
  frequency: string;
  earTag: string;
  gender?: string;
}

interface AnimalPassportModalProps {
  animalId: string;
  onClose: () => void;
  onSave?: (animalData: AnimalData) => void;
}

interface BackendAnimal {
  animal_id: string;
  animal_type?: string;
  ear_tag?: string | null;
  rfid?: string | null;
  breed?: string | null;
  sex?: string | null;
  date_of_birth?: string | null;
  dam_id?: string | null;
  sire_id?: string | null;
  lifecycle_status?: string | null;
  status?: string | null;
  milking_frequency?: string | null;
  production_group?: string | null;
  location?: string | null;
  active?: boolean;
}

const API_BASE = 'http://localhost:8000';

function categoryFromLifecycle(lifecycle?: string | null): string {
  switch ((lifecycle || '').toUpperCase()) {
    case 'LACTATING': return 'Milking Cows';
    case 'DRY': return 'Dry Cows';
    case 'HEIFER':
    case 'CLOSE_UP': return 'Heifers';
    case 'CALF': return 'Female Calves';
    default: return 'Heifers';
  }
}

function lifecycleFromCategory(category: string): string {
  switch (category) {
    case 'Milking Cows': return 'LACTATING';
    case 'Dry Cows': return 'DRY';
    case 'Heifers': return 'HEIFER';
    case 'Male Calves':
    case 'Female Calves': return 'CALF';
    case 'Bulls': return 'HEIFER';
    default: return 'HEIFER';
  }
}

function ageFromBirthDate(value?: string | null): string {
  if (!value) return 'Unknown';
  const birth = new Date(value);
  if (Number.isNaN(birth.getTime())) return 'Unknown';
  const now = new Date();
  let years = now.getFullYear() - birth.getFullYear();
  const beforeBirthday =
    now.getMonth() < birth.getMonth() ||
    (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate());
  if (beforeBirthday) years -= 1;
  return years >= 1 ? `${years} Years` : `${Math.max(0, Math.floor((now.getTime() - birth.getTime()) / 2592000000))} Months`;
}

function toUiAnimal(animal: BackendAnimal): AnimalData {
  return {
    id: animal.animal_id,
    category: categoryFromLifecycle(animal.lifecycle_status),
    breed: animal.breed || 'Unknown',
    age: ageFromBirthDate(animal.date_of_birth),
    status: animal.active === false ? 'Inactive' : (animal.status || animal.lifecycle_status || 'Active'),
    frequency: animal.milking_frequency || 'NONE',
    earTag: animal.ear_tag || animal.animal_id,
    gender: animal.sex === 'MALE' ? 'Male' : 'Female',
  };
}

export default function AnimalPassportModal({ animalId, onClose, onSave }: AnimalPassportModalProps) {
  const isNew = animalId === 'NEW-ANIMAL';

  const [formData, setFormData] = useState({
    tagId: isNew ? '' : animalId,
    category: 'Milking Cows',
    breed: 'Holstein Friesian',
    birthDate: '2023-01-15',
    sire: '',
    dam: '',
    rfid: '',
    status: 'ACTIVE',
    frequency: 'TWICE_DAILY',
  });

  const [activeSubTab, setActiveSubTab] = useState<'profile' | 'milk' | 'health' | 'breeding' | 'finance'>('profile');
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState<string | null>(null);
  const [retiring, setRetiring] = useState(false);

  useEffect(() => {
    if (isNew) return;

    let cancelled = false;
    setLoading(true);
    fetch(`${API_BASE}/farm/animals/${encodeURIComponent(animalId)}`)
      .then(async response => {
        if (!response.ok) throw new Error((await response.text()) || `Unable to load animal (${response.status})`);
        return response.json() as Promise<BackendAnimal>;
      })
      .then(animal => {
        if (cancelled) return;
        setFormData({
          tagId: animal.animal_id,
          category: categoryFromLifecycle(animal.lifecycle_status),
          breed: animal.breed || 'Unknown',
          birthDate: animal.date_of_birth || '',
          sire: animal.sire_id || '',
          dam: animal.dam_id || '',
          rfid: animal.rfid || '',
          status: animal.status || (animal.active === false ? 'INACTIVE' : 'ACTIVE'),
          frequency: animal.milking_frequency || 'NONE',
        });
      })
      .catch(err => {
        if (!cancelled) setError(err?.message || 'Unable to load animal passport');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [animalId, isNew]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const lifecycle = lifecycleFromCategory(formData.category);
      const payload = {
        breed: formData.breed,
        date_of_birth: formData.birthDate || null,
        sire_id: formData.sire || null,
        dam_id: formData.dam || null,
        rfid: formData.rfid || null,
        lifecycle_status: lifecycle,
        milking_frequency: lifecycle === 'LACTATING' ? formData.frequency : undefined,
        operator: 'Operator UI',
      };

      let response: Response;
      if (isNew) {
        response = await fetch(`${API_BASE}/farm/animals`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            animal_type: 'CATTLE',
            sex: formData.category.includes('Male') || formData.category === 'Bulls' ? 'MALE' : 'FEMALE',
            breed: formData.breed,
            date_of_birth: formData.birthDate || null,
            sire_id: formData.sire || null,
            dam_id: formData.dam || null,
            rfid: formData.rfid || null,
            lifecycle_status: lifecycle,
            milking_frequency: lifecycle === 'LACTATING' ? formData.frequency : undefined,
          }),
        });
      } else {
        response = await fetch(`${API_BASE}/farm/animals/${encodeURIComponent(animalId)}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      if (!response.ok) throw new Error((await response.text()) || `Unable to save animal (${response.status})`);
      const savedAnimal = await response.json() as BackendAnimal;
      setSaved(true);
      onSave?.(toUiAnimal(savedAnimal));
      setTimeout(onClose, 500);
    } catch (err: any) {
      setError(err?.message || 'Unable to save animal');
    }
  };

  const handleRetire = async () => {
    if (isNew || retiring) return;
    if (!window.confirm(`Retire animal ${animalId}? The record will remain in the permanent register and linked history will be preserved.`)) return;
    setRetiring(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/farm/animals/${encodeURIComponent(animalId)}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operator: 'Operator UI', reason: 'Retired from Herd register' }),
      });
      if (!response.ok) throw new Error((await response.text()) || `Unable to retire animal (${response.status})`);
      const retired = await response.json() as BackendAnimal;
      onSave?.(toUiAnimal(retired));
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Unable to retire animal');
    } finally {
      setRetiring(false);
    }
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0, 0, 0, 0.75)', zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#0f172a', width: '900px', maxHeight: '90vh', borderRadius: '12px', border: '1px solid #1f2937', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)' }}>
        <div style={{ padding: '20px 24px', background: '#111827', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Database size={20} color="#38bdf8" />
            <div>
              <h2 style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold', margin: 0 }}>
                {isNew ? 'New Animal Comprehensive Passport' : `Animal Passport: ${animalId}`}
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '12px', margin: 0 }}>
                {isNew ? 'Create a permanent system-generated Animal ID.' : 'Edit the authoritative animal master record.'}
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={20} /></button>
        </div>

        <div style={{ display: 'flex', background: '#1e293b', padding: '0 24px', borderBottom: '1px solid #334155' }}>
          {[
            { id: 'profile', label: 'Identity & Lineage', icon: <Database size={14} /> },
            { id: 'milk', label: 'Milk & Yield Link', icon: <Milk size={14} /> },
            { id: 'health', label: 'Health & Safety', icon: <HeartPulse size={14} /> },
            { id: 'breeding', label: 'Breeding & Heat', icon: <Activity size={14} /> },
            { id: 'finance', label: 'Valuation & Feed', icon: <DollarSign size={14} /> },
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveSubTab(tab.id as any)} style={{ background: 'transparent', color: activeSubTab === tab.id ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeSubTab === tab.id ? '2px solid #38bdf8' : '2px solid transparent', padding: '12px 16px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSave} style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {loading && <div style={{ background: '#1e293b', color: '#cbd5e1', padding: '10px', borderRadius: '6px', fontSize: '12px' }}>Loading authoritative animal record...</div>}
          {saved && <div style={{ background: '#064e3b', color: '#34d399', padding: '12px', borderRadius: '6px', fontSize: '13px', fontWeight: 'bold', textAlign: 'center' }}>Animal record saved to the persistent Herd register.</div>}
          {error && <div style={{ background: '#450a0a', color: '#fca5a5', padding: '12px', borderRadius: '6px', fontSize: '12px', border: '1px solid #7f1d1d' }}>{error}</div>}

          {activeSubTab === 'profile' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>System Animal ID</label>
                <input type="text" value={formData.tagId || '(generated on save)'} disabled style={{ width: '100%', boxSizing: 'border-box', background: '#111827', border: '1px solid #334155', color: '#64748b', padding: '10px', borderRadius: '6px', fontSize: '13px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Category</label>
                <select value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} style={{ width: '100%', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}>
                  <option value="Milking Cows">Milking Cows</option>
                  <option value="Dry Cows">Dry Cows</option>
                  <option value="Heifers">Heifers</option>
                  <option value="Female Calves">Female Calves</option>
                  <option value="Male Calves">Male Calves</option>
                  <option value="Bulls">Bulls</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Breed</label>
                <input type="text" value={formData.breed} onChange={(e) => setFormData({...formData, breed: e.target.value})} style={{ width: '100%', boxSizing: 'border-box', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>RFID</label>
                <input type="text" value={formData.rfid} onChange={(e) => setFormData({...formData, rfid: e.target.value})} style={{ width: '100%', boxSizing: 'border-box', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Date of Birth</label>
                <input type="date" value={formData.birthDate} onChange={(e) => setFormData({...formData, birthDate: e.target.value})} style={{ width: '100%', boxSizing: 'border-box', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Sire (Father ID)</label>
                <input type="text" value={formData.sire} onChange={(e) => setFormData({...formData, sire: e.target.value})} style={{ width: '100%', boxSizing: 'border-box', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Dam (Mother ID)</label>
                <input type="text" value={formData.dam} onChange={(e) => setFormData({...formData, dam: e.target.value})} style={{ width: '100%', boxSizing: 'border-box', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }} />
              </div>
              {formData.category === 'Milking Cows' && (
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Milking Frequency</label>
                  <select value={formData.frequency} onChange={(e) => setFormData({...formData, frequency: e.target.value})} style={{ width: '100%', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}>
                    <option value="TWICE_DAILY">Twice Daily</option>
                    <option value="THRICE_DAILY">Thrice Daily</option>
                  </select>
                </div>
              )}
            </div>
          )}

          {activeSubTab === 'milk' && <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', border: '1px solid #1f2937' }}><h4 style={{ color: '#38bdf8', margin: '0 0 10px 0', fontSize: '14px' }}>Milk Module Integration</h4><p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>Milking-frequency remains an Animal Passport rule and is consumed by the existing session scheduling service.</p></div>}
          {activeSubTab === 'health' && <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', border: '1px solid #1f2937' }}><h4 style={{ color: '#f87171', margin: '0 0 10px 0', fontSize: '14px' }}>Health & Withdrawal Safety</h4><p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>Health events remain in the Health module; this tab shows the master animal identity only.</p></div>}
          {activeSubTab === 'breeding' && <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', border: '1px solid #1f2937' }}><h4 style={{ color: '#f472b6', margin: '0 0 10px 0', fontSize: '14px' }}>Reproductive Cycle</h4><p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>Breeding events remain governed by the Breeding module and linked to this permanent Animal ID.</p></div>}
          {activeSubTab === 'finance' && <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', border: '1px solid #1f2937' }}><h4 style={{ color: '#fbbf24', margin: '0 0 10px 0', fontSize: '14px' }}>Financial Link</h4><p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>Animal-linked financial facts remain in the Finance ledger; this passport only retains the permanent identity link.</p></div>}

          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginTop: 'auto', borderTop: '1px solid #1f2937', paddingTop: '16px' }}>
            <div>{!isNew && <button type="button" onClick={handleRetire} disabled={retiring} style={{ background: '#450a0a', border: '1px solid #7f1d1d', color: '#fca5a5', padding: '10px 16px', borderRadius: '6px', fontSize: '13px', cursor: retiring ? 'wait' : 'pointer', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '7px' }}><ArchiveRestore size={15} /> {retiring ? 'Retiring...' : 'Retire Animal'}</button>}</div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button type="button" onClick={onClose} style={{ background: 'transparent', border: '1px solid #334155', color: '#94a3b8', padding: '10px 18px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', fontWeight: 'bold' }}>Cancel</button>
              <button type="submit" disabled={loading} style={{ background: '#0284c7', border: 'none', color: '#fff', padding: '10px 20px', borderRadius: '6px', fontSize: '13px', cursor: loading ? 'wait' : 'pointer', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}><Save size={16} /> {isNew ? 'Create Animal' : 'Save Changes'}</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
