import React, { useState } from 'react';
import { 
  Milk, Activity, HeartPulse, DollarSign, Database, 
  Layers, Sliders, AlertTriangle, TrendingUp, Calendar, 
  Plus, Search, ThermometerSun, Snowflake, CloudRain
} from 'lucide-react';
import { 
  ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  Legend, CartesianGrid, Area, Scatter
} from 'recharts';

type AnalyticsTabId = 'milk' | 'breeding' | 'health' | 'financial' | 'dynamics';

export default function Analytics() {
  const [selectedTabs, setSelectedTabs] = useState<AnalyticsTabId[]>(['milk']);
  const [isCompareMode, setIsCompareMode] = useState<boolean>(false);

  // --- QUERY BUILDER STATES ---
  
  // 1. Milk Analytics State
  const [milkMetric, setMilkMetric] = useState<'YIELD' | 'BUTTERFAT'>('YIELD');
  const [milkDimension, setMilkDimension] = useState<'DIM' | 'THI' | 'MONTH'>('THI');
  const [milkCohort, setMilkCohort] = useState<'ALL' | 'HF' | 'CROSS'>('ALL');

  // 2. Breeding Analytics State
  const [breedMetric, setBreedMetric] = useState<'CONCEPTION_RATE' | 'PREG_RATE'>('CONCEPTION_RATE');
  const [breedDimension, setBreedDimension] = useState<'MONTH' | 'SIRE_TYPE' | 'THI'>('MONTH');

  // 3. Health Analytics State
  const [healthMetric, setHealthMetric] = useState<'MORTALITY' | 'MASTITIS'>('MORTALITY');
  const [healthDimension, setHealthDimension] = useState<'CALVING_SEASON' | 'PARITY'>('CALVING_SEASON');

  // --- CORRELATION DATASETS (Realistic Punjab Climate Models) ---

  // Milk vs THI & Season
  const milkData = [
    { period: 'Jan (Winter)', thi: 62, dim: 45, yield_HF: 36.5, yield_Cross: 28.0, fat: 4.2 },
    { period: 'Mar (Spring)', thi: 68, dim: 90, yield_HF: 38.0, yield_Cross: 29.5, fat: 4.0 },
    { period: 'May (Dry Summer)', thi: 78, dim: 150, yield_HF: 31.0, yield_Cross: 27.5, fat: 3.6 },
    { period: 'Jul (Monsoon)', thi: 85, dim: 210, yield_HF: 22.5, yield_Cross: 25.0, fat: 3.2 },
    { period: 'Sep (Humid)', thi: 82, dim: 260, yield_HF: 24.0, yield_Cross: 24.5, fat: 3.4 },
    { period: 'Nov (Cooling)', thi: 65, dim: 300, yield_HF: 29.5, yield_Cross: 26.0, fat: 4.0 },
  ];

  // Health vs Season (Calving Survivability)
  const healthData = [
    { season: 'Winter Calving', mortality: 2.1, mastitisIncidence: 4.5, bcsDrop: 0.5 },
    { season: 'Spring Calving', mortality: 3.0, mastitisIncidence: 5.2, bcsDrop: 0.6 },
    { season: 'Summer Calving', mortality: 8.5, mastitisIncidence: 8.0, bcsDrop: 1.2 },
    { season: 'Monsoon Calving', mortality: 6.2, mastitisIncidence: 14.5, bcsDrop: 0.9 },
  ];

  // Breeding vs Environment
  const breedingData = [
    { month: 'Jan', thi: 62, conception_Conventional: 45, conception_Sexed: 42, pregRate: 26 },
    { month: 'Apr', thi: 72, conception_Conventional: 38, conception_Sexed: 35, pregRate: 21 },
    { month: 'Jul', thi: 85, conception_Conventional: 18, conception_Sexed: 12, pregRate: 9 },
    { month: 'Oct', thi: 75, conception_Conventional: 35, conception_Sexed: 31, pregRate: 19 },
  ];

  const tabsMeta: { id: AnalyticsTabId; label: string; icon: React.ReactNode; color: string }[] = [
    { id: 'milk', label: 'Milk & Environment', icon: <Milk size={14} />, color: '#38bdf8' },
    { id: 'breeding', label: 'Reproduction ROI', icon: <Activity size={14} />, color: '#f472b6' },
    { id: 'health', label: 'Health & Survival', icon: <HeartPulse size={14} />, color: '#f87171' },
    { id: 'financial', label: 'Unit Economics', icon: <DollarSign size={14} />, color: '#fbbf24' },
    { id: 'dynamics', label: 'Herd Dynamics', icon: <Database size={14} />, color: '#22d3ee' },
  ];

  const handleTabClick = (tabId: AnalyticsTabId) => {
    if (isCompareMode) {
      if (selectedTabs.includes(tabId)) {
        if (selectedTabs.length > 1) setSelectedTabs(selectedTabs.filter(id => id !== tabId));
      } else {
        setSelectedTabs([...selectedTabs, tabId]);
      }
    } else {
      setSelectedTabs([tabId]);
    }
  };

  const getGridLayout = () => {
    const count = selectedTabs.length;
    if (count === 1) return '1fr';
    if (count === 2) return '1fr 1fr';
    if (count === 3) return '1fr 1fr 1fr';
    if (count === 4) return '1fr 1fr';
    return 'repeat(auto-fit, minmax(450px, 1fr))';
  };

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      
      {/* HEADER & GLOBAL CONTROLS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={20} /> Multivariate Analytics Query Engine
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Cross-correlate environmental factors, manual interventions, and biological performance.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button style={{ background: '#111827', border: '1px solid #1f2937', color: '#34d399', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <Plus size={12} /> Log Manual Event (Silage / Weather)
          </button>
          <button 
            onClick={() => {
              setIsCompareMode(!isCompareMode);
              if (isCompareMode && selectedTabs.length > 1) setSelectedTabs([selectedTabs[0]]);
            }}
            style={{
              background: isCompareMode ? '#0284c7' : '#111827',
              color: '#fff',
              border: `1px solid ${isCompareMode ? '#38bdf8' : '#1f2937'}`,
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 'bold',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Sliders size={13} /> {isCompareMode ? 'Comparison Mode: ON' : 'Enable Compare Mode'}
          </button>
        </div>
      </div>

      {/* TOP DOMAIN TABS */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {tabsMeta.map(tab => {
          const isSelected = selectedTabs.includes(tab.id);
          return (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              style={{
                background: isSelected ? tab.color + '22' : '#111827',
                color: isSelected ? tab.color : '#94a3b8',
                border: `1px solid ${isSelected ? tab.color : '#1f2937'}`,
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s ease'
              }}
            >
              <span style={{ color: tab.color }}>{tab.icon}</span>
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* DYNAMIC SCREEN GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: getGridLayout(), gap: '16px', alignItems: 'start' }}>

        {/* ============================================================== */}
        {/* 1. MILK ANALYTICS PANE (Multivariate) */}
        {/* ============================================================== */}
        {selectedTabs.includes('milk') && (
          <div style={{ background: '#0f172a', border: '1px solid #38bdf844', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38bdf8', fontWeight: 'bold', fontSize: '14px' }}>
                <Milk size={16} /> Production vs. Environment Analyzer
              </div>
            </div>

            {/* QUERY BUILDER CONTROLS */}
            <div style={{ background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}><Search size={12}/> BUILD QUERY</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Y-Axis (Metric)</label>
                  <select value={milkMetric} onChange={e => setMilkMetric(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="YIELD">Avg Daily Yield (L)</option>
                    <option value="BUTTERFAT">Butterfat %</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>X-Axis (Dimension)</label>
                  <select value={milkDimension} onChange={e => setMilkDimension(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="THI">Heat Stress (THI)</option>
                    <option value="MONTH">Calendar Month</option>
                    <option value="DIM">Days in Milk (DIM)</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Filter (Cohort)</label>
                  <select value={milkCohort} onChange={e => setMilkCohort(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="ALL">Compare Breeds</option>
                    <option value="HF">Holstein Only</option>
                    <option value="CROSS">Crossbreds Only</option>
                  </select>
                </div>
              </div>
            </div>

            {/* DYNAMIC CHART */}
            <div style={{ height: '220px', background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={milkData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey={milkDimension === 'THI' ? 'thi' : (milkDimension === 'DIM' ? 'dim' : 'period')} stroke="#64748b" tick={{ fontSize: 9 }} />
                  <YAxis allowDecimals={false} yAxisId="left" stroke="#64748b" tick={{ fontSize: 9 }} domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                  <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
                  
                  {milkMetric === 'YIELD' && (milkCohort === 'ALL' || milkCohort === 'HF') && (
                    <Line yAxisId="left" type="monotone" dataKey="yield_HF" name="Holstein Yield (L)" stroke="#38bdf8" strokeWidth={3} dot={{ r: 4 }} />
                  )}
                  {milkMetric === 'YIELD' && (milkCohort === 'ALL' || milkCohort === 'CROSS') && (
                    <Line yAxisId="left" type="monotone" dataKey="yield_Cross" name="Crossbred Yield (L)" stroke="#34d399" strokeWidth={3} dot={{ r: 4 }} />
                  )}
                  {milkMetric === 'BUTTERFAT' && (
                    <Area yAxisId="left" type="monotone" dataKey="fat" name="Butterfat %" fill="rgba(251, 191, 36, 0.2)" stroke="#fbbf24" strokeWidth={2} />
                  )}
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* ANALYTICS INSIGHT GENERATOR */}
            <div style={{ background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', padding: '10px', borderRadius: '6px', display: 'flex', gap: '8px' }}>
              <ThermometerSun size={18} color="#38bdf8" style={{ flexShrink: 0 }} />
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                <strong style={{ color: '#38bdf8' }}>Engine Insight:</strong> 
                {milkMetric === 'YIELD' && milkDimension === 'THI' 
                  ? " Holstein yields drop by 38% when THI exceeds 78, whereas Crossbred yields only drop by 10%. Heat abatement ROI is highest for purebred pens."
                  : " Butterfat depression strongly correlates with summer months, indicating potential sub-acute ruminal acidosis (SARA) from feed sorting during heat stress."}
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* 2. HEALTH & SURVIVAL PANE (Mortality Correlation) */}
        {/* ============================================================== */}
        {selectedTabs.includes('health') && (
          <div style={{ background: '#0f172a', border: '1px solid #f8717144', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: 'bold', fontSize: '14px' }}>
                <HeartPulse size={16} /> Clinical Health & Mortality Etiology
              </div>
            </div>

            {/* QUERY BUILDER */}
            <div style={{ background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}><Search size={12}/> BUILD QUERY</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Y-Axis (Clinical Metric)</label>
                  <select value={healthMetric} onChange={e => setHealthMetric(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="MORTALITY">Calf Mortality %</option>
                    <option value="MASTITIS">Clinical Mastitis Incidence %</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>X-Axis (Risk Dimension)</label>
                  <select value={healthDimension} onChange={e => setHealthDimension(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="CALVING_SEASON">Calving Season / Weather</option>
                    <option value="PARITY">Parity (Lactation #)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* DYNAMIC CHART */}
            <div style={{ height: '220px', background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={healthData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="season" stroke="#64748b" tick={{ fontSize: 9 }} />
                  <YAxis allowDecimals={false} yAxisId="left" stroke="#64748b" tick={{ fontSize: 9 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                  <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
                  
                  {healthMetric === 'MORTALITY' && (
                    <Bar yAxisId="left" dataKey="mortality" name="Calf Mortality Rate %" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={40} />
                  )}
                  {healthMetric === 'MASTITIS' && (
                    <Bar yAxisId="left" dataKey="mastitisIncidence" name="Mastitis Cases / 100 Cows" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={40} />
                  )}
                  {/* Secondary Correlation Line */}
                  <Line yAxisId="left" type="monotone" dataKey="bcsDrop" name="Avg BCS Drop Post-Calving" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* ANALYTICS INSIGHT GENERATOR */}
            <div style={{ background: 'rgba(248, 113, 113, 0.1)', border: '1px solid rgba(248, 113, 113, 0.3)', padding: '10px', borderRadius: '6px', display: 'flex', gap: '8px' }}>
              {healthMetric === 'MORTALITY' ? <ThermometerSun size={18} color="#f87171" style={{ flexShrink: 0 }}/> : <CloudRain size={18} color="#f87171" style={{ flexShrink: 0 }}/>}
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                <strong style={{ color: '#f87171' }}>Engine Insight:</strong> 
                {healthMetric === 'MORTALITY' 
                  ? " Calves born in Summer (June-Aug) suffer 4x higher mortality (8.5%) than Winter births (2.1%). Postpone inseminations to avoid summer calvings."
                  : " Mastitis incidence spikes dramatically (14.5%) during Monsoon calvings. High humidity severely degrades sand bedding hygiene."}
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* 3. BREEDING ANALYTICS PANE (Reproductive ROI) */}
        {/* ============================================================== */}
        {selectedTabs.includes('breeding') && (
          <div style={{ background: '#0f172a', border: '1px solid #f472b644', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f472b6', fontWeight: 'bold', fontSize: '14px' }}>
                <Activity size={16} /> Reproductive Economics & Fertility Trends
              </div>
            </div>

            {/* QUERY BUILDER */}
            <div style={{ background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}><Search size={12}/> BUILD QUERY</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Y-Axis (Metric)</label>
                  <select value={breedMetric} onChange={e => setBreedMetric(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="CONCEPTION_RATE">First Service Conception %</option>
                    <option value="PREG_RATE">21-Day Pregnancy Rate</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>X-Axis (Environment)</label>
                  <select value={breedDimension} onChange={e => setBreedDimension(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="MONTH">Calendar Month / Season</option>
                    <option value="THI">THI on Day of Insemination</option>
                  </select>
                </div>
              </div>
            </div>

            {/* DYNAMIC CHART */}
            <div style={{ height: '220px', background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={breedingData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey={breedDimension === 'THI' ? 'thi' : 'month'} stroke="#64748b" tick={{ fontSize: 9 }} />
                  <YAxis allowDecimals={false} yAxisId="left" stroke="#64748b" tick={{ fontSize: 9 }} domain={[0, 60]}/>
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                  <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
                  
                  {breedMetric === 'CONCEPTION_RATE' && (
                    <>
                      <Line yAxisId="left" type="monotone" dataKey="conception_Conventional" name="Conventional Semen %" stroke="#60a5fa" strokeWidth={3} dot={{ r: 4 }} />
                      <Line yAxisId="left" type="monotone" dataKey="conception_Sexed" name="Sexed Semen (Expensive) %" stroke="#ec4899" strokeWidth={3} dot={{ r: 4 }} strokeDasharray="4 4" />
                    </>
                  )}
                  {breedMetric === 'PREG_RATE' && (
                    <Bar yAxisId="left" dataKey="pregRate" name="Overall 21-Day PR %" fill="#f472b6" radius={[4, 4, 0, 0]} barSize={40} />
                  )}
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* ANALYTICS INSIGHT GENERATOR */}
            <div style={{ background: 'rgba(244, 114, 182, 0.1)', border: '1px solid rgba(244, 114, 182, 0.3)', padding: '10px', borderRadius: '6px', display: 'flex', gap: '8px' }}>
              <Snowflake size={18} color="#f472b6" style={{ flexShrink: 0 }}/>
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                <strong style={{ color: '#f472b6' }}>Engine Insight:</strong> 
                {breedMetric === 'CONCEPTION_RATE' 
                  ? " Sexed Semen conception plummets to 12% in July. Suspend use of expensive sexed straws from June to August to prevent severe financial waste."
                  : " Pregnancy rate crashes in summer due to both poor conception AND poor heat expression (HDR). Consider timed AI (Ovsynch) during hot months."}
              </div>
            </div>
          </div>
        )}

        {/* Placeholder tiles for remaining tabs to maintain the unified view */}
        {selectedTabs.includes('financial') && (
           <div style={{ background: '#0f172a', border: '1px solid #fbbf2444', borderRadius: '10px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px' }}>
             <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: '12px' }}>
               <DollarSign size={32} color="#fbbf24" style={{ margin: '0 auto 8px' }} />
               Financial Multivariate Engine Active.<br/>Select 'Compare' to build cross-domain unit economics queries.
             </div>
           </div>
        )}

        {selectedTabs.includes('dynamics') && (
           <div style={{ background: '#0f172a', border: '1px solid #22d3ee44', borderRadius: '10px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px' }}>
             <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: '12px' }}>
               <Database size={32} color="#22d3ee" style={{ margin: '0 auto 8px' }} />
               Herd Dynamics Engine Active.<br/>Query Parity Survival and Culling trends based on local environment variables.
             </div>
           </div>
        )}

      </div>
    </div>
  );
}

