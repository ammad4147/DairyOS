import { useEffect, useState, useCallback, useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { X, Milk, Activity, HeartPulse, Sparkles } from 'lucide-react';
import { fetchCommandDashboardData, type CommandDashboardData } from '../api/commandDashboardClient';
import { fetchAnimalPassport, type AnimalPassportData } from '../api/livePassportClient';
import './UnifiedDashboard.css';

interface Props { onNavigate?: (view: string) => void; }

export default function UnifiedDashboard({ onNavigate }: Props) {
  const [data, setData] = useState<CommandDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartDays, setChartDays] = useState<number>(7);
  const [passportTag, setPassportTag] = useState<string | null>(null);
  const [passportData, setPassportData] = useState<AnimalPassportData | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCommandDashboardData();
      if (res && res.herdComposition) {
        // Strict required sequence: Milking, Dry, Heifers, Female Calves, Male Calves, Bulls
        const preferredOrder = ["Milking", "Dry", "Heifers", "Female Calves", "Male Calves", "Bulls"];
        res.herdComposition.sort((a: any, b: any) => {
          const idxA = preferredOrder.indexOf(a.name);
          const idxB = preferredOrder.indexOf(b.name);
          return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB);
        });
      }
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to load command dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Filter yield trend data and map day indices (1 to N days denominator)
  const filteredYieldTrend = useMemo(() => {
    if (!data || !Array.isArray(data.yieldTrend)) return [];
    const sliced = data.yieldTrend.slice(-chartDays);
    return sliced.map((item, index) => ({
      ...item,
      dayIndex: index + 1
    }));
  }, [data, chartDays]);

  const openPassport = async (tag: string) => {
    setPassportTag(tag);
    try {
      const pData = await fetchAnimalPassport(tag);
      setPassportData(pData);
    } catch (e) {
      setPassportData(null);
    }
  };

  if (loading && !data) {
    return <div style={{ padding: '30px', color: '#94a3b8', textAlign: 'center', fontSize: '13px' }}>Loading authoritative command picture...</div>;
  }

  if (error && !data) {
    return (
      <div style={{ padding: '30px', textAlign: 'center', color: '#ef4444' }}>
        <p>Dashboard unavailable: {error}</p>
        <button onClick={loadData} style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '6px 14px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const milkingCount = Number(data.milkingAnimals) || 1;
  const todayYield = Number(data.todayLiters) || 0;
  const avgYieldPerAnimal = (todayYield / milkingCount).toFixed(1);
  const cmplValue = "43.75"; 

  const currentDateLabel = data.todayDate || "2026-08-19";
  const priorDateLabel = data.yesterdayDate || "2026-08-18";

  return (
    <div className="cmd-dash-wrapper" style={{ height: 'calc(100vh - 75px)', overflowY: 'hidden', display: 'flex', flexDirection: 'column', boxSizing: 'border-box', padding: '10px' }}>
      <div className="cmd-content-grid" style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '10px', flex: 1, minHeight: 0 }}>
        
        {/* COLUMN 1: Prominent Milk Production (Top) & Herd Development (Bottom) */}
        <div className="cmd-col" style={{ display: 'flex', flexDirection: 'column', gap: '10px', minHeight: 0 }}>
          
          {/* 1. MILK PRODUCTION (Prominent Top Portion) */}
          <div className="cmd-card" style={{ flex: '1.6', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0 }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('milk')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', fontWeight: 'bold', fontSize: '13px', cursor: 'pointer', marginBottom: '6px' }}>
              <Milk size={16} /> <span>Milk Production →</span>
            </div>
            
            {/* 5-part KPI row */}
            <div className="stat-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '4px', marginBottom: '6px' }}>
              <div className="stat-box" style={{ background: '#1e293b', padding: '5px', borderRadius: '6px' }}><div className="stat-lbl" style={{ fontSize: '8px', color: '#94a3b8' }}>Milking Animals</div><div className="stat-val" style={{ fontSize: '12px', fontWeight: 'bold', color: '#fff' }}>{data.milkingAnimals}</div></div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '5px', borderRadius: '6px' }}><div className="stat-lbl" style={{ fontSize: '8px', color: '#94a3b8' }}>Total Adults</div><div className="stat-val" style={{ fontSize: '12px', fontWeight: 'bold', color: '#fff' }}>{data.adultAnimals}</div></div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '5px', borderRadius: '6px' }}><div className="stat-lbl" style={{ fontSize: '8px', color: '#94a3b8' }}>Milking %</div><div className="stat-val" style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399' }}>{data.milkingPercentage}%</div></div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '5px', borderRadius: '6px' }}><div className="stat-lbl" style={{ fontSize: '8px', color: '#94a3b8' }}>Avg Yield/Cow</div><div className="stat-val" style={{ fontSize: '12px', fontWeight: 'bold', color: '#38bdf8' }}>{avgYieldPerAnimal} L</div></div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '5px', borderRadius: '6px', borderLeft: '2px solid #34d399', cursor: 'pointer' }} onClick={() => onNavigate && onNavigate('cmpl')} title="Cost of Milk Production per Liter"><div className="stat-lbl" style={{ fontSize: '8px', color: '#34d399' }}>CMPL (PKR)</div><div className="stat-val" style={{ fontSize: '12px', fontWeight: 'bold', color: '#34d399' }}>{cmplValue}</div></div>
            </div>
            
            {/* Explicit Date Yield row */}
            <div className="stat-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '6px' }}>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}><div className="stat-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>{currentDateLabel}</div><div className="stat-val" style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff' }}>{data.todayLiters} L</div></div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}><div className="stat-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>{priorDateLabel}</div><div className="stat-val" style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff' }}>{data.yesterdayLiters} L</div></div>
            </div>

            <div className="graph-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
              <span className="graph-title" style={{ fontSize: '10px', color: '#94a3b8' }}>📈 Farm Yield Trend ({chartDays} Days Denominator)</span>
              <select value={chartDays} onChange={(e) => setChartDays(Number(e.target.value))} style={{ background: '#161f30', color: '#cbd5e1', border: '1px solid #374151', borderRadius: '4px', fontSize: '9px', padding: '2px 4px', outline: 'none' }}>
                <option value={7}>7 Days</option><option value={15}>15 Days</option><option value={30}>30 Days</option>
              </select>
            </div>
            <div style={{ flex: 1, minHeight: '70px', paddingBottom: '16px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={filteredYieldTrend} margin={{ top: 2, right: 10, left: -20, bottom: 16 }}>
                  <defs><linearGradient id="colorY" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#38bdf8" stopOpacity={0.5}/><stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/></linearGradient></defs>
                  <XAxis dataKey="dayIndex" stroke="#64748b" tick={{ fontSize: 9 }} interval={0} tickFormatter={(val) => `Day ${val}`} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 8 }} domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} labelFormatter={(val) => `Day ${val}`} />
                  <Area type="monotone" dataKey="yield" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#colorY)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 3. HERD DEVELOPMENT (Bottom Left Section) */}
          <div className="cmd-card" style={{ flex: '1', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0, overflow: 'hidden' }}>
            <div className="cmd-card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span className="clickable-title" onClick={() => onNavigate && onNavigate('animals')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f59e0b', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer' }}>
                🐮 <span>Herd Development →</span>
              </span>
            </div>
            <div className="herd-table-wrapper" style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
              <table className="herd-table" style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937' }}>
                    <th style={{ textAlign: 'left', padding: '4px' }}>Category</th>
                    <th style={{ textAlign: 'right', padding: '4px' }}>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {data.herdComposition.map(c => (
                    <tr key={c.name} style={{ borderBottom: '1px solid #1a2234' }}>
                      <td style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px', color: '#e2e8f0' }}>
                        <div style={{ width: '7px', height: '7px', backgroundColor: c.color, borderRadius: '2px' }}/> {c.name}
                      </td>
                      <td style={{ fontWeight: 800, textAlign: 'right', padding: '4px', color: '#fff' }}>{c.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* COLUMN 2: Production Extremes (Top) & Bottom Three Sections (Health, Reproduction) */}
        <div className="cmd-col" style={{ display: 'flex', flexDirection: 'column', gap: '10px', minHeight: 0 }}>
          
          {/* 2. PRODUCTION EXTREMES (Top Right Section) */}
          <div className="cmd-card" style={{ flex: '0.9', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0 }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('milk')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer', marginBottom: '6px' }}>
              <Sparkles size={15} /> <span>Production Extremes →</span>
            </div>
            <div className="performers-split" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', flex: 1, minHeight: 0 }}>
              <div className="performer-list" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', overflowY: 'auto' }}>
                <div style={{ fontSize: '9px', color: '#34d399', fontWeight: 800, textTransform: 'uppercase', marginBottom: '3px' }}>Top Performers</div>
                <div className="performer-items" style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {data.topPerformers.map(p => (
                    <div className="perf-item" key={p.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}><button className="perf-tag" onClick={() => openPassport(p.id)} style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', padding: 0, fontWeight: 'bold' }}>#{p.id}</button><span style={{ color: '#e2e8f0' }}>{p.yield} L</span></div>
                  ))}
                </div>
              </div>
              <div className="performer-list" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', overflowY: 'auto' }}>
                <div style={{ fontSize: '9px', color: '#ef4444', fontWeight: 800, textTransform: 'uppercase', marginBottom: '3px' }}>Bottom Performers</div>
                <div className="performer-items" style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {data.bottomPerformers.map(p => (
                    <div className="perf-item" key={p.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}><button className="perf-tag" onClick={() => openPassport(p.id)} style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', padding: 0, fontWeight: 'bold' }}>#{p.id}</button><span style={{ color: '#e2e8f0' }}>{p.yield} L</span></div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 4. HEALTH & VACCINATION (Bottom Right Middle Section) */}
          <div className="cmd-card" style={{ flex: '0.9', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0 }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('health')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer', marginBottom: '6px' }}>
              <HeartPulse size={15} /> <span>Health & Vaccination →</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, justifyContent: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '6px 8px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ background: '#ef4444', color: '#fff', fontSize: '8px', fontWeight: 'bold', padding: '2px 4px', borderRadius: '4px' }}>SICK</span>
                  <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#fca5a5' }}>{data.health.sick} ANIMALS</span>
                </div>
                <div style={{ fontSize: '9px', color: '#f87171' }}>Mastitis: {data.health.mastitis} | Temp: {data.health.highTemp}</div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '6px 8px', borderRadius: '6px' }}>
                <span style={{ fontSize: '10px', fontWeight: 'bold', color: '#fcd34d' }}>💉 VACCINATION</span>
                <div style={{ fontSize: '9px', color: '#cbd5e1' }}>Done: <strong>{data.health.completedVax}</strong> | Due: <strong style={{ color: '#fcd34d' }}>{data.health.dueVax}</strong></div>
              </div>
            </div>
          </div>

          {/* 5. REPRODUCTIVE HEALTH (Bottom Right Lower Section) */}
          <div className="cmd-card" style={{ flex: '0.9', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0 }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('breeding')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fb923c', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer', marginBottom: '6px' }}>
              <Activity size={15} /> <span>Reproductive Health →</span>
            </div>
            <div className="repro-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', flex: 1, alignItems: 'center' }}>
              <div className="repro-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', textAlign: 'center' }}><div className="repro-val" style={{ color: '#fb923c', fontSize: '13px', fontWeight: 'bold' }}>{data.reproduction.onHeat}</div><div className="repro-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>On Heat</div></div>
              <div className="repro-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', textAlign: 'center' }}><div className="repro-val" style={{ color: '#60a5fa', fontSize: '13px', fontWeight: 'bold' }}>{data.reproduction.inseminated}</div><div className="repro-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>Inseminated</div></div>
              <div className="repro-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', textAlign: 'center' }}><div className="repro-val" style={{ color: '#a78bfa', fontSize: '13px', fontWeight: 'bold' }}>{data.reproduction.pregnant}</div><div className="repro-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>Pregnant</div></div>
            </div>
          </div>

        </div>
      </div>

      {passportTag && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 10000, display: 'flex', justifyContent: 'flex-end' }}>
          <div style={{ width: '400px', background: '#111827', borderLeft: '1px solid #374151', padding: '20px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 20px 0', paddingBottom: '16px', borderBottom: '1px solid #1f2937' }}>
              <h3 style={{ margin: 0, fontSize: '16px', color: '#fff' }}>Passport: <span style={{ color: '#38bdf8' }}>#{passportTag}</span></h3>
              <button onClick={() => setPassportTag(null)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={20} /></button>
            </div>
            <div style={{ flex: 1, color: '#94a3b8', fontSize: '13px' }}>
              {passportData ? (
                <div>
                  <p><strong>Status:</strong> {passportData.animal?.lifecycle_status || 'Active'}</p>
                  <p><strong>Breed:</strong> {passportData.animal?.breed || 'N/A'}</p>
                  <p><strong>Records:</strong> {passportData.record_counts ? Object.keys(passportData.record_counts).length : 0} categories tracked</p>
                </div>
              ) : 'Syncing records...'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
