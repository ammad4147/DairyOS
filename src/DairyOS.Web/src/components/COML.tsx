import React, { useEffect, useState } from 'react';
import { Calculator, Lock, TrendingUp, AlertTriangle, Milk, Wheat, DollarSign } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

export default function COML() {
  const [period, setPeriod] = useState({ start: '', end: '' });
  const [production, setProduction] = useState<any>(null);
  const [contracts, setContracts] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE}/farm/coml/integrated`).then(r => r.json()),
      fetch(`${API_BASE}/farm/coml/contracts`).then(r => r.json()),
    ]).then(([metricsData, contractsData]) => {
      setMetrics(metricsData);
      setContracts(contractsData.contracts || []);
      setProduction(metricsData.production || { totalLiters: 0, avgQuality: {} });
      setPeriod(metricsData.period || { start: '', end: '' });
    }).catch(() => {
      setMetrics(null);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: 20, color: '#64748b' }}>Loading integrated COML data...</div>;

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calculator size={20} /> Revenue Operations Center
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Auto-integrated from Feed, Milk, and Finance tabs. No manual entry required.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button style={{ background: '#1e293b', border: '1px solid #334155', color: '#34d399', padding: '8px 14px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <TrendingUp size={12} /> View Margin Trend
          </button>
          <button style={{ background: '#1e293b', border: '1px solid #334155', color: '#f59e0b', padding: '8px 14px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Lock size={12} /> Lock Month
          </button>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <MetricCard 
          title="Total Production" 
          value={`${production?.totalLiters?.toLocaleString() || 0} L`} 
          subtitle="Auto from Milk Tab"
          color="#38bdf8" 
          icon={<Milk size={16} />} 
        />
        <MetricCard 
          title="Feed Cost / L" 
          value={`PKR ${metrics?.feed_cost_per_liter?.toFixed(2) || '0.00'}`} 
          subtitle="Auto from Feed Tab"
          color="#34d399" 
          icon={<Wheat size={16} />} 
        />
        <MetricCard 
          title="OPEX / L" 
          value={`PKR ${metrics?.opex_cost_per_liter?.toFixed(2) || '0.00'}`} 
          subtitle="Auto from Finance Tab"
          color="#f59e0b" 
          icon={<DollarSign size={16} />} 
        />
        <MetricCard 
          title="Total COML / L" 
          value={`PKR ${metrics?.total_coml_per_liter?.toFixed(2) || '0.00'}`} 
          subtitle="Fully loaded cost"
          color="#a78bfa" 
          icon={<Calculator size={16} />} 
        />
      </div>

      {/* Contract Fulfillment + Batch Traceability */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        
        {/* Contract Tracker */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '16px' }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '14px', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DollarSign size={16} /> Contract Fulfillment
          </h3>
          {contracts.length === 0 ? (
            <div style={{ color: '#64748b', fontSize: 12, padding: '20px 0' }}>
              No active milk sale contracts. Add contracts in Finance Tab.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {contracts.map((c: any, i: number) => {
                const pct = Math.min(100, Math.round((c.fulfilled / c.commitment) * 100));
                const isAtRisk = pct < 80 && new Date(c.deadline) < new Date(Date.now() + 7 * 86400000);
                return (
                  <div key={i} style={{ padding: '10px', background: '#0f172a', borderRadius: '6px', border: `1px solid ${isAtRisk ? '#ef4444' : '#1f2937'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 'bold', fontSize: 12, color: '#e2e8f0' }}>{c.customer}</span>
                      <span style={{ fontSize: 10, color: isAtRisk ? '#fca5a5' : '#34d399' }}>
                        {isAtRisk && <AlertTriangle size={10} style={{ display: 'inline', marginRight: 4 }} />}
                        {pct}% fulfilled
                      </span>
                    </div>
                    <div style={{ width: '100%', height: 6, background: '#1f2937', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: isAtRisk ? '#ef4444' : '#34d399', borderRadius: 3 }} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: 10, color: '#94a3b8' }}>
                      <span>{c.fulfilled.toLocaleString()} / {c.commitment.toLocaleString()} L</span>
                      <span>Deadline: {c.deadline}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Batch Traceability */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '16px' }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '14px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Milk size={16} /> Batch Traceability
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {(production?.batches || []).slice(0, 5).map((batch: any, i: number) => (
              <div key={i} style={{ padding: '10px', background: '#0f172a', borderRadius: '6px', border: '1px solid #1f2937' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 'bold', fontSize: 12, color: '#e2e8f0' }}>Tank #{batch.tank_id}</span>
                  <span style={{ fontSize: 10, color: '#94a3b8' }}>{batch.date}</span>
                </div>
                <div style={{ fontSize: 11, color: '#cbd5e1', marginTop: 4 }}>
                  {batch.volume.toLocaleString()} L | {batch.fat}% Fat | {batch.protein}% Protein | {batch.scc} SCC
                </div>
                <div style={{ fontSize: 10, color: '#64748b', marginTop: 4 }}>
                  Sold to: {batch.customer || 'Unallocated'} | 
                  <button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', marginLeft: 4 }}>
                    View Herd Segment →
                  </button>
                </div>
              </div>
            ))}
            {!production?.batches?.length && (
              <div style={{ color: '#64748b', fontSize: 12, padding: '20px 0' }}>
                No batch records. Record milk collections in Milk Tab.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Predictive Insight Banner */}
      <div style={{ marginTop: '16px', padding: '14px', background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.2)', borderRadius: '8px' }}>
        <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#a78bfa', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <TrendingUp size={14} /> Predictive Insight
        </div>
        <div style={{ fontSize: '12px', color: '#cbd5e1' }}>
          Based on current feed prices and projected milk volumes, your margin per liter is forecast to 
          <span style={{ color: metrics?.margin_trend === 'down' ? '#ef4444' : '#34d399', fontWeight: 'bold' }}> {metrics?.margin_trend === 'down' ? 'decline 8%' : 'improve 5%'} </span>
          next month. 
          <button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', textDecoration: 'underline', marginLeft: 8 }}>
            Adjust Ration
          </button>
          <button style={{ background: 'none', border: 'none', color: '#fb923c', cursor: 'pointer', textDecoration: 'underline', marginLeft: 8 }}>
            Review Cull List
          </button>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle, color, icon }: { title: string; value: string; subtitle: string; color: string; icon: React.ReactNode }) {
  return (
    <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: `4px solid ${color}` }}>
      <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        {icon} {title}
      </div>
      <div style={{ fontSize: '22px', fontWeight: 'bold', color, marginBottom: '2px' }}>{value}</div>
      <div style={{ fontSize: '10px', color: '#64748b' }}>{subtitle}</div>
    </div>
  );
}