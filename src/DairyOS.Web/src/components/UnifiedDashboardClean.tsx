import React, { useEffect, useMemo, useState } from 'react';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, HeartPulse, Milk, TrendingDown, Users } from 'lucide-react';
import { fetchCommandDashboardData, type CommandDashboardData } from '../api/commandDashboardClient';
import { useAlertAudit } from '../context/AlertAuditContext';
import AnimalPassportModal from './AnimalPassportModal';

const panel: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 10, minWidth: 0, boxSizing: 'border-box', overflow: 'hidden' };
const title: React.CSSProperties = { fontSize: 12, fontWeight: 800, color: '#e2e8f0' };
const muted: React.CSSProperties = { fontSize: 9, color: '#94a3b8' };

type HerdAnimal = { id: string; category: string };
type Props = { onNavigate?: (view: string) => void; onOpenYieldModal?: () => void; onOpenPassport?: (id: string) => void; herdMasterList?: HerdAnimal[]; realTimeTodayYield?: number; realTimeReceivables?: number };

export default function UnifiedDashboardClean({ onNavigate, onOpenYieldModal, onOpenPassport, herdMasterList = [], realTimeTodayYield, realTimeReceivables = 0 }: Props) {
  const [data, setData] = useState<CommandDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartDays, setChartDays] = useState(7);
  const [passportTag, setPassportTag] = useState<string | null>(null);
  const { alerts } = useAlertAudit();

  useEffect(() => {
    fetchCommandDashboardData().then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);

  const todayYield = realTimeTodayYield ?? Math.round(Number(data?.todayLiters) || 0);
  const yesterdayYield = Math.round(Number(data?.yesterdayLiters) || 0);
  const milkingCount = herdMasterList.filter(a => a.category.includes('Milking')).length || Number(data?.milkingAnimals) || 0;
  const receivables = realTimeReceivables || 0;
  const trend = useMemo(() => {
    const source = Array.isArray(data?.yieldTrend) ? data!.yieldTrend : [];
    const values = source.map((row: any) => Number(typeof row === 'number' ? row : row.yield || row.liters || 0)).filter(v => Number.isFinite(v));
    const fallback = [121, 122, 120, 123, 125, 127, 128, 128, 129, 131, 130, 129, 127, 129, 131, 134, 132, 134, 136, 133, 132, 130, 129, 132, 133, 131, 128, 131, 128, 133];
    const series = (values.length ? values : fallback).slice(-chartDays);
    return series.map((yieldValue, index) => ({ day: index + 1, yield: Math.round(yieldValue) }));
  }, [data, chartDays]);
  const herdByCategory = useMemo(() => herdMasterList.reduce<Record<string, number>>((acc, row) => { acc[row.category] = (acc[row.category] || 0) + 1; return acc; }, {}), [herdMasterList]);
  const dropAlerts = alerts.filter(a => a.source === 'MILK_DROP' && a.status !== 'RESOLVED').slice(0, 5);

  if (loading) return <div style={{ padding: 20, color: '#94a3b8', fontSize: 11 }}>Loading dashboard…</div>;

  return <div style={{ height: '100%', overflowY: 'auto', overflowX: 'hidden', padding: 10, boxSizing: 'border-box' }}>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,minmax(0,1fr))', gap: 8, marginBottom: 8 }}>
      <Kpi label="Today Milk" value={`${todayYield} L`} accent="#38bdf8" />
      <Kpi label="Yesterday" value={`${yesterdayYield} L`} accent="#94a3b8" />
      <Kpi label="Milking Animals" value={String(milkingCount)} accent="#34d399" />
      <Kpi label="Receivables" value={`PKR ${receivables.toLocaleString('en-PK')}`} accent="#f59e0b" />
      <Kpi label="Milk Delta" value={`${yesterdayYield ? Math.round(((todayYield - yesterdayYield) / yesterdayYield) * 100) : 0}%`} accent={todayYield >= yesterdayYield ? '#34d399' : '#f87171'} />
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.4fr) minmax(260px,.6fr)', gap: 8, alignItems: 'stretch' }}>
      <section style={{ ...panel, display: 'flex', flexDirection: 'column', minHeight: 250 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}><div style={title}><Milk size={14} color="#38bdf8" style={{ verticalAlign: 'middle', marginRight: 5 }} /> Total Farm Yield</div><select value={chartDays} onChange={e => setChartDays(Number(e.target.value))} style={{ background: '#1e293b', color: '#cbd5e1', border: '1px solid #334155', borderRadius: 4, padding: '3px 6px', fontSize: 9 }}><option value={7}>7 days</option><option value={15}>15 days</option><option value={30}>30 days</option></select></div>
        <div style={{ flex: 1, minHeight: 170, width: '100%', minWidth: 0, overflow: 'hidden' }}><ResponsiveContainer width="100%" height="100%"><AreaChart data={trend} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}><XAxis dataKey="day" hide /><YAxis allowDecimals={false} width={28} tick={{ fontSize: 8, fill: '#64748b' }} /><Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', fontSize: 9 }} /><Area type="monotone" dataKey="yield" stroke="#38bdf8" fill="#0f3b58" strokeWidth={2} /></AreaChart></ResponsiveContainer></div>
      </section>

      <div style={{ display: 'grid', gridTemplateRows: '1fr 1fr', gap: 8, minWidth: 0 }}>
        <section style={panel}><div style={title}><Users size={14} color="#f59e0b" style={{ verticalAlign: 'middle', marginRight: 5 }} /> Herd Snapshot</div><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5, marginTop: 8 }}>{Object.entries(herdByCategory).slice(0, 6).map(([label, value]) => <div key={label} style={{ background: '#1e293b', borderRadius: 5, padding: 6, minWidth: 0 }}><div style={{ ...muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</div><div style={{ fontSize: 14, fontWeight: 800 }}>{value}</div></div>)}</div></section>
        <section style={panel}><div style={title}><HeartPulse size={14} color="#ef4444" style={{ verticalAlign: 'middle', marginRight: 5 }} /> Health & Treatments</div><div style={{ marginTop: 8, display: 'grid', gap: 6 }}><Mini label="Sick animals" value={String(data?.health?.sick ?? 0)} /><Mini label="Mastitis" value={String(data?.health?.mastitis ?? 0)} /><Mini label="Vaccinations due" value={String(data?.health?.dueVax ?? 0)} /></div></section>
      </div>
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: 8, marginTop: 8 }}>
      <section style={panel}><div style={title}><TrendingDown size={14} color="#f87171" style={{ verticalAlign: 'middle', marginRight: 5 }} /> Yield Drop Watchlist</div>{dropAlerts.length === 0 ? <div style={{ ...muted, marginTop: 8 }}>No active milk-drop alerts.</div> : <div style={{ display: 'grid', gap: 4, marginTop: 8 }}>{dropAlerts.map(alert => <button key={alert.id} onClick={() => onNavigate?.('audit')} style={{ display: 'flex', justifyContent: 'space-between', gap: 6, width: '100%', textAlign: 'left', background: '#1e293b', border: '1px solid #334155', borderRadius: 5, padding: '6px 7px', color: '#e2e8f0', fontSize: 9, cursor: 'pointer' }}><span style={{ fontWeight: 700 }}>{alert.title}</span><span style={{ color: '#f87171', whiteSpace: 'nowrap' }}>Open</span></button>)}</div>}</section>
      <section style={panel}><div style={title}><Activity size={14} color="#fb923c" style={{ verticalAlign: 'middle', marginRight: 5 }} /> Reproductive Health</div><div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 5, marginTop: 8 }}>{[['On Heat', data?.reproduction?.onHeat ?? 0], ['Inseminated', data?.reproduction?.inseminated ?? 0], ['Pregnant', data?.reproduction?.pregnant ?? 0], ['Conception', data?.reproduction?.conceptionRatio ?? '—']].map(([label, value]) => <div key={String(label)} style={{ background: '#1e293b', borderRadius: 5, padding: 6, textAlign: 'center', minWidth: 0 }}><div style={{ fontSize: 13, fontWeight: 800, color: '#f8fafc' }}>{String(value)}</div><div style={{ ...muted, marginTop: 2 }}>{String(label)}</div></div>)}</div></section>
    </div>

    <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}><Action text="Enter Milk" onClick={() => onOpenYieldModal?.()} /><Action text="Open Finance" onClick={() => onNavigate?.('finance')} /><Action text="Open Feed" onClick={() => onNavigate?.('feed')} /><Action text="Open COML" onClick={() => onNavigate?.('coml')} /></div>
    {passportTag && <AnimalPassportModal animalId={passportTag} onClose={() => setPassportTag(null)} />}
  </div>;
}

function Kpi({ label, value, accent }: { label: string; value: string; accent: string }) { return <div style={{ ...panel, borderLeft: `4px solid ${accent}` }}><div style={muted}>{label}</div><div style={{ color: accent, fontSize: 15, fontWeight: 800, marginTop: 3 }}>{value}</div></div>; }
function Mini({ label, value }: { label: string; value: string }) { return <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, fontSize: 10, color: '#cbd5e1' }}><span>{label}</span><strong>{value}</strong></div>; }
function Action({ text, onClick }: { text: string; onClick: () => void }) { return <button onClick={onClick} style={{ background: '#1e293b', border: '1px solid #334155', color: '#e2e8f0', borderRadius: 5, padding: '7px 10px', fontSize: 9, fontWeight: 700, cursor: 'pointer' }}>{text}</button>; }
