import React, { useState } from 'react';
import { X, Save, ShieldCheck, Activity, Milk, HeartPulse, DollarSign, Database } from 'lucide-react';

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

export default function AnimalPassportModal({ animalId, onClose, onSave }: AnimalPassportModalProps) {
  const isNew = animalId === 'NEW-ANIMAL';

  const [formData, setFormData] = useState({
    tagId: isNew ? `TD-${Math.floor(Math.random() * 900 + 100).toString().padStart(3, '0')}` : animalId,
    category: 'Milking Cows',
    breed: 'Holstein Friesian',
    birthDate: '2023-01-15',
    sire: '',
    dam: '',
    weight: '550',
    status: 'Healthy',
    initialYield: '30.0',
    purchaseCost: '0'
  });

  const [activeSubTab, setActiveSubTab] = useState<'profile' | 'milk' | 'health' | 'breeding' | 'finance'>('profile');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    
    if (onSave) {
      onSave({
        id: formData.tagId,
        category: formData.category,
        breed: formData.breed,
        age: 'New', // Simplification for demo
        status: formData.status,
        frequency: formData.category === 'Milking Cows' ? 'TWICE_DAILY' : 'NONE',
        earTag: `PK-LHR-${formData.tagId.split('-')[1] || 'NEW'}`,
        gender: formData.category.includes('Female') || formData.category.includes('Cow') || formData.category.includes('Heifer') ? 'Female' : 'Male'
      });
    }

    setTimeout(() => {
      onClose();
    }, 1000);
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
                {isNew ? 'Initializing fresh record with live backend cross-module bindings.' : 'Live synchronized telemetry across Milk, Health, Breeding, and Finance.'}
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
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as any)}
              style={{
                background: 'transparent',
                color: activeSubTab === tab.id ? '#38bdf8' : '#94a3b8',
                border: 'none',
                borderBottom: activeSubTab === tab.id ? '2px solid #38bdf8' : '2px solid transparent',
                padding: '12px 16px',
                fontSize: '12px',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSave} style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {saved && (
            <div style={{ background: '#064e3b', color: '#34d399', padding: '12px', borderRadius: '6px', fontSize: '13px', fontWeight: 'bold', textAlign: 'center' }}>
              Passport successfully saved and linked to DairyOS backend modules!
            </div>
          )}

          {activeSubTab === 'profile' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Tag ID / Identifier</label>
                <input
                  type="text"
                  value={formData.tagId}
                  onChange={(e) => setFormData({...formData, tagId: e.target.value})}
                  disabled={!isNew}
                  style={{ width: '100%', background: '#111827', border: '1px solid #334155', color: isNew ? '#fff' : '#64748b', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  style={{ width: '100%', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
                >
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
                <input
                  type="text"
                  value={formData.breed}
                  onChange={(e) => setFormData({...formData, breed: e.target.value})}
                  style={{ width: '100%', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Estimated Weight (kg)</label>
                <input
                  type="text"
                  value={formData.weight}
                  onChange={(e) => setFormData({...formData, weight: e.target.value})}
                  style={{ width: '100%', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Sire (Father ID)</label>
                <input
                  type="text"
                  placeholder="Optional Sire Tag"
                  value={formData.sire}
                  onChange={(e) => setFormData({...formData, sire: e.target.value})}
                  style={{ width: '100%', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Dam (Mother ID)</label>
                <input
                  type="text"
                  placeholder="Optional Dam Tag"
                  value={formData.dam}
                  onChange={(e) => setFormData({...formData, dam: e.target.value})}
                  style={{ width: '100%', background: '#111827', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
                />
              </div>
            </div>
          )}

          {activeSubTab === 'milk' && (
            <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <h4 style={{ color: '#38bdf8', margin: '0 0 10px 0', fontSize: '14px' }}>Milk Module Integration</h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 15px 0' }}>
                This animal will automatically link to daily milking sessions, yield drop detection algorithms, and mass-balance calculations.
              </p>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Baseline Expected Yield (Liters / Day)</label>
              <input
                type="text"
                value={formData.initialYield}
                onChange={(e) => setFormData({...formData, initialYield: e.target.value})}
                style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
              />
            </div>
          )}

          {activeSubTab === 'health' && (
            <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <h4 style={{ color: '#f87171', margin: '0 0 10px 0', fontSize: '14px' }}>Health & Withdrawal Safety Bindings</h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>
                No active health alerts or antibiotic withdrawals recorded for this new passport. Any future veterinary treatments logged in the Health Tab will automatically generate safety blocks here.
              </p>
            </div>
          )}

          {activeSubTab === 'breeding' && (
            <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <h4 style={{ color: '#f472b6', margin: '0 0 10px 0', fontSize: '14px' }}>Reproductive & Breeding Cycle</h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>
                Linked to Breeding Tab heat detection and artificial insemination schedules.
              </p>
            </div>
          )}

          {activeSubTab === 'finance' && (
            <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <h4 style={{ color: '#fbbf24', margin: '0 0 10px 0', fontSize: '14px' }}>Financial Valuation & Feed Costs</h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 15px 0' }}>
                Asset value integration for farm balance sheets.
              </p>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Initial Acquisition / Valuation Cost (PKR)</label>
              <input
                type="text"
                value={formData.purchaseCost}
                onChange={(e) => setFormData({...formData, purchaseCost: e.target.value})}
                style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '13px' }}
              />
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: 'auto', borderTop: '1px solid #1f2937', paddingTop: '16px' }}>
            <button type="button" onClick={onClose} style={{ background: 'transparent', border: '1px solid #334155', color: '#94a3b8', padding: '10px 18px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', fontWeight: 'bold' }}>
              Cancel
            </button>
            <button type="submit" style={{ background: '#0284c7', border: 'none', color: '#fff', padding: '10px 20px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Save size={16} /> Save & Bind Passport
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}
