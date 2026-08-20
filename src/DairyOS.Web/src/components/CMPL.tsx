import React, { useState, useEffect, useCallback } from 'react';
import { Calculator, DollarSign, TrendingUp, TrendingDown, PieChart as PieChartIcon, Settings2, Calendar, AlertTriangle, Link, Edit3, CheckCircle2 } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { fetchCommandDashboardData, type CommandDashboardData } from '../api/commandDashboardClient';

export default function CMPL() {
  const [dataMode, setDataMode] = useState<'AUTO' | 'MANUAL'>('AUTO');
  const [liveData, setLiveData] = useState<CommandDashboardData | null>(null);

  // 1. Timeframe & Core Metrics
  const [periodDays, setPeriodDays] = useState<number>(30);
  const [yieldLiters, setYieldLiters] = useState<number>(48500); 
  const [milkingCows, setMilkingCows] = useState<number>(42);

  // 2. Cost Buckets (Manual / Hybrid Overrides in PKR)
  const [feedCost, setFeedCost] = useState<number>(5200000); 
  const [laborCost, setLaborCost] = useState<number>(450000); 
  const [utilitiesCost, setUtilitiesCost] = useState<number>(180000); 
  const [healthCost, setHealthCost] = useState<number>(120000); 
  const [overheads, setOverheads] = useState<number>(80000); 

  // 3. Multi-Tier Revenue Streams
  const [retailVol, setRetailVol] = useState<number>(20000);
  const [retailPrice, setRetailPrice] = useState<number>(220); 
  const [wholesaleVol, setWholesaleVol] = useState<number>(28500);
  const [wholesalePrice, setWholesalePrice] = useState<number>(180);

  const loadData = useCallback(async () => {
    try {
      const res = await fetchCommandDashboardData();
      setLiveData(res);
    } catch (err) {
      console.warn("Failed to load live data for CMPL", err);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Sync Logic
  useEffect(() => {
    if (dataMode === 'AUTO' && liveData) {
      // Extrapolate daily yield to selected period
      const extrapolatedYield = liveData.todayLiters * periodDays;
      setYieldLiters(extrapolatedYield);
      setMilkingCows(liveData.milkingAnimals);
      
      // Auto-balance default sales to match extrapolated yield
      setWholesaleVol(Math.floor(extrapolatedYield * 0.6));
      setRetailVol(Math.floor(extrapolatedYield * 0.4));
    }
  }, [dataMode, liveData, periodDays]);

  // --- CALCULATIONS ---
  const totalCosts = feedCost + laborCost + utilitiesCost + healthCost + overheads;
  const cmpl = yieldLiters > 0 ? (totalCosts / yieldLiters) : 0;
  
  const totalRevenue = (retailVol * retailPrice) + (wholesaleVol * wholesalePrice);
  const totalSoldVolume = retailVol + wholesaleVol;
  const blendedSalePrice = totalSoldVolume > 0 ? (totalRevenue / totalSoldVolume) : 0;
  
  const marginPerLiter = blendedSalePrice - cmpl;
  const totalProfit = totalRevenue - totalCosts;
  const costPerCowPerDay = (milkingCows > 0 && periodDays > 0) ? (totalCosts / milkingCows / periodDays) : 0;

  // Chart & Sensitivity
  const costDistribution = [
    { name: 'Feed & Fodder', value: feedCost, color: '#38bdf8' },
    { name: 'Labor & Wages', value: laborCost, color: '#f59e0b' },
    { name: 'Utilities & Fuel', value: utilitiesCost, color: '#a855f7' },
    { name: 'Health & Breeding', value: healthCost, color: '#ef4444' },
    { name: 'Overheads', value: overheads, color: '#94a3b8' },
  ];

  const [feedCostSimPct, setFeedCostSimPct] = useState<number>(0);
  const simulatedFeedCost = feedCost * (1 + (feedCostSimPct / 100));
  const simulatedTotalCost = simulatedFeedCost + laborCost + utilitiesCost + healthCost + overheads;
  const simulatedCMPL = yieldLiters > 0 ? (simulatedTotalCost / yieldLiters) : 0;

  const formatPKR = (num: number) => `Rs. ${num.toLocaleString('en-PK', { maximumFractionDigits: 0 })}`;
  const formatCurrency = (num: number) => num.toLocaleString('en-PK', { maximumFractionDigits: 2, minimumFractionDigits: 2 });

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      
      {/* HEADER & SYNC CONTROLS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#34d399', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calculator size={22} /> Cost of Milk Production per Liter (CMPL)
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Calculate break-even points, analyze cost distribution, and track multi-tier revenue margins.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          
          {/* DATA SOURCE TOGGLE */}
          <div style={{ display: 'flex', background: '#0f172a', border: '1px solid #1f2937', borderRadius: '6px', overflow: 'hidden' }}>
            <button 
              onClick={() => setDataMode('AUTO')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', background: dataMode === 'AUTO' ? 'rgba(52, 211, 153, 0.2)' : 'transparent', color: dataMode === 'AUTO' ? '#34d399' : '#64748b', border: 'none', padding: '6px 12px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
            >
              <Link size={14} /> Live Farm Sync
            </button>
            <button 
              onClick={() => setDataMode('MANUAL')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', background: dataMode === 'MANUAL' ? 'rgba(245, 158, 11, 0.2)' : 'transparent', color: dataMode === 'MANUAL' ? '#f59e0b' : '#64748b', border: 'none', borderLeft: '1px solid #1f2937', padding: '6px 12px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer' }}
            >
              <Edit3 size={14} /> Manual Override
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#111827', padding: '6px 12px', borderRadius: '6px', border: '1px solid #1f2937' }}>
            <Calendar size={14} color="#94a3b8" />
            <select 
              value={periodDays} 
              onChange={e => setPeriodDays(Number(e.target.value))}
              style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '4px 8px', borderRadius: '4px', fontSize: '12px', outline: 'none', cursor: 'pointer' }}
            >
              <option value={7}>Last 7 Days</option>
              <option value={15}>Last 15 Days</option>
              <option value={30}>Last 30 Days (Monthly)</option>
              <option value={90}>Quarterly (90 Days)</option>
              <option value={365}>Annual (365 Days)</option>
            </select>
          </div>
        </div>
      </div>

      {dataMode === 'MANUAL' && (
        <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', color: '#fbbf24', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <AlertTriangle size={16} /> <strong>Manual Override Active:</strong> Live farm data linkage is disconnected. You may edit all operational fields directly.
        </div>
      )}

      {/* TOP KPI DASHBOARD */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #ef4444', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 'bold' }}>CMPL (Cost to Produce 1L)</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#f87171' }}>Rs. {formatCurrency(cmpl)}</div>
          <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '4px' }}>Break-even threshold</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #38bdf8', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 'bold' }}>Blended Sale Price</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#38bdf8' }}>Rs. {formatCurrency(blendedSalePrice)}</div>
          <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '4px' }}>Avg across Retail & Wholesale</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: `4px solid ${marginPerLiter >= 0 ? '#34d399' : '#ef4444'}`, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 'bold' }}>Net Margin per Liter</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: marginPerLiter >= 0 ? '#34d399' : '#f87171', display: 'flex', alignItems: 'center', gap: '8px' }}>
            {marginPerLiter >= 0 ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
            Rs. {formatCurrency(marginPerLiter)}
          </div>
          <div style={{ fontSize: '10px', color: marginPerLiter >= 0 ? '#34d399' : '#f87171', marginTop: '4px' }}>
            {marginPerLiter >= 0 ? 'Profitable operation' : 'Operating at a loss'}
          </div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: `4px solid ${totalProfit >= 0 ? '#10b981' : '#dc2626'}`, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 'bold' }}>Period Net Profit / Loss</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: totalProfit >= 0 ? '#10b981' : '#dc2626' }}>
            {totalProfit >= 0 ? '+' : ''}{formatPKR(totalProfit)}
          </div>
          <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '4px' }}>Total Revenue vs Total Costs</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: '20px' }}>
        
        {/* LEFT COLUMN: DATA INPUTS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Production Constants */}
          <div style={{ background: '#111827', border: `1px solid ${dataMode === 'AUTO' ? '#34d399' : '#1f2937'}`, padding: '16px', borderRadius: '8px', position: 'relative' }}>
            {dataMode === 'AUTO' && (
              <div style={{ position: 'absolute', top: '-8px', right: '12px', background: '#34d399', color: '#0f172a', fontSize: '9px', fontWeight: 'bold', padding: '2px 6px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={10}/> AUTO-SYNCED
              </div>
            )}
            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Settings2 size={16} color="#38bdf8" /> Operational Data ({periodDays} Days)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8' }}>Total Milk Yield (Liters) {dataMode === 'AUTO' && <span style={{color: '#34d399'}}>(Extrapolated)</span>}</label>
                <input 
                  type="number" 
                  value={yieldLiters} 
                  onChange={e => setYieldLiters(Number(e.target.value))} 
                  disabled={dataMode === 'AUTO'}
                  style={{ width: '100%', background: dataMode === 'AUTO' ? '#0f172a' : '#1e293b', color: dataMode === 'AUTO' ? '#34d399' : '#38bdf8', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', boxSizing: 'border-box', marginTop: '4px', cursor: dataMode === 'AUTO' ? 'not-allowed' : 'text', opacity: dataMode === 'AUTO' ? 0.8 : 1 }} 
                />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8' }}>Milking Herd Count</label>
                <input 
                  type="number" 
                  value={milkingCows} 
                  onChange={e => setMilkingCows(Number(e.target.value))} 
                  disabled={dataMode === 'AUTO'}
                  style={{ width: '100%', background: dataMode === 'AUTO' ? '#0f172a' : '#1e293b', color: dataMode === 'AUTO' ? '#34d399' : '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '14px', fontWeight: 'bold', boxSizing: 'border-box', marginTop: '4px', cursor: dataMode === 'AUTO' ? 'not-allowed' : 'text', opacity: dataMode === 'AUTO' ? 0.8 : 1 }} 
                />
              </div>
            </div>
          </div>

          {/* Revenue Engine */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
            {/* Keeping rest of Revenue Engine the same as previous */}
            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#34d399', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <DollarSign size={16} /> Multi-Tier Revenue Streams
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '10px' }}>
              <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                <div style={{ fontSize: '11px', color: '#34d399', fontWeight: 'bold', marginBottom: '8px' }}>Retail / Direct Sales</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: '9px', color: '#94a3b8' }}>Volume (L)</label>
                    <input type="number" value={retailVol} onChange={e => setRetailVol(Number(e.target.value))} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: '9px', color: '#94a3b8' }}>Price (PKR/L)</label>
                    <input type="number" value={retailPrice} onChange={e => setRetailPrice(Number(e.target.value))} style={{ width: '100%', background: '#1e293b', color: '#34d399', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                </div>
              </div>
              <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                <div style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 'bold', marginBottom: '8px' }}>Wholesale / Commercial</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: '9px', color: '#94a3b8' }}>Volume (L)</label>
                    <input type="number" value={wholesaleVol} onChange={e => setWholesaleVol(Number(e.target.value))} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: '9px', color: '#94a3b8' }}>Price (PKR/L)</label>
                    <input type="number" value={wholesalePrice} onChange={e => setWholesalePrice(Number(e.target.value))} style={{ width: '100%', background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
                  </div>
                </div>
              </div>
            </div>
            <div style={{ fontSize: '10px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
              <span>Total Volume Sold: {totalSoldVolume.toLocaleString()} L</span>
              <span>Total Revenue: {formatPKR(totalRevenue)}</span>
            </div>
          </div>

          {/* Expense Overrides */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#ef4444', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <PieChartIcon size={16} /> Operational Expenditures (PKR)
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0f172a', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
                <span style={{ fontSize: '12px', color: '#cbd5e1' }}>Feed & Fodder (Silage, Vanda)</span>
                <input type="number" value={feedCost} onChange={e => setFeedCost(Number(e.target.value))} style={{ width: '120px', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', textAlign: 'right' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0f172a', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}>
                <span style={{ fontSize: '12px', color: '#cbd5e1' }}>Labor & Wages</span>
                <input type="number" value={laborCost} onChange={e => setLaborCost(Number(e.target.value))} style={{ width: '120px', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', textAlign: 'right' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0f172a', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid #a855f7' }}>
                <span style={{ fontSize: '12px', color: '#cbd5e1' }}>Utilities & Fuel (Solar/WAPDA)</span>
                <input type="number" value={utilitiesCost} onChange={e => setUtilitiesCost(Number(e.target.value))} style={{ width: '120px', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', textAlign: 'right' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0f172a', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid #ef4444' }}>
                <span style={{ fontSize: '12px', color: '#cbd5e1' }}>Health & Breeding (Meds, Semen)</span>
                <input type="number" value={healthCost} onChange={e => setHealthCost(Number(e.target.value))} style={{ width: '120px', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', textAlign: 'right' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0f172a', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid #94a3b8' }}>
                <span style={{ fontSize: '12px', color: '#cbd5e1' }}>Overheads & Maintenance</span>
                <input type="number" value={overheads} onChange={e => setOverheads(Number(e.target.value))} style={{ width: '120px', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px', borderRadius: '4px', fontSize: '12px', textAlign: 'right' }} />
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: CHARTS & ANALYSIS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff', marginBottom: '12px' }}>Expenditure Distribution</div>
            <div style={{ flex: 1, minHeight: '220px', position: 'relative' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={costDistribution} innerRadius={70} outerRadius={100} paddingAngle={3} dataKey="value" stroke="none">
                    {costDistribution.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                  </Pie>
                  <Tooltip formatter={(value: any) => formatPKR(Number(value))} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px', color: '#fff' }} />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ position: 'absolute', top: '42%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', pointerEvents: 'none' }}>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Total Cost</div>
                <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#fff' }}>{formatPKR(totalCosts)}</div>
              </div>
            </div>
          </div>

          <div style={{ background: 'linear-gradient(to right, #1e293b, #0f172a)', border: '1px solid #334155', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <TrendingUp size={16} color="#34d399" /> Sensitivity Analysis: Feed Cost Volatility
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <span style={{ fontSize: '12px', color: '#cbd5e1', width: '40px' }}>-20%</span>
              <input type="range" min="-20" max="20" step="1" value={feedCostSimPct} onChange={(e) => setFeedCostSimPct(Number(e.target.value))} style={{ flex: 1, accentColor: feedCostSimPct > 0 ? '#ef4444' : '#34d399' }} />
              <span style={{ fontSize: '12px', color: '#cbd5e1', width: '40px', textAlign: 'right' }}>+20%</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div style={{ background: '#111827', padding: '10px', borderRadius: '6px', textAlign: 'center', border: `1px solid ${feedCostSimPct > 0 ? '#ef4444' : '#334155'}` }}>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Simulated CMPL</div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: feedCostSimPct > 0 ? '#f87171' : '#fff' }}>Rs. {formatCurrency(simulatedCMPL)}</div>
              </div>
              <div style={{ background: '#111827', padding: '10px', borderRadius: '6px', textAlign: 'center', border: `1px solid ${feedCostSimPct > 0 ? '#ef4444' : '#334155'}` }}>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Simulated Profit/Loss</div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: (totalRevenue - simulatedTotalCost) >= 0 ? '#34d399' : '#f87171' }}>{formatPKR(totalRevenue - simulatedTotalCost)}</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

