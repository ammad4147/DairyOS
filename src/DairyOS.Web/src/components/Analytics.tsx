import React, { useState, useEffect, useCallback } from 'react';
import { BarChart3, TrendingUp, Skull, DollarSign, Activity, Settings2, CheckSquare, Square, X, Calendar, Wheat, HeartPulse, PieChart as PieChartIcon, Link, Edit3, AlertTriangle } from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, PieChart, Pie, Cell, Legend } from 'recharts';
import { fetchCommandDashboardData, type CommandDashboardData } from '../api/commandDashboardClient';

export default function Analytics() {
  const [dataMode, setDataMode] = useState<'AUTO' | 'MANUAL'>('AUTO');
  const [liveData, setLiveData] = useState<CommandDashboardData | null>(null);

  // --- 1. CONFIGURATION & STATE ---
  const [timeframe, setTimeframe] = useState<string>('30');
  const [showSettings, setShowSettings] = useState(false);

  const [visibleWidgets, setVisibleWidgets] = useState({
    FCE: true,
    REPRO: true,
    DEMOGRAPHICS: true,
    MORTALITY: true,
  });

  const [benchmarks, setBenchmarks] = useState({
    targetFCE: 1.50, 
    targetDaysOpen: 110, 
    targetMilkingPct: 82, 
  });

  // KPI States (Can be overwritten by live API or manual entry)
  const [currentAvgDaysOpen, setCurrentAvgDaysOpen] = useState<number>(124);
  const [currentConceptionRate, setCurrentConceptionRate] = useState<number>(42);
  const [milkingCowsCount, setMilkingCowsCount] = useState<number>(42);
  const [dryCowsCount, setDryCowsCount] = useState<number>(16);
  const [totalMortality, setTotalMortality] = useState<number>(3);
  const [totalHistoricalRegistered, setTotalHistoricalRegistered] = useState<number>(52);
  const [totalSold, setTotalSold] = useState<number>(6);
  const [totalCulled, setTotalCulled] = useState<number>(1);
  const [latestFCE, setLatestFCE] = useState<number>(1.49);

  const loadData = useCallback(async () => {
    try {
      const res = await fetchCommandDashboardData();
      setLiveData(res);
    } catch (err) {
      console.warn("Failed to load live data for Analytics", err);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Sync Logic
  useEffect(() => {
    if (dataMode === 'AUTO' && liveData) {
      // Sync Demographics
      const milking = liveData.herdComposition.find(c => c.name === 'Milking')?.value || 42;
      const dry = liveData.herdComposition.find(c => c.name === 'Dry')?.value || 16;
      setMilkingCowsCount(milking);
      setDryCowsCount(dry);
      
      // Auto-calculate FCE (Assuming roughly 22kg DMI per cow logic for demo)
      const calculatedFCE = liveData.todayLiters / (milking * 22);
      setLatestFCE(Number(calculatedFCE.toFixed(2)));

      // If API provided advanced repro/health, we'd sync here. (Using smart defaults if missing).
      setCurrentAvgDaysOpen(115); // Example improved sync value
      setCurrentConceptionRate(44);
    }
  }, [dataMode, liveData]);

  // Derived Calculations
  const totalAdults = milkingCowsCount + dryCowsCount;
  const currentMilkingPct = totalAdults > 0 ? ((milkingCowsCount / totalAdults) * 100).toFixed(1) : '0.0';
  const mortalityRatePct = totalHistoricalRegistered > 0 ? ((totalMortality / totalHistoricalRegistered) * 100).toFixed(1) : '0.0';
  const cullingRatePct = totalHistoricalRegistered > 0 ? (((totalSold + totalCulled) / totalHistoricalRegistered) * 100).toFixed(1) : '0.0';

  // --- 2. DATASETS FOR CHARTS ---
  const fceData = [
    { day: 'D1', fce: 1.42 }, { day: 'D5', fce: 1.45 }, 
    { day: 'D10', fce: 1.41 }, { day: 'D15', fce: 1.38 }, 
    { day: 'D20', fce: 1.44 }, { day: 'D25', fce: 1.47 }, 
    { day: 'Current', fce: latestFCE }
  ];

  const demoData = [
    { name: 'Milking Cows', value: milkingCowsCount, color: '#38bdf8' },
    { name: 'Dry Cows', value: dryCowsCount, color: '#94a3b8' },
  ];

  const monthlyMortalityTrend = [
    { month: 'Mar', deaths: 0, sales: 1 }, { month: 'Apr', deaths: 1, sales: 2 },
    { month: 'May', deaths: 0, sales: 0 }, { month: 'Jun', deaths: 1, sales: 1 },
    { month: 'Jul', deaths: 0, sales: 2 }, { month: 'Current', deaths: totalMortality, sales: totalSold },
  ];

  const handleWidgetToggle = (key: keyof typeof visibleWidgets) => setVisibleWidgets(prev => ({ ...prev, [key]: !prev[key] }));

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box', position: 'relative' }}>
      
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={22} /> Analytics, KPIs & Benchmarks
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Track biological efficiency against customizable performance targets.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          
          {/* DATA SOURCE TOGGLE */}
          <div style={{ display: 'flex', background: '#0f172a', border: '1px solid #1f2937', borderRadius: '6px', overflow: 'hidden' }}>
            <button 
              onClick={() => setDataMode('AUTO')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', background: dataMode === 'AUTO' ? 'rgba(52, 211, 153, 0.2)' : 'transparent', color: dataMode === 'AUTO' ? '#34d399' : '#64748b', border: 'none', padding: '6px 12px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
            >
              <Link size={14} /> Live Farm Sync
            </button>
            <button 
              onClick={() => setDataMode('MANUAL')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', background: dataMode === 'MANUAL' ? 'rgba(245, 158, 11, 0.2)' : 'transparent', color: dataMode === 'MANUAL' ? '#f59e0b' : '#64748b', border: 'none', borderLeft: '1px solid #1f2937', padding: '6px 12px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
            >
              <Edit3 size={14} /> Manual Override
            </button>
          </div>

          <button 
            onClick={() => setShowSettings(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#1e293b', color: '#38bdf8', border: '1px solid #38bdf8', padding: '8px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            <Settings2 size={16} /> Configure Targets & Data
          </button>
        </div>
      </div>

      {dataMode === 'MANUAL' && (
        <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', color: '#fbbf24', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <AlertTriangle size={16} /> <strong>Manual Override Active:</strong> Live data disconnected. Open "Configure Targets & Data" to override KPI inputs manually.
        </div>
      )}

      {/* DYNAMIC GRID LAYOUT */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        
        {/* WIDGET 1: FCE */}
        {visibleWidgets.FCE && (
          <div style={{ background: '#111827', border: `1px solid ${dataMode === 'AUTO' ? '#1f2937' : '#f59e0b'}`, padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '14px', color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Wheat size={16} /> Feed Conversion Efficiency (FCE) Trend
                </h3>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Liters of milk produced per 1kg of Dry Matter Intake</div>
              </div>
              <div style={{ background: '#0f172a', padding: '6px 10px', borderRadius: '6px', border: '1px solid #1e293b', textAlign: 'right' }}>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Target Benchmark</div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#34d399' }}>{benchmarks.targetFCE.toFixed(2)}</div>
              </div>
            </div>
            <div style={{ height: '200px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={fceData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155', fontSize: '12px', color: '#fff' }} />
                  <ReferenceLine y={benchmarks.targetFCE} stroke="#34d399" strokeDasharray="4 4" label={{ position: 'top', value: 'Target', fill: '#34d399', fontSize: 10 }} />
                  <Line type="monotone" dataKey="fce" stroke={dataMode === 'MANUAL' ? '#f59e0b' : '#38bdf8'} strokeWidth={3} dot={{ r: 4, fill: '#0f172a', stroke: dataMode === 'MANUAL' ? '#f59e0b' : '#38bdf8', strokeWidth: 2 }} name="Farm FCE" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* WIDGET 2: REPRO */}
        {visibleWidgets.REPRO && (
          <div style={{ background: '#111827', border: `1px solid ${dataMode === 'AUTO' ? '#1f2937' : '#f59e0b'}`, padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', color: '#fb923c', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={16} /> Reproductive Efficiency KPIs
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', flex: 1 }}>
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Avg Days Open</div>
                <div style={{ fontSize: '32px', fontWeight: 'bold', color: currentAvgDaysOpen <= benchmarks.targetDaysOpen ? '#34d399' : '#f87171' }}>
                  {currentAvgDaysOpen} <span style={{ fontSize: '14px', color: '#64748b' }}>days</span>
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px' }}>
                  Target: &lt; {benchmarks.targetDaysOpen} days
                </div>
              </div>

              <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>AI Conception Rate</div>
                <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#38bdf8' }}>
                  {currentConceptionRate}<span style={{ fontSize: '20px' }}>%</span>
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px' }}>Target Benchmark: &gt; 45%</div>
              </div>
            </div>
          </div>
        )}

        {/* WIDGET 3: DEMOGRAPHICS */}
        {visibleWidgets.DEMOGRAPHICS && (
          <div style={{ background: '#111827', border: `1px solid ${dataMode === 'AUTO' ? '#1f2937' : '#f59e0b'}`, padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '14px', color: '#a855f7', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <PieChartIcon size={16} /> Adult Herd Demographics
                </h3>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Milking vs. Dry ratio management</div>
              </div>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', height: '180px' }}>
              <div style={{ flex: 1, height: '100%', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={demoData} innerRadius={55} outerRadius={80} paddingAngle={2} dataKey="value" stroke="none">
                      {demoData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px', color: '#fff' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: '12px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>Current Milking %</div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: Number(currentMilkingPct) >= benchmarks.targetMilkingPct ? '#34d399' : '#f59e0b' }}>
                    {currentMilkingPct}%
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b' }}>Target: {benchmarks.targetMilkingPct}%</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* WIDGET 4: MORTALITY */}
        {visibleWidgets.MORTALITY && (
          <div style={{ background: '#111827', border: `1px solid ${dataMode === 'AUTO' ? '#1f2937' : '#f59e0b'}`, padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Skull size={16} /> Asset Depletion & Offtake
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
               <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Mortality Rate</div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f87171' }}>{mortalityRatePct}%</div>
               </div>
               <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Replacement Cull Rate</div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f59e0b' }}>{cullingRatePct}%</div>
               </div>
            </div>
            <div style={{ height: '120px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyMortalityTrend}>
                  <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 9 }} />
                  <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                  <Bar dataKey="sales" fill="#34d399" name="Sold" stackId="a" />
                  <Bar dataKey="deaths" fill="#ef4444" name="Mortality" stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* SETTINGS / OVERRIDE MODAL */}
      {showSettings && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '16px' }}>
          <div style={{ background: '#111827', border: '1px solid #374151', borderRadius: '12px', width: '100%', maxWidth: '700px', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)' }}>
            
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Settings2 size={18} color="#38bdf8" /> Configure Targets & Data
              </h3>
              <button onClick={() => setShowSettings(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '24px', overflowY: 'auto' }}>
              
              {/* Manual Override Fields (Only shown if mode is MANUAL) */}
              {dataMode === 'MANUAL' && (
                <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', padding: '16px', borderRadius: '8px' }}>
                  <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Edit3 size={14} /> Manual Data Override Input
                  </h4>
                  <p style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '12px' }}>Enter correct data below. This bypasses the farm sensors and automatic database extraction.</p>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ fontSize: '11px', color: '#94a3b8' }}>Latest FCE (Milk/DMI)</label>
                      <input type="number" step="0.01" value={latestFCE} onChange={e => setLatestFCE(Number(e.target.value))} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                    <div>
                      <label style={{ fontSize: '11px', color: '#94a3b8' }}>Avg Days Open</label>
                      <input type="number" value={currentAvgDaysOpen} onChange={e => setCurrentAvgDaysOpen(Number(e.target.value))} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                    <div>
                      <label style={{ fontSize: '11px', color: '#94a3b8' }}>Milking Cows Count</label>
                      <input type="number" value={milkingCowsCount} onChange={e => setMilkingCowsCount(Number(e.target.value))} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                    <div>
                      <label style={{ fontSize: '11px', color: '#94a3b8' }}>Dry Cows Count</label>
                      <input type="number" value={dryCowsCount} onChange={e => setDryCowsCount(Number(e.target.value))} style={{ width: '100%', background: '#0f172a', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                    </div>
                  </div>
                </div>
              )}

              {/* Benchmark Overrides */}
              <div>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#cbd5e1' }}>Farm Benchmark Targets (Local Overrides)</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0f172a', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                    <div>
                      <div style={{ fontSize: '12px', color: '#fff', fontWeight: 'bold' }}>Target FCE</div>
                    </div>
                    <input type="number" step="0.01" value={benchmarks.targetFCE} onChange={e => setBenchmarks({ ...benchmarks, targetFCE: Number(e.target.value) })} style={{ width: '80px', background: '#1e293b', color: '#34d399', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', textAlign: 'center' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0f172a', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                    <div>
                      <div style={{ fontSize: '12px', color: '#fff', fontWeight: 'bold' }}>Target Max Days Open</div>
                    </div>
                    <input type="number" value={benchmarks.targetDaysOpen} onChange={e => setBenchmarks({ ...benchmarks, targetDaysOpen: Number(e.target.value) })} style={{ width: '80px', background: '#1e293b', color: '#fb923c', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', textAlign: 'center' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0f172a', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                    <div>
                      <div style={{ fontSize: '12px', color: '#fff', fontWeight: 'bold' }}>Target % of Herd in Milk</div>
                    </div>
                    <input type="number" value={benchmarks.targetMilkingPct} onChange={e => setBenchmarks({ ...benchmarks, targetMilkingPct: Number(e.target.value) })} style={{ width: '80px', background: '#1e293b', color: '#a855f7', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', textAlign: 'center' }} />
                  </div>
                </div>
              </div>

              {/* Widget Visibility Toggles */}
              <div>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#cbd5e1' }}>Visible Dashboard Modules</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  {Object.entries(visibleWidgets).map(([key, isVisible]) => (
                    <div key={key} onClick={() => handleWidgetToggle(key as keyof typeof visibleWidgets)} style={{ display: 'flex', alignItems: 'center', gap: '10px', background: isVisible ? 'rgba(56, 189, 248, 0.1)' : '#0f172a', border: `1px solid ${isVisible ? '#38bdf8' : '#334155'}`, padding: '10px 14px', borderRadius: '6px', cursor: 'pointer' }}>
                      {isVisible ? <CheckSquare size={16} color="#38bdf8" /> : <Square size={16} color="#64748b" />}
                      <span style={{ fontSize: '12px', color: isVisible ? '#fff' : '#94a3b8', fontWeight: isVisible ? 'bold' : 'normal' }}>
                        {key === 'FCE' && 'Feed Conversion Efficiency'}
                        {key === 'REPRO' && 'Reproductive Efficiency'}
                        {key === 'DEMOGRAPHICS' && 'Herd Demographics'}
                        {key === 'MORTALITY' && 'Depletion & Mortality'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            <div style={{ padding: '16px 20px', borderTop: '1px solid #1f2937', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowSettings(false)} style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 20px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
                Save & Apply Configuration
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
