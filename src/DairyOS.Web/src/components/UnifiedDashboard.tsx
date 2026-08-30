import { useEffect, useMemo, useState, useCallback } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Milk, Sparkles, AlertTriangle, X, TrendingDown, HeartPulse, Activity, Plus } from 'lucide-react';
import { fetchCommandDashboardData, type CommandDashboardData } from '../api/commandDashboardClient';
import { useAlertAudit } from '../context/AlertAuditContext';
import AnimalPassportModal from './AnimalPassportModal';
import './UnifiedDashboard.css';

const CowIcon = ({ size = 16, color = 'currentColor' }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 3L3 7v3l2 1v5a4 4 0 0 0 4 4h6a4 4 0 0 0 4-4v-5l2-1V7l-2-4-3 2H8L5 3z" />
    <path d="M9 13v.01" /><path d="M15 13v.01" /><path d="M10 18a2 2 0 0 0 4 0" />
  </svg>
);

interface HerdAnimal { id: string; breed: string; category: string; }
interface Props {
  onNavigate?: (view: string) => void;
  onOpenYieldModal?: () => void;
  onOpenPassport?: (id: string) => void;
  herdMasterList?: HerdAnimal[];
  dashboardRefreshVersion?: number;
  realTimeReceivables?: number;
}
interface DropComparisonDetail {
  animalId: string; breed: string; alertTitle: string; prior3DayAvg: number; currentYield: number;
  dropLiters: number; dropPercent: number; flagDate: string; possibleCauses: string[]; recommendedAction: string;
}

type MonthlyComlOutput = {
  month: string;
  costOfMilkProductionPerLiter: number;
};

function monthLabel(month: string): string {
  return new Date(`${month}-01T00:00:00`).toLocaleDateString('en-PK', {
    month: 'short',
    year: 'numeric',
  });
}

import { API_BASE_URL } from '../config/api';
const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

export default function UnifiedDashboard({ onNavigate, onOpenYieldModal, onOpenPassport, herdMasterList = [], dashboardRefreshVersion = 0, realTimeReceivables = 0 }: Props) {
  const [data, setData] = useState<CommandDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartDays, setChartDays] = useState(7);
  const [extremesCount, setExtremesCount] = useState(3);
  const [passportTag, setPassportTag] = useState<string | null>(null);
  const [selectedDropDetail, setSelectedDropDetail] = useState<DropComparisonDetail | null>(null);
  const [comlOutput, setComlOutput] = useState<MonthlyComlOutput | null>(null);
  const { alerts } = useAlertAudit();

  const loadData = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      setData(await fetchCommandDashboardData());
    } catch (err: any) {
      setError(err?.message || 'Failed to load command dashboard data');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void loadData(); }, [loadData, dashboardRefreshVersion]);

  useEffect(() => {
    let cancelled = false;

    const loadComl = async () => {
      try {
        const response = await fetch(`${API_BASE}/farm/coml/current`, {
          headers: { Accept: 'application/json' },
        });
        if (!response.ok) throw new Error(`COML request failed: ${response.status}`);
        const body = await response.json() as {
          record?: {
            month_start?: string | null;
            total_coml_per_liter?: number | null;
          } | null;
        };

        const record = body.record;
        const month = record?.month_start ? String(record.month_start).slice(0, 7) : null;
        const value = Number(record?.total_coml_per_liter);
        if (!cancelled) {
          setComlOutput(
            month && Number.isFinite(value)
              ? { month, costOfMilkProductionPerLiter: value }
              : null,
          );
        }
      } catch {
        if (!cancelled) setComlOutput(null);
      }
    };

    void loadComl();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredYieldTrend = useMemo(() => {
    const values = Array.isArray(data?.yieldTrend)
      ? data.yieldTrend.map((item:any) =>
          Number(
            typeof item === 'number'
              ? item
              : (item?.yield ?? item?.liters ?? 0)
          )
        )
      : [];



    return values
      .slice(-chartDays)
      .map((value, index) => ({
        dayIndex: index + 1,
        yield: Math.round(Number(value)),
      }));
  }, [data, chartDays]);

  const trendPoints = (
    Array.isArray(data?.yieldTrend)
      ? data.yieldTrend
          .map((item: any) => ({
            day: String(item?.day || ''),
            yield:
              item?.yield === null || item?.yield === undefined
                ? null
                : Number(item.yield),
          }))
          .filter((item) => item.day)
      : []
  );

  // The trend is date-complete and anchored to the authoritative current
  // operational date. Therefore its rightmost point is today's dashboard date.
  const currentTrendPoint =
    trendPoints.length > 0
      ? trendPoints[trendPoints.length - 1]
      : null;

  const priorTrendPoint =
    trendPoints.length > 1
      ? trendPoints[trendPoints.length - 2]
      : null;

  const currentDateLabel =
    currentTrendPoint?.day ||
    data?.todayDate ||
    '';

  const priorDateLabel =
    priorTrendPoint?.day ||
    data?.yesterdayDate ||
    '';

  const currentTrendYield =
    currentTrendPoint?.yield ?? null;

  const priorTrendYield =
    priorTrendPoint?.yield ?? null;

  const openPassportHandler = (tag: string) => onOpenPassport ? onOpenPassport(tag) : setPassportTag(tag);

  const handleOpenDropComparison = (animalId: string, alertTitle: string) => {
    const alert = alerts.find(
      (item:any) =>
        item.source === 'MILK_DROP' &&
        (item.animalId || item.animal_id) === animalId &&
        item.status !== 'RESOLVED'
    ) as any;

    if (!alert) return;

    setSelectedDropDetail({
      animalId,
      breed: alert.breed || 'Unavailable',
      alertTitle,
      prior3DayAvg: Number(alert.prior3DayAvg ?? alert.prior_3_day_avg ?? 0),
      currentYield: Number(alert.currentYield ?? alert.current_yield ?? 0),
      dropLiters: Number(alert.dropLiters ?? alert.drop_liters ?? 0),
      dropPercent: Number(alert.dropPercent ?? alert.drop_percent ?? 0),
      flagDate: alert.flagDate || alert.flag_date || alert.date || '',
      possibleCauses: Array.isArray(alert.possibleCauses)
        ? alert.possibleCauses
        : Array.isArray(alert.possible_causes)
          ? alert.possible_causes
          : [],
      recommendedAction:
        alert.recommendedAction ||
        alert.recommended_action ||
        'Review the linked milk-production and animal records.',
    });
  };
  if (loading && !data) return <div style={{ padding:30, color:'#94a3b8', textAlign:'center', fontSize:12 }}>Loading authoritative command picture...</div>;

  const dynamicMilkingCount = herdMasterList.filter(
    a => a.category.includes('Milking')
  ).length;

  const milkingCount =
    dynamicMilkingCount > 0
      ? dynamicMilkingCount
      : Number(data?.milkingAnimals || 0);

  // Today's displayed yield is the rightmost operational-date observation.
  // null means no milk has been entered yet; it is not fabricated as zero.
  const todayYield =
    currentTrendYield !== null
      ? currentTrendYield
      : Number(data?.todayLiters || 0);

  const avgYieldPerAnimal = Number(
    data?.averageYieldPerCow ??
      (
        todayYield > 0 && milkingCount > 0
          ? todayYield / milkingCount
          : 0
      )
  );

  const yesterdayLiters =
    priorTrendYield !== null
      ? priorTrendYield
      : Number(data?.yesterdayLiters || 0);

  const yieldDropPercent =
    yesterdayLiters > 0 && todayYield > 0
      ? ((yesterdayLiters - todayYield) / yesterdayLiters) * 100
      : 0;
  const todayYieldColor = yieldDropPercent >= 20 ? '#ef4444' : yieldDropPercent >= 10 ? '#f59e0b' : '#34d399';

  const countCategory = (keywords: string[]) => herdMasterList.filter(a => keywords.some(k => a.category.includes(k))).length;
  const canonicalHerd = [
    { name:'Milking Cows', value:countCategory(['Milking']), color:'#38bdf8' },
    { name:'Dry Cows', value:countCategory(['Dry']), color:'#94a3b8' },
    { name:'Heifers', value:countCategory(['Heifer']), color:'#f59e0b' },
    { name:'Female Calves', value:countCategory(['Female Calf']), color:'#ec4899' },
    { name:'Male Calves', value:countCategory(['Male Calf']), color:'#3b82f6' },
    { name:'Bulls', value:countCategory(['Bull','Sire']), color:'#a855f7' },
  ];
  const herdCol1 = canonicalHerd.slice(0,3), herdCol2 = canonicalHerd.slice(3,6);
  const totalHerdCount = canonicalHerd.reduce((sum,c) => sum + c.value, 0);
  const milkingAdultCount = canonicalHerd[0].value;
  const dryAdultCount = canonicalHerd[1].value;
  const totalAdultCount = milkingAdultCount + dryAdultCount;
  const milkingPercentage =
    totalAdultCount > 0
      ? `${Math.round((milkingAdultCount / totalAdultCount) * 100)}%`
      : '0%';
  const extremesOptions = [1,2,3,4,5,6,7,8,9,10];
  const allTopPerformers = Array.isArray(data?.topPerformers) ? data.topPerformers : [];
  const allBottomPerformers = Array.isArray(data?.bottomPerformers) ? data.bottomPerformers : [];
  const displayedTop = allTopPerformers.slice(0,extremesCount), displayedBottom = allBottomPerformers.slice(0,extremesCount);
  const activeDropAlerts = alerts.filter(a => a.source === 'MILK_DROP' && a.status !== 'RESOLVED');
  const healthData = data?.health || { sick:0, mastitis:0, highTemp:0, completedVax:0, dueVax:0 };
  const reproSource = data?.reproduction as { onHeat?:number; inseminated?:number; pregnant?:number; conceptionRatio?:string; } | undefined;
  const reproData = { onHeat:reproSource?.onHeat ?? 0, inseminated:reproSource?.inseminated ?? 0, pregnant:reproSource?.pregnant ?? 0, conceptionRatio:reproSource ? undefined : undefined };
  const currentComlMonth = comlOutput?.month || new Date().toISOString().slice(0, 7);
  const currentComlValue = Number(comlOutput?.costOfMilkProductionPerLiter || 0);

  return (
    <div className="cmd-dash-wrapper" style={{ height:'calc(100vh - 60px)', overflow:'hidden', display:'flex', flexDirection:'column', boxSizing:'border-box', padding:10, minWidth:0 }}>
      {error && <div style={{ marginBottom:8, padding:8, background:'rgba(239,68,68,.10)', border:'1px solid #ef4444', color:'#fecaca', borderRadius:6, fontSize:10, flexShrink:0 }}>{error}</div>}
      <div className="cmd-content-grid" style={{ display:'grid', gridTemplateColumns:'minmax(0,1.2fr) minmax(260px,.8fr)', gap:10, flex:1, minHeight:0, minWidth:0, overflow:'hidden' }}>
        <div className="cmd-col" style={{ display:'flex', flexDirection:'column', gap:10, minHeight:0, minWidth:0 }}>
          <div className="cmd-card" style={{ flex:'1.6 1 0', display:'flex', flexDirection:'column', background:'#111827', border:'1px solid #1f2937', borderRadius:8, padding:10, minHeight:0, minWidth:0, overflow:'hidden' }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate?.('milk')} style={{ display:'flex', alignItems:'center', gap:6, color:'#38bdf8', fontWeight:'bold', fontSize:12, cursor:'pointer', marginBottom:8 }}> <Milk size={16} /> <span>Milk Production & Farm Yield</span></div>
            <div className="stat-row" style={{ display:'grid', gridTemplateColumns:'repeat(5,minmax(0,1fr))', gap:6, marginBottom:8, minWidth:0 }}>
              <SmallStat label="Milking Animals" value={milkingAdultCount} /><SmallStat label="Total Adults" value={totalAdultCount} /><SmallStat label="Milking %" value={milkingPercentage} color="#34d399" /><SmallStat
                label="Avg Yield/Cow"
                value={
                  todayYield > 0 && milkingCount > 0
                    ? `${avgYieldPerAnimal.toFixed(2)} L`
                    : 'No milk entered'
                }
                color="#38bdf8"
              /><SmallStat label="Cost of Milk Production/Liter" value={`PKR ${currentComlValue.toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} color="#a78bfa" sublabel={monthLabel(currentComlMonth)} />
            </div>
            <div className="stat-row" style={{ display:'grid', gridTemplateColumns:'repeat(3,minmax(0,1fr))', gap:8, marginBottom:8, minWidth:0 }}>
              <WideStat
                label={currentDateLabel}
                value={
                  currentTrendYield === null
                    ? 'No milk entered'
                    : `${Number(currentTrendYield).toFixed(1)} L`
                }
                color={todayYieldColor}
              />
              <WideStat
                label={priorDateLabel}
                value={
                  priorTrendYield === null
                    ? 'No milk entered'
                    : `${Number(priorTrendYield).toFixed(1)} L`
                }
                color="#cbd5e1"
                border="#64748b"
              />
              <WideStat label="Receivables" value={`Rs. ${realTimeReceivables.toLocaleString()}`} color="#f59e0b" border="#f59e0b" />
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'minmax(0,1.05fr) minmax(0,.95fr)', gap:8, flex:1, minHeight:0, minWidth:0, overflow:'hidden' }}>
              <div style={panel}><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:6,marginBottom:4,minWidth:0}}><span style={graphTitle}><Activity size={12}/> Total Farm Yield Trend</span><select value={chartDays} onChange={e=>setChartDays(Number(e.target.value))} style={selectStyle}><option value={7}>7 Days</option><option value={15}>15 Days</option><option value={30}>30 Days</option></select></div><div style={{flex:1,minHeight:0,height:'100%',position:'relative',overflow:'hidden'}}><ResponsiveContainer width="100%" height="100%"><AreaChart data={filteredYieldTrend} margin={{top:2,right:6,left:0,bottom:0}}><XAxis dataKey="dayIndex" hide/><YAxis allowDecimals={false} stroke="#64748b" tick={{fontSize:8}} width={24} domain={['auto','auto']}/><Tooltip
  contentStyle={{backgroundColor:'#0f172a',borderColor:'#334155',fontSize:'10px'}}
  labelFormatter={(_, payload) => {
    const point = payload?.[0]?.payload as any;
    return point?.date || '';
  }}
  formatter={(value) => [
    value === null || value === undefined
      ? 'No milk entered'
      : `${Number(value).toFixed(1)} L`,
    'Milk',
  ]}
/><Area type="monotone" dataKey="yield" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="rgba(56,189,248,.18)" isAnimationActive={false} connectNulls={false}/></AreaChart></ResponsiveContainer></div></div>
              <div style={panel}><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:4,gap:6}}><span style={{fontSize:10,fontWeight:800,color:'#f87171',display:'flex',alignItems:'center',gap:4}}><AlertTriangle size={11}/> Yield Drop Watchlist ({activeDropAlerts.length})</span><span style={{fontSize:9,color:'#94a3b8'}}>Click row</span></div><div style={{flex:1,minHeight:0,overflowY:'auto',display:'flex',flexDirection:'column',gap:4}}>{activeDropAlerts.length===0 ? <div style={{fontSize:10,color:'#34d399',textAlign:'center',padding:12}}>âœ“ No active yield drop warnings</div> : activeDropAlerts.map((item:any)=><div key={item.id} onClick={()=>handleOpenDropComparison(item.animalId||'TD-004',item.title)} style={{background:'#161f30',borderLeft:item.currentLevel==='RED'?'3px solid #ef4444':'3px solid #f59e0b',padding:'5px 8px',borderRadius:4,display:'flex',justifyContent:'space-between',cursor:'pointer',fontSize:10}}><span style={{color:'#38bdf8',fontWeight:700}}>#{item.animalId || 'Animal'}</span><span style={{color:item.currentLevel==='RED'?'#ef4444':'#f59e0b',fontWeight:700}}>{(() => {
  const directPct = item.dropPercent ?? item.drop_percent;
  const detailText = String(item.details ?? item.detail ?? '');
  const detailMatch = detailText.match(/(-?\d+(?:\.\d+)?)%\s*decline/i);
  const pct = directPct !== undefined && directPct !== null
    ? Math.abs(Number(directPct))
    : detailMatch
      ? Math.abs(Number(detailMatch[1]))
      : null;
  return pct !== null && Number.isFinite(pct) ? `${pct.toFixed(1)}% Drop` : 'Drop';
})()}</span></div>)}</div></div>
            </div>
          </div>
          <div style={{ flex:'1 1 0', display:'grid', gridTemplateColumns:'minmax(0,1.3fr) minmax(220px,.7fr)', gap:10, minHeight:0, minWidth:0 }}><div className="cmd-card" style={{display:'flex',flexDirection:'column',...cardBase}}><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:6}}><span onClick={()=>onNavigate?.('animals')} style={{display:'flex',alignItems:'center',gap:6,color:'#f59e0b',fontWeight:800,fontSize:12,cursor:'pointer'}}><CowIcon size={16} color="#f59e0b"/> Total Herd</span><span style={{fontSize:10,color:'#94a3b8'}}>Total: {totalHerdCount} Head</span></div><div style={{flex:1,minHeight:0,display:'grid',gridTemplateColumns:'1fr 1fr',gap:8,overflow:'hidden'}}><HerdTable rows={herdCol1}/><HerdTable rows={herdCol2}/></div></div><div className="cmd-card" style={{display:'flex',flexDirection:'column',...cardBase}}><div style={{color:'#38bdf8',fontWeight:800,fontSize:12,marginBottom:8}}><Plus size={15} style={{verticalAlign:'middle',marginRight:4}}/> Data Entry</div><div style={{display:'flex',flexDirection:'column',gap:8,justifyContent:'center',flex:1}}><ActionButton onClick={()=>onOpenYieldModal ? onOpenYieldModal() : onNavigate?.('milk')} text="Enter Milk Production" icon={<Milk size={14}/>} color="#0284c7"/><ActionButton onClick={()=>onNavigate?.('finance')} text="Enter Milk Sale" icon={<span style={{fontWeight:900}}>â‚¨</span>} color="#059669"/></div></div></div>
        </div>
        <div className="cmd-col" style={{display:'flex',flexDirection:'column',gap:10,minHeight:0,minWidth:0,overflow:'hidden'}}>
          <div className="cmd-card" style={{flex:'0.9 1 0',...cardBase}}><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:6}}><span style={{display:'flex',alignItems:'center',gap:6,color:'#34d399',fontWeight:800,fontSize:12}}><Sparkles size={15}/> Production Extremes</span><select value={extremesCount} onChange={e=>setExtremesCount(Number(e.target.value))} style={selectStyle}>{extremesOptions.map(n=><option key={n}>{n}</option>)}</select></div><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8,flex:1,minHeight:0,overflowY:'auto'}}><ExtremeList title="Highest" rows={displayedTop} color="#34d399" onOpen={openPassportHandler}/><ExtremeList title="Lowest" rows={displayedBottom} color="#f87171" onOpen={openPassportHandler}/></div></div>
          <div className="cmd-card" style={{flex:'0.85 1 0',...cardBase}}><div style={{display:'flex',alignItems:'center',gap:6,color:'#ef4444',fontWeight:800,fontSize:12,marginBottom:6,cursor:'pointer'}} onClick={()=>onNavigate?.('health')}><HeartPulse size={15}/> Health & Treatments</div><div style={{display:'flex',flexDirection:'column',gap:6,justifyContent:'center',flex:1,minHeight:0}}><div style={healthBox}><span style={{fontWeight:800,color:'#fca5a5',fontSize:10}}><b style={{background:'#ef4444',color:'#fff',padding:'2px 4px',borderRadius:4,fontSize:8,marginRight:5}}>SICK</b>{healthData.sick} ANIMALS</span><span style={{fontSize:10,color:'#f87171'}}>Mastitis: {healthData.mastitis} | Temp: {healthData.highTemp}</span></div><div style={{...healthBox,background:'rgba(245,158,11,.10)',borderColor:'rgba(245,158,11,.3)'}}><span style={{fontWeight:800,color:'#fcd34d',fontSize:10}}>VACCINATION</span><span style={{fontSize:10,color:'#cbd5e1'}}>Done: <b>{healthData.completedVax}</b> | Due: <b style={{color:'#fcd34d'}}>{healthData.dueVax}</b></span></div></div></div>
          <div className="cmd-card" style={{flex:'0.85 1 0',...cardBase}}><div style={{display:'flex',alignItems:'center',gap:6,color:'#fb923c',fontWeight:800,fontSize:12,marginBottom:6,cursor:'pointer'}} onClick={()=>onNavigate?.('breeding')}><Activity size={15}/> Reproductive Health</div><div style={{display:'grid',gridTemplateColumns:'repeat(4,minmax(0,1fr))',gap:6,flex:1,alignItems:'center',minWidth:0}}>{[['On Heat',reproData.onHeat,'#fb923c'],['Inseminated',reproData.inseminated,'#60a5fa'],['Pregnant',reproData.pregnant,'#a78bfa'],['Concep. Ratio',reproData.conceptionRatio,'#ec4899']].map(([label,value,color])=><div key={String(label)} style={{background:'#1e293b',padding:6,borderRadius:6,textAlign:'center',minWidth:0}}><div style={{color:String(color),fontSize:13,fontWeight:900}}>{String(value)}</div><div style={{fontSize:9,color:'#94a3b8'}}>{String(label)}</div></div>)}</div></div>
        </div>
      </div>
      {selectedDropDetail && <div style={modalOverlay}><div style={modalCard}><div style={modalHeader}><div style={{display:'flex',alignItems:'center',gap:8}}><TrendingDown size={18} color="#ef4444"/><h3 style={{margin:0,fontSize:14}}>Yield Drop Diagnostic: #{selectedDropDetail.animalId}</h3></div><button onClick={()=>setSelectedDropDetail(null)} style={iconButton}><X size={18}/></button></div><div style={{padding:18,display:'flex',flexDirection:'column',gap:14}}><div style={{display:'grid',gridTemplateColumns:'repeat(3,minmax(0,1fr))',gap:10}}><KpiMini label="Prior 3-Day Avg" value={`${Math.round(selectedDropDetail.prior3DayAvg)} L`}/><KpiMini label="Current Yield" value={`${Math.round(selectedDropDetail.currentYield)} L`}/><KpiMini label="Drop Variance" value={`-${Math.round(selectedDropDetail.dropLiters)} L (${Math.round(selectedDropDetail.dropPercent)}%)`} danger/></div><div style={{background:'#161f30',padding:12,borderRadius:6,fontSize:11,color:'#cbd5e1'}}><div><b>Breed:</b> {selectedDropDetail.breed}</div><div style={{marginTop:5}}><b>Triggered Alert:</b> {selectedDropDetail.alertTitle}</div><div style={{marginTop:5}}><b>Flagged Date:</b> {selectedDropDetail.flagDate}</div></div><div><div style={{fontSize:11,fontWeight:800,color:'#fbbf24',marginBottom:6}}>Probable Causes</div><ul style={{margin:0,paddingLeft:18,fontSize:11,color:'#cbd5e1'}}>{selectedDropDetail.possibleCauses.map(c=><li key={c}>{c}</li>)}</ul></div><div style={{background:'rgba(56,189,248,.10)',borderLeft:'3px solid #38bdf8',padding:10,borderRadius:4,fontSize:11}}><b style={{color:'#38bdf8'}}>Recommended Action:</b> <span style={{color:'#e2e8f0'}}>{selectedDropDetail.recommendedAction}</span></div><div style={{display:'flex',justifyContent:'flex-end',gap:8}}><button onClick={()=>{const tag=selectedDropDetail.animalId;setSelectedDropDetail(null);openPassportHandler(tag);}} style={button('#0284c7')}>Open Passport #{selectedDropDetail.animalId}</button><button onClick={()=>setSelectedDropDetail(null)} style={button('#334155')}>Close</button></div></div></div></div>}
      {passportTag && <AnimalPassportModal animalId={passportTag} onClose={()=>setPassportTag(null)}/>}    
    </div>
  );
}

function SmallStat({label,value,color='#fff',sublabel}:{label:string,value:string|number,color?:string,sublabel?:string}){return <div style={{background:'#1e293b',padding:6,borderRadius:6,minWidth:0}}><div style={{fontSize:8,color:'#94a3b8'}}>{label}</div><div style={{fontSize:13,fontWeight:900,color,marginTop:2,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{value}</div>{sublabel && <div style={{fontSize:7,color:'#64748b',marginTop:2}}>{sublabel}</div>}</div>}
function WideStat({label,value,color,border='#38bdf8'}:{label:string,value:string,color:string,border?:string}){return <div style={{background:'#1e293b',padding:'8px 12px',borderRadius:6,borderLeft:`3px solid ${border}`,display:'flex',justifyContent:'space-between',alignItems:'center',minWidth:0}}><div style={{fontSize:10,color:'#94a3b8',fontWeight:800}}>{label}</div><div style={{fontSize:15,fontWeight:900,color}}>{value}</div></div>}
function HerdTable({rows}:{rows:{name:string;value:number;color:string}[]}){return <div style={{minHeight:0,overflow:'auto'}}><table style={{width:'100%',fontSize:10,borderCollapse:'collapse'}}><thead><tr style={{color:'#94a3b8',borderBottom:'1px solid #1f2937'}}><th style={{textAlign:'left',padding:3}}>Category</th><th style={{textAlign:'right',padding:3}}>Count</th></tr></thead><tbody>{rows.map(c=><tr key={c.name} style={{borderBottom:'1px solid #1a2234'}}><td style={{display:'flex',alignItems:'center',gap:4,padding:4,color:'#e2e8f0'}}><div style={{width:6,height:6,backgroundColor:c.color,borderRadius:2}}/>{c.name}</td><td style={{fontWeight:800,textAlign:'right',padding:4}}>{c.value}</td></tr>)}</tbody></table></div>}
function ExtremeList({title,rows,color,onOpen}:{title:string,rows:{id:string;yield:number}[],color:string,onOpen:(id:string)=>void}){return <div style={{background:'#0b1120',border:'1px solid #1e293b',borderRadius:6,padding:'6px 8px',minWidth:0}}><div style={{fontSize:10,fontWeight:800,color,marginBottom:4,display:'flex',justifyContent:'space-between'}}><span>{title}</span><span>Liters</span></div>{rows.map((p,i)=><div key={p.id} style={{display:'flex',justifyContent:'space-between',fontSize:10,padding:'2px 4px',background:'#161f30',borderRadius:3,marginBottom:3}}><span onClick={()=>onOpen(p.id)} style={{color:'#38bdf8',fontWeight:700,cursor:'pointer',textDecoration:'underline'}}>{i+1}. #{p.id}</span><span style={{color,fontWeight:700}}>{Math.round(p.yield)} L</span></div>)}</div>}
function ActionButton({onClick,text,icon,color}:{onClick:()=>void;text:string;icon:React.ReactNode;color:string}){return <button onClick={onClick} style={{width:'100%',background:color,border:'1px solid rgba(255,255,255,.22)',borderRadius:6,padding:10,color:'#fff',fontSize:10,fontWeight:800,cursor:'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:6}}>{icon}{text}</button>}
function KpiMini({label,value,danger=false}:{label:string;value:string;danger?:boolean}){return <div style={{background:danger?'rgba(239,68,68,.15)':'#0f172a',border:`1px solid ${danger?'#ef4444':'#1e293b'}`,padding:10,borderRadius:6}}><div style={{fontSize:10,color:'#94a3b8'}}>{label}</div><div style={{fontSize:16,fontWeight:900,color:danger?'#ef4444':'#38bdf8'}}>{value}</div></div>}
const panel:React.CSSProperties={background:'#0b1120',border:'1px solid #1e293b',borderRadius:6,padding:'6px 8px',display:'flex',flexDirection:'column',minHeight:0,minWidth:0,overflow:'hidden'};
const graphTitle:React.CSSProperties={fontSize:10,color:'#94a3b8',fontWeight:800,display:'flex',alignItems:'center',gap:4};
const selectStyle:React.CSSProperties={background:'#161f30',color:'#cbd5e1',border:'1px solid #374151',borderRadius:4,fontSize:9,padding:'1px 4px'};
const cardBase:React.CSSProperties={background:'#111827',border:'1px solid #1f2937',borderRadius:8,padding:10,minHeight:0,minWidth:0,overflow:'hidden'};
const healthBox:React.CSSProperties={display:'flex',justifyContent:'space-between',alignItems:'center',gap:6,background:'rgba(239,68,68,.10)',border:'1px solid rgba(239,68,68,.3)',padding:'6px 8px',borderRadius:6};
const modalOverlay:React.CSSProperties={position:'fixed',inset:0,background:'rgba(0,0,0,.8)',display:'flex',alignItems:'center',justifyContent:'center',zIndex:1000,padding:20};
const modalCard:React.CSSProperties={background:'#111827',border:'1px solid #ef4444',borderRadius:10,width:520,maxWidth:'100%',overflow:'hidden'};
const modalHeader:React.CSSProperties={background:'#1e293b',padding:'14px 18px',display:'flex',justifyContent:'space-between',alignItems:'center',borderBottom:'1px solid #334155'};
const iconButton:React.CSSProperties={background:'none',border:'none',color:'#94a3b8',cursor:'pointer'};
const button=(background:string):React.CSSProperties=>({background,color:'#fff',border:'none',padding:'8px 14px',borderRadius:6,fontSize:11,fontWeight:800,cursor:'pointer'});
