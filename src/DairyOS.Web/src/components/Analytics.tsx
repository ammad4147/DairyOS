import { TrendingUp, BarChart3 } from 'lucide-react';

export default function AnalyticsTab() {
  return (
    <div style={{ padding: '16px', color: '#f8fafc', height: 'calc(100vh - 120px)', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '12px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}><BarChart3 size={20}/> Dairy Farm Analytics & KPIs</h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>Standard dairy productivity indicators and herd performance metrics computed from live records.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Average Daily Yield / Cow</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#38bdf8' }}>24.5 L</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Conception Rate (30D)</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#34d399' }}>68.0%</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Herd Health Index</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fcd34d' }}>98.2%</div>
        </div>
      </div>
    </div>
  );
}
