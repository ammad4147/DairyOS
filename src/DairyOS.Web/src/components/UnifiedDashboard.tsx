import { useEffect, useMemo, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { X } from "lucide-react";
import {
  fetchCommandDashboardData,
  type CommandDashboardData,
} from "../api/commandDashboardClient";
import {
  fetchAnimalPassport,
  type AnimalPassportData,
} from "../api/livePassportClient";
import "./UnifiedDashboard.css";

interface Props {
  onNavigate?: (view: string) => void;
}

const PERIODS = [
  { label: "7 Days", days: 7 },
  { label: "15 Days", days: 15 },
  { label: "30 Days", days: 30 },
  { label: "90 Days", days: 90 },
] as const;

export default function UnifiedDashboard({ onNavigate }: Props) {
  const [data, setData] = useState<CommandDashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [chartPeriod, setChartPeriod] = useState("7 Days");
  const [herdView, setHerdView] = useState<"pie" | "table">("pie");
  const [passportTag, setPassportTag] = useState<string | null>(null);
  const [passportData, setPassportData] = useState<AnimalPassportData | null>(null);

  const periodDays = useMemo(
    () => PERIODS.find((period) => period.label === chartPeriod)?.days ?? 7,
    [chartPeriod],
  );

  useEffect(() => {
    let active = true;
    setError(null);

    fetchCommandDashboardData(periodDays)
      .then((result) => {
        if (active) setData(result);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setData(null);
        setError(reason instanceof Error ? reason.message : "Dashboard data unavailable");
      });

    return () => {
      active = false;
    };
  }, [periodDays]);

  const openPassport = async (tag: string) => {
    setPassportTag(tag);
    setPassportData(null);
    try {
      setPassportData(await fetchAnimalPassport(tag));
    } catch {
      setPassportData(null);
    }
  };

  if (error) {
    return (
      <div className="cmd-card" style={{ padding: "24px" }}>
        <div className="cmd-card-title">Dashboard unavailable</div>
        <div style={{ color: "#fca5a5", marginTop: "12px", fontSize: "13px" }}>{error}</div>
      </div>
    );
  }

  if (!data) return <div style={{ padding: "20px" }}>Loading live dashboard data...</div>;

  return (
    <div className="cmd-dash-wrapper">
      <div className="cmd-content-grid">
        <div className="cmd-col">
          <div className="cmd-card" style={{ flex: "1.2" }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate?.("milk")}>
              <span>Milk Production →</span>
            </div>

            <div className="stat-row">
              <div className="stat-box"><div className="stat-lbl">Total Milking Animals</div><div className="stat-val">{data.milkingAnimals}</div></div>
              <div className="stat-box"><div className="stat-lbl">Total Animals</div><div className="stat-val">{data.adultAnimals}</div></div>
              <div className="stat-box"><div className="stat-lbl">Milking Percentage</div><div className="stat-val" style={{ color: "#34d399" }}>{data.milkingPercentage}%</div></div>
            </div>

            <div className="stat-row" style={{ gridTemplateColumns: "1fr 1fr" }}>
              <div className="stat-box" style={{ borderLeft: "3px solid #38bdf8" }}><div className="stat-lbl">Current Date Yield</div><div className="stat-val">{data.todayLiters} L</div></div>
              <div className="stat-box" style={{ borderLeft: "3px solid #94a3b8" }}><div className="stat-lbl">Previous Date Yield</div><div className="stat-val">{data.yesterdayLiters == null ? "—" : `${data.yesterdayLiters} L`}</div></div>
            </div>

            <div className="graph-header">
              <span className="graph-title">Overall Farm Yield Trend</span>
              <select value={chartPeriod} onChange={(event) => setChartPeriod(event.target.value)} style={{ background: "#161f30", color: "#cbd5e1", border: "1px solid #374151", borderRadius: "4px", fontSize: "10px", padding: "2px 4px", outline: "none" }}>
                {PERIODS.map((period) => <option key={period.label}>{period.label}</option>)}
              </select>
            </div>

            <div style={{ flex: 1, minHeight: 0 }}>
              {data.yieldTrend.length === 0 ? (
                <div style={{ padding: "24px", color: "#94a3b8", fontSize: "12px" }}>
                  No milk-production records are available for the selected period.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.yieldTrend} margin={{ top: 5, right: 0, left: -25, bottom: 0 }}>
                    <defs><linearGradient id="colorY" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#38bdf8" stopOpacity={0.5}/><stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/></linearGradient></defs>
                    <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "11px" }} />
                    <Area type="monotone" dataKey="yield" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#colorY)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="cmd-card" style={{ flex: "0.8" }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate?.("milk")}>
              <span>Production Extremes →</span>
            </div>
            <div className="performers-split">
              <div className="performer-list">
                <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 800, textTransform: "uppercase", marginBottom: "4px" }}>Top Performers</div>
                <div className="performer-items">
                  {data.topPerformers.length === 0 ? <span style={{ color: "#64748b", fontSize: "11px" }}>No recorded production.</span> : data.topPerformers.map((p) => (
                    <div className="perf-item" key={p.id}><button className="perf-tag" onClick={() => openPassport(p.id)}>#{p.id}</button><span style={{ color: "#e2e8f0" }}>{p.yield} L</span></div>
                  ))}
                </div>
              </div>
              <div className="performer-list">
                <div style={{ fontSize: "11px", color: "#ef4444", fontWeight: 800, textTransform: "uppercase", marginBottom: "4px" }}>Bottom Performers</div>
                <div className="performer-items">
                  {data.bottomPerformers.length === 0 ? <span style={{ color: "#64748b", fontSize: "11px" }}>No recorded production.</span> : data.bottomPerformers.map((p) => (
                    <div className="perf-item" key={p.id}><button className="perf-tag" onClick={() => openPassport(p.id)}>#{p.id}</button><span style={{ color: "#e2e8f0" }}>{p.yield} L</span></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="cmd-col">
          <div className="cmd-card" style={{ flex: "1.2" }}>
            <div className="cmd-card-title">
              <span className="clickable-title" onClick={() => onNavigate?.("animals")}>Herd Development →</span>
              <div style={{ display: "flex", gap: "4px", background: "#1e293b", padding: "2px", borderRadius: "4px" }}>
                <button onClick={() => setHerdView("pie")} style={{ background: herdView === "pie" ? "#334155" : "transparent", color: herdView === "pie" ? "#fff" : "#94a3b8", border: "none", borderRadius: "2px", fontSize: "10px", padding: "2px 8px", cursor: "pointer" }}>Pie</button>
                <button onClick={() => setHerdView("table")} style={{ background: herdView === "table" ? "#334155" : "transparent", color: herdView === "table" ? "#fff" : "#94a3b8", border: "none", borderRadius: "2px", fontSize: "10px", padding: "2px 8px", cursor: "pointer" }}>Table</button>
              </div>
            </div>

            <div className="herd-table-wrapper">
              {data.herdComposition.length === 0 ? (
                <div style={{ padding: "24px", color: "#94a3b8", fontSize: "12px" }}>No animal records are currently available.</div>
              ) : herdView === "pie" ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={data.herdComposition} innerRadius={35} outerRadius={70} paddingAngle={2} dataKey="value" stroke="none">
                      {data.herdComposition.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                    </Pie>
                    <Legend verticalAlign="middle" align="right" layout="vertical" wrapperStyle={{ fontSize: "11px", color: "#cbd5e1" }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <table className="herd-table">
                  <thead><tr><th>Category</th><th>Count</th></tr></thead>
                  <tbody>
                    {data.herdComposition.map((c) => (
                      <tr key={c.name}>
                        <td style={{ display: "flex", alignItems: "center", gap: "8px" }}><div style={{ width: "8px", height: "8px", backgroundColor: c.color, borderRadius: "2px" }}/> {c.name}</td>
                        <td style={{ fontWeight: 800 }}>{c.value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          <div className="cmd-card" style={{ flex: "0.8" }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate?.("health")}>
              <span>Health & Alerts →</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", flex: 1, justifyContent: "center" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", padding: "12px", borderRadius: "6px" }}>
                <div style={{ fontSize: "12px", fontWeight: "bold", color: "#fca5a5" }}>STATUS</div>
                <div style={{ fontSize: "14px", fontWeight: 800, color: data.health.status === "RED" ? "#ef4444" : data.health.status === "AMBER" ? "#f59e0b" : "#34d399" }}>{data.health.status}</div>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", background: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.3)", padding: "12px", borderRadius: "6px" }}>
                <span style={{ fontSize: "12px", fontWeight: "bold", color: "#fcd34d" }}>ACTIVE EXCEPTIONS</span>
                <strong style={{ color: "#f8fafc" }}>{data.health.activeExceptions}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", background: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.2)", padding: "12px", borderRadius: "6px" }}>
                <span style={{ fontSize: "12px", fontWeight: "bold", color: "#fca5a5" }}>CRITICAL CASES</span>
                <strong style={{ color: "#f8fafc" }}>{data.health.criticalCases}</strong>
              </div>
            </div>
          </div>

          <div className="cmd-card" style={{ flex: "1" }}>
            <div className="cmd-card-title clickable-title" onClick={() => onNavigate?.("breeding")}>
              <span>Reproductive Health →</span>
            </div>
            <div className="repro-row" style={{ flex: 1, alignItems: "center" }}>
              <div className="repro-box"><div className="repro-val" style={{ color: "#94a3b8" }}>—</div><div className="repro-lbl">On Heat</div></div>
              <div className="repro-box"><div className="repro-val" style={{ color: "#94a3b8" }}>—</div><div className="repro-lbl">Inseminated</div></div>
              <div className="repro-box"><div className="repro-val" style={{ color: "#94a3b8" }}>—</div><div className="repro-lbl">Pregnant</div></div>
            </div>
            <div style={{ padding: "0 12px 12px", color: "#94a3b8", fontSize: "11px" }}>
              Reproductive summary is not currently exposed by the dashboard contract; use the Breeding module for authoritative state.
            </div>
          </div>
        </div>
      </div>

      {passportTag && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 10000, display: "flex", justifyContent: "flex-end" }}>
          <div style={{ width: "400px", background: "#111827", borderLeft: "1px solid #374151", padding: "20px", display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "0 0 20px 0", paddingBottom: "16px", borderBottom: "1px solid #1f2937" }}>
              <h3 style={{ margin: 0, fontSize: "16px", color: "#fff" }}>Passport: <span style={{ color: "#38bdf8" }}>#{passportTag}</span></h3>
              <button onClick={() => setPassportTag(null)} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer" }}><X size={20} /></button>
            </div>
            <div style={{ flex: 1, color: "#94a3b8", fontSize: "13px" }}>
              {passportData ? "Live records loaded." : "No passport record loaded."}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
