import React, { useEffect, useState } from 'react';
import { BarChart3, AlertTriangle, ArrowRight, Activity, HeartPulse, Milk, DollarSign } from 'lucide-react';
import { ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

export default function Analytics({ onNavigate }: { onNavigate?: (view: string) => void }) {
  const [kpis, setKpis] = useState<any[]>([]);
  const [charts, setCharts] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/farm/analytics/integrated`)
      .then(r => r.json())
      .then(data => {
        setKpis(data.kpis || []);
        setCharts(data.charts || null);
      })
      .catch(() => { setKpis([]); setCharts(null); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: 20, color: '#64748b' }}>Loading decision intelligence...</div>;

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ marginBottom: '16px' }}>
        <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 size={20} /> Decision Intelligence Cockpit
        </h2>
        <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
          Every data point is actionable. Click any insight to jump to the relevant operational tab.
        </p>
      </div>

      {/* KPI Alert Panel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
        {kpis.map((kpi: any, i: number) => (
          <div 
            key={i} 
            style={{ 
              display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px',
              background: kpi.severity === 'critical' ? 'rgba(239,68,68,0.08)' : kpi.severity === 'warning' ? 'rgba(245,158,11,0.08)' : 'rgba(52,211,153,0.08)',
              border: `1px solid ${kpi.severity === 'critical' ? 'rgba(239,68,68,0.2)' : kpi.severity === 'warning' ? 'rgba(245,158,11,0.2)' : 'rgba(52,211,153,0.2)'}`,
              borderRadius: '8px'
            }}
          >
            {kpi.severity === 'critical' ? <AlertTriangle size={16} color="#ef4444" /> : 
             kpi.severity === 'warning' ? <AlertTriangle size={16} color="#f59e0b" /> : 
             <Activity size={16} color="#34d399" />}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#e2e8f0' }}>{kpi.title}</div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>{kpi.detail}</div>
            </div>
            {kpi.actionTab && onNavigate && (
              <button 
                onClick={() => onNavigate(kpi.actionTab)}
                style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}
              >
                {kpi.actionLabel} <ArrowRight size={12} />
              </button>
            )}
          </div>
        ))}
        {kpis.length === 0 && (
          <div style={{ padding: '12px', color: '#64748b', fontSize: 12, textAlign: 'center' }}>
            No active alerts. All systems operating within normal parameters.
          </div>
        )}
      </div>

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        
        {/* Lactation Curve */}
        <ChartCard title="Lactation Performance" icon={<Milk size={14} color="#38bdf8" />} color="#38bdf8">
          {charts?.lactation ? (
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={charts.lactation} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="dim" stroke="#64748b" tick={{ fontSize: 9 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                <Line type="monotone" dataKey="yield" name="Yield (L)" stroke="#38bdf8" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : <NoData />}
        </ChartCard>

        {/* Health Trend */}
        <ChartCard title="Clinical Events Trend" icon={<HeartPulse size={14} color="#ef4444" />} color="#ef4444">
          {charts?.health ? (
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={charts.health} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="period" stroke="#64748b" tick={{ fontSize: 9 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                <Bar dataKey="observations" name="Observations" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={20} />
                <Bar dataKey="treatments" name="Treatments" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={20} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : <NoData />}
        </ChartCard>

        {/* Conception Rate */}
        <ChartCard title="Reproductive Performance" icon={<Activity size={14} color="#f472b6" />} color="#f472b6">
          {charts?.breeding ? (
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={charts.breeding} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="period" stroke="#64748b" tick={{ fontSize: 9 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 9 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                <Line type="monotone" dataKey="conception_rate" name="Conception %" stroke="#f472b6" strokeWidth={2} dot={{ r: 3 }} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : <NoData />}
        </ChartCard>

        {/* Unit Economics */}
        <ChartCard title="Unit Economics Trend" icon={<DollarSign size={14} color="#fbbf24" />} color="#fbbf24">
          {charts?.financial ? (
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={charts.financial} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="period" stroke="#64748b" tick={{ fontSize: 9 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                <Line type="monotone" dataKey="coml" name="COML/L" stroke="#fbbf24" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="revenue" name="Revenue/L" stroke="#34d399" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : <NoData />}
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({ title, icon, color, children }: { title: string; icon: React.ReactNode; color: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#0f172a', border: `1px solid ${color}22`, borderRadius: '10px', padding: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color, fontWeight: 'bold', fontSize: '13px', marginBottom: '12px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
        {icon} {title}
      </div>
      {children}
    </div>
  );
}

function NoData() {
  return <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: 11 }}>No data available for this period.</div>;
}