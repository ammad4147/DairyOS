import React, { useState, useEffect } from 'react';
import { Milk, Plus, X } from 'lucide-react';

interface Props {
  initialOpenModal?: boolean;
  onModalClose?: () => void;
}

export default function MilkTab({ initialOpenModal, onModalClose }: Props) {
  const [isModalOpen, setIsModalOpen] = useState(initialOpenModal || false);
  const [yieldInput, setYieldInput] = useState<string>('');
  const [selectedAnimal, setSelectedAnimal] = useState('TD-001');
  const [shift, setShift] = useState('Morning');

  useEffect(() => {
    if (initialOpenModal) setIsModalOpen(true);
  }, [initialOpenModal]);

  const handleClose = () => {
    setIsModalOpen(false);
    if (onModalClose) onModalClose();
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    // Calculations continue in background as actuals, but UI ensures integer entry
    console.log(`Saved ${yieldInput} L for ${selectedAnimal} during ${shift} shift`);
    setYieldInput('');
    handleClose();
  };

  const handleYieldChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Strip out ANY non-digit character (prevents pasting decimals)
    const val = e.target.value.replace(/\D/g, '');
    setYieldInput(val);
  };

  // Background data can have decimals, UI will display whole numbers
  const recentYields = [
    { id: 'TD-001', shift: 'Morning', yield: 16.2, time: '05:30 AM' },
    { id: 'TD-002', shift: 'Morning', yield: 14.8, time: '05:35 AM' },
    { id: 'TD-003', shift: 'Morning', yield: 18.5, time: '05:40 AM' },
    { id: 'TD-009', shift: 'Morning', yield: 21.1, time: '05:45 AM' },
  ];

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Milk size={22} /> Milk Production Register
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Record and monitor daily herd yields. Displaying whole numbers only.
          </p>
        </div>
        <button onClick={() => setIsModalOpen(true)} style={{ background: 'linear-gradient(135deg, #0ea5e9, #0284c7)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)' }}>
          <Plus size={16}/> Enter Yield
        </button>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #38bdf8' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Today's Total (Liters)</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff' }}>{(133.5).toFixed(0)}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #34d399' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Avg Yield / Cow</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#34d399' }}>{(22.25).toFixed(0)}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #f59e0b' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Top Producer</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>{(45.8).toFixed(0)}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #a855f7' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Milking Herd Size</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#a855f7' }}>6</div>
        </div>
      </div>

      {/* Data Table - Forcing display to whole numbers */}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', background: '#161f30', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '14px', color: '#e2e8f0' }}>Today's Sessions</h3>
        </div>
        <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#0f172a', borderBottom: '1px solid #1f2937', textAlign: 'left', color: '#94a3b8' }}>
              <th style={{ padding: '12px 16px' }}>Animal ID</th>
              <th style={{ padding: '12px 16px' }}>Shift</th>
              <th style={{ padding: '12px 16px' }}>Time Recorded</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>Yield (Liters)</th>
            </tr>
          </thead>
          <tbody>
            {recentYields.map((r, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #1a2234' }}>
                <td style={{ padding: '12px 16px', color: '#38bdf8', fontWeight: 'bold' }}>{r.id}</td>
                <td style={{ padding: '12px 16px', color: '#cbd5e1' }}>{r.shift}</td>
                <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{r.time}</td>
                <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 'bold', color: '#fff' }}>
                  {r.yield.toFixed(0)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Strict Integer Entry Modal */}
      {isModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #38bdf8', borderRadius: '10px', width: '400px', overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(2, 132, 199, 0.5)' }}>
            <div style={{ background: '#1e293b', padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #334155' }}>
              <h3 style={{ margin: 0, fontSize: '16px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus size={18} color="#38bdf8" /> Record Milk Yield
              </h3>
              <button onClick={handleClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={18} /></button>
            </div>
            
            <form onSubmit={handleSave} style={{ padding: '20px' }}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Animal ID</label>
                <select value={selectedAnimal} onChange={e => setSelectedAnimal(e.target.value)} style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '14px', outline: 'none' }}>
                  <option value="TD-001">TD-001 (Holstein Friesian)</option>
                  <option value="TD-002">TD-002 (Sahiwal Cross)</option>
                  <option value="TD-003">TD-003 (Cholistani)</option>
                  <option value="TD-009">TD-009 (Holstein Purebred)</option>
                </select>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>Milking Shift</label>
                <select value={shift} onChange={e => setShift(e.target.value)} style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '6px', fontSize: '14px', outline: 'none' }}>
                  <option>Morning</option>
                  <option>Afternoon</option>
                  <option>Evening</option>
                </select>
              </div>

              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>
                  Yield (Whole Liters Only)
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    required
                    value={yieldInput}
                    onChange={handleYieldChange}
                    onKeyDown={(e) => {
                      // ABSOLUTE BLOCK: Stop user from pressing period, comma, minus, or 'e'
                      if (e.key === '.' || e.key === ',' || e.key === 'e' || e.key === 'E' || e.key === '-') {
                        e.preventDefault();
                      }
                    }}
                    placeholder="e.g. 16"
                    style={{ width: '100%', background: '#0f172a', border: '1px solid #38bdf8', color: '#fff', padding: '12px 12px 12px 40px', borderRadius: '6px', fontSize: '18px', fontWeight: 'bold', outline: 'none', boxSizing: 'border-box' }}
                  />
                  <Milk size={18} color="#38bdf8" style={{ position: 'absolute', left: '12px', top: '14px' }} />
                  <span style={{ position: 'absolute', right: '16px', top: '14px', color: '#94a3b8', fontSize: '14px', fontWeight: 'bold' }}>L</span>
                </div>
                <p style={{ fontSize: '10px', color: '#64748b', marginTop: '6px' }}>
                  * Decimals are disabled. Please enter whole numbers (e.g., 16 not 16.2).
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={handleClose} style={{ background: 'none', border: '1px solid #334155', color: '#e2e8f0', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>Cancel</button>
                <button type="submit" style={{ background: 'linear-gradient(135deg, #0ea5e9, #0284c7)', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)' }}>
                  Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
