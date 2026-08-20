import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { X } from 'lucide-react';
import { fetchCommandDashboardData, type CommandDashboardData } from '../api/commandDashboardClient';
import { fetchAnimalPassport, type AnimalPassportData } from '../api/livePassportClient';
import './UnifiedDashboard.css';

interface Props { onNavigate?: (view: string) => void; }

export default function UnifiedDashboard({ onNavigate }: Props) {
  const [data, setData] = useState<CommandDashboardData | null>(null);
  const [chartPeriod, setChartPeriod] = useState('7 Days');
  const [herdView, setHerdView] = useState<'pie' | 'table'>('pie');
  const [passportTag, setPassportTag] = useState<string | null>(null);
  const [passportData, setPassportData] = useState<AnimalPassportData | null>(null);

  useEffect(() => { fetchCommandDashboardData().then(setData); }, []);

  const openPassport = async (tag: string) => {
    setPassportTag(tag);
    setPassportData(await fetchAnimalPassport(tag));
  };

  if (!data) return <div style={{ padding: '20px' }}>Loading Data...</div>;

  return (
    <div className="cmd-dash-wrapper">
      <div className="cmd-content-grid">
        
        {/* LEFT COLUMN */}
        <div className="cmd-col">
          {/* MILK PRODUCTION */}
          <div className="cmd-card" style={{ flex: '1.2' }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('milk')}>
              <span>Milk Production →</span>
            </div>
            
            <div className="stat-row">
              <div className="stat-box"><div className="stat-lbl">Total Milking Animals</div><div className="stat-val">{data.milkingAnimals}</div></div>
              <div className="stat-box"><div className="stat-lbl">Total Adult Animals</div><div className="stat-val">{data.adultAnimals}</div></div>
              <div className="stat-box"><div className="stat-lbl">Milking Percentage</div><div className="stat-val" style={{ color: '#34d399' }}>{data.milkingPercentage}%</div></div>
            </div>
            <div className="stat-row" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <div className="stat-box" style={{ borderLeft: '3px solid #38bdf8' }}><div className="stat-lbl">Current Date Yield</div><div className="stat-val">{data.todayLiters} L</div></div>
              <div className="stat-box" style={{ borderLeft: '3px solid #94a3b8' }}><div className="stat-lbl">Last Date Yield</div><div className="stat-val">{data.yesterdayLiters} L</div></div>
            </div>

            <div className="graph-header">
              <span className="graph-title">Overall Farm Yield Trend</span>
              <select value={chartPeriod} onChange={(e) => setChartPeriod(e.target.value)} style={{ background: '#161f30', color: '#cbd5e1', border: '1px solid #374151', borderRadius: '4px', fontSize: '10px', padding: '2px 4px', outline: 'none' }}>
                <option>7 Days</option><option>15 Days</option><option>30 Days</option><option>90 Days</option>
              </select>
            </div>
            <div style={{ flex: 1, minHeight: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.yieldTrend} margin={{ top: 5, right: 0, left: -25, bottom: 0 }}>
                  <defs><linearGradient id="colorY" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#38bdf8" stopOpacity={0.5}/><stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/></linearGradient></defs>
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                  <Area type="monotone" dataKey="yield" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#colorY)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* EXTREMES */}
          <div className="cmd-card" style={{ flex: '0.8' }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('milk')}>
              <span>Production Extremes →</span>
            </div>
            <div className="performers-split">
              <div className="performer-list">
                <div style={{ fontSize: '11px', color: '#34d399', fontWeight: 800, textTransform: 'uppercase', marginBottom: '4px' }}>Top Performers</div>
                <div className="performer-items">
                  {data.topPerformers.map(p => (
                    <div className="perf-item" key={p.id}><button className="perf-tag" onClick={() => openPassport(p.id)}>#{p.id}</button><span style={{ color: '#e2e8f0' }}>{p.yield} L</span></div>
                  ))}
                </div>
              </div>
              <div className="performer-list">
                <div style={{ fontSize: '11px', color: '#ef4444', fontWeight: 800, textTransform: 'uppercase', marginBottom: '4px' }}>Bottom Performers</div>
                <div className="performer-items">
                  {data.bottomPerformers.map(p => (
                    <div className="perf-item" key={p.id}><button className="perf-tag" onClick={() => openPassport(p.id)}>#{p.id}</button><span style={{ color: '#e2e8f0' }}>{p.yield} L</span></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="cmd-col">
          {/* HERD */}
          <div className="cmd-card" style={{ flex: '1.2' }}>
            <div className="cmd-card-title">
              <span className="clickable-title" onClick={() => onNavigate && onNavigate('animals')}>Herd Development →</span>
              <div style={{ display: 'flex', gap: '4px', background: '#1e293b', padding: '2px', borderRadius: '4px' }}>
                <button onClick={() => setHerdView('pie')} style={{ background: herdView === 'pie' ? '#334155' : 'transparent', color: herdView === 'pie' ? '#fff' : '#94a3b8', border: 'none', borderRadius: '2px', fontSize: '10px', padding: '2px 8px', cursor: 'pointer' }}>Pie</button>
                <button onClick={() => setHerdView('table')} style={{ background: herdView === 'table' ? '#334155' : 'transparent', color: herdView === 'table' ? '#fff' : '#94a3b8', border: 'none', borderRadius: '2px', fontSize: '10px', padding: '2px 8px', cursor: 'pointer' }}>Table</button>
              </div>
            </div>
            
            <div className="herd-table-wrapper">
              {herdView === 'pie' ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={data.herdComposition} innerRadius={35} outerRadius={70} paddingAngle={2} dataKey="value" stroke="none">
                      {data.herdComposition.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                    </Pie>
                    <Legend verticalAlign="middle" align="right" layout="vertical" wrapperStyle={{ fontSize: '11px', color: '#cbd5e1' }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <table className="herd-table">
                  <thead><tr><th>Category</th><th>Count</th></tr></thead>
                  <tbody>
                    {data.herdComposition.map(c => (
                      <tr key={c.name}>
                        <td style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '8px', height: '8px', backgroundColor: c.color, borderRadius: '2px' }}/> {c.name}</td>
                        <td style={{ fontWeight: 800 }}>{c.value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* HEALTH */}
          <div className="cmd-card" style={{ flex: '0.8' }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('health')}>
              <span>Health & Vaccination →</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, justifyContent: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '12px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ background: '#ef4444', color: '#fff', fontSize: '10px', fontWeight: 'bold', padding: '2px 6px', borderRadius: '4px' }}>SICK</span>
                  <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#fca5a5' }}>{data.health.sick} ANIMALS</span>
                </div>
                <div style={{ fontSize: '11px', color: '#f87171' }}>Mastitis: {data.health.mastitis} | Temp: {data.health.highTemp}</div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '12px', borderRadius: '6px' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#fcd34d' }}>VACCINATION</span>
                <div style={{ fontSize: '11px', color: '#cbd5e1' }}>Done: <strong>{data.health.completedVax}</strong> | Due: <strong style={{ color: '#fcd34d' }}>{data.health.dueVax}</strong></div>
              </div>
            </div>
          </div>

          {/* REPRODUCTION */}
          <div className="cmd-card" style={{ flex: '1' }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate && onNavigate('breeding')}>
              <span>Reproductive Health →</span>
            </div>
            <div className="repro-row" style={{ flex: 1, alignItems: 'center' }}>
              <div className="repro-box"><div className="repro-val" style={{ color: '#fb923c' }}>{data.reproduction.onHeat}</div><div className="repro-lbl">On Heat</div></div>
              <div className="repro-box"><div className="repro-val" style={{ color: '#60a5fa' }}>{data.reproduction.inseminated}</div><div className="repro-lbl">Inseminated</div></div>
              <div className="repro-box"><div className="repro-val" style={{ color: '#a78bfa' }}>{data.reproduction.pregnant}</div><div className="repro-lbl">Pregnant</div></div>
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
              {passportData ? 'Live records loaded.' : 'Syncing records...'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
