import { useState } from 'react';
import { Calculator, DollarSign } from 'lucide-react';

export default function CMPL() {
  const [feedCost, setFeedCost] = useState('890000');
  const [laborCost, setLaborCost] = useState('250000');
  const [overheadCost, setOverheadCost] = useState('150000');
  const [totalLitres, setTotalLitres] = useState('32000');

  const totalCost = parseFloat(feedCost || '0') + parseFloat(laborCost || '0') + parseFloat(overheadCost || '0');
  const litres = parseFloat(totalLitres || '1');
  const costPerLitre = litres > 0 ? (totalCost / litres).toFixed(2) : '0.00';

  return (
    <div style={{ padding: '16px', color: '#f8fafc', height: 'calc(100vh - 120px)', overflowY: 'auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '12px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}><Calculator size={20}/> Cost of Milk Production per Liter (CMPL)</h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>Manual interactive scenario modeling combining feed, labor, overhead, and milk yield totals.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#e2e8f0' }}>Cost & Yield Parameters</h3>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Total Feed Cost (PKR)</label>
            <input type="number" value={feedCost} onChange={e => setFeedCost(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Labor & Wages (PKR)</label>
            <input type="number" value={laborCost} onChange={e => setLaborCost(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Overhead & Utilities (PKR)</label>
            <input type="number" value={overheadCost} onChange={e => setOverheadCost(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Total Milk Produced (Litres)</label>
            <input type="number" value={totalLitres} onChange={e => setTotalLitres(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
          </div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '20px', borderRadius: '8px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', gap: '16px' }}>
          <div style={{ fontSize: '14px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '1px' }}>Computed Cost of Production</div>
          <div style={{ fontSize: '42px', fontWeight: 'bold', color: '#34d399' }}>PKR {costPerLitre} <span style={{ fontSize: '16px', color: '#94a3b8' }}>/ Litre</span></div>
          <div style={{ background: '#1e293b', padding: '12px', borderRadius: '6px', width: '100%', textAlign: 'left', fontSize: '12px', color: '#cbd5e1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}><span>Total Expenses:</span> <strong>PKR {totalCost.toLocaleString()}</strong></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Feed Cost Share:</span> <strong>{((parseFloat(feedCost)/totalCost)*100).toFixed(1)}%</strong></div>
          </div>
        </div>
      </div>
    </div>
  );
}
