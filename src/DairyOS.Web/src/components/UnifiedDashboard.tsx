import { useEffect, useState, useCallback, useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Milk, Activity, HeartPulse, Sparkles, AlertTriangle, AlertCircle, PlusCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import { fetchCommandDashboardData, type CommandDashboardData } from '../api/commandDashboardClient';
import { useAlertAudit } from '../context/AlertAuditContext';
import AnimalPassportModal from './AnimalPassportModal';
import './UnifiedDashboard.css';

interface Props { 
  onNavigate?: (view: string) => void;
  onOpenYieldModal?: () => void;
  onOpenPassport?: (id: string) => void;
}

export default function UnifiedDashboard({ onNavigate, onOpenYieldModal, onOpenPassport }: Props) {
  const [data, setData] = useState<CommandDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartDays, setChartDays] = useState<number>(7);
  const [extremesCount, setExtremesCount] = useState<number>(3); // Default 3
  const [passportTag, setPassportTag] = useState<string | null>(null);

  const { alerts, markResolved } = useAlertAudit();

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCommandDashboardData();
      if (res && res.herdComposition) {
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

  const filteredYieldTrend = useMemo(() => {
    if (!data || !Array.isArray(data.yieldTrend)) return [];
    const sliced = data.yieldTrend.slice(-chartDays);
    return sliced.map((item, index) => ({
      ...item,
      dayIndex: index + 1
    }));
  }, [data, chartDays]);

  const openPassportHandler = (tag: string) => {
    if (onOpenPassport) onOpenPassport(tag);
    else setPassportTag(tag);
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

  const currentDateLabel = data.todayDate || "2026-08-20";
  const priorDateLabel = data.yesterdayDate || "2026-08-19";

  const herdCol1 = (data.herdComposition || []).slice(0, 3);
  const herdCol2 = (data.herdComposition || []).slice(3, 6);

  // Maximum selectable extremes count is 50% of total milking herd (minimum 1)
  const maxExtremesAllowed = Math.max(1, Math.floor(milkingCount * 0.5));

  // Generate selectable dropdown values (e.g. 1, 2, 3, 4, 5, 6... up to 50% of herd)
  const extremesOptions: number[] = [];
  for (let i = 1; i <= Math.min(maxExtremesAllowed, 10); i++) {
    extremesOptions.push(i);
  }
  if (maxExtremesAllowed > 10 && !extremesOptions.includes(maxExtremesAllowed)) {
    if (maxExtremesAllowed >= 15) extremesOptions.push(15);
    extremesOptions.push(maxExtremesAllowed);
  }

  // Expanded fallback pool for demonstration if API provides fewer items
  const allTopPerformers = [
    { id: 'TD-009', yield: 44.5 },
    { id: 'TD-001', yield: 38.5 },
    { id: 'TD-014', yield: 37.0 },
    { id: 'TD-002', yield: 36.2 },
    { id: 'TD-021', yield: 35.8 },
    { id: 'TD-025', yield: 35.0 },
    { id: 'TD-028', yield: 34.6 },
    { id: 'TD-031', yield: 34.0 }
  ];

  const allBottomPerformers = [
    { id: 'TD-004', yield: 18.0 },
    { id: 'TD-018', yield: 21.5 },
    { id: 'TD-003', yield: 24.0 },
    { id: 'TD-012', yield: 25.5 },
    { id: 'TD-022', yield: 26.0 },
    { id: 'TD-027', yield: 26.8 },
    { id: 'TD-030', yield: 27.2 },
    { id: 'TD-033', yield: 27.9 }
  ];

  const displayedTop = (data.topPerformers && data.topPerformers.length >= extremesCount ? data.topPerformers : allTopPerformers).slice(0, extremesCount);
  const displayedBottom = (data.bottomPerformers && data.bottomPerformers.length >= extremesCount ? data.bottomPerformers : allBottomPerformers).slice(0, extremesCount);

  // Active Drop Alerts from Audit Ledger
  const activeDropAlerts = alerts.filter(a => a.source === 'MILK_DROP' && a.status !== 'RESOLVED');

  return (
    <div className="cmd-dash-wrapper" style={{ height: 'calc(100vh - 75px)', overflowY: 'hidden', display: 'flex', flexDirection: 'column', boxSizing: 'border-box', padding: '10px' }}>
      <div className="cmd-content-grid" style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '10px', flex: 1, minHeight: 0 }}>

        {/* COLUMN 1 */}
        <div className="cmd-col" style={{ display: 'flex', flexDirection: 'column', gap: '10px', minHeight: 0 }}>

          {/* 1. MILK PRODUCTION SECTION */}
          <div className="cmd-card" style={{ flex: '1.6', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0 }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('milk')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', fontWeight: 'bold', fontSize: '13px', cursor: 'pointer', marginBottom: '8px' }}>
              <Milk size={16} /> <span>Milk Production & Farm Yield →</span>
            </div>

            {/* KPI row */}
            <div className="stat-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px', marginBottom: '8px' }}>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px' }}>
                <div className="stat-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>Milking Animals</div>
                <div className="stat-val" style={{ fontSize: '14px', fontWeight: 'bold', color: '#fff' }}>{data.milkingAnimals}</div>
              </div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px' }}>
                <div className="stat-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>Total Adults</div>
                <div className="stat-val" style={{ fontSize: '14px', fontWeight: 'bold', color: '#fff' }}>{data.adultAnimals}</div>
              </div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px' }}>
                <div className="stat-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>Milking %</div>
                <div className="stat-val" style={{ fontSize: '14px', fontWeight: 'bold', color: '#34d399' }}>{data.milkingPercentage}%</div>
              </div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px' }}>
                <div className="stat-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>Avg Yield/Cow</div>
                <div className="stat-val" style={{ fontSize: '14px', fontWeight: 'bold', color: '#38bdf8' }}>{avgYieldPerAnimal} L</div>
              </div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', borderLeft: '2px solid #34d399', cursor: 'pointer' }} onClick={() => onNavigate && onNavigate('cmpl')} title="Cost of Milk Production per Liter">
                <div className="stat-lbl" style={{ fontSize: '9px', color: '#34d399' }}>CMPL (PKR)</div>
                <div className="stat-val" style={{ fontSize: '14px', fontWeight: 'bold', color: '#34d399' }}>{cmplValue}</div>
              </div>
            </div>

            {/* Farm Yield Date row */}
            <div className="stat-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px 10px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
                <div className="stat-lbl" style={{ fontSize: '10px', color: '#94a3b8' }}>{currentDateLabel} (Total Farm Yield)</div>
                <div className="stat-val" style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff' }}>{data.todayLiters} L</div>
              </div>
              <div className="stat-box" style={{ background: '#1e293b', padding: '6px 10px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
                <div className="stat-lbl" style={{ fontSize: '10px', color: '#94a3b8' }}>{priorDateLabel} (Prior Farm Yield)</div>
                <div className="stat-val" style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff' }}>{data.yesterdayLiters} L</div>
              </div>
            </div>

            {/* 2-PART SPLIT */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.05fr 0.95fr', gap: '8px', flex: 1, minHeight: 0 }}>
              
              <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: '6px', padding: '6px 8px', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <div className="graph-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span className="graph-title" style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 'bold' }}>📈 Total Farm Yield Trend</span>
                  <select value={chartDays} onChange={(e) => setChartDays(Number(e.target.value))} style={{ background: '#161f30', color: '#cbd5e1', border: '1px solid #374151', borderRadius: '4px', fontSize: '9px', padding: '1px 4px', outline: 'none' }}>
                    <option value={7}>7 Days</option>
                    <option value={15}>15 Days</option>
                    <option value={30}>30 Days</option>
                  </select>
                </div>
                <div style={{ flex: 1, minHeight: '65px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={filteredYieldTrend} margin={{ top: 2, right: 6, left: -24, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorY" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.5}/>
                          <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="dayIndex" stroke="#64748b" tick={{ fontSize: 8 }} interval={0} tickFormatter={(val) => `D${val}`} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 8 }} domain={['auto', 'auto']} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '10px', padding: '4px 8px' }} labelFormatter={(val) => `Day ${val}`} />
                      <Area type="monotone" dataKey="yield" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#colorY)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* AUDITED YIELD DROP WATCHLIST WITH RESOLVE ACTION */}
              <div style={{ background: '#0b1120', border: '1px solid #1e293b', borderRadius: '6px', padding: '6px 8px', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '10px', fontWeight: 'bold', color: '#f87171', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <AlertTriangle size={11} /> Yield Drop Watchlist ({activeDropAlerts.length})
                  </span>
                  <span style={{ fontSize: '8px', color: '#94a3b8' }}>Click ✓ to Resolve</span>
                </div>
                
                <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {activeDropAlerts.length === 0 ? (
                    <div style={{ fontSize: '10px', color: '#34d399', textAlign: 'center', padding: '12px 0' }}>
                      ✓ All yield drop warnings resolved
                    </div>
                  ) : (
                    activeDropAlerts.map((item) => {
                      const isReinstated = item.status === 'REINSTATED';
                      return (
                        <div 
                          key={item.id} 
                          style={{ 
                            background: isReinstated ? 'rgba(239, 68, 68, 0.35)' : '#161f30', 
                            borderLeft: `3px solid ${isReinstated ? '#dc2626' : (item.currentLevel === 'RED' ? '#ef4444' : '#f59e0b')}`, 
                            border: isReinstated ? '1px solid #ef4444' : 'none',
                            padding: '3px 6px', 
                            borderRadius: '4px', 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            alignItems: 'center',
                            fontSize: '10px'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                            {item.animalId && (
                              <button 
                                onClick={() => openPassportHandler(item.animalId!)} 
                                style={{ background: 'none', border: 'none', color: isReinstated ? '#fff' : '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, fontSize: '10px', textDecoration: 'underline' }}
                                title="Open Biological Passport"
                              >
                                #{item.animalId}
                              </button>
                            )}
                            <span style={{ color: isReinstated ? '#fee2e2' : '#cbd5e1', fontSize: '9px', fontWeight: isReinstated ? 'bold' : 'normal' }}>
                              {item.title}
                            </span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <button 
                              onClick={() => markResolved(item.id, 'Ammad Hassan', 'Resolved via Dashboard Watchlist')}
                              style={{ background: '#059669', color: '#fff', border: 'none', padding: '2px 5px', borderRadius: '3px', fontSize: '9px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '2px' }}
                              title="Mark this drop warning as resolved (registers date, time & operator)"
                            >
                              <CheckCircle2 size={10} /> Resolve
                            </button>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

            </div>
          </div>

          {/* 3. HERD DEVELOPMENT */}
          <div className="cmd-card" style={{ flex: '1', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0, overflow: 'hidden' }}>
            <div className="cmd-card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span className="clickable-title" onClick={() => onNavigate && onNavigate('animals')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f59e0b', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer' }}>
                🐮 <span>Herd Development Register →</span>
              </span>
            </div>
            <div className="herd-table-wrapper" style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', minHeight: 0 }}>
              
              <table className="herd-table" style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937' }}>
                    <th style={{ textAlign: 'left', padding: '3px' }}>Category</th>
                    <th style={{ textAlign: 'right', padding: '3px' }}>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {herdCol1.map(c => (
                    <tr key={c.name} style={{ borderBottom: '1px solid #1a2234' }}>
                      <td style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px', color: '#e2e8f0' }}>
                        <div style={{ width: '6px', height: '6px', backgroundColor: c.color, borderRadius: '2px' }}/> {c.name}
                      </td>
                      <td style={{ fontWeight: 800, textAlign: 'right', padding: '4px', color: '#fff' }}>{c.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <table className="herd-table" style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937' }}>
                    <th style={{ textAlign: 'left', padding: '3px' }}>Category</th>
                    <th style={{ textAlign: 'right', padding: '3px' }}>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {herdCol2.map(c => (
                    <tr key={c.name} style={{ borderBottom: '1px solid #1a2234' }}>
                      <td style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px', color: '#e2e8f0' }}>
                        <div style={{ width: '6px', height: '6px', backgroundColor: c.color, borderRadius: '2px' }}/> {c.name}
                      </td>
                      <td style={{ fontWeight: 800, textAlign: 'right', padding: '4px', color: '#fff' }}>{c.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

            </div>
          </div>
        </div>

        {/* COLUMN 2 */}
        <div className="cmd-col" style={{ display: 'flex', flexDirection: 'column', gap: '10px', minHeight: 0 }}>

          {/* 2. PRODUCTION EXTREMES WITH DYNAMIC 50% HERD DROPDOWN */}
          <div className="cmd-card" style={{ flex: '0.85', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0 }}>
            <div className="cmd-card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span className="clickable-title" onClick={() => onNavigate && onNavigate('milk')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer' }}>
                <Sparkles size={15} /> <span>Production Extremes →</span>
              </span>

              {/* Dynamic Dropdown for number of animals (Max 50% of Milking Herd) */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ fontSize: '9px', color: '#94a3b8' }}>Show:</span>
                <select 
                  value={extremesCount} 
                  onChange={(e) => setExtremesCount(Number(e.target.value))}
                  style={{ 
                    background: '#161f30', 
                    color: '#34d399', 
                    border: '1px solid #334155', 
                    borderRadius: '4px', 
                    fontSize: '9px', 
                    fontWeight: 'bold',
                    padding: '1px 5px', 
                    outline: 'none',
                    cursor: 'pointer'
                  }}
                  title={`Select number of extreme performers (Max 50% of milking herd = ${maxExtremesAllowed})`}
                >
                  {extremesOptions.map(n => (
                    <option key={n} value={n}>
                      {n} {n === 1 ? 'Cow' : 'Cows'} {n === 3 ? '(Default)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Split List */}
            <div className="performers-split" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', flex: 1, minHeight: 0 }}>
              <div className="performer-list" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', overflowY: 'auto' }}>
                <div style={{ fontSize: '9px', color: '#34d399', fontWeight: 800, textTransform: 'uppercase', marginBottom: '4px' }}>Top Performers ({displayedTop.length})</div>
                <div className="performer-items" style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {displayedTop.map(p => (
                    <div className="perf-item" key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px' }}>
                      <button 
                        className="perf-tag" 
                        onClick={() => openPassportHandler(p.id)} 
                        style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', padding: 0, fontWeight: 'bold', textDecoration: 'underline', fontSize: '10px' }}
                        title="Open Biological Passport"
                      >
                        #{p.id}
                      </button>
                      <span style={{ color: '#cbd5e1', fontSize: '10px', fontWeight: 'bold' }}>{p.yield} L</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="performer-list" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', overflowY: 'auto' }}>
                <div style={{ fontSize: '9px', color: '#ef4444', fontWeight: 800, textTransform: 'uppercase', marginBottom: '4px' }}>Bottom Performers ({displayedBottom.length})</div>
                <div className="performer-items" style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {displayedBottom.map(p => (
                    <div className="perf-item" key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px' }}>
                      <button 
                        className="perf-tag" 
                        onClick={() => openPassportHandler(p.id)} 
                        style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', padding: 0, fontWeight: 'bold', textDecoration: 'underline', fontSize: '10px' }}
                        title="Open Biological Passport"
                      >
                        #{p.id}
                      </button>
                      <span style={{ color: '#cbd5e1', fontSize: '10px', fontWeight: 'bold' }}>{p.yield} L</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 4. HEALTH & VACCINATION */}
          <div className="cmd-card" style={{ flex: '0.85', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0 }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('health')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer', marginBottom: '6px' }}>
              <HeartPulse size={15} /> <span>Health & Treatments →</span>
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

          {/* 5. REPRODUCTIVE HEALTH */}
          <div className="cmd-card" style={{ flex: '0.85', display: 'flex', flexDirection: 'column', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '10px', minHeight: 0 }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('breeding')} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fb923c', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer', marginBottom: '6px' }}>
              <Activity size={15} /> <span>Reproductive Health →</span>
            </div>
            <div className="repro-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', flex: 1, alignItems: 'center' }}>
              <div className="repro-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', textAlign: 'center' }}><div className="repro-val" style={{ color: '#fb923c', fontSize: '13px', fontWeight: 'bold' }}>{data.reproduction.onHeat}</div><div className="repro-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>On Heat</div></div>
              <div className="repro-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', textAlign: 'center' }}><div className="repro-val" style={{ color: '#60a5fa', fontSize: '13px', fontWeight: 'bold' }}>{data.reproduction.inseminated}</div><div className="repro-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>Inseminated</div></div>
              <div className="repro-box" style={{ background: '#1e293b', padding: '6px', borderRadius: '6px', textAlign: 'center' }}><div className="repro-val" style={{ color: '#a78bfa', fontSize: '13px', fontWeight: 'bold' }}>{data.reproduction.pregnant}</div><div className="repro-lbl" style={{ fontSize: '9px', color: '#94a3b8' }}>Pregnant</div></div>
            </div>
          </div>

          {/* ACTION BUTTON */}
          <button 
            onClick={() => {
              if (onOpenYieldModal) onOpenYieldModal();
              else if (onNavigate) onNavigate('milk');
            }}
            style={{ 
              width: '100%', 
              background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)', 
              border: '1px solid #38bdf8', 
              borderRadius: '8px', 
              padding: '10px 14px', 
              cursor: 'pointer', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              boxShadow: '0 4px 12px rgba(2, 132, 199, 0.3)',
              boxSizing: 'border-box'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.2)', borderRadius: '50%', padding: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <PlusCircle size={16} color="#fff" />
              </div>
              <div style={{ textAlign: 'left', lineHeight: '1.2' }}>
                <div style={{ fontSize: '12px', fontWeight: '800', color: '#fff', letterSpacing: '0.3px' }}>Log Individual Animal Yield</div>
                <div style={{ fontSize: '9px', color: '#e0f2fe' }}>Fast 2-field entry • Current time auto-stamped</div>
              </div>
            </div>
            <ArrowRight size={15} color="#fff" />
          </button>

        </div>
      </div>

      {passportTag && (
        <AnimalPassportModal 
          animalId={passportTag} 
          onClose={() => setPassportTag(null)} 
        />
      )}
    </div>
  );
}
