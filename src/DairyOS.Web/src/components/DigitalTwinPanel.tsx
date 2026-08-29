import React, { useEffect, useState } from 'react';
import { BrainCircuit, Play, RefreshCw } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';
const field: React.CSSProperties = { width:'100%', boxSizing:'border-box', background:'#1e293b', color:'#fff', border:'1px solid #334155', borderRadius:5, padding:'7px 8px', fontSize:10 };
const panel: React.CSSProperties = { background:'#111827', border:'1px solid #1f2937', borderRadius:8, padding:12 };
const button: React.CSSProperties = { background:'#334155', color:'#fff', border:0, borderRadius:5, padding:'8px 10px', fontSize:10, fontWeight:800, cursor:'pointer', display:'inline-flex', alignItems:'center', gap:5 };

export default function DigitalTwinPanel(){
 const [metric,setMetric]=useState('MILK_LITERS'),[periodDays,setPeriodDays]=useState('30'),[horizonDays,setHorizonDays]=useState('30'),[growth,setGrowth]=useState('0'),[change,setChange]=useState('0'),[scenarioName,setScenarioName]=useState('Base Scenario'),[baseline,setBaseline]=useState<any>(null),[result,setResult]=useState<any>(null),[loading,setLoading]=useState(false),[error,setError]=useState('');
 const loadBaseline=async()=>{setError('');try{const response=await fetch(`${API_BASE}/farm/digital-twin/baseline?metric=${metric}&days=${Math.max(1,Number(periodDays)||30)}`);const data=await response.json();if(!response.ok)throw new Error(data.detail||'Digital Twin baseline unavailable.');setBaseline(data)}catch(exc){setBaseline(null);setError(exc instanceof Error?exc.message:'Digital Twin baseline unavailable.')}};
 useEffect(()=>{void loadBaseline()},[metric]);
 const runScenario=async()=>{setLoading(true);setError('');try{const response=await fetch(`${API_BASE}/farm/digital-twin/scenario`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({metric,scenario_name:scenarioName,parameter:metric,change_percent:Number(change),growth_rate_percent:Number(growth),horizon_days:Math.max(1,Number(horizonDays)||30),baseline_period_days:Math.max(1,Number(periodDays)||30)})});const data=await response.json();if(!response.ok)throw new Error(data.detail||'Digital Twin scenario failed.');setResult(data)}catch(exc){setResult(null);setError(exc instanceof Error?exc.message:'Digital Twin scenario failed.')}finally{setLoading(false)}};
 const twin=result?.digital_twin;
 const forecast=twin?.forecast_summary?.metric;
 const simulation=twin?.simulation_summary?.risk;
 return <section style={panel}>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:8,flexWrap:'wrap',marginBottom:9}}><div><div style={{fontSize:13,fontWeight:800,display:'flex',alignItems:'center',gap:6}}><BrainCircuit size={14} color="#a78bfa"/> Digital Twin — Scenario Lab</div><div style={{fontSize:9,color:'#64748b'}}>Forecasts and what-if scenarios over persisted farm baselines. Assumptions are explicit; forecasts never become farm facts.</div></div><button onClick={()=>void loadBaseline()} style={button}><RefreshCw size={12}/> Refresh Baseline</button></div>
  <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr 1fr 1fr',gap:6}}><label style={label}>Metric<select value={metric} onChange={e=>setMetric(e.target.value)} style={field}><option value="MILK_LITERS">Milk litres</option><option value="HERD_SIZE">Active herd size</option><option value="FEED_KG">Feed kg</option></select></label><label style={label}>Baseline Days<input type="number" min="1" max="3650" value={periodDays} onChange={e=>setPeriodDays(e.target.value)} style={field}/></label><label style={label}>Growth %<input type="number" step="0.1" value={growth} onChange={e=>setGrowth(e.target.value)} style={field}/></label><label style={label}>Scenario %<input type="number" step="0.1" value={change} onChange={e=>setChange(e.target.value)} style={field}/></label><label style={label}>Horizon Days<input type="number" min="1" max="3650" value={horizonDays} onChange={e=>setHorizonDays(e.target.value)} style={field}/></label></div>
  <div style={{display:'grid',gridTemplateColumns:'1fr auto',gap:6,marginTop:7}}><label style={label}>Scenario Name<input value={scenarioName} onChange={e=>setScenarioName(e.target.value)} style={field}/></label><button disabled={loading} onClick={()=>void runScenario()} style={{...button,background:'#7c3aed',alignSelf:'end'}}><Play size={12}/>{loading?'Running…':'Run Scenario'}</button></div>
  {error&&<div style={{marginTop:8,color:'#fecaca',background:'#450a0a',border:'1px solid #7f1d1d',padding:8,borderRadius:6,fontSize:10}}>{error}</div>}
  {baseline&&<div style={{marginTop:8,display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:7}}><div style={metricCard}><div style={eyebrow}>Live baseline</div><div style={value}>{Number(baseline.baseline_value).toLocaleString()}</div><div style={muted}>{baseline.metric} · {baseline.baseline_period_days} days</div></div><div style={metricCard}><div style={eyebrow}>Forecast</div><div style={value}>{forecast==null?'—':Number(forecast).toLocaleString()}</div><div style={muted}>{result?.horizon_days||horizonDays} day horizon</div></div><div style={metricCard}><div style={eyebrow}>Scenario risk</div><div style={{...value,color:'#fbbf24'}}>{simulation||'—'}</div><div style={muted}>{result?.scenario_name||scenarioName}</div></div></div>}
  {result&&<div style={{marginTop:8,fontSize:9,color:'#94a3b8'}}>Data status: {result.data_status}. Baseline evidence is preserved with the scenario; decision signal severity is derived from the explicit forecast change.</div>}
 </section>;
}
const label:React.CSSProperties={fontSize:8,color:'#94a3b8',textTransform:'uppercase',fontWeight:800,display:'block'};
const eyebrow:React.CSSProperties={fontSize:8,color:'#64748b',textTransform:'uppercase',fontWeight:800};
const value:React.CSSProperties={fontSize:17,fontWeight:900,color:'#a78bfa',marginTop:4};
const muted:React.CSSProperties={fontSize:9,color:'#94a3b8',marginTop:2};
const metricCard:React.CSSProperties={background:'#0f172a',border:'1px solid #1f2937',borderRadius:6,padding:9};
