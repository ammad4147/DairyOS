import React from 'react';
import { Activity, AlertTriangle, Database, Layers } from 'lucide-react';

export default function FeedTab() {
  return (
    <div style={{ padding: 20, color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ margin: '0 0 4px', fontSize: 20, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: 8 }}><Layers size={22} /> Feed &amp; Nutrition Operations</h2>
        <p style={{ margin: 0, fontSize: 12, color: '#94a3b8' }}>Operational feed monitoring. Monthly COML and TMR preparation are managed in the COML tab.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 16 }}>
        <div style={card('#34d399')}>
          <h3 style={title}><Database size={16} color="#34d399" /> Silage Bunker Status</h3>
          <div style={{ fontSize: 24, fontWeight: 900, color: '#34d399' }}>180 <span style={muted}>Tons Remaining</span></div>
          <div style={bar}><div style={{ width: '45%', height: '100%', background: '#34d399' }} /></div>
          <div style={smallMuted}>Est. depletion in 42 days at current feed rate.</div>
        </div>

        <div style={card('#f59e0b')}>
          <h3 style={title}><Database size={16} color="#f59e0b" /> Vanda / Concentrate Stock</h3>
          <div style={{ fontSize: 24, fontWeight: 900, color: '#f59e0b' }}>4,250 <span style={muted}>KG Remaining</span></div>
          <div style={bar}><div style={{ width: '25%', height: '100%', background: '#f87171' }} /></div>
          <div style={{ ...smallMuted, color: '#fca5a5', display: 'flex', alignItems: 'center', gap: 4 }}><AlertTriangle size={10} /> Low stock warning: Reorder soon.</div>
        </div>

        <div style={card('#38bdf8')}>
          <h3 style={title}><Activity size={16} color="#38bdf8" /> Daily Feed Distribution</h3>
          <div style={{ fontSize: 24, fontWeight: 900, color: '#38bdf8' }}>1,850 <span style={muted}>KG Fed Today</span></div>
          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 8, display: 'flex', justifyContent: 'space-between' }}><span>Target: 1,900 KG</span><span style={{ color: '#f87171' }}>-2.6%</span></div>
        </div>
      </div>
    </div>
  );
}

const title: React.CSSProperties = { margin: '0 0 12px', fontSize: 13, color: '#fff', display: 'flex', alignItems: 'center', gap: 6 };
const muted: React.CSSProperties = { fontSize: 12, color: '#94a3b8' };
const smallMuted: React.CSSProperties = { fontSize: 10, color: '#64748b', marginTop: 6 };
const bar: React.CSSProperties = { marginTop: 8, background: '#1e293b', height: 8, borderRadius: 4, overflow: 'hidden' };
const card = (accent: string): React.CSSProperties => ({ background: '#111827', border: '1px solid #1f2937', padding: 16, borderRadius: 8, borderLeft: `3px solid ${accent}` });
