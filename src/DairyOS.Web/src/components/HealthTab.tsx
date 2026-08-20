import React, { useState } from 'react';
import { HeartPulse, Plus, Search, ShieldAlert, CheckCircle2, Award, AlertTriangle, Stethoscope } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';

interface HealthTabProps {
  onOpenPassport?: (tag: string) => void;
}

export default function HealthTab({ onOpenPassport }: HealthTabProps) {
  const [activeModalPassport, setActiveModalPassport] = useState<string | null>(null);

  const [healthCases] = useState([
    { id: 'HLT-101', tag: 'TD-004', condition: 'Clinical Mastitis', severity: 'Critical', temp: '39.8°C', treatment: 'Intramammary Antibiotic + Flunixin', vet: 'Dr. Tariq', withdrawal: true, daysRemaining: 3 },
    { id: 'HLT-102', tag: 'TD-009', condition: 'Sub-acute Ruminal Acidosis', severity: 'Amber Warning', temp: '38.8°C', treatment: 'Buffer Drench + Hay adjustment', vet: 'Dr. Tariq', withdrawal: false, daysRemaining: 0 },
    { id: 'HLT-103', tag: 'TD-012', condition: 'Hoof Trimming / Lameness', severity: 'Mild', temp: '38.5°C', treatment: 'Footbath (Copper Sulphate)', vet: 'Farm Paravet', withdrawal: false, daysRemaining: 0 },
  ]);

  const [vaxRecords] = useState([
    { id: 'VAX-201', tag: 'TD-001', vaccine: 'FMD (Foot & Mouth Disease)', date: '2026-07-15', nextDue: '2027-01-15', status: 'Completed' },
    { id: 'VAX-202', tag: 'TD-002', vaccine: 'HS (Haemorrhagic Septicaemia)', date: '2026-06-10', nextDue: '2026-12-10', status: 'Completed' },
    { id: 'VAX-203', tag: 'TD-003', vaccine: 'Anthrax Spore Vaccine', date: '2026-08-01', nextDue: '2027-08-01', status: 'Completed' },
    { id: 'VAX-204', tag: 'TD-005', vaccine: 'Brucellosis (Heifer Dose)', date: '2026-08-25', nextDue: '2026-08-25', status: 'Scheduled Due' },
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
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <HeartPulse size={20} /> Herd Health, Treatments & Mandatory Safety Controls
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Click any Animal ID to open the comprehensive Biological Passport and audit full veterinary histories.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #ef4444' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Active Medical Cases</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f87171' }}>{healthCases.length} Head</div>
          <div style={{ fontSize: '10px', color: '#f87171' }}>Under veterinary care</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Milk Withdrawal Lock (Antibiotics)</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fbbf24' }}>1 Cow (TD-004)</div>
          <div style={{ fontSize: '10px', color: '#fbbf24' }}>Milk withheld from sale</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Vaccination Coverage</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>94.2%</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Up-to-date protocol</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Upcoming Scheduled Shots</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#38bdf8' }}>1 Due This Week</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Heifer TD-005</div>
        </div>
      </div>

      {/* ACTIVE CLINICAL TREATMENTS TABLE */}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden', marginBottom: '20px' }}>
        <div style={{ padding: '12px 14px', background: '#161f30', borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Stethoscope size={16} color="#ef4444" />
          <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff' }}>Active Clinical & Sick Animal Register</span>
        </div>
        <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#111827' }}>
              <th style={{ padding: '10px 12px' }}>Animal ID (Passport)</th>
              <th style={{ padding: '10px 12px' }}>Diagnosed Condition</th>
              <th style={{ padding: '10px 12px' }}>Temperature</th>
              <th style={{ padding: '10px 12px' }}>Treatment / Protocol</th>
              <th style={{ padding: '10px 12px' }}>Attending Vet</th>
              <th style={{ padding: '10px 12px' }}>Withdrawal Lock</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Dossier</th>
            </tr>
          </thead>
          <tbody>
            {healthCases.map(h => (
              <tr key={h.id} style={{ borderBottom: '1px solid #1a2234' }}>
                <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#38bdf8' }}>
                  <button onClick={() => openPassportHandler(h.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', textDecoration: 'underline', padding: 0, fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <Award size={13}/> #{h.tag}
                  </button>
                </td>
                <td style={{ padding: '10px 12px', color: '#fff', fontWeight: 'bold' }}>{h.condition}</td>
                <td style={{ padding: '10px 12px', color: '#f87171' }}>{h.temp}</td>
                <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{h.treatment}</td>
                <td style={{ padding: '10px 12px', color: '#94a3b8' }}>{h.vet}</td>
                <td style={{ padding: '10px 12px' }}>
                  {h.withdrawal ? (
                    <span style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', border: '1px solid #ef4444', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' }}>
                      LOCK ACTIVE ({h.daysRemaining}d)
                    </span>
                  ) : (
                    <span style={{ color: '#34d399', fontSize: '11px' }}>Clear</span>
                  )}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  <button onClick={() => openPassportHandler(h.tag)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#38bdf8', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}>
                    Open Passport
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* VACCINATION SCHEDULE TABLE */}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
        <div style={{ padding: '12px 14px', background: '#161f30', borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={16} color="#34d399" />
          <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff' }}>Immunization & Preventive Vaccination Registry</span>
        </div>
        <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#111827' }}>
              <th style={{ padding: '10px 12px' }}>Animal ID (Passport)</th>
              <th style={{ padding: '10px 12px' }}>Vaccine Name</th>
              <th style={{ padding: '10px 12px' }}>Administered Date</th>
              <th style={{ padding: '10px 12px' }}>Next Booster Due</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {vaxRecords.map(v => (
              <tr key={v.id} style={{ borderBottom: '1px solid #1a2234' }}>
                <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#38bdf8' }}>
                  <button onClick={() => openPassportHandler(v.tag)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', textDecoration: 'underline', padding: 0, fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <Award size={13}/> #{v.tag}
                  </button>
                </td>
                <td style={{ padding: '10px 12px', color: '#fff' }}>{v.vaccine}</td>
                <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{v.date}</td>
                <td style={{ padding: '10px 12px', color: '#fbbf24', fontWeight: 'bold' }}>{v.nextDue}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  <span style={{ background: v.status === 'Completed' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(251, 191, 36, 0.15)', color: v.status === 'Completed' ? '#34d399' : '#fbbf24', padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' }}>
                    {v.status}
                  </span>
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
