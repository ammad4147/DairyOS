import { useEffect, useState } from "react";
import { apiUrl } from "../config/api";

export default function AnalyticsTab() {
  const [kpis, setKpis] = useState<any>(null);
  useEffect(() => {
    fetch(apiUrl("/farm/kpis?days=30")).then(r => r.json()).then(d => { if(d.kpis) setKpis(d.kpis); }).catch(()=>null);
  }, []);

  if(!kpis) return <div style={{ padding: '20px', color: '#94a3b8' }}>Loading actual metrics from backend...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ fontSize: '14px', color: '#64748b', textTransform: 'uppercase', marginBottom: '16px' }}>Standard 30-Day KPIs</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Avg Milk / Animal / Day</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', marginTop: '8px' }}>{kpis.average_milk_liters_per_animal_day || '--'} L</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Peak Daily Yield</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#38bdf8', marginTop: '8px' }}>{kpis.peak_daily_milk_liters || '--'} L</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Conception Rate</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#a78bfa', marginTop: '8px' }}>{kpis.conception_rate_percent ? `${kpis.conception_rate_percent}%` : '--'}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Treatment Rate</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fca5a5', marginTop: '8px' }}>{kpis.treatment_rate_percent ? `${kpis.treatment_rate_percent}%` : '--'}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Feed Conversion</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fcd34d', marginTop: '8px' }}>{kpis.feed_kg_per_liter_milk || '--'} kg/L</div>
        </div>
      </div>
    </div>
  );
}
