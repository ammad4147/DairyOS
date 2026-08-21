import React, { useState } from 'react';
import { Activity, Plus, Search, AlertTriangle, Calendar, CheckCircle2, Award, Heart, Sparkles } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';

interface BreedingTabProps {
  onOpenPassport?: (tag: string) => void;
}

export default function BreedingTab({ onOpenPassport }: BreedingTabProps) {
  const [activeModalPassport, setActiveModalPassport] = useState<string | null>(null);

  const [breedingRecords] = useState([
    { id: 'BRD-01', tag: 'TD-001', status: 'Confirmed Pregnant', aiDate: '2026-03-28', sireCode: 'ABS-SUPERIOR-991', daysPregnant: 145, expectedCalving: '2027-01-02', sexedSemen: true },
    { id: 'BRD-02', tag: 'TD-002', status: 'Inseminated', aiDate: '2026-08-05', sireCode: 'WWS-SAHIWAL-STAR', daysPregnant: 15, expectedCalving: 'Pending PD (Day 35)', sexedSemen: false },
    { id: 'BRD-03', tag: 'TD-003', status: 'On Heat (Ready for AI)', aiDate: '-', sireCode: 'Assigned: US-HO-882', daysPregnant: 0, expectedCalving: '-', sexedSemen: true },
    { id: 'BRD-04', tag: 'TD-005', status: 'Heifer Ready for 1st Service', aiDate: '-', sireCode: 'Candidate: ABS-EASY-CALV', daysPregnant: 0, expectedCalving: '-', sexedSemen: true },
  ]);

  const openPassportHandler = (tag: string) => {
    if (onOpenPassport) {
      onOpenPassport(tag);
    } else {
      setActiveModalPassport(tag);
    }
  };

  return (
    <div style={{ padding: '20px', color: '#fff' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#fb923c', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} /> Breeding, Artificial Insemination (AI) & Gestation Ledger
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Click any Animal ID to view the full biological passport, pedigree family tree, and lactation timeline.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Active Heat Standing</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fb923c' }}>1 Animal (TD-003)</div>
          <div style={{ fontSize: '10px', color: '#fb923c' }}>AI Window: Next 12 Hours</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #60a5fa' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Inseminated (Pending PD)</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#60a5fa' }}>1 Animal (TD-002)</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>PD Check due Day 35</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a78bfa' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Confirmed Pregnant</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#a78bfa' }}>1 Animal (TD-001)</div>
          <div style={{ fontSize: '10px', color: '#a78bfa' }}>145d Gestation Progress</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Heifers Eligible for AI</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>1 Head (TD-005)</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Weight &gt; 340 kg verified</div>
        </div>
      </div>

      {/* BREEDING REGISTRY TABLE */}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
              <th style={{ padding: '10px 12px' }}>Animal ID (Click Passport)</th>
              <th style={{ padding: '10px 12px' }}>Reproductive Stage</th>
              <th style={{ padding: '10px 12px' }}>AI Date</th>
              <th style={{ padding: '10px 12px' }}>Sire Straw Code</th>
              <th style={{ padding: '10px 12px' }}>Gestation Progress</th>
              <th style={{ padding: '10px 12px' }}>Expected Calving</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Dossier</th>
            </tr>
          </thead>
          <tbody>
            {breedingRecords.map(b => (
              <tr key={b.id} style={{ borderBottom: '1px solid #1a2234' }}>
                <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#38bdf8' }}>
                  <button onClick={() => openPassportHandler(b.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', textDecoration: 'underline', padding: 0, fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <Award size={13}/> #{b.tag}
                  </button>
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{ 
                    background: b.status.includes('Pregnant') ? 'rgba(167, 139, 250, 0.2)' : (b.status.includes('Inseminated') ? 'rgba(96, 165, 250, 0.2)' : 'rgba(251, 146, 60, 0.2)'),
                    color: b.status.includes('Pregnant') ? '#a78bfa' : (b.status.includes('Inseminated') ? '#60a5fa' : '#fb923c'),
                    padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' 
                  }}>
                    {b.status}
                  </span>
                </td>
                <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{b.aiDate}</td>
                <td style={{ padding: '10px 12px', color: '#fff', fontWeight: 'bold' }}>{b.sireCode}</td>
                <td style={{ padding: '10px 12px', color: b.daysPregnant > 0 ? '#a78bfa' : '#94a3b8', fontWeight: 'bold' }}>
                  {b.daysPregnant > 0 ? `${b.daysPregnant} Days` : '-'}
                </td>
                <td style={{ padding: '10px 12px', color: '#34d399', fontWeight: 'bold' }}>{b.expectedCalving}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  <button onClick={() => openPassportHandler(b.tag)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#38bdf8', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}>
                    Open Passport
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {activeModalPassport && (
        <AnimalPassportModal 
          animalId={activeModalPassport} 
          onClose={() => setActiveModalPassport(null)} 
        />
      )}

    </div>
  );
}
