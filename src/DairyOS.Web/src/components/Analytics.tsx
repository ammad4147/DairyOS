import React, { useState } from 'react';
import {
  BarChart3, TrendingUp, Activity, PieChart, ShieldCheck,
  AlertTriangle, DollarSign, Milk, Calendar, Award
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart as RePieChart, Pie, Cell, LineChart, Line
} from 'recharts';

export default function Analytics() {
  const [timeRange, setTimeRange] = useState<'30D' | '90D' | '1Y'>('30D');

  // Performance Data Series
  const lactationCurve = [
    { dim: '0-30', avgYield: 24.5, target: 26.0 },
    { dim: '31-60', avgYield: 34.2, target: 35.0 },
    { dim: '61-90', avgYield: 38.6, target: 38.0 },
    { dim: '91-120', avgYield: 35.1, target: 34.0 },
    { dim: '121-180', avgYield: 29.8, target: 30.0 },
    { dim: '181-240', avgYield: 24.2, target: 25.0 },
    { dim: '241-305', avgYield: 18.5, target: 19.0 },
  ];

  const cmplBreakdown = [
    { name: 'Feed & Silage', value: 27.5, color: '#38bdf8' },
    { name: 'Labor & Management', value: 6.8, color: '#34d399' },
    { name: 'Power & Solar', value: 4.2, color: '#f59e0b' },
    { name: 'Vet & Reproduction', value: 3.1, color: '#ec4899' },
    { name: 'Overheads & Bedding', value: 2.15, color: '#a78bfa' },
  ];

  const reproductionFunnel = [
    { metric: 'Eligible Herd', count: 8 },
    { metric: 'Heat Detected', count: 7 },
    { metric: 'Inseminated', count: 7 },
    { metric: 'Confirmed Pregnant', count: 5 },
  ];

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>

      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={20} /> Advanced Farm Analytics & Executive KPIs
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Decision intelligence synthesizing herd biology, CMPL cost dynamics, and reproductive efficiency.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '4px', background: '#111827', padding: '3px', borderRadius: '6px', border: '1px solid #1f2937' }}>
          {(['30D', '90D', '1Y'] as const).map(period => (
            <button
              key={period}
              onClick={() => setTimeRange(period)}
              style={{
                background: timeRange === period ? '#38bdf8' : 'transparent',
                color: timeRange === period ? '#0f172a' : '#94a3b8',
                border: 'none',
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              {period === '30D' ? 'Last 30 Days' : period === '90D' ? 'Quarterly' : 'Annual'}
            </button>
          ))}
        </div>
      </div>

      {/* 4 STRATEGIC KPI PILLARS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Feed Conversion Ratio (FCR)</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#38bdf8' }}>1.42 kg/kg</div>
          <div style={{ fontSize: '10px', color: '#34d399' }}>+4.5% vs Punjab benchmark</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Feed Cost % of Revenue</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>52.4%</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Target &lt; 55% Healthy margin</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Pregnancy Rate (21d Cycle)</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fb923c' }}>24.8%</div>
          <div style={{ fontSize: '10px', color: '#fb923c' }}>Heat detection rate: 87.5%</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a78bfa' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Average Days in Milk (DIM)</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#a78bfa' }}>164 Days</div>
          <div style={{ fontSize: '10px', color: '#34d399' }}>Optimal herd peak zone</div>
        </div>

      </div>

      {/* 2x2 ANALYTICS GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: '14px', marginBottom: '14px' }}>

        {/* 1. Lactation Curve vs Standard Target */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '14px' }}>
          <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
            <span>📈 Lactation Curve (Yield by Days in Milk)</span>
            <span style={{ fontSize: '10px', color: '#94a3b8' }}>Litres / Cow / Day</span>
          </div>
          <div style={{ height: '180px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lactationCurve} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="dim" stroke="#64748b" tick={{ fontSize: 9 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 9 }} domain={[10, 45]} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '10px' }} />
                <Line type="monotone" dataKey="avgYield" name="Actual Herd Average" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="target" name="Target Curve" stroke="#34d399" strokeWidth={2} strokeDasharray="4 4" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', fontSize: '10px', marginTop: '6px' }}>
            <span style={{ color: '#38bdf8' }}>● Actual Herd Yield</span>
            <span style={{ color: '#34d399' }}>- - Benchmark Target (Purebred Holstein)</span>
          </div>
        </div>

        {/* 2. CMPL Unit Cost Breakdown (PKR 43.75 total) */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '14px' }}>
          <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
            <span>🥧 CMPL Cost Composition (PKR 43.75 / Liter)</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', alignItems: 'center' }}>
            <div style={{ height: '170px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RePieChart>
                  <Pie data={cmplBreakdown} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={65} paddingAngle={4}>
                    {cmplBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '10px' }} formatter={(val: any) => `PKR ${val}/L`} />
                </RePieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '10px' }}>
              {cmplBreakdown.map(item => (
                <div key={item.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#cbd5e1' }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: item.color }} />
                    {item.name}
                  </span>
                  <span style={{ fontWeight: 'bold', color: '#fff' }}>PKR {item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* 3. Biological Reproduction Funnel & Clinical Risk Monitor */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>

        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '14px' }}>
          <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#fb923c', marginBottom: '10px' }}>
            🧬 Reproduction & Pregnancy Conversion Funnel
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {reproductionFunnel.map((step, i) => (
              <div key={step.metric} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '130px', fontSize: '11px', color: '#94a3b8' }}>{step.metric}</span>
                <div style={{ flex: 1, background: '#1e293b', borderRadius: '4px', height: '18px', overflow: 'hidden' }}>
                  <div style={{ width: `${(step.count / 8) * 100}%`, background: i === 3 ? '#a78bfa' : '#fb923c', height: '100%', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', paddingRight: '6px', fontSize: '10px', fontWeight: 'bold', color: '#0f172a' }}>
                    {step.count}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '14px' }}>
          <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8', marginBottom: '10px' }}>
            🛡️ Udder Health & Milk Quality Index
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ background: '#161f30', padding: '10px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
              <div style={{ fontSize: '10px', color: '#94a3b8' }}>Bulk Tank SCC</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#34d399' }}>185,000 / mL</div>
              <div style={{ fontSize: '9px', color: '#64748b' }}>Grade-A Milk Standard</div>
            </div>
            <div style={{ background: '#161f30', padding: '10px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
              <div style={{ fontSize: '10px', color: '#94a3b8' }}>Average Butterfat</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#38bdf8' }}>3.85%</div>
              <div style={{ fontSize: '9px', color: '#64748b' }}>Protein: 3.25%</div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
