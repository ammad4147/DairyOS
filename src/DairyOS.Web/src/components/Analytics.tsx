import React, { useEffect, useMemo, useState } from 'react';
import {
  Milk, Activity, HeartPulse, DollarSign, Database,
  Layers, Sliders, AlertTriangle, Search, ThermometerSun,
  Snowflake, CloudRain
} from 'lucide-react';
import {
  ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Legend, CartesianGrid
} from 'recharts';
import { API_BASE_URL } from '../config/api';

type AnalyticsTabId = 'milk' | 'breeding' | 'health' | 'financial' | 'dynamics';

type LiveAnalytics = {
  status: string;
  data_status: 'LIVE_PERSISTED_DATA' | 'NO_DATA';
  synthetic_values: boolean;
  frontend_calculation_authority: boolean;
  period: { start: string; end: string; days: number };
  milk_environment: { period: string; thi: number; yield: number }[];
  health: { period: string; observations: number; treatments: number }[];
  breeding: { period: string; inseminations: number; pregnancy_checks: number; confirmed_pregnancies: number; conception_rate_percent: number | null }[];
  financial: { feed_cost_per_litre: number | null; opex_cost_per_litre: number | null; cost_of_milk_production_per_litre: number | null; feed_cost: number; opex: number; data_status: string };
  herd_dynamics: { active_herd: number; lifecycle_counts: Record<string, number> };
  heat_stress: { observations: { period: string; thi: number }[]; data_status: string };
  coverage: Record<string, number>;
};

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

export default function Analytics() {
  const [selectedTabs, setSelectedTabs] = useState<AnalyticsTabId[]>(['milk']);
  const [isCompareMode, setIsCompareMode] = useState<boolean>(false);
  const [data, setData] = useState<LiveAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [milkMetric, setMilkMetric] = useState<'YIELD' | 'BUTTERFAT'>('YIELD');
  const [milkDimension, setMilkDimension] = useState<'DIM' | 'THI' | 'MONTH'>('THI');
  const [milkCohort, setMilkCohort] = useState<'ALL' | 'HF' | 'CROSS'>('ALL');
  const [breedMetric, setBreedMetric] = useState<'CONCEPTION_RATE' | 'PREG_RATE'>('CONCEPTION_RATE');
  const [breedDimension, setBreedDimension] = useState<'MONTH' | 'SIRE_TYPE' | 'THI'>('MONTH');
  const [healthMetric, setHealthMetric] = useState<'MORTALITY' | 'MASTITIS'>('MORTALITY');
  const [healthDimension, setHealthDimension] = useState<'CALVING_SEASON' | 'PARITY'>('CALVING_SEASON');

  const load = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/farm/analytics-live?days=30`);
      if (!response.ok) throw new Error(`Live analytics request failed: ${response.status}`);
      setData(await response.json() as LiveAnalytics);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const milkData = useMemo(() => (data?.milk_environment ?? []).map((row, index) => ({
    period: row.period,
    thi: row.thi,
    dim: index + 1,
    yield_total: row.yield,
  })), [data]);

  const healthData = useMemo(() => data?.health ?? [], [data]);
  const breedingData = useMemo(() => data?.breeding ?? [], [data]);
  const currentHerd = data?.herd_dynamics.active_herd ?? 0;
  const feedPerL = data?.financial.feed_cost_per_litre;
  const opexPerL = data?.financial.opex_cost_per_litre;
  const comlPerL = data?.financial.cost_of_milk_production_per_litre;
  const hasThiSeries = milkData.length > 0;

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
          <button style={{ background: '#111827', border: '1px solid #1f2937', color: '#34d399', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }} title="Manual analytics input is not connected to a persisted contract">
            <AlertTriangle size={12} /> Log Manual Event (Silage / Weather)
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

        {/* 1. MILK ANALYTICS PANE */}
        {selectedTabs.includes('milk') && (
          <div style={{ background: '#0f172a', border: '1px solid #38bdf844', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38bdf8', fontWeight: 'bold', fontSize: '14px' }}>
                <Milk size={16} /> Production vs. Environment Analyzer
              </div>
            </div>

            <div style={{ background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}><Search size={12}/> BUILD QUERY</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Y-Axis (Metric)</label>
                  <select value={milkMetric} onChange={e => setMilkMetric(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="YIELD">Daily Yield (L)</option>
                    <option value="BUTTERFAT" disabled>Butterfat % (no live composition contract)</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>X-Axis (Dimension)</label>
                  <select value={milkDimension} onChange={e => setMilkDimension(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="THI">Heat Stress (THI)</option>
                    <option value="MONTH">Calendar Date</option>
                    <option value="DIM">Observation Sequence</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Filter (Cohort)</label>
                  <select value={milkCohort} onChange={e => setMilkCohort(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}>
                    <option value="ALL">All governed animals</option>
                    <option value="HF" disabled>Holstein only (not exposed by live contract)</option>
                    <option value="CROSS" disabled>Crossbred only (not exposed by live contract)</option>
                  </select>
                </div>
              </div>
            </div>

            <div style={{ height: '220px', background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              {loading ? <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 11 }}>Loading live milk analytics…</div> : milkData.length === 0 ? <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 11 }}>No complete milk/environment observations are available for this period.</div> : <ResponsiveContainer width="100%" height="100%"><ComposedChart data={milkData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} /><XAxis dataKey={milkDimension === 'THI' ? 'thi' : (milkDimension === 'DIM' ? 'dim' : 'period')} stroke="#64748b" tick={{ fontSize: 9 }} /><YAxis allowDecimals={false} yAxisId="left" stroke="#64748b" tick={{ fontSize: 9 }} domain={['auto', 'auto']} /><Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} /><Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />{milkMetric === 'YIELD' ? <Line yAxisId="left" type="monotone" dataKey="yield_total" name="Farm Daily Yield (L)" stroke="#38bdf8" strokeWidth={3} dot={{ r: 4 }} /> : <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" fill="#64748b" fontSize="11">No live composition analytics contract</text>}</ComposedChart></ResponsiveContainer>}
            </div>

            <div style={{ background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', padding: '10px', borderRadius: '6px', display: 'flex', gap: '8px' }}>
              <ThermometerSun size={18} color="#38bdf8" style={{ flexShrink: 0 }} />
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                <strong style={{ color: '#38bdf8' }}>Engine Insight:</strong>
                {hasThiSeries ? ' Live complete milk days are joined only where persisted THI observations exist. No unsupported seasonal benchmark is inferred.' : ' No persisted THI observations overlap complete milk days in this period; no heat-stress correlation is asserted.'}
              </div>
            </div>
          </div>
        )}

        {/* 2. HEALTH & SURVIVAL PANE */}
        {selectedTabs.includes('health') && (
          <div style={{ background: '#0f172a', border: '1px solid #f8717144', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: 'bold', fontSize: '14px' }}><HeartPulse size={16} /> Clinical Health & Mortality Etiology</div>
            </div>
            <div style={{ background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}><Search size={12}/> BUILD QUERY</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div><label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Y-Axis (Clinical Metric)</label><select value={healthMetric} onChange={e => setHealthMetric(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}><option value="MORTALITY">Health Observations</option><option value="MASTITIS">Treatments</option></select></div>
                <div><label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>X-Axis (Risk Dimension)</label><select value={healthDimension} onChange={e => setHealthDimension(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}><option value="CALVING_SEASON">Calendar Date</option><option value="PARITY" disabled>Parity (no live contract)</option></select></div>
              </div>
            </div>
            <div style={{ height: '220px', background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
              {loading ? <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 11 }}>Loading live health analytics…</div> : healthData.length === 0 ? <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 11 }}>No persisted health/treatment observations in this period.</div> : <ResponsiveContainer width="100%" height="100%"><ComposedChart data={healthData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} /><XAxis dataKey="period" stroke="#64748b" tick={{ fontSize: 9 }} /><YAxis allowDecimals={false} yAxisId="left" stroke="#64748b" tick={{ fontSize: 9 }} /><Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} /><Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />{healthMetric === 'MORTALITY' ? <Bar yAxisId="left" dataKey="observations" name="Health Observations" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={40} /> : <Bar yAxisId="left" dataKey="treatments" name="Treatments" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={40} />}</ComposedChart></ResponsiveContainer>}
            </div>
            <div style={{ background: 'rgba(248, 113, 113, 0.1)', border: '1px solid rgba(248, 113, 113, 0.3)', padding: '10px', borderRadius: '6px', display: 'flex', gap: '8px' }}><CloudRain size={18} color="#f87171" style={{ flexShrink: 0 }}/><div style={{ fontSize: '11px', color: '#cbd5e1' }}><strong style={{ color: '#f87171' }}>Engine Insight:</strong> {healthData.length ? 'Only persisted health observations and treatments are displayed. No mortality, mastitis or seasonal causal rates are invented.' : 'No persisted health evidence is available for causal analytics in this period.'}</div></div>
          </div>
        )}

        {/* 3. BREEDING ANALYTICS PANE */}
        {selectedTabs.includes('breeding') && (
          <div style={{ background: '#0f172a', border: '1px solid #f472b644', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}><div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f472b6', fontWeight: 'bold', fontSize: '14px' }}><Activity size={16} /> Reproductive Economics & Fertility Trends</div></div>
            <div style={{ background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}><div style={{ fontSize: '10px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}><Search size={12}/> BUILD QUERY</div><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}><div><label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Y-Axis (Metric)</label><select value={breedMetric} onChange={e => setBreedMetric(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}><option value="CONCEPTION_RATE">Conception %</option><option value="PREG_RATE">Confirmed Pregnancies</option></select></div><div><label style={{ fontSize: '9px', color: '#64748b', display: 'block', marginBottom: '2px' }}>X-Axis (Environment)</label><select value={breedDimension} onChange={e => setBreedDimension(e.target.value as any)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '11px' }}><option value="MONTH">Calendar Month</option><option value="THI" disabled>THI on Day of Insemination (not joined)</option><option value="SIRE_TYPE" disabled>Sire Type (not exposed)</option></select></div></div></div>
            <div style={{ height: '220px', background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>{loading ? <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 11 }}>Loading live breeding analytics…</div> : breedingData.length === 0 ? <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 11 }}>No persisted reproductive events in this period.</div> : <ResponsiveContainer width="100%" height="100%"><ComposedChart data={breedingData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} /><XAxis dataKey="period" stroke="#64748b" tick={{ fontSize: 9 }} /><YAxis allowDecimals={false} yAxisId="left" stroke="#64748b" tick={{ fontSize: 9 }} domain={[0, 100]}/><Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} /><Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />{breedMetric === 'CONCEPTION_RATE' ? <Line yAxisId="left" type="monotone" dataKey="conception_rate_percent" name="Conception %" stroke="#ec4899" strokeWidth={3} dot={{ r: 4 }} /> : <Bar yAxisId="left" dataKey="confirmed_pregnancies" name="Confirmed Pregnancies" fill="#f472b6" radius={[4, 4, 0, 0]} barSize={40} />}</ComposedChart></ResponsiveContainer>}</div>
            <div style={{ background: 'rgba(244, 114, 182, 0.1)', border: '1px solid rgba(244, 114, 182, 0.3)', padding: '10px', borderRadius: '6px', display: 'flex', gap: '8px' }}><Snowflake size={18} color="#f472b6" style={{ flexShrink: 0 }}/><div style={{ fontSize: '11px', color: '#cbd5e1' }}><strong style={{ color: '#f472b6' }}>Engine Insight:</strong> {breedingData.length ? 'Only persisted breeding events with explicit chronology are included. Unsupported environmental or semen-type effects are not inferred.' : 'No persisted reproductive evidence is available in this period.'}</div></div>
          </div>
        )}

        {/* Placeholder tiles for remaining tabs to maintain the unified view */}
        {selectedTabs.includes('financial') && (
           <div style={{ background: '#0f172a', border: '1px solid #fbbf2444', borderRadius: '10px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px' }}>
             <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: '12px' }}>
               <DollarSign size={32} color="#fbbf24" style={{ margin: '0 auto 8px' }} />
               {comlPerL != null ? <>Feed Cost/L: PKR {Number(feedPerL || 0).toFixed(2)}<br/>OPEX/L: PKR {Number(opexPerL || 0).toFixed(2)}<br/>CMPL/L: PKR {Number(comlPerL).toFixed(2)}</> : 'No persisted financial + milk evidence is available for live unit economics.'}
             </div>
           </div>
        )}

        {selectedTabs.includes('dynamics') && (
           <div style={{ background: '#0f172a', border: '1px solid #22d3ee44', borderRadius: '10px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px' }}>
             <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: '12px' }}>
               <Database size={32} color="#22d3ee" style={{ margin: '0 auto 8px' }} />
               Active persisted herd: {currentHerd}<br/>
               {Object.entries(data?.herd_dynamics.lifecycle_counts || {}).map(([key, value]) => <React.Fragment key={key}>{key}: {value}<br/></React.Fragment>)}
             </div>
           </div>
        )}

      </div>
    </div>
  );
}