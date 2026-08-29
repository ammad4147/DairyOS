import React, { useEffect, useState } from 'react';
import { DollarSign, Thermometer, Wind, AlertTriangle, RefreshCw } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

type Props = { defaultDays?: number; defaultMilkPrice?: number };
type IntelligenceResponse = { data_status?: string; values?: { milk_litres?: number; feed_kg?: number; cost_per_litre?: number|null }; financial?: { feed_cost_per_litre?: number|null; opex_cost_per_litre?: number|null; cost_of_milk_production_per_litre?: number|null }; milk_environment?: { period:string; thi:number; yield:number }[] };
type MofcResponse = { data_status?:string; milk_price_per_litre?:number; period_days?:number; milk_litres?:number; feed_cost?:number; milk_revenue?:number; margin_over_feed_cost?:number; margin_per_litre?:number; quality?:string };

export default function FarmIntelligenceWidget({ defaultDays = 30, defaultMilkPrice = 225 }: Props) {
  const [days, setDays] = useState(String(defaultDays));
  const [milkPrice, setMilkPrice] = useState(String(defaultMilkPrice));
  const [analytics, setAnalytics] = useState<IntelligenceResponse | null>(null);
  const [mofc, setMofc] = useState<MofcResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try {
      const period = Math.max(1, Math.min(366, Number(days) || defaultDays));
      const price = Number(milkPrice);
      if (!(price > 0)) throw new Error('Milk price must be greater than zero.');
      const [analyticsResponse, mofcResponse] = await Promise.all([
        fetch(`${API_BASE}/farm/analytics-live?days=${period}`),
        fetch(`${API_BASE}/farm/finance/mofc?milk_price_per_litre=${encodeURIComponent(price)}&days=${period}`),
      ]);
      const [analyticsBody, mofcBody] = await Promise.all([analyticsResponse.json(), mofcResponse.json()]);
      if (!analyticsResponse.ok) throw new Error(analyticsBody.detail || 'Live analytics unavailable.');
      if (!mofcResponse.ok) throw new Error(mofcBody.detail || 'Margin-over-feed-cost service unavailable.');
      setAnalytics(analyticsBody); setMofc(mofcBody);
    } catch (exc) {
      setAnalytics(null); setMofc(null); setError(exc instanceof Error ? exc.message : 'Unable to load farm intelligence.');
    } finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, []);

  const latestThi = analytics?.milk_environment?.length ? analytics.milk_environment[analytics.milk_environment.length - 1].thi : null;
  const heatStressLevel = latestThi == null ? 'No live THI' : latestThi < 68 ? 'Normal' : latestThi < 72 ? 'Mild Stress' : latestThi < 80 ? 'High Stress' : 'Severe Stress';
  const heatStressMessage = latestThi == null ? 'No persisted THI observation is available for the selected period.' : latestThi >= 80 ? 'Review cooling, water access, shade and holding-pen exposure immediately.' : latestThi >= 72 ? 'Review cooling and water availability for the affected period.' : latestThi >= 68 ? 'Monitor intake, respiration and shed ventilation.' : 'No elevated heat-stress signal from persisted THI data.';

  return <section style={{ background:'#111827', border:'1px solid #1f2937', borderRadius:8, padding:14, color:'#fff' }}>
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', gap:8, flexWrap:'wrap', marginBottom:10 }}>
      <div><div style={{ fontSize:13, fontWeight:800, display:'flex', alignItems:'center', gap:6 }}><DollarSign size={14} color="#34d399"/> Farm Intelligence</div><div style={{ fontSize:9, color:'#64748b' }}>Backend-derived margin and heat-stress intelligence. Inputs are explicit assumptions; persisted farm facts remain authoritative.</div></div>
      <div style={{ display:'flex', alignItems:'center', gap:6 }}><input type="number" min="1" max="366" value={days} onChange={e=>setDays(e.target.value)} style={smallInput} title="Calculation period in days"/><input type="number" min="0.01" step="0.01" value={milkPrice} onChange={e=>setMilkPrice(e.target.value)} style={smallInput} title="Milk price assumption PKR/L"/><button onClick={()=>void load()} style={button}><RefreshCw size={12}/> Refresh</button></div>
    </div>
    {error&&<div style={{ background:'#450a0a', border:'1px solid #7f1d1d', color:'#fecaca', padding:8, borderRadius:6, fontSize:10, marginBottom:9 }}>{error}</div>}
    {loading ? <div style={{ color:'#64748b', fontSize:10 }}>Loading backend intelligence…</div> : <div style={{ display:'grid', gridTemplateColumns:'repeat(3,minmax(0,1fr))', gap:8 }}>
      <div style={card}><div style={eyebrow}>Margin over feed cost</div><div style={metric}>{mofc?.margin_over_feed_cost != null ? `PKR ${Number(mofc.margin_over_feed_cost).toLocaleString('en-PK',{maximumFractionDigits:2})}` : '—'}</div><div style={muted}>{mofc?.period_days ?? days} day period · milk price assumption PKR {Number(milkPrice).toLocaleString('en-PK')}</div></div>
      <div style={card}><div style={eyebrow}>Feed / litre</div><div style={metric}>{analytics?.financial?.feed_cost_per_litre != null ? `PKR ${Number(analytics.financial.feed_cost_per_litre).toFixed(2)}` : '—'}</div><div style={muted}>Derived from persisted financial and milk evidence.</div></div>
      <div style={card}><div style={eyebrow}>Cost of milk / litre</div><div style={metric}>{analytics?.financial?.cost_of_milk_production_per_litre != null ? `PKR ${Number(analytics.financial.cost_of_milk_production_per_litre).toFixed(2)}` : '—'}</div><div style={muted}>Backend unit-economics result.</div></div>
    </div>}
    <div style={{ marginTop:8, ...card, display:'flex', alignItems:'center', gap:9 }}><Thermometer size={18} color="#38bdf8"/><div style={{ flex:1 }}><div style={eyebrow}>Persisted thermal comfort</div><div style={{ fontSize:14, fontWeight:900 }}>{latestThi == null ? '—' : `THI ${Number(latestThi).toFixed(0)} — ${heatStressLevel}`}</div><div style={muted}>{heatStressMessage}</div></div><Wind size={16} color="#38bdf8"/></div>
    <div style={{ marginTop:8, fontSize:9, color:'#94a3b8', display:'flex', alignItems:'center', gap:5 }}><AlertTriangle size={11} color="#f59e0b"/> No hardcoded production, feed cost, temperature or humidity facts are used by this widget.</div>
  </section>;
}

const card:React.CSSProperties={background:'#0f172a',border:'1px solid #1f2937',borderRadius:6,padding:10};
const eyebrow:React.CSSProperties={fontSize:8,color:'#64748b',textTransform:'uppercase',fontWeight:800};
const metric:React.CSSProperties={fontSize:18,fontWeight:900,color:'#34d399',marginTop:4};
const muted:React.CSSProperties={fontSize:9,color:'#94a3b8',marginTop:3};
const smallInput:React.CSSProperties={width:110,boxSizing:'border-box',background:'#1e293b',color:'#fff',border:'1px solid #334155',borderRadius:5,padding:'6px 7px',fontSize:10};
const button:React.CSSProperties={background:'#1e293b',color:'#cbd5e1',border:'1px solid #334155',borderRadius:5,padding:'7px 9px',fontSize:10,fontWeight:800,cursor:'pointer',display:'inline-flex',alignItems:'center',gap:5};
