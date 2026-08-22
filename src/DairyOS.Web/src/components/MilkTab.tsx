import React, { useState } from 'react';
import { Milk, Calendar, Droplets, Plus, X, Save, List } from 'lucide-react';

interface HerdAnimal {
  id: string;
  breed: string;
  category: string;
}

interface MilkTabProps {
  initialOpenModal?: boolean;
  onModalClose?: () => void;
  herdMasterList?: HerdAnimal[];
  onSaveYield?: (addedLiters: number) => void;
  realTimeTodaySold?: number;
}

export default function MilkTab({ initialOpenModal = false, onModalClose, herdMasterList = [], onSaveYield, realTimeTodaySold = 110 }: MilkTabProps) {
  // Data Entry Modal State
  const [activeModal, setActiveModal] = useState<'Production' | 'Domestic' | 'Calves' | null>(initialOpenModal ? 'Production' : null);
  const [inputValue, setInputValue] = useState('');
  const [selectedAnimal, setSelectedAnimal] = useState('BULK');
  
  // List Viewing Modal State
  const [viewList, setViewList] = useState<'MonthlyProduced' | 'MonthlySold' | 'TodayProduced' | 'MonthlyReconciliation' | null>(null);

  // Local Today's State
  const [todayProduced, setTodayProduced] = useState(133); // Baseline mock
  const [todayDomestic, setTodayDomestic] = useState(5);
  const [todayCalves, setTodayCalves] = useState(10);
  const todaySold = realTimeTodaySold;

  // Live Today's Log (Updates when you enter milk)
  const [todayLogs, setTodayLogs] = useState<{id: string, time: string, animalId: string, liters: number}[]>([
    { id: 'LOG-1', time: '06:00 AM', animalId: 'TD-001', liters: 14.5 },
    { id: 'LOG-2', time: '06:05 AM', animalId: 'TD-002', liters: 12.0 }
  ]);

  // Mock Monthly Data for Lists
  const monthlyProducedLogs = [
    { date: 'August 22, 2026', liters: 133 },
    { date: 'August 21, 2026', liters: 128 },
    { date: 'August 20, 2026', liters: 131 },
    { date: 'August 19, 2026', liters: 129 },
  ];
  
  const monthlySoldLogs = [
    { date: 'August 22, 2026', liters: 110 },
    { date: 'August 21, 2026', liters: 108 },
    { date: 'August 20, 2026', liters: 112 },
    { date: 'August 19, 2026', liters: 105 },
  ];

  const monthlyReconLogs = [
    { date: 'August 21, 2026', variance: 0 },
    { date: 'August 20, 2026', variance: -2.0 },
    { date: 'August 19, 2026', variance: 0 },
    { date: 'August 18, 2026', variance: +2.0 }, // Total historical variance balances to 0 for the mock
  ];

  // Daily True Variance Calculation (Produced - ALL OUTFLOWS)
  const todayReconciliation = todayProduced - (todaySold + todayDomestic + todayCalves);

  // FORENSIC AUDIT INJECTION: True Monthly Mass Balance
  const monthlyProduced = 3980;
  const monthlySold = 3700;
  const monthlyDomestic = 150;
  const monthlyCalves = 130;
  const historicalMonthlyVariance = monthlyProduced - (monthlySold + monthlyDomestic + monthlyCalves);
  
  // Mathematically binds monthlyReconciliation to dynamically include todayReconciliation
  const monthlyReconciliation = historicalMonthlyVariance + todayReconciliation;

  const todayDateStr = new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' });

  const handleCloseEntry = () => {
    setActiveModal(null);
    if (onModalClose) onModalClose();
  };

  const handleSaveEntry = (e: React.FormEvent) => {
    e.preventDefault();
    const amount = parseFloat(inputValue);
    if (!isNaN(amount) && amount > 0) {
      if (activeModal === 'Production') {
        setTodayProduced(prev => prev + amount);
        
        // Add to live list
        setTodayLogs([{
          id: `LOG-${Date.now()}`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          animalId: selectedAnimal,
          liters: amount
        }, ...todayLogs]);

        if (onSaveYield) onSaveYield(amount);
      } else if (activeModal === 'Domestic') {
        setTodayDomestic(prev => prev + amount);
      } else if (activeModal === 'Calves') {
        setTodayCalves(prev => prev + amount);
      }
    }
    setInputValue('');
    setSelectedAnimal('BULK');
    handleCloseEntry();
  };

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      
      {/* HEADER */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Milk size={20} /> Mass Balance & Milk Distribution
        </h2>
        <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Track production, sales linkages, and internal farm utilization.</p>
      </div>

      {/* MONTHLY MILK REGISTER */}
      <h3 style={{ fontSize: '14px', color: '#cbd5e1', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Calendar size={16} color="#3b82f6" /> Monthly Milk Register
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '32px' }}>
        {/* Clickable Monthly Produced */}
        <div onClick={() => setViewList('MonthlyProduced')} style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #38bdf8', cursor: 'pointer', transition: 'background 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.background = '#1e293b'} onMouseLeave={(e) => e.currentTarget.style.background = '#111827'}>
          <div style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '6px' }}>Total Milk Produced</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff' }}>{monthlyProduced.toLocaleString()} <span style={{ fontSize: '14px', color: '#94a3b8', fontWeight: 'normal' }}>Liters</span></div>
        </div>
        
        {/* Clickable Monthly Sold */}
        <div onClick={() => setViewList('MonthlySold')} style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #10b981', cursor: 'pointer', transition: 'background 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.background = '#1e293b'} onMouseLeave={(e) => e.currentTarget.style.background = '#111827'}>
          <div style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '6px' }}>Total Milk Sold</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>{monthlySold.toLocaleString()} <span style={{ fontSize: '14px', color: '#94a3b8', fontWeight: 'normal' }}>Liters</span></div>
        </div>

        {/* NOW CLICKABLE: Monthly Reconciliation */}
        <div onClick={() => setViewList('MonthlyReconciliation')} style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #8b5cf6', cursor: 'pointer', transition: 'background 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.background = '#1e293b'} onMouseLeave={(e) => e.currentTarget.style.background = '#111827'}>
          <div style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '6px' }}>Monthly Milk Reconciliation</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: monthlyReconciliation === 0 ? '#10b981' : '#ef4444' }}>{monthlyReconciliation > 0 ? '+' : ''}{monthlyReconciliation.toLocaleString()} <span style={{ fontSize: '14px', color: '#94a3b8', fontWeight: 'normal' }}>Liters</span></div>
        </div>
      </div>

      {/* TODAY'S MILK REGISTER */}
      <h3 style={{ fontSize: '14px', color: '#cbd5e1', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Droplets size={16} color="#38bdf8" /> Today's Milk Register - {todayDateStr}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '24px' }}>
        
        {/* Box 1: Milk Produced */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', borderTop: '3px solid #38bdf8' }}>
          <div onClick={() => setViewList('TodayProduced')} style={{ cursor: 'pointer' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Milk Produced</div>
            <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#fff', marginBottom: '12px' }}>{todayProduced.toFixed(1)} <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 'normal' }}>L</span></div>
          </div>
          <button onClick={() => setActiveModal('Production')} style={{ background: '#1e293b', border: '1px solid #334155', color: '#38bdf8', padding: '8px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', transition: 'all 0.2s' }}>
            <Plus size={12}/> Enter Milk Production
          </button>
        </div>

        {/* Box 2: Milk Sold */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', borderTop: '3px solid #10b981' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Milk Sold</div>
          <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#10b981', marginBottom: '12px' }}>{todaySold.toFixed(1)} <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 'normal' }}>L</span></div>
          <div style={{ fontSize: '11px', color: '#64748b', marginTop: 'auto', padding: '8px 0', fontStyle: 'italic', textAlign: 'center' }}>
            Taken from sales
          </div>
        </div>

        {/* Box 3: Domestic Use */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', borderTop: '3px solid #f59e0b' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Domestic Use</div>
          <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#f59e0b', marginBottom: '12px' }}>{todayDomestic.toFixed(1)} <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 'normal' }}>L</span></div>
          <button onClick={() => setActiveModal('Domestic')} style={{ background: '#1e293b', border: '1px solid #334155', color: '#f59e0b', padding: '8px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
            <Plus size={12}/> Enter Milk for Domestic Use
          </button>
        </div>

        {/* Box 4: Calves Feed */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', borderTop: '3px solid #ec4899' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Calves Feed</div>
          <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#ec4899', marginBottom: '12px' }}>{todayCalves.toFixed(1)} <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 'normal' }}>L</span></div>
          <button onClick={() => setActiveModal('Calves')} style={{ background: '#1e293b', border: '1px solid #334155', color: '#ec4899', padding: '8px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
            <Plus size={12}/> Enter Milk for Calves Feed
          </button>
        </div>

        {/* Box 5: Reconciliation */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '14px', borderRadius: '8px', display: 'flex', flexDirection: 'column', borderTop: '3px solid #8b5cf6' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Reconciliation</div>
          <div style={{ fontSize: '22px', fontWeight: 'bold', color: todayReconciliation === 0 ? '#10b981' : '#ef4444', marginBottom: '12px' }}>
            {todayReconciliation > 0 ? '+' : ''}{todayReconciliation.toFixed(1)} <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 'normal' }}>L</span>
          </div>
          <div style={{ fontSize: '11px', color: '#64748b', marginTop: 'auto', padding: '8px 0', textAlign: 'center' }}>
            Unallocated Balance
          </div>
        </div>

      </div>

      {/* ------------------------------------------------------------- */}
      {/* MODALS FOR LIST VIEWS */}
      {/* ------------------------------------------------------------- */}
      {viewList && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', width: '500px', maxHeight: '80vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)' }}>
            
            <div style={{ padding: '16px 24px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <List size={18} color="#38bdf8" /> 
                {viewList === 'MonthlyProduced' && 'Monthly Daily Production List'}
                {viewList === 'MonthlySold' && 'Monthly Daily Sold List'}
                {viewList === 'TodayProduced' && "Today's Milk Production List"}
                {viewList === 'MonthlyReconciliation' && 'Monthly Reconciliation History'}
              </h3>
              <button onClick={() => setViewList(null)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={18}/></button>
            </div>

            <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ color: '#94a3b8', borderBottom: '1px solid #334155', textAlign: 'left' }}>
                    {viewList === 'TodayProduced' ? (
                      <>
                        <th style={{ padding: '10px' }}>Time</th>
                        <th style={{ padding: '10px' }}>Animal ID</th>
                        <th style={{ padding: '10px', textAlign: 'right' }}>Yield (Liters)</th>
                      </>
                    ) : viewList === 'MonthlyReconciliation' ? (
                      <>
                        <th style={{ padding: '10px' }}>Date</th>
                        <th style={{ padding: '10px', textAlign: 'right' }}>Variance (Liters)</th>
                      </>
                    ) : (
                      <>
                        <th style={{ padding: '10px' }}>Date</th>
                        <th style={{ padding: '10px', textAlign: 'right' }}>Amount (Liters)</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {viewList === 'TodayProduced' && todayLogs.map((log) => (
                    <tr key={log.id} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '10px', color: '#94a3b8' }}>{log.time}</td>
                      <td style={{ padding: '10px', color: '#fff', fontWeight: 'bold' }}>{log.animalId}</td>
                      <td style={{ padding: '10px', color: '#38bdf8', fontWeight: 'bold', textAlign: 'right' }}>{log.liters.toFixed(1)} L</td>
                    </tr>
                  ))}

                  {viewList === 'MonthlyProduced' && monthlyProducedLogs.map((log, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '10px', color: '#e2e8f0' }}>{log.date}</td>
                      <td style={{ padding: '10px', color: '#38bdf8', fontWeight: 'bold', textAlign: 'right' }}>{log.liters.toFixed(1)} L</td>
                    </tr>
                  ))}

                  {viewList === 'MonthlySold' && monthlySoldLogs.map((log, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '10px', color: '#e2e8f0' }}>{log.date}</td>
                      <td style={{ padding: '10px', color: '#10b981', fontWeight: 'bold', textAlign: 'right' }}>{log.liters.toFixed(1)} L</td>
                    </tr>
                  ))}

                  {/* NEW RECONCILIATION LIST WIRE-UP */}
                  {viewList === 'MonthlyReconciliation' && (
                    <>
                      {/* Inject Today's Live Variance at the top */}
                      <tr style={{ borderBottom: '1px solid #1e293b', background: 'rgba(56, 189, 248, 0.05)' }}>
                        <td style={{ padding: '10px', color: '#38bdf8', fontWeight: 'bold' }}>Today (Live)</td>
                        <td style={{ padding: '10px', color: todayReconciliation === 0 ? '#10b981' : '#ef4444', fontWeight: 'bold', textAlign: 'right' }}>
                          {todayReconciliation > 0 ? '+' : ''}{todayReconciliation.toFixed(1)} L
                        </td>
                      </tr>
                      {/* Historical Daily Logs */}
                      {monthlyReconLogs.map((log, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                          <td style={{ padding: '10px', color: '#e2e8f0' }}>{log.date}</td>
                          <td style={{ padding: '10px', color: log.variance === 0 ? '#10b981' : '#ef4444', fontWeight: 'bold', textAlign: 'right' }}>
                            {log.variance > 0 ? '+' : ''}{log.variance.toFixed(1)} L
                          </td>
                        </tr>
                      ))}
                    </>
                  )}
                </tbody>
              </table>
            </div>

          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* UNIVERSAL DATA ENTRY MODAL */}
      {/* ------------------------------------------------------------- */}
      {activeModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', width: '380px', padding: '24px', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)' }}>
            <h3 style={{ margin: '0 0 16px 0', color: activeModal === 'Production' ? '#38bdf8' : activeModal === 'Domestic' ? '#f59e0b' : '#ec4899', fontSize: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>
                {activeModal === 'Production' && 'Enter Milk Production'}
                {activeModal === 'Domestic' && 'Enter Milk for Domestic Use'}
                {activeModal === 'Calves' && 'Enter Milk for Calves Feed'}
              </span>
              <button onClick={handleCloseEntry} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={18}/></button>
            </h3>
            
            <form onSubmit={handleSaveEntry} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              
              {activeModal === 'Production' && (
                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Select Source Animal</label>
                  <select value={selectedAnimal} onChange={e => setSelectedAnimal(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '6px', fontSize: '13px' }}>
                    <option value="BULK">Bulk / Whole Herd Entry</option>
                    {herdMasterList.map(a => (
                       <option key={a.id} value={a.id}>{a.id} ({a.breed})</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Amount (Liters)</label>
                <input 
                  type="number" 
                  step="0.1" 
                  min="0.1"
                  required
                  autoFocus
                  placeholder="e.g. 10.5"
                  value={inputValue} 
                  onChange={e => setInputValue(e.target.value)} 
                  style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '12px', borderRadius: '6px', fontSize: '16px', fontWeight: 'bold', boxSizing: 'border-box' }} 
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button type="button" onClick={handleCloseEntry} style={{ background: '#334155', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}>Cancel</button>
                <button type="submit" style={{ background: activeModal === 'Production' ? '#38bdf8' : activeModal === 'Domestic' ? '#f59e0b' : '#ec4899', color: '#0f172a', border: 'none', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Save size={14} /> Save Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
