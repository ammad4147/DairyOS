import React, { useState, useEffect } from 'react';
import { Milk, Plus, Search, AlertTriangle, AlertCircle, CheckCircle2, Clock, Home, Baby, Scale, ArrowRightLeft, Award } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';

export interface MilkingAnimalProfile {
  tag: string;
  breed: string;
  modality: 'TWICE_DAILY' | 'THRICE_DAILY';
  expectedBaseline: number;
}

export interface MilkLogRecord {
  id: string;
  tag: string;
  liters: number;
  timestamp: string;
  modality: 'TWICE_DAILY' | 'THRICE_DAILY';
  expected: number;
  variancePct: number;
  warningLevel: 'GREEN' | 'AMBER' | 'RED';
}

export interface DomesticMilkLog {
  id: string;
  date: string;
  recipient: string;
  liters: number;
  notes: string;
}

export interface CalfMilkLog {
  id: string;
  date: string;
  calfTag: string;
  liters: number;
  feedingSession: 'Morning' | 'Evening';
  feederName: string;
}

interface MilkTabProps {
  initialOpenModal?: boolean;
  onModalClose?: () => void;
  milkingAnimals?: MilkingAnimalProfile[];
}

export default function MilkTab({ initialOpenModal = false, onModalClose, milkingAnimals }: MilkTabProps) {
  const [activeSubTab, setActiveSubTab] = useState<'FARM_YIELD' | 'DOMESTIC' | 'CALVES' | 'RECONCILIATION'>('FARM_YIELD');
  const [selectedPassportAnimalId, setSelectedPassportAnimalId] = useState<string | null>(null);

  const activeMilkingList: MilkingAnimalProfile[] = milkingAnimals && milkingAnimals.length > 0 ? milkingAnimals : [
    { tag: 'TD-001', breed: 'Holstein Friesian', modality: 'TWICE_DAILY', expectedBaseline: 38.0 },
    { tag: 'TD-002', breed: 'Sahiwal Cross', modality: 'THRICE_DAILY', expectedBaseline: 36.0 },
    { tag: 'TD-003', breed: 'Cholistani', modality: 'TWICE_DAILY', expectedBaseline: 35.0 },
    { tag: 'TD-009', breed: 'Holstein Purebred', modality: 'THRICE_DAILY', expectedBaseline: 44.0 },
    { tag: 'TD-014', breed: 'Jersey Cross', modality: 'THRICE_DAILY', expectedBaseline: 37.0 },
    { tag: 'TD-018', breed: 'Sahiwal Purebred', modality: 'TWICE_DAILY', expectedBaseline: 28.0 }
  ];

  // 1. Farm Records
  const [records, setRecords] = useState<MilkLogRecord[]>([
    { id: 'REC-101', tag: 'TD-001', liters: 38.5, timestamp: '2026-08-20 06:15 AM', modality: 'TWICE_DAILY', expected: 38.0, variancePct: 1.3, warningLevel: 'GREEN' },
    { id: 'REC-102', tag: 'TD-002', liters: 36.2, timestamp: '2026-08-20 06:30 AM', modality: 'THRICE_DAILY', expected: 36.0, variancePct: 0.6, warningLevel: 'GREEN' },
    { id: 'REC-103', tag: 'TD-003', liters: 29.0, timestamp: '2026-08-20 06:45 AM', modality: 'TWICE_DAILY', expected: 35.0, variancePct: -17.1, warningLevel: 'AMBER' },
    { id: 'REC-104', tag: 'TD-009', liters: 29.0, timestamp: '2026-08-20 07:00 AM', modality: 'THRICE_DAILY', expected: 44.0, variancePct: -34.1, warningLevel: 'RED' },
  ]);

  // 2. Domestic Allocation Logs
  const [domesticLogs, setDomesticLogs] = useState<DomesticMilkLog[]>([
    { id: 'DOM-01', date: '2026-08-20', recipient: 'Farm Main House', liters: 8.0, notes: 'Daily morning fresh milk' },
    { id: 'DOM-02', date: '2026-08-20', recipient: 'Staff Kitchen', liters: 3.5, notes: 'Tea & culinary use' },
  ]);

  // 3. Calf Feeding Logs
  const [calfLogs, setCalfLogs] = useState<CalfMilkLog[]>([
    { id: 'CALF-01', date: '2026-08-20', calfTag: 'TD-006 (Heifer Calf)', liters: 4.0, feedingSession: 'Morning', feederName: 'Muhammad Ali' },
    { id: 'CALF-02', date: '2026-08-20', calfTag: 'TD-007 (Bull Calf)', liters: 3.5, feedingSession: 'Morning', feederName: 'Muhammad Ali' },
    { id: 'CALF-03', date: '2026-08-20', calfTag: 'TD-011 (Heifer Calf)', liters: 4.0, feedingSession: 'Morning', feederName: 'Kashif' },
  ]);

  const [showYieldModal, setShowYieldModal] = useState<boolean>(initialOpenModal);
  const [showDomesticModal, setShowDomesticModal] = useState(false);
  const [showCalfModal, setShowCalfModal] = useState(false);
  
  const [selectedTag, setSelectedTag] = useState<string>(activeMilkingList[0]?.tag || 'TD-001');
  const [milkYieldInput, setMilkYieldInput] = useState<string>('');

  const [domRecipient, setDomRecipient] = useState('Farm Main House');
  const [domLiters, setDomLiters] = useState('');
  const [domNotes, setDomNotes] = useState('');

  const [calfTagInput, setCalfTagInput] = useState('TD-006 (Female Calf)');
  const [calfLitersInput, setCalfLitersInput] = useState('');
  const [calfSessionInput, setCalfSessionInput] = useState<'Morning' | 'Evening'>('Morning');
  const [feederNameInput, setFeederNameInput] = useState('Muhammad Ali');

  useEffect(() => {
    if (initialOpenModal) setShowYieldModal(true);
  }, [initialOpenModal]);

  const handleCloseYieldModal = () => {
    setShowYieldModal(false);
    setMilkYieldInput('');
    if (onModalClose) onModalClose();
  };

  const handleQuickSaveYield = async (e: React.FormEvent) => {
    e.preventDefault();
    const liters = parseFloat(milkYieldInput);
    if (isNaN(liters) || liters <= 0) return;

    const profile = activeMilkingList.find(a => a.tag === selectedTag) || {
      tag: selectedTag,
      breed: 'Custom Breed',
      modality: 'TWICE_DAILY',
      expectedBaseline: 30.0
    };

    const exp = profile.expectedBaseline;
    const variancePct = parseFloat((((liters - exp) / exp) * 100).toFixed(1));
    
    let warningLevel: 'GREEN' | 'AMBER' | 'RED' = 'GREEN';
    if (variancePct <= -25) warningLevel = 'RED';
    else if (variancePct <= -10) warningLevel = 'AMBER';

    const now = new Date();
    const formattedTimestamp = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) + ' ' +
                               now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    const newEntry: MilkLogRecord = {
      id: `REC-${Date.now().toString().slice(-4)}`,
      tag: selectedTag,
      liters,
      timestamp: formattedTimestamp,
      modality: profile.modality,
      expected: exp,
      variancePct,
      warningLevel
    };

          try {
        await fetch('/farm/milk/' + selectedTag + '/milk-entry', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ liters: liters, session: profile.modality, expected: exp, variance: variancePct })
        });
      } catch (err) { console.error('OS Sync Failed', err); }
      setRecords([newEntry, ...records]);
      handleCloseYieldModal();
  };

  const handleSaveDomestic = async (e: React.FormEvent) => {
    e.preventDefault();
    const l = parseFloat(domLiters);
    if (isNaN(l) || l <= 0) return;

          const currentYield = records.reduce((sum, r) => sum + r.liters, 0);
      const currentDisposed = domesticLogs.reduce((sum, d) => sum + d.liters, 0) + calfLogs.reduce((sum, c) => sum + c.liters, 0);
      if ((currentDisposed + l) > currentYield) {
        alert('MASS BALANCE ANOMALY: Cannot allocate ' + l + 'L. Only ' + (currentYield - currentDisposed).toFixed(1) + 'L remains from today\'s physical yield. Disposition rejected.');
        return;
      }
      const newDom: DomesticMilkLog = {
      id: `DOM-${Date.now().toString().slice(-4)}`,
      date: new Date().toISOString().split('T')[0],
      recipient: domRecipient,
      liters: l,
      notes: domNotes || 'Domestic kitchen consumption'
    };
          try {
        await fetch('/farm/milk/disposition', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ production_date: new Date().toISOString().split('T')[0], disposition_type: 'DOMESTIC', quantity_litres: l, notes: domNotes })
        });
      } catch (err) { console.error('OS Sync Failed', err); }
      setDomesticLogs([newDom, ...domesticLogs]);
    setShowDomesticModal(false);
    setDomLiters('');
    setDomNotes('');
  };

  const handleSaveCalf = async (e: React.FormEvent) => {
    e.preventDefault();
    const l = parseFloat(calfLitersInput);
    if (isNaN(l) || l <= 0) return;

          const currentYield = records.reduce((sum, r) => sum + r.liters, 0);
      const currentDisposed = domesticLogs.reduce((sum, d) => sum + d.liters, 0) + calfLogs.reduce((sum, c) => sum + c.liters, 0);
      if ((currentDisposed + l) > currentYield) {
        alert('MASS BALANCE ANOMALY: Cannot allocate ' + l + 'L. Only ' + (currentYield - currentDisposed).toFixed(1) + 'L remains from today\'s physical yield. Disposition rejected.');
        return;
      }
      const newCalf: CalfMilkLog = {
      id: `CALF-${Date.now().toString().slice(-4)}`,
      date: new Date().toISOString().split('T')[0],
      calfTag: calfTagInput,
      liters: l,
      feedingSession: calfSessionInput,
      feederName: feederNameInput
    };
          try {
        await fetch('/farm/milk/disposition', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ production_date: new Date().toISOString().split('T')[0], disposition_type: 'CALF_FEEDING', quantity_litres: l, notes: calfSessionInput })
        });
      } catch (err) { console.error('OS Sync Failed', err); }
      setCalfLogs([newCalf, ...calfLogs]);
    setShowCalfModal(false);
    setCalfLitersInput('');
  };

  const totalFarmYield = records.reduce((acc, r) => acc + r.liters, 0);
  const totalDomestic = domesticLogs.reduce((acc, r) => acc + r.liters, 0);
  const totalCalfFeeding = calfLogs.reduce((acc, r) => acc + r.liters, 0);
  const commercialSoldLiters = 120.0;
  const totalAllocated = totalDomestic + totalCalfFeeding + commercialSoldLiters;
  const reconciliationVariance = parseFloat((totalFarmYield - totalAllocated).toFixed(2));
  const isReconciled = reconciliationVariance === 0;

  return (
    <div style={{ padding: '20px', color: '#fff' }}>
      
      {/* Header & Sub-Tab Navigation Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Milk size={20} /> Milk Production & Farm Yield Management
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Track Total Farm Yield, domestic household allocation, calf nursery feeding, and commercial sales reconciliation.
          </p>
        </div>

        {/* Sub-tab Switcher */}
        <div style={{ display: 'flex', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '3px' }}>
          <button 
            onClick={() => setActiveSubTab('FARM_YIELD')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: activeSubTab === 'FARM_YIELD' ? '#1e293b' : 'transparent', color: activeSubTab === 'FARM_YIELD' ? '#38bdf8' : '#94a3b8', border: 'none', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <Milk size={13} /> Farm Production
          </button>
          <button 
            onClick={() => setActiveSubTab('DOMESTIC')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: activeSubTab === 'DOMESTIC' ? '#1e293b' : 'transparent', color: activeSubTab === 'DOMESTIC' ? '#38bdf8' : '#94a3b8', border: 'none', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <Home size={13} /> Domestic Use ({totalDomestic} L)
          </button>
          <button 
            onClick={() => setActiveSubTab('CALVES')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: activeSubTab === 'CALVES' ? '#1e293b' : 'transparent', color: activeSubTab === 'CALVES' ? '#38bdf8' : '#94a3b8', border: 'none', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <Baby size={13} /> Calf Feeding ({totalCalfFeeding} L)
          </button>
          <button 
            onClick={() => setActiveSubTab('RECONCILIATION')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: activeSubTab === 'RECONCILIATION' ? (isReconciled ? '#065f46' : '#7f1d1d') : 'transparent', color: activeSubTab === 'RECONCILIATION' ? '#fff' : (isReconciled ? '#34d399' : '#f87171'), border: 'none', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <Scale size={13} /> Reconciliation Audit {!isReconciled && `(${reconciliationVariance} L)`}
          </button>
        </div>
      </div>

      {/* SUMMARY TILES */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px', marginBottom: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '10px 12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>1. Total Farm Yield</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff' }}>{totalFarmYield.toFixed(1)} L</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '10px 12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>2. Commercial Sold</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>{commercialSoldLiters.toFixed(1)} L</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '10px 12px', borderRadius: '6px', borderLeft: '3px solid #a855f7' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>3. Domestic Use</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#c084fc' }}>{totalDomestic.toFixed(1)} L</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '10px 12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>4. Calf Feeding</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fb923c' }}>{totalCalfFeeding.toFixed(1)} L</div>
        </div>

        <div style={{ background: isReconciled ? '#064e3b' : '#450a0a', border: `1px solid ${isReconciled ? '#059669' : '#dc2626'}`, padding: '10px 12px', borderRadius: '6px' }}>
          <div style={{ fontSize: '10px', color: isReconciled ? '#a7f3d0' : '#fecaca', fontWeight: 'bold' }}>5. Reconciliation Variance</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: isReconciled ? '#34d399' : '#f87171' }}>
            {reconciliationVariance > 0 ? `+${reconciliationVariance} L` : `${reconciliationVariance} L`}
          </div>
        </div>
      </div>

      {/* RECONCILIATION UNBALANCED ALERT BANNER */}
      {!isReconciled && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', padding: '10px 14px', borderRadius: '8px', marginBottom: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="#ef4444" />
            <span style={{ fontSize: '12px', color: '#fca5a5', fontWeight: 'bold' }}>
              Mass-Balance Discrepancy: Unallocated volume of {reconciliationVariance} Liters detected between total produced ({totalFarmYield} L) and allocated volumes ({totalAllocated} L).
            </span>
          </div>
          <button 
            onClick={() => setActiveSubTab('RECONCILIATION')}
            style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            Audit Balance
          </button>
        </div>
      )}

      {/* SUB-TAB 1: FARM PRODUCTION LOGS */}
      {activeSubTab === 'FARM_YIELD' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#38bdf8' }}>Farm Milking Log Entries</span>
            <button 
              onClick={() => setShowYieldModal(true)} 
              style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
            >
              <Plus size={15} /> Enter Milk Production
            </button>
          </div>

          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
                  <th style={{ padding: '10px 12px' }}>Animal ID (Click Passport)</th>
                  <th style={{ padding: '10px 12px' }}>Timestamp</th>
                  <th style={{ padding: '10px 12px' }}>Modality</th>
                  <th style={{ padding: '10px 12px' }}>Logged Yield</th>
                  <th style={{ padding: '10px 12px' }}>Target Baseline</th>
                  <th style={{ padding: '10px 12px' }}>Variance</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>Drop Alert</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid #1a2234' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#38bdf8' }}>
                      <button 
                        onClick={() => setSelectedPassportAnimalId(r.tag)} 
                        style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', textDecoration: 'underline', padding: 0, fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Award size={13} /> {r.tag}
                      </button>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8' }}>{r.timestamp}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{ color: r.modality === 'THRICE_DAILY' ? '#c084fc' : '#fb923c', fontWeight: 'bold' }}>
                        {r.modality === 'THRICE_DAILY' ? '3x Daily' : '2x Daily'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#fff' }}>{r.liters} L</td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8' }}>{r.expected} L</td>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: r.variancePct < -25 ? '#ef4444' : (r.variancePct < -10 ? '#fbbf24' : '#34d399') }}>
                      {r.variancePct > 0 ? `+${r.variancePct}%` : `${r.variancePct}%`}
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                      {r.warningLevel === 'GREEN' && <span style={{ color: '#34d399', fontWeight: 'bold' }}>Normal</span>}
                      {r.warningLevel === 'AMBER' && <span style={{ color: '#fbbf24', fontWeight: 'bold' }}>Amber (-10%)</span>}
                      {r.warningLevel === 'RED' && <span style={{ color: '#f87171', fontWeight: 'bold' }}>Red (&gt;25%)</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: DOMESTIC USE */}
      {activeSubTab === 'DOMESTIC' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#c084fc' }}>Domestic Household Allocations</span>
            <button 
              onClick={() => setShowDomesticModal(true)} 
              style={{ background: '#a855f7', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
            >
              <Plus size={15} /> Log Domestic Milk
            </button>
          </div>

          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
                  <th style={{ padding: '10px 12px' }}>Log ID</th>
                  <th style={{ padding: '10px 12px' }}>Date</th>
                  <th style={{ padding: '10px 12px' }}>Recipient Entity</th>
                  <th style={{ padding: '10px 12px' }}>Quantity (Liters)</th>
                  <th style={{ padding: '10px 12px' }}>Purpose / Notes</th>
                </tr>
              </thead>
              <tbody>
                {domesticLogs.map((d) => (
                  <tr key={d.id} style={{ borderBottom: '1px solid #1a2234' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#38bdf8' }}>{d.id}</td>
                    <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{d.date}</td>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#c084fc' }}>{d.recipient}</td>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#fff' }}>{d.liters} L</td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8' }}>{d.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-TAB 3: CALVES FEEDING */}
      {activeSubTab === 'CALVES' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#fb923c' }}>Calf Nursery Milk Feeding Logs</span>
            <button 
              onClick={() => setShowCalfModal(true)} 
              style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
            >
              <Plus size={15} /> Log Calf Milk
            </button>
          </div>

          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
                  <th style={{ padding: '10px 12px' }}>Log ID</th>
                  <th style={{ padding: '10px 12px' }}>Date</th>
                  <th style={{ padding: '10px 12px' }}>Calf Tag</th>
                  <th style={{ padding: '10px 12px' }}>Session</th>
                  <th style={{ padding: '10px 12px' }}>Quantity Fed</th>
                  <th style={{ padding: '10px 12px' }}>Attendant / Feeder</th>
                </tr>
              </thead>
              <tbody>
                {calfLogs.map((c) => (
                  <tr key={c.id} style={{ borderBottom: '1px solid #1a2234' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#38bdf8' }}>{c.id}</td>
                    <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{c.date}</td>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#fb923c' }}>{c.calfTag}</td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8' }}>{c.feedingSession}</td>
                    <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#fff' }}>{c.liters} L</td>
                    <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{c.feederName}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-TAB 4: RECONCILIATION */}
      {activeSubTab === 'RECONCILIATION' && (
        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '16px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '15px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ArrowRightLeft size={18} color="#38bdf8" /> Daily Milk Balance Reconciliation
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
            <div style={{ background: '#1e293b', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '8px' }}>Total Farm Yield (Production)</div>
              <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#38bdf8' }}>{totalFarmYield.toFixed(1)} Liters</div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Aggregated across all active milking cows</div>
            </div>

            <div style={{ background: '#1e293b', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '8px' }}>Total Allocated Volume (Outflow)</div>
              <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#fff' }}>{totalAllocated.toFixed(1)} Liters</div>
              <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                Sold ({commercialSoldLiters}L) + Domestic ({totalDomestic}L) + Calves ({totalCalfFeeding}L)
              </div>
            </div>
          </div>

          <div style={{ background: isReconciled ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: `1px solid ${isReconciled ? '#10b981' : '#ef4444'}`, padding: '14px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {isReconciled ? <CheckCircle2 size={22} color="#34d399" /> : <AlertCircle size={22} color="#f87171" />}
              <div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', color: isReconciled ? '#34d399' : '#f87171' }}>
                  {isReconciled ? 'Reconciled: All produced milk is fully accounted for.' : `Discrepancy: ${reconciliationVariance} Liters unaccounted.`}
                </div>
                <div style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '2px' }}>
                  {isReconciled 
                    ? 'Finance and analytics modules are accurately balanced against physical farm outflow.'
                    : 'Unaccounted milk will distort Cost of Milk Production per Liter (CMPL) and gross revenue realization.'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 1: FAST YIELD ENTRY */}
      {showYieldModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '16px' }}>
          <form onSubmit={handleQuickSaveYield} style={{ background: '#111827', border: '2px solid #38bdf8', padding: '24px', borderRadius: '12px', width: '100%', maxWidth: '460px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1f2937', paddingBottom: '10px' }}>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '16px' }}>Enter Milk Production</h3>
              <button type="button" onClick={handleCloseYieldModal} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '18px' }}>?</button>
            </div>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8', marginBottom: '6px', display: 'block' }}>1. Select Milking Animal ID</label>
              <select value={selectedTag} onChange={e => setSelectedTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #475569', padding: '12px', borderRadius: '6px', fontSize: '16px', fontWeight: 'bold' }}>
                {activeMilkingList.map(cow => (
                  <option key={cow.tag} value={cow.tag}>{cow.tag}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399', marginBottom: '6px', display: 'block' }}>2. Milk Yield (Liters)</label>
              <input type="number" step="0.1" required placeholder="0.0" value={milkYieldInput} onChange={e => setMilkYieldInput(e.target.value)} autoFocus style={{ width: '100%', background: '#1e293b', color: '#34d399', border: '1px solid #475569', padding: '12px', borderRadius: '6px', fontSize: '20px', fontWeight: 'bold', boxSizing: 'border-box' }} />
            </div>
            <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '12px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>Commit Entry</button>
          </form>
        </div>
      )}

      {/* MODAL 2: DOMESTIC USE */}
      {showDomesticModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '16px' }}>
          <form onSubmit={handleSaveDomestic} style={{ background: '#111827', border: '1px solid #a855f7', padding: '24px', borderRadius: '12px', width: '100%', maxWidth: '440px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1f2937', paddingBottom: '10px' }}>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '16px' }}>Log Domestic Milk Use</h3>
              <button type="button" onClick={() => setShowDomesticModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '18px' }}>?</button>
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8' }}>Recipient Entity</label>
              <select value={domRecipient} onChange={e => setDomRecipient(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
                <option value="Farm Main House">Farm Main House</option>
                <option value="Staff Kitchen">Staff Kitchen</option>
                <option value="Guest Hospitality">Guest Hospitality</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8' }}>Quantity (Liters)</label>
              <input type="number" step="0.5" required placeholder="0.0" value={domLiters} onChange={e => setDomLiters(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '14px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8' }}>Notes</label>
              <input type="text" placeholder="Remarks..." value={domNotes} onChange={e => setDomNotes(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
            </div>
            <button type="submit" style={{ background: '#a855f7', color: '#fff', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>Commit Domestic Allocation</button>
          </form>
        </div>
      )}

      {/* MODAL 3: CALF FEEDING */}
      {showCalfModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '16px' }}>
          <form onSubmit={handleSaveCalf} style={{ background: '#111827', border: '1px solid #fb923c', padding: '24px', borderRadius: '12px', width: '100%', maxWidth: '440px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1f2937', paddingBottom: '10px' }}>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '16px' }}>Log Calf Nursery Milk</h3>
              <button type="button" onClick={() => setShowCalfModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '18px' }}>?</button>
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8' }}>Calf Tag / ID</label>
              <select value={calfTagInput} onChange={e => setCalfTagInput(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
                <option value="TD-006 (Female Calf)">TD-006 (Female Calf)</option>
                <option value="TD-007 (Male Calf)">TD-007 (Male Calf)</option>
                <option value="TD-011 (Female Calf)">TD-011 (Female Calf)</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8' }}>Session</label>
              <select value={calfSessionInput} onChange={e => setCalfSessionInput(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
                <option value="Morning">Morning</option>
                <option value="Evening">Evening</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8' }}>Quantity (Liters)</label>
              <input type="number" step="0.5" required placeholder="0.0" value={calfLitersInput} onChange={e => setCalfLitersInput(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '14px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8' }}>Attendant / Feeder</label>
              <input type="text" value={feederNameInput} onChange={e => setFeederNameInput(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
            </div>
            <button type="submit" style={{ background: '#fb923c', color: '#0f172a', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>Commit Calf Allocation</button>
          </form>
        </div>
      )}

      {/* FULL PASSPORT MODAL */}
      {selectedPassportAnimalId && (
        <AnimalPassportModal 
          animalId={selectedPassportAnimalId} 
          onClose={() => setSelectedPassportAnimalId(null)} 
        />
      )}

    </div>
  );
}
