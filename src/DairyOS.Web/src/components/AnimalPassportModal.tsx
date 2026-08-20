import React, { useState } from 'react';
import { 
  X, Award, Milk, HeartPulse, Activity, Wheat, 
  Calendar, FileText, CheckCircle2, AlertTriangle, 
  TrendingUp, Dna, ShieldCheck, Stethoscope, Clock,
  LogOut, DollarSign, Skull, Archive
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface PassportProps {
  animalId: string;
  onClose: () => void;
  onUpdateAnimal?: (updatedData: any) => void;
}

export default function AnimalPassportModal({ animalId, onClose, onUpdateAnimal }: PassportProps) {
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'MILK' | 'BREEDING' | 'HEALTH' | 'FEED' | 'EXIT'>('OVERVIEW');

  // Core Biological & Pedigree State
  const [tag, setTag] = useState(animalId || 'TD-001');
  const [rfidTag, setRfidTag] = useState(`982.00012847${animalId.replace(/\D/g, '') || '01'}`);
  const [visualTag, setVisualTag] = useState(`PK-LHR-${animalId || '001'}`);
  const [breed, setBreed] = useState('Holstein Friesian');
  const [customBreedName, setCustomBreedName] = useState('');
  const [category, setCategory] = useState('Milking Cows');
  const [dob, setDob] = useState('2022-03-15');
  const [damId, setDamId] = useState('DAM-PK-782 (Sahiwal Cross)');
  const [sireId, setSireId] = useState('SIRE-US-9941 (Holstein Pure)');
  const [weightKg, setWeightKg] = useState('585');
  const [bcsScore, setBcsScore] = useState('3.25');

  // Milking Modality & Production Governance
  const [milkingModality, setMilkingModality] = useState<'TWICE_DAILY' | 'THRICE_DAILY' | 'NONE'>('TWICE_DAILY');
  const [targetBaseline, setTargetBaseline] = useState('38.0');
  const [lactationNumber, setLactationNumber] = useState('2');
  const [daysInMilk, setDaysInMilk] = useState('124');
  const [cumulativeLactationYield, setCumulativeLactationYield] = useState('4,712');
  const [peakYield, setPeakYield] = useState('44.5');

  // Reproductive Health State
  const [reproStatus, setReproStatus] = useState<'Open' | 'Inseminated' | 'Pregnant' | 'Dry'>('Pregnant');
  const [aiDate, setAiDate] = useState('2026-03-28');
  const [aiBullCode, setAiBullCode] = useState('SEMEN-ABS-SUPERIOR-991');
  const [gestationDays, setGestationDays] = useState('145');
  const [expectedCalving, setExpectedCalving] = useState('2027-01-02');

  // Veterinary & Health State
  const [healthStatus, setHealthStatus] = useState<'Healthy' | 'Under Observation' | 'Critical'>('Healthy');
  const [withdrawalActive, setWithdrawalActive] = useState(false);
  const [tempCelsius, setTempCelsius] = useState('38.6');
  const [somaticCellCount, setSomaticCellCount] = useState('145,000');

  // Nutrition State
  const [dmiKg, setDmiKg] = useState('22.4');
  const [fceRatio, setFceRatio] = useState('1.71');

  // EXIT, SALE & MORTALITY GOVERNANCE
  const [lifecycleStatus, setLifecycleStatus] = useState<'ACTIVE' | 'SOLD' | 'DECEASED' | 'CULLED'>('ACTIVE');
  const [exitDate, setExitDate] = useState('2026-08-20');
  const [exitReason, setExitReason] = useState('Commercial Asset Realization');
  const [salePricePKR, setSalePricePKR] = useState('450,000');
  const [buyerDetails, setBuyerDetails] = useState('Sahiwal Commercial Cattle Farm');
  const [mortalityCause, setMortalityCause] = useState('Acute Bloat / Ruminal Acidosis');
  const [autopsyVet, setAutopsyVet] = useState('Dr. Tariq Mahmood (DVM)');
  const [assetValuationAtExit, setAssetValuationAtExit] = useState('420,000');

  const [savedSuccess, setSavedSuccess] = useState(false);

  const yieldHistory = [
    { day: 'D10', yield: 24.5 },
    { day: 'D30', yield: 34.0 },
    { day: 'D60', yield: 44.5 },
    { day: 'D90', yield: 41.2 },
    { day: 'D120', yield: 38.5 },
    { day: 'D150', yield: 36.0 },
    { day: 'D180', yield: 33.5 },
  ];

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    if (onUpdateAnimal) {
      onUpdateAnimal({
        tag,
        breed: breed === 'Custom' ? customBreedName : breed,
        modality: milkingModality,
        expectedBaseline: parseFloat(targetBaseline) || 30.0,
        lifecycleStatus,
        exitData: lifecycleStatus !== 'ACTIVE' ? {
          exitDate,
          exitReason,
          salePricePKR: parseFloat(salePricePKR) || 0,
          buyerDetails,
          mortalityCause,
          autopsyVet,
          assetValuationAtExit: parseFloat(assetValuationAtExit) || 0
        } : null
      });
    }
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  const isArchived = lifecycleStatus !== 'ACTIVE';

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '16px' }}>
      <div style={{ background: '#111827', border: isArchived ? '2px solid #ef4444' : '1px solid #374151', borderRadius: '12px', width: '100%', maxWidth: '870px', maxHeight: '92vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)' }}>
        
        {/* TOP DOSSIER BANNER */}
        <div style={{ padding: '14px 20px', background: isArchived ? '#3f1515' : '#161f30', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '8px', background: isArchived ? '#b91c1c' : '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold' }}>
              {isArchived ? <Archive size={22} /> : <Dna size={22} />}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ margin: 0, color: '#fff', fontSize: '18px', fontWeight: 'bold' }}>Biological Passport: #{tag}</h2>
                <span style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>
                  {breed === 'Custom' ? (customBreedName || 'Custom Breed') : breed}
                </span>
                {isArchived ? (
                  <span style={{ background: '#ef4444', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {lifecycleStatus === 'SOLD' && <DollarSign size={12} />}
                    {lifecycleStatus === 'DECEASED' && <Skull size={12} />}
                    ARCHIVED: {lifecycleStatus}
                  </span>
                ) : (
                  <span style={{ background: milkingModality === 'THRICE_DAILY' ? 'rgba(168, 85, 247, 0.2)' : 'rgba(251, 146, 60, 0.2)', color: milkingModality === 'THRICE_DAILY' ? '#c084fc' : '#fb923c', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>
                    {milkingModality === 'THRICE_DAILY' ? '3x Milking' : (milkingModality === 'TWICE_DAILY' ? '2x Milking' : 'Non-Milking')}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '11px', color: isArchived ? '#fca5a5' : '#94a3b8', marginTop: '2px' }}>
                RFID: {rfidTag} • Ear Tag: {visualTag} • {isArchived ? 'Excluded from Active Headcount (Preserved for Analytics)' : 'Active Herd Asset'}
              </div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* PASSPORT NAVIGATION TABS */}
        <div style={{ display: 'flex', background: '#0f172a', borderBottom: '1px solid #1f2937', padding: '0 10px', overflowX: 'auto' }}>
          <button 
            onClick={() => setActiveTab('OVERVIEW')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'OVERVIEW' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'OVERVIEW' ? '2px solid #38bdf8' : 'none', padding: '12px 14px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <FileText size={14} /> Profile & Pedigree
          </button>
          <button 
            onClick={() => setActiveTab('MILK')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'MILK' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'MILK' ? '2px solid #38bdf8' : 'none', padding: '12px 14px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <Milk size={14} /> Milking & Yield Curve
          </button>
          <button 
            onClick={() => setActiveTab('BREEDING')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'BREEDING' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'BREEDING' ? '2px solid #38bdf8' : 'none', padding: '12px 14px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <Activity size={14} /> Breeding & Gestation
          </button>
          <button 
            onClick={() => setActiveTab('HEALTH')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'HEALTH' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'HEALTH' ? '2px solid #38bdf8' : 'none', padding: '12px 14px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <HeartPulse size={14} /> Health Ledger
          </button>
          <button 
            onClick={() => setActiveTab('FEED')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'FEED' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'FEED' ? '2px solid #38bdf8' : 'none', padding: '12px 14px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <Wheat size={14} /> Nutrition & FCE
          </button>
          <button 
            onClick={() => setActiveTab('EXIT')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'EXIT' ? (isArchived ? '#f87171' : '#fb923c') : (isArchived ? '#ef4444' : '#94a3b8'), border: 'none', borderBottom: activeTab === 'EXIT' ? '2px solid #ef4444' : 'none', padding: '12px 14px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <LogOut size={14} /> Exit, Sale & Mortality
          </button>
        </div>

        {/* TAB CONTENT AREA */}
        <form onSubmit={handleSave} style={{ padding: '20px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* 1. OVERVIEW & PEDIGREE */}
          {activeTab === 'OVERVIEW' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8', marginBottom: '10px', textTransform: 'uppercase' }}>
                  Identity & Pedigree Lineage
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Animal Tag ID</label>
                    <input type="text" value={tag} onChange={e => setTag(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Visual Ear Tag</label>
                    <input type="text" value={visualTag} onChange={e => setVisualTag(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Electronic RFID</label>
                    <input type="text" value={rfidTag} onChange={e => setRfidTag(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginTop: '10px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Breed Type</label>
                    <select value={breed} onChange={e => setBreed(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px' }}>
                      <option value="Holstein Friesian">Holstein Friesian</option>
                      <option value="Sahiwal">Sahiwal</option>
                      <option value="Cholistani">Cholistani</option>
                      <option value="Jersey">Jersey</option>
                      <option value="Nili-Ravi Buffalo">Nili-Ravi Buffalo</option>
                      <option value="Crossbred">Crossbred</option>
                      <option value="Custom">Custom / Other</option>
                    </select>
                  </div>
                  {breed === 'Custom' ? (
                    <div>
                      <label style={{ fontSize: '11px', color: '#94a3b8' }}>Custom Breed Name</label>
                      <input type="text" placeholder="e.g. Sahiwal x HF F1" value={customBreedName} onChange={e => setCustomBreedName(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                  ) : (
                    <div>
                      <label style={{ fontSize: '11px', color: '#94a3b8' }}>Date of Birth</label>
                      <input type="date" value={dob} onChange={e => setDob(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                  )}
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Current Category</label>
                    <select value={category} onChange={e => setCategory(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px' }}>
                      <option value="Milking Cows">Milking Cows</option>
                      <option value="Dry">Dry</option>
                      <option value="Heifers">Heifers</option>
                      <option value="Female Calves">Female Calves</option>
                      <option value="Male Calves">Male Calves</option>
                      <option value="Bulls">Bulls</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '10px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Dam (Mother Lineage)</label>
                    <input type="text" value={damId} onChange={e => setDamId(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Sire (Father Straw / Bull)</label>
                    <input type="text" value={sireId} onChange={e => setSireId(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>Body Weight (kg)</div>
                  <input type="number" value={weightKg} onChange={e => setWeightKg(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', boxSizing: 'border-box', marginTop: '4px' }} />
                </div>
                <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>Body Condition Score (BCS)</div>
                  <input type="number" step="0.25" value={bcsScore} onChange={e => setBcsScore(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', boxSizing: 'border-box', marginTop: '4px' }} />
                </div>
              </div>
            </div>
          )}

          {/* 2. MILKING MODALITY & YIELD */}
          {activeTab === 'MILK' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '8px', borderLeft: '3px solid #38bdf8' }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8', marginBottom: '8px' }}>
                  Farm Milking Modality & Production Expectations
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 'bold' }}>Milking Modality</label>
                    <select 
                      value={milkingModality} 
                      onChange={e => setMilkingModality(e.target.value as any)} 
                      style={{ width: '100%', background: '#0f172a', color: '#38bdf8', border: '1px solid #38bdf8', padding: '8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}
                    >
                      <option value="TWICE_DAILY">Twice Daily (2x Daily)</option>
                      <option value="THRICE_DAILY">Thrice Daily (3x Daily)</option>
                      <option value="NONE">Non-Milking (Dry / Calf / Bull)</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Expected Target Daily Yield (L)</label>
                    <input type="number" step="0.1" value={targetBaseline} onChange={e => setTargetBaseline(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#34d399', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Lactation # / DIM</label>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <input type="number" value={lactationNumber} onChange={e => setLactationNumber(e.target.value)} placeholder="Lact" style={{ width: '50%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                      <input type="number" value={daysInMilk} onChange={e => setDaysInMilk(e.target.value)} placeholder="DIM" style={{ width: '50%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Lactation Curve Chart */}
              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#fff' }}>Historical Lactation Curve (Preserved Forever)</span>
                  <span style={{ fontSize: '11px', color: '#34d399' }}>Peak: {peakYield} L • Cumulative: {cumulativeLactationYield} L</span>
                </div>
                <div style={{ height: '140px', width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={yieldHistory} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                      <defs>
                        <linearGradient id="pColor" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.6}/>
                          <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                      <Area type="monotone" dataKey="yield" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#pColor)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* 3. BREEDING & GESTATION */}
          {activeTab === 'BREEDING' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '8px', borderLeft: '3px solid #fb923c' }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#fb923c', marginBottom: '10px' }}>
                  Reproductive Status & Insemination Tracker
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Reproductive Stage</label>
                    <select value={reproStatus} onChange={e => setReproStatus(e.target.value as any)} style={{ width: '100%', background: '#0f172a', color: '#fb923c', border: '1px solid #fb923c', padding: '8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>
                      <option value="Open">Open (Cycling)</option>
                      <option value="Inseminated">Inseminated (Pending Check)</option>
                      <option value="Pregnant">Confirmed Pregnant</option>
                      <option value="Dry">Dry Cow</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>AI Date</label>
                    <input type="date" value={aiDate} onChange={e => setAiDate(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Semen Straw Code / Sire</label>
                    <input type="text" value={aiBullCode} onChange={e => setAiBullCode(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 4. HEALTH & TREATMENTS */}
          {activeTab === 'HEALTH' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '8px', borderLeft: '3px solid #ef4444' }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#ef4444', marginBottom: '10px' }}>
                  Clinical Status & Safety Controls
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Health Status</label>
                    <select value={healthStatus} onChange={e => setHealthStatus(e.target.value as any)} style={{ width: '100%', background: '#0f172a', color: healthStatus === 'Healthy' ? '#34d399' : '#f87171', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>
                      <option value="Healthy">Healthy</option>
                      <option value="Under Observation">Under Observation</option>
                      <option value="Critical">Critical / Sick</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Body Temperature (°C)</label>
                    <input type="text" value={tempCelsius} onChange={e => setTempCelsius(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Somatic Cell Count (SCC)</label>
                    <input type="text" value={somaticCellCount} onChange={e => setSomaticCellCount(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 5. FEED & INTAKE */}
          {activeTab === 'FEED' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ background: '#1e293b', padding: '14px', borderRadius: '8px', borderLeft: '3px solid #34d399' }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399', marginBottom: '10px' }}>
                  Feed Intake & Feed Conversion Efficiency
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Estimated TMR DMI (kg/day)</label>
                    <input type="number" step="0.1" value={dmiKg} onChange={e => setDmiKg(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Feed Conversion Efficiency (L / kg DMI)</label>
                    <input type="number" step="0.01" value={fceRatio} onChange={e => setFceRatio(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#34d399', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', boxSizing: 'border-box' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 6. EXIT, SALE & MORTALITY GOVERNANCE */}
          {activeTab === 'EXIT' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ background: '#1e293b', padding: '16px', borderRadius: '8px', borderLeft: `4px solid ${isArchived ? '#ef4444' : '#f59e0b'}` }}>
                <div style={{ fontSize: '13px', fontWeight: 'bold', color: isArchived ? '#f87171' : '#f59e0b', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <LogOut size={16} /> Animal Depletion & Herd Exit Notations
                </div>
                <p style={{ fontSize: '11px', color: '#94a3b8', margin: '0 0 14px 0', lineHeight: '1.4' }}>
                  Marking an animal as <strong>Sold</strong>, <strong>Deceased (Mortality)</strong>, or <strong>Culled</strong> automatically deducts the head from active farm inventory while permanently preserving its historical health, milk curve, and ancestry for Data Analytics (Mortality Rates, Asset Realization, and CMPL balance sheets).
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 'bold' }}>Lifecycle / Depletion Status</label>
                    <select 
                      value={lifecycleStatus} 
                      onChange={e => setLifecycleStatus(e.target.value as any)} 
                      style={{ width: '100%', background: '#0f172a', color: lifecycleStatus === 'ACTIVE' ? '#34d399' : '#f87171', border: `1px solid ${lifecycleStatus === 'ACTIVE' ? '#334155' : '#ef4444'}`, padding: '8px', borderRadius: '4px', fontSize: '13px', fontWeight: 'bold' }}
                    >
                      <option value="ACTIVE">Active in Herd (Milking / Growing)</option>
                      <option value="SOLD">Sold (Commercial Asset Realization)</option>
                      <option value="DECEASED">Deceased (Mortality Incident)</option>
                      <option value="CULLED">Culled / Emergency Slaughter</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: '#94a3b8' }}>Date of Exit / Occurrence</label>
                    <input type="date" value={exitDate} onChange={e => setExitDate(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                </div>

                {/* DYNAMIC FORM BASED ON SALE */}
                {lifecycleStatus === 'SOLD' && (
                  <div style={{ marginTop: '14px', padding: '12px', background: '#0f172a', borderRadius: '6px', border: '1px solid #34d399' }}>
                    <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#34d399', marginBottom: '8px' }}>
                      💰 Commercial Sale Ledger Entry
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      <div>
                        <label style={{ fontSize: '11px', color: '#94a3b8' }}>Sale Realization Amount (PKR)</label>
                        <input type="number" value={salePricePKR} onChange={e => setSalePricePKR(e.target.value)} placeholder="0" style={{ width: '100%', background: '#1e293b', color: '#34d399', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', boxSizing: 'border-box' }} />
                      </div>
                      <div>
                        <label style={{ fontSize: '11px', color: '#94a3b8' }}>Buyer / Destination Entity</label>
                        <input type="text" value={buyerDetails} onChange={e => setBuyerDetails(e.target.value)} placeholder="Buyer Name / Farm" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                      </div>
                    </div>
                  </div>
                )}

                {/* DYNAMIC FORM BASED ON MORTALITY */}
                {(lifecycleStatus === 'DECEASED' || lifecycleStatus === 'CULLED') && (
                  <div style={{ marginTop: '14px', padding: '12px', background: '#0f172a', borderRadius: '6px', border: '1px solid #ef4444' }}>
                    <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#f87171', marginBottom: '8px' }}>
                      ⚠️ Mortality & Autopsy Record
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      <div>
                        <label style={{ fontSize: '11px', color: '#94a3b8' }}>Confirmed Cause of Death</label>
                        <input type="text" value={mortalityCause} onChange={e => setMortalityCause(e.target.value)} placeholder="Diagnosis / Clinical Cause" style={{ width: '100%', background: '#1e293b', color: '#fca5a5', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                      </div>
                      <div>
                        <label style={{ fontSize: '11px', color: '#94a3b8' }}>Attending Vet / Autopsy Examiner</label>
                        <input type="text" value={autopsyVet} onChange={e => setAutopsyVet(e.target.value)} placeholder="Dr. Name" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                      </div>
                    </div>
                    <div style={{ marginTop: '8px' }}>
                      <label style={{ fontSize: '11px', color: '#94a3b8' }}>Asset Value Written Off (PKR)</label>
                      <input type="number" value={assetValuationAtExit} onChange={e => setAssetValuationAtExit(e.target.value)} placeholder="0" style={{ width: '50%', background: '#1e293b', color: '#f87171', border: '1px solid #334155', padding: '7px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {savedSuccess && (
            <div style={{ background: 'rgba(52, 211, 153, 0.2)', border: '1px solid #34d399', color: '#34d399', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle2 size={16} /> Biological Passport updated! Headcount and asset registers dynamically refreshed.
            </div>
          )}

          {/* SUBMIT BUTTONS */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
            <button type="button" onClick={onClose} style={{ background: '#1e293b', border: '1px solid #374151', color: '#94a3b8', padding: '8px 16px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}>
              Close
            </button>
            <button type="submit" style={{ background: isArchived ? '#ef4444' : '#38bdf8', border: 'none', color: isArchived ? '#fff' : '#0f172a', fontWeight: 'bold', padding: '8px 20px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}>
              {isArchived ? 'Commit Archive & Exit Ledger' : 'Save Passport'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
