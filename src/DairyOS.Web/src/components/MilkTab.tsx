import React, { useEffect, useMemo, useState } from 'react';
import { Check, Edit3, Milk, RefreshCw, Save, Trash2, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000';
type HerdAnimal = { id: string; breed: string; category: string; frequency?: string };
type ProductionRow = { id:number; animal_id:string; production_date:string; milking_session?:string|null; session_ledger:boolean; morning_yield?:number|null; afternoon_yield?:number|null; evening_yield?:number|null; total_yield?:number|null; status:string; notes?:string|null };
type DispositionRow = { id:number; production_date:string; disposition_type:string; quantity_litres:number; sale_id?:string|null; counterparty?:string|null; selling_price_per_litre?:number|null; amount_due:number; amount_received:number; receivable_outstanding:number; notes?:string|null; status:string };
type Reconciliation = { production_date:string; production_complete:boolean; produced_litres:number|null; accounted_litres:number; sold_litres:number; non_sale_accounted_litres:number; unaccounted_litres:number|null; over_accounted_litres:number|null; sale_value:number; cash_received:number; receivable_outstanding:number; status:string };
type NextSession = { animal_id:string; milking_frequency?:string; expected_sessions:string[]; settled_sessions:string[]; next_session:string|null; status:string };
type QualitySample = { id:number; quality_date:string; fat_pct:number; snf_pct:number; sample_type:string; notes?:string|null; recorded_by:string; status:string; recorded_at:string; updated_at:string };
type FinanceTransaction = { id:number; transaction_type:string; category?:string|null; amount:number; quantity?:number|null; unit?:string|null; unit_rate?:number|null; date?:string|null; reference?:string|null; counterparty?:string|null; status?:string|null; notes?:string|null };
type Props = { initialOpenModal?:boolean; onModalClose?:()=>void; herdMasterList?:HerdAnimal[]; onSaveYield?:(addedLiters:number)=>void; realTimeTodaySold?:number };
type DailySummary = { date:string; produced:number; sold:number; domestic:number; calves:number; wastage:number; reconciliation:number };
type DetailMode = 'MONTH_PRODUCED'|'MONTH_SOLD'|'MONTH_RECON'|'DAY_PRODUCED'|'DAY_SOLD'|'DAY_DOMESTIC'|'DAY_CALVES'|'DAY_WASTAGE'|'DAY_RECON';

const inputStyle:React.CSSProperties={background:'#1e293b',color:'#fff',border:'1px solid #334155',padding:'7px 8px',borderRadius:5,fontSize:11,boxSizing:'border-box',width:'100%'};
const smallButton:React.CSSProperties={background:'#1e293b',border:'1px solid #334155',color:'#cbd5e1',padding:'5px 8px',borderRadius:4,fontSize:9,cursor:'pointer',display:'inline-flex',alignItems:'center',gap:4};
const actionButton=(background:string):React.CSSProperties=>({background,color:'#fff',border:'1px solid transparent',padding:'7px 10px',borderRadius:5,fontSize:9,fontWeight:800,cursor:'pointer',display:'inline-flex',alignItems:'center',gap:4});
const today=()=>new Date().toISOString().slice(0,10);
const monthRange=(value:string)=>{const d=new Date(`${value}T00:00:00`);const start=new Date(d.getFullYear(),d.getMonth(),1);const end=new Date(d.getFullYear(),d.getMonth()+1,0);const iso=(x:Date)=>x.toISOString().slice(0,10);return {start:iso(start),end:iso(end),label:d.toLocaleDateString('en-PK',{month:'long',year:'numeric'})};};
const litre=(value:number|null|undefined)=>`${Number(value||0).toLocaleString('en-PK',{minimumFractionDigits:1,maximumFractionDigits:1})} L`;
const signedLitre=(value:number)=>`${value>=0?'+':''}${litre(value)}`;
const money=(value:number)=>`PKR ${Number(value||0).toLocaleString('en-PK',{maximumFractionDigits:0})}`;

async function request<T>(url:string,init?:RequestInit):Promise<T>{
  const response=await fetch(`${API_BASE}${url}`,{headers:{'Content-Type':'application/json'},...init});
  if(!response.ok){let detail=`Request failed: ${response.status}`;try{const body=await response.json() as {detail?:unknown};if(body.detail)detail=typeof body.detail==='string'?body.detail:JSON.stringify(body.detail);}catch{}throw new Error(detail);}
  return response.json() as Promise<T>;
}

function Card({label,value,sub,onClick,accent,children}:{label:string;value:string;sub?:string;onClick:()=>void;accent:string;children?:React.ReactNode}){
  return <div role="button" tabIndex={0} onClick={onClick} onKeyDown={e=>{if(e.key==='Enter'||e.key===' ')onClick();}} style={{background:'#111827',border:'1px solid #263244',borderLeft:`4px solid ${accent}`,borderRadius:8,padding:'10px 12px',cursor:'pointer',minWidth:0,boxSizing:'border-box'}}>
    <div style={{fontSize:9,color:'#94a3b8',textTransform:'uppercase',fontWeight:800,letterSpacing:'.25px'}}>{label}</div>
    <div style={{fontSize:18,fontWeight:850,color:'#fff',marginTop:4,lineHeight:1.1}}>{value}</div>
    {sub&&<div style={{fontSize:9,color:'#64748b',marginTop:4}}>{sub}</div>}
    {children}
  </div>;
}

export default function MilkTab({initialOpenModal=false,onModalClose,herdMasterList=[],onSaveYield}:Props){
  const [selectedDate,setSelectedDate]=useState(today());
  const [monthRows,setMonthRows]=useState<DailySummary[]>([]);
  const [dayProduction,setDayProduction]=useState<ProductionRow[]>([]);
  const [dayDispositions,setDayDispositions]=useState<DispositionRow[]>([]);
  const [financeSales,setFinanceSales]=useState<FinanceTransaction[]>([]);
  const [reconciliation,setReconciliation]=useState<Reconciliation|null>(null);
  const [qualitySample,setQualitySample]=useState<QualitySample|null>(null);
  const [productionAnimal,setProductionAnimal]=useState(herdMasterList[0]?.id||'');
  const [nextSession,setNextSession]=useState<NextSession|null>(null);
  const [productionSession,setProductionSession]=useState('');
  const [productionLitres,setProductionLitres]=useState('');
  const [productionNotes,setProductionNotes]=useState('');
  const [dispositionType,setDispositionType]=useState('DOMESTIC_USE');
  const [dispositionLitres,setDispositionLitres]=useState('');
  const [dispositionNotes,setDispositionNotes]=useState('');
  const [showProductionForm,setShowProductionForm]=useState(initialOpenModal);
  const [showDispositionForm,setShowDispositionForm]=useState(false);
  const [editingProduction,setEditingProduction]=useState<ProductionRow|null>(null);
  const [editingDisposition,setEditingDisposition]=useState<DispositionRow|null>(null);
  const [detailMode,setDetailMode]=useState<DetailMode>('DAY_PRODUCED');
  const [qualityFat,setQualityFat]=useState('');
  const [qualitySnf,setQualitySnf]=useState('');
  const [qualityType,setQualityType]=useState('BULK_TANK');
  const [qualityNotes,setQualityNotes]=useState('');
  const [loading,setLoading]=useState(true);
  const [saving,setSaving]=useState(false);
  const [qualitySaving,setQualitySaving]=useState(false);
  const [error,setError]=useState('');
  const [message,setMessage]=useState('');

  const load=async()=>{
    setLoading(true);setError('');
    try{
      const month=monthRange(selectedDate);
      const [monthLedger,dayLedger,dayRecon,quality,finance] = await Promise.all([
        request<{production:ProductionRow[];dispositions:DispositionRow[]}>(`/farm/milk/ledger?start_date=${month.start}&end_date=${month.end}`),
        request<{production:ProductionRow[];dispositions:DispositionRow[]}>(`/farm/milk/ledger?start_date=${selectedDate}&end_date=${selectedDate}`),
        request<Reconciliation>(`/farm/milk/reconciliation?production_date=${selectedDate}`),
        request<{sample:QualitySample|null}>(`/farm/milk/quality?quality_date=${selectedDate}`),
        request<{transactions:FinanceTransaction[]}>(`/farm/finance-ledger`),
      ]);
      setDayProduction(dayLedger.production||[]);
      setDayDispositions(dayLedger.dispositions||[]);
      setReconciliation(dayRecon);
      setQualitySample(quality.sample||null);
      if(quality.sample){setQualityFat(String(quality.sample.fat_pct));setQualitySnf(String(quality.sample.snf_pct));setQualityType(quality.sample.sample_type);setQualityNotes(quality.sample.notes||'');}
      else{setQualityFat('');setQualitySnf('');setQualityType('BULK_TANK');setQualityNotes('');}
      const sales=(finance.transactions||[]).filter(t=>t.status!=='VOID' && ['INCOME','RECEIPT'].includes(String(t.transaction_type||'').toUpperCase()) && (String(t.category||'').toUpperCase()==='MILK_SALES' || String(t.reference||'').toUpperCase().includes('MILK')));
      setFinanceSales(sales);
      const byDate=new Map<string,DailySummary>();
      const ensure=(date:string)=>{if(!byDate.has(date))byDate.set(date,{date,produced:0,sold:0,domestic:0,calves:0,wastage:0,reconciliation:0});return byDate.get(date)!;};
      for(const row of monthLedger.production||[]){const d=ensure(row.production_date.slice(0,10));d.produced+=Number(row.total_yield||0);}
      for(const row of monthLedger.dispositions||[]){const d=ensure(row.production_date.slice(0,10));const qty=Number(row.quantity_litres||0);const type=String(row.disposition_type||'').toUpperCase();if(type==='SOLD')d.sold+=qty;else if(type.includes('DOMESTIC'))d.domestic+=qty;else if(type.includes('CALF'))d.calves+=qty;else if(type.includes('WAST'))d.wastage+=qty;}
      for(const d of byDate.values())d.reconciliation=d.produced-d.sold-d.domestic-d.calves-d.wastage;
      setMonthRows([...byDate.values()].sort((a,b)=>b.date.localeCompare(a.date)));
    }catch(err){setError(err instanceof Error?err.message:'Unable to load Milk data.');}
    finally{setLoading(false);}
  };

  useEffect(()=>{void load();},[selectedDate]);
  useEffect(()=>{if(!productionAnimal&&herdMasterList[0])setProductionAnimal(herdMasterList[0].id);},[herdMasterList,productionAnimal]);
  useEffect(()=>{if(!productionAnimal)return;void request<NextSession>(`/farm/milk/next-session?animal_id=${encodeURIComponent(productionAnimal)}&operational_date=${selectedDate}`).then(v=>{setNextSession(v);setProductionSession(v.next_session||v.expected_sessions[0]||'');}).catch(()=>setNextSession(null));},[productionAnimal,selectedDate]);

  const daily=useMemo(()=>{
    const produced=dayProduction.reduce((s,r)=>s+Number(r.total_yield||0),0);
    const sold=dayDispositions.filter(r=>String(r.disposition_type).toUpperCase()==='SOLD').reduce((s,r)=>s+Number(r.quantity_litres||0),0);
    const domestic=dayDispositions.filter(r=>String(r.disposition_type).toUpperCase().includes('DOMESTIC')).reduce((s,r)=>s+Number(r.quantity_litres||0),0);
    const calves=dayDispositions.filter(r=>String(r.disposition_type).toUpperCase().includes('CALF')).reduce((s,r)=>s+Number(r.quantity_litres||0),0);
    const wastage=dayDispositions.filter(r=>String(r.disposition_type).toUpperCase().includes('WAST')).reduce((s,r)=>s+Number(r.quantity_litres||0),0);
    return {produced,sold,domestic,calves,wastage,reconciliation:produced-sold-domestic-calves-wastage};
  },[dayProduction,dayDispositions]);

  const monthTotals=useMemo(()=>monthRows.reduce((a,d)=>({produced:a.produced+d.produced,sold:a.sold+d.sold,domestic:a.domestic+d.domestic,calves:a.calves+d.calves,wastage:a.wastage+d.wastage,reconciliation:a.reconciliation+d.reconciliation}),{produced:0,sold:0,domestic:0,calves:0,wastage:0,reconciliation:0}),[monthRows]);

  const financeSoldRows=useMemo(()=>financeSales.filter(t=>(t.date||'').slice(0,10)===selectedDate),[financeSales,selectedDate]);
  const financeSoldQty=useMemo(()=>financeSoldRows.reduce((s,t)=>s+Number(t.quantity||0),0),[financeSoldRows]);
  const displayedSold=financeSoldQty>0?financeSoldQty:daily.sold;

  const resetProduction=()=>{setProductionLitres('');setProductionNotes('');setEditingProduction(null);setShowProductionForm(false);onModalClose?.();};
  const resetDisposition=()=>{setDispositionLitres('');setDispositionNotes('');setEditingDisposition(null);setShowDispositionForm(false);};

  const saveProduction=async(e:React.FormEvent)=>{e.preventDefault();setSaving(true);setError('');try{const litres=Number(productionLitres);if(litres<=0)throw new Error('Milk litres must be greater than zero.');if(!productionAnimal||!productionSession)throw new Error('Animal and expected milking session are required.');if(editingProduction){await request(`/farm/milk/production/${editingProduction.id}`,{method:'PATCH',body:JSON.stringify({production_date:selectedDate,morning_yield:productionSession==='MORNING'?litres:editingProduction.morning_yield,afternoon_yield:productionSession==='AFTERNOON'?litres:editingProduction.afternoon_yield,evening_yield:productionSession==='EVENING'?litres:editingProduction.evening_yield,notes:productionNotes})});setMessage('Milk production record updated.');}else{await request('/farm/milk',{method:'POST',body:JSON.stringify({animal_id:productionAnimal,milking_session:productionSession,morning_yield:productionSession==='MORNING'?litres:null,afternoon_yield:productionSession==='AFTERNOON'?litres:null,evening_yield:productionSession==='EVENING'?litres:null,production_date:selectedDate,notes:productionNotes,operator:'WEB'})});if(onSaveYield&&selectedDate===today())onSaveYield(litres);setMessage('Milk production recorded.');}resetProduction();await load();}catch(err){setError(err instanceof Error?err.message:'Milk production save failed.');}finally{setSaving(false);}};

  const saveDisposition=async(e:React.FormEvent)=>{e.preventDefault();setSaving(true);setError('');try{const litres=Number(dispositionLitres);if(litres<=0)throw new Error('Milk litres must be greater than zero.');if(editingDisposition){await request(`/farm/milk/dispositions/${editingDisposition.id}`,{method:'PATCH',body:JSON.stringify({production_date:selectedDate,quantity_litres:litres,notes:dispositionNotes})});setMessage('Milk usage record updated.');}else{await request('/farm/milk/dispositions',{method:'POST',body:JSON.stringify({production_date:selectedDate,disposition_type:dispositionType,quantity_litres:litres,sale_id:null,counterparty:null,selling_price_per_litre:null,notes:dispositionNotes||null})});setMessage(dispositionType==='DOMESTIC_USE'?'Domestic milk use recorded.':dispositionType==='CALF_FEED'?'Calf milk feeding recorded.':'Milk wastage/unusable quantity recorded.');}resetDisposition();await load();}catch(err){setError(err instanceof Error?err.message:'Milk usage save failed.');}finally{setSaving(false);}};

  const saveQuality=async(e:React.FormEvent)=>{e.preventDefault();setQualitySaving(true);setError('');try{const fat=Number(qualityFat),snf=Number(qualitySnf);if(!(fat>0)||!(snf>0))throw new Error('Fat % and SNF % must be greater than zero.');await request('/farm/milk/quality',{method:'POST',body:JSON.stringify({quality_date:selectedDate,fat_pct:fat,snf_pct:snf,sample_type:qualityType,notes:qualityNotes||null,recorded_by:'UI Operator'})});setMessage('Milk quality sample saved.');await load();}catch(err){setError(err instanceof Error?err.message:'Milk quality save failed.');}finally{setQualitySaving(false);}};

  const editProduction=(row:ProductionRow)=>{setEditingProduction(row);setProductionAnimal(row.animal_id);setProductionSession(row.milking_session||'MORNING');setProductionLitres(String(row.morning_yield??row.afternoon_yield??row.evening_yield??''));setProductionNotes(row.notes||'');setShowProductionForm(true);};
  const editDisposition=(row:DispositionRow)=>{setEditingDisposition(row);setDispositionType(row.disposition_type);setDispositionLitres(String(row.quantity_litres));setDispositionNotes(row.notes||'');setShowDispositionForm(true);};
  const voidProduction=async(row:ProductionRow)=>{if(!window.confirm(`Void milk production record ${row.id}? This remains in the audit ledger.`))return;try{await request(`/farm/milk/production/${row.id}/void`,{method:'POST',body:JSON.stringify({reason:'Operator void from Milk register'})});setMessage('Milk production record voided.');await load();}catch(err){setError(err instanceof Error?err.message:'Unable to void production.');}};
  const voidDisposition=async(row:DispositionRow)=>{if(!window.confirm(`Void milk usage record ${row.id}? This remains in the audit ledger.`))return;try{await request(`/farm/milk/dispositions/${row.id}/void`,{method:'POST',body:JSON.stringify({reason:'Operator void from Milk register'})});setMessage('Milk usage record voided.');await load();}catch(err){setError(err instanceof Error?err.message:'Unable to void milk usage.');}};

  const setDetail=(mode:DetailMode)=>{setDetailMode(mode);if(mode==='DAY_PRODUCED')setShowProductionForm(false);if(!['DAY_DOMESTIC','DAY_CALVES','DAY_WASTAGE'].includes(mode))setShowDispositionForm(false);};
  const openUsage=(type:'DOMESTIC_USE'|'CALF_FEED'|'WASTAGE')=>{setDispositionType(type);setDispositionLitres('');setDispositionNotes('');setEditingDisposition(null);setShowDispositionForm(true);setDetailMode(type==='DOMESTIC_USE'?'DAY_DOMESTIC':type==='CALF_FEED'?'DAY_CALVES':'DAY_WASTAGE');};

  const month=monthRange(selectedDate);
  const titleMap:Record<DetailMode,string>={MONTH_PRODUCED:`Daily Milk Production — ${month.label}`,MONTH_SOLD:`Milk Sold — ${month.label}`,MONTH_RECON:`Daily Reconciliation — ${month.label}`,DAY_PRODUCED:`Milk Produced — ${selectedDate}`,DAY_SOLD:`Milk Sold — ${selectedDate}`,DAY_DOMESTIC:`Domestic Use — ${selectedDate}`,DAY_CALVES:`Calves Feed — ${selectedDate}`,DAY_WASTAGE:`Wastage / Not Usable — ${selectedDate}`,DAY_RECON:`Daily Reconciliation — ${selectedDate}`};

  return <div style={{padding:16,color:'#fff',height:'100%',overflowY:'auto',boxSizing:'border-box'}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:10,flexWrap:'wrap',marginBottom:12}}>
      <div><div style={{fontSize:20,fontWeight:850,display:'flex',alignItems:'center',gap:8}}><Milk size={20} color="#38bdf8"/> Milk</div><div style={{fontSize:10,color:'#64748b'}}>Monthly control view with daily production, disposition and reconciliation detail.</div></div>
      <div style={{display:'flex',gap:6,alignItems:'center'}}><label style={{fontSize:9,color:'#94a3b8'}}>Selected date</label><input aria-label="Selected operational date" type="date" value={selectedDate} onChange={e=>setSelectedDate(e.target.value)} style={{...inputStyle,width:145}}/><button onClick={()=>void load()} style={smallButton}><RefreshCw size={12}/> Refresh</button></div>
    </div>
    {error&&<div style={{background:'rgba(239,68,68,.12)',border:'1px solid #ef4444',color:'#fecaca',padding:9,borderRadius:6,marginBottom:10,fontSize:11}}>{error}</div>}
    {message&&<div style={{background:'rgba(52,211,153,.10)',border:'1px solid #34d399',color:'#bbf7d0',padding:9,borderRadius:6,marginBottom:10,fontSize:11,display:'flex',alignItems:'center',gap:5}}><Check size={13}/>{message}</div>}

    <div style={{fontSize:10,color:'#94a3b8',fontWeight:800,textTransform:'uppercase',letterSpacing:'.3px',marginBottom:6}}>Month — {month.label}</div>
    <div style={{display:'grid',gridTemplateColumns:'repeat(3,minmax(0,1fr))',gap:8,marginBottom:12}}>
      <Card label="Total Milk Produced" value={litre(monthTotals.produced)} sub="Current month • click for daily production" accent="#38bdf8" onClick={()=>setDetail('MONTH_PRODUCED')} />
      <Card label="Milk Sold" value={litre(monthTotals.sold)} sub="Current month • Finance-linked sales where available" accent="#34d399" onClick={()=>setDetail('MONTH_SOLD')} />
      <Card label="Overall Reconciliation" value={signedLitre(monthTotals.reconciliation)} sub="Sum of daily reconciliation values" accent={monthTotals.reconciliation===0?'#34d399':monthTotals.reconciliation>0?'#38bdf8':'#f87171'} onClick={()=>setDetail('MONTH_RECON')} />
    </div>

    <div style={{fontSize:10,color:'#94a3b8',fontWeight:800,textTransform:'uppercase',letterSpacing:'.3px',marginBottom:6}}>Daily — {selectedDate}</div>
    <div style={{display:'grid',gridTemplateColumns:'repeat(6,minmax(0,1fr))',gap:8,marginBottom:12}}>
      <Card label="Milk Produced" value={litre(daily.produced)} sub="Click for animal-level production" accent="#38bdf8" onClick={()=>setDetail('DAY_PRODUCED')}>
        <div onClick={e=>e.stopPropagation()} style={{marginTop:7}}><input type="date" value={selectedDate} onChange={e=>setSelectedDate(e.target.value)} style={{...inputStyle,fontSize:9,padding:'5px 6px'}}/></div>
      </Card>
      <Card label="Milk Sold" value={litre(displayedSold)} sub={financeSoldQty>0?'Finance-linked quantity':'Milk sales ledger'} accent="#34d399" onClick={()=>setDetail('DAY_SOLD')} />
      <Card label="Domestic Use" value={litre(daily.domestic)} sub="Enter Milk for Domestic Use" accent="#f59e0b" onClick={()=>setDetail('DAY_DOMESTIC')}>
        <div style={{marginTop:7}}><button onClick={e=>{e.stopPropagation();openUsage('DOMESTIC_USE');}} style={actionButton('#b45309')}>Enter Milk for Domestic Use</button></div>
      </Card>
      <Card label="Calves Feed" value={litre(daily.calves)} sub="Enter Milk for Calves" accent="#a78bfa" onClick={()=>setDetail('DAY_CALVES')}>
        <div style={{marginTop:7}}><button onClick={e=>{e.stopPropagation();openUsage('CALF_FEED');}} style={actionButton('#7c3aed')}>Enter Milk for Calves</button></div>
      </Card>
      <Card label="Wastage / Not Usable" value={litre(daily.wastage)} sub="Enter Wastage / Unusable" accent="#f87171" onClick={()=>setDetail('DAY_WASTAGE')}>
        <div style={{marginTop:7}}><button onClick={e=>{e.stopPropagation();openUsage('WASTAGE');}} style={actionButton('#dc2626')}>Enter Wastage / Unusable</button></div>
      </Card>
      <Card label="Reconciliation" value={signedLitre(daily.reconciliation)} sub="Produced − Sold − Domestic − Calves − Wastage" accent={daily.reconciliation===0?'#34d399':daily.reconciliation>0?'#38bdf8':'#f87171'} onClick={()=>setDetail('DAY_RECON')} />
    </div>

    <div style={{background:'#0f172a',border:'1px solid #263244',borderRadius:8,padding:12,marginBottom:12}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:8,marginBottom:8}}><div><div style={{fontSize:12,fontWeight:800,color:'#e2e8f0'}}>{titleMap[detailMode]}</div><div style={{fontSize:9,color:'#64748b'}}>Click any summary or daily box above to change this detail area.</div></div>{loading&&<span style={{fontSize:9,color:'#38bdf8'}}>Loading…</span>}</div>

      {detailMode==='MONTH_PRODUCED' && <div style={{maxHeight:260,overflowY:'auto'}}><div style={{display:'grid',gridTemplateColumns:'100px 1fr 1fr',fontSize:9,color:'#64748b',padding:'6px 8px',borderBottom:'1px solid #1f2937'}}><span>Date</span><span>Daily production</span><span>Status</span></div>{monthRows.length===0?<div style={{padding:14,fontSize:10,color:'#64748b'}}>No milk production entries recorded for this month.</div>:monthRows.map(d=><div key={d.date} style={{display:'grid',gridTemplateColumns:'100px 1fr 1fr',fontSize:10,padding:'8px',borderBottom:'1px solid #182234'}}><span>{d.date}</span><span style={{color:'#38bdf8',fontWeight:800}}>{litre(d.produced)}</span><span style={{color:d.produced>0?'#34d399':'#64748b'}}>{d.produced>0?'RECORDED':'NO ENTRY'}</span></div>)}</div>}

      {detailMode==='MONTH_SOLD' && <div style={{maxHeight:260,overflowY:'auto'}}><div style={{display:'grid',gridTemplateColumns:'100px 1fr 1fr',fontSize:9,color:'#64748b',padding:'6px 8px',borderBottom:'1px solid #1f2937'}}><span>Date</span><span>Milk sold</span><span>Source</span></div>{monthRows.length===0?<div style={{padding:14,fontSize:10,color:'#64748b'}}>No sales records found for this month.</div>:monthRows.map(d=><div key={d.date} style={{display:'grid',gridTemplateColumns:'100px 1fr 1fr',fontSize:10,padding:'8px',borderBottom:'1px solid #182234'}}><span>{d.date}</span><span style={{color:'#34d399',fontWeight:800}}>{litre(d.sold)}</span><span>{financeSales.some(t=>(t.date||'').slice(0,10)===d.date&&Number(t.quantity||0)>0)?'FINANCE':'MILK SALES LEDGER'}</span></div>)}</div>}

      {detailMode==='MONTH_RECON' && <div style={{maxHeight:260,overflowY:'auto'}}><div style={{display:'grid',gridTemplateColumns:'100px repeat(3,1fr)',fontSize:9,color:'#64748b',padding:'6px 8px',borderBottom:'1px solid #1f2937'}}><span>Date</span><span>Produced</span><span>Accounted</span><span>Reconciliation</span></div>{monthRows.length===0?<div style={{padding:14,fontSize:10,color:'#64748b'}}>No daily records available for this month.</div>:monthRows.map(d=><div key={d.date} style={{display:'grid',gridTemplateColumns:'100px repeat(3,1fr)',fontSize:10,padding:'8px',borderBottom:'1px solid #182234'}}><span>{d.date}</span><span>{litre(d.produced)}</span><span>{litre(d.sold+d.domestic+d.calves+d.wastage)}</span><span style={{color:d.reconciliation===0?'#34d399':d.reconciliation>0?'#38bdf8':'#f87171',fontWeight:800}}>{signedLitre(d.reconciliation)}</span></div>)}</div>}

      {detailMode==='DAY_PRODUCED' && <div>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8,gap:8}}><div style={{fontSize:10,color:'#94a3b8'}}>Recorded milk by animal and milking session.</div><button onClick={()=>{setEditingProduction(null);setShowProductionForm(true);}} style={actionButton('#0284c7')}><Save size={11}/> Enter Milk Production</button></div>
        <div style={{maxHeight:230,overflowY:'auto'}}>{dayProduction.length===0?<div style={{padding:14,fontSize:10,color:'#64748b'}}>No production entries for this date.</div>:dayProduction.map(row=><div key={row.id} style={{display:'grid',gridTemplateColumns:'1.1fr 1fr 1fr auto',gap:8,alignItems:'center',fontSize:10,padding:'8px',borderBottom:'1px solid #182234'}}><span style={{fontWeight:800,color:'#fff'}}>{row.animal_id}</span><span>{row.milking_session||'—'}</span><span style={{color:'#38bdf8',fontWeight:800}}>{litre(row.total_yield)}</span><span style={{display:'flex',gap:4}}><button onClick={()=>editProduction(row)} style={smallButton}><Edit3 size={10}/></button><button onClick={()=>voidProduction(row)} style={{...smallButton,color:'#fca5a5'}}><Trash2 size={10}/></button></span></div>)}</div>
      </div>}

      {detailMode==='DAY_SOLD' && <div><div style={{fontSize:10,color:'#94a3b8',marginBottom:8}}>Milk sales are read from Finance-linked sales records where quantity is persisted; the Milk sales ledger remains the operational fallback.</div><div style={{maxHeight:220,overflowY:'auto'}}>{financeSoldRows.length>0?financeSoldRows.map(row=><div key={row.id} style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr auto',gap:8,fontSize:10,padding:'8px',borderBottom:'1px solid #182234'}}><span>{row.reference||row.counterparty||'Milk Sale'}</span><span>{row.status||'—'}</span><span style={{color:'#34d399',fontWeight:800}}>{row.quantity?litre(row.quantity):'Quantity not stored'}</span><span style={{fontWeight:800}}>{money(row.amount)}</span></div>):<div style={{padding:14,fontSize:10,color:'#64748b'}}>No Finance milk-sale rows were found for this date. Milk sales ledger total: {litre(daily.sold)}.</div>}</div></div>}

      {(['DAY_DOMESTIC','DAY_CALVES','DAY_WASTAGE'] as DetailMode[]).includes(detailMode) && <div>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8,gap:8}}><div style={{fontSize:10,color:'#94a3b8'}}>Operational milk disposition records for {selectedDate}.</div><button onClick={()=>{setEditingDisposition(null);setDispositionType(detailMode==='DAY_DOMESTIC'?'DOMESTIC_USE':detailMode==='DAY_CALVES'?'CALF_FEED':'WASTAGE');setShowDispositionForm(true);}} style={actionButton(detailMode==='DAY_WASTAGE'?'#dc2626':detailMode==='DAY_CALVES'?'#7c3aed':'#b45309')}><Save size={11}/> Enter {detailMode==='DAY_DOMESTIC'?'Domestic Use':detailMode==='DAY_CALVES'?'Calves Feed':'Wastage'}</button></div>
        <div style={{maxHeight:220,overflowY:'auto'}}>{dayDispositions.filter(r=>String(r.disposition_type).toUpperCase().includes(detailMode==='DAY_DOMESTIC'?'DOMESTIC':detailMode==='DAY_CALVES'?'CALF':'WAST')).length===0?<div style={{padding:14,fontSize:10,color:'#64748b'}}>No records for this category on this date.</div>:dayDispositions.filter(r=>String(r.disposition_type).toUpperCase().includes(detailMode==='DAY_DOMESTIC'?'DOMESTIC':detailMode==='DAY_CALVES'?'CALF':'WAST')).map(row=><div key={row.id} style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr auto',gap:8,alignItems:'center',fontSize:10,padding:'8px',borderBottom:'1px solid #182234'}}><span>{row.notes||'Operational milk use'}</span><span>{row.status}</span><span style={{color:'#f59e0b',fontWeight:800}}>{litre(row.quantity_litres)}</span><span style={{display:'flex',gap:4}}><button onClick={()=>editDisposition(row)} style={smallButton}><Edit3 size={10}/></button><button onClick={()=>voidDisposition(row)} style={{...smallButton,color:'#fca5a5'}}><Trash2 size={10}/></button></span></div>)}</div>
      </div>}

      {detailMode==='DAY_RECON' && <div style={{display:'grid',gridTemplateColumns:'repeat(5,minmax(0,1fr))',gap:8}}>{[['Produced',daily.produced,'#38bdf8'],['Sold',displayedSold,'#34d399'],['Domestic',daily.domestic,'#f59e0b'],['Calves',daily.calves,'#a78bfa'],['Wastage',daily.wastage,'#f87171']].map(([label,value,color])=><div key={String(label)} style={{background:'#111827',border:'1px solid #1f2937',borderRadius:6,padding:9}}><div style={{fontSize:9,color:'#94a3b8'}}>{label}</div><div style={{fontSize:15,fontWeight:800,color:String(color)}}>{litre(Number(value))}</div></div>)}<div style={{gridColumn:'1/-1',padding:10,borderTop:'1px solid #263244',marginTop:2,fontSize:11}}><strong>Daily Reconciliation = {litre(daily.produced)} − {litre(displayedSold)} − {litre(daily.domestic)} − {litre(daily.calves)} − {litre(daily.wastage)} = </strong><span style={{color:daily.reconciliation===0?'#34d399':daily.reconciliation>0?'#38bdf8':'#f87171',fontWeight:900}}>{signedLitre(daily.reconciliation)}</span></div></div>}
    </div>

    {(showProductionForm||showDispositionForm) && <div style={{background:'#111827',border:'1px solid #334155',borderRadius:8,padding:12,marginBottom:12}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}><div style={{fontSize:12,fontWeight:800}}>{showProductionForm?'Enter Milk Production':`Enter ${dispositionType==='DOMESTIC_USE'?'Milk for Domestic Use':dispositionType==='CALF_FEED'?'Milk for Calves':'Wastage / Unusable'}`}</div><button onClick={()=>{resetProduction();resetDisposition();}} style={smallButton}><X size={11}/> Close</button></div>
      {showProductionForm && <form onSubmit={saveProduction} style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr 1fr',gap:7}}><select value={productionAnimal} onChange={e=>setProductionAnimal(e.target.value)} style={inputStyle} required><option value="">Select Animal</option>{herdMasterList.map(a=><option key={a.id} value={a.id}>{a.id} — {a.breed}</option>)}</select><select value={productionSession} onChange={e=>setProductionSession(e.target.value)} style={inputStyle} required><option value="">Session</option>{(nextSession?.expected_sessions||['MORNING','AFTERNOON','EVENING']).map(s=><option key={s} value={s}>{s}</option>)}</select><input type="number" min="0.01" step="0.01" value={productionLitres} onChange={e=>setProductionLitres(e.target.value)} style={inputStyle} placeholder="Milk litres" required/><button type="submit" disabled={saving} style={actionButton('#0284c7')}>{saving?'Saving…':'Save Milk'}</button><input value={productionNotes} onChange={e=>setProductionNotes(e.target.value)} style={{...inputStyle,gridColumn:'1/4'}} placeholder="Notes (optional)"/></form>}
      {showDispositionForm && <form onSubmit={saveDisposition} style={{display:'grid',gridTemplateColumns:'1fr 1fr 2fr auto',gap:7}}><select value={dispositionType} onChange={e=>setDispositionType(e.target.value)} style={inputStyle}><option value="DOMESTIC_USE">Domestic Use</option><option value="CALF_FEED">Calves Feed</option><option value="WASTAGE">Wastage / Not Usable</option></select><input type="number" min="0.01" step="0.01" value={dispositionLitres} onChange={e=>setDispositionLitres(e.target.value)} style={inputStyle} placeholder="Milk litres" required/><input value={dispositionNotes} onChange={e=>setDispositionNotes(e.target.value)} style={inputStyle} placeholder="Purpose / notes (optional)"/><button type="submit" disabled={saving} style={actionButton(dispositionType==='WASTAGE'?'#dc2626':dispositionType==='CALF_FEED'?'#7c3aed':'#b45309')}>{saving?'Saving…':'Save Entry'}</button></form>}
    </div>}

    <div style={{background:'#0f172a',border:'1px solid #263244',borderRadius:8,padding:11}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:7}}><div><div style={{fontSize:11,fontWeight:800}}>Daily Milk Quality</div><div style={{fontSize:9,color:'#64748b'}}>Retained from the existing Milk quality ledger.</div></div><span style={{fontSize:9,color:qualitySample?'#34d399':'#64748b',fontWeight:800}}>{qualitySample?'RECORDED':'NOT RECORDED'}</span></div>
      <form onSubmit={saveQuality} style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr 2fr auto',gap:7}}><input type="number" min="0.001" max="15" step="0.001" value={qualityFat} onChange={e=>setQualityFat(e.target.value)} style={inputStyle} placeholder="Fat %" required/><input type="number" min="0.001" max="15" step="0.001" value={qualitySnf} onChange={e=>setQualitySnf(e.target.value)} style={inputStyle} placeholder="SNF %" required/><select value={qualityType} onChange={e=>setQualityType(e.target.value)} style={inputStyle}><option value="BULK_TANK">Bulk Tank</option><option value="COMPOSITE">Composite</option><option value="INDIVIDUAL">Individual</option></select><input value={qualityNotes} onChange={e=>setQualityNotes(e.target.value)} style={inputStyle} placeholder="Quality notes"/><button type="submit" disabled={qualitySaving} style={actionButton('#7c3aed')}>{qualitySaving?'Saving…':'Save Quality'}</button></form>
    </div>
  </div>;
}
