import React, { useState } from 'react';
import { DollarSign, Plus, ArrowUpRight, ArrowDownRight, Scale, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function FinanceTab() {
  const [milkSoldLiters] = useState(120.0);
  const [milkRatePerLiter] = useState(195.0); // PKR per Liter
  const totalProduced = 132.7;
  const domesticLiters = 11.5;
  const calfLiters = 11.5;
  
  const grossMilkRevenue = milkSoldLiters * milkRatePerLiter;
  const internalAbsorptionCost = (domesticLiters + calfLiters) * 115.0; // Valued at production cost

  // Mass balance audit
  const totalAllocated = milkSoldLiters + domesticLiters + calfLiters;
  const variance = parseFloat((totalProduced - totalAllocated).toFixed(1));
  const isBalanced = variance === 0;

  return (
    <div style={{ padding: '20px', color: '#fff' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DollarSign size={20} /> Finance & Milk Revenue Reconciliation
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Commercial revenue is strictly recognized on billed milk sold. Internal domestic and calf feeding allocations are reconciled to prevent cash flow leakages.
          </p>
        </div>
      </div>

      {/* Variance Alert */}
      {!isBalanced && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', padding: '12px 16px', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertTriangle size={20} color="#ef4444" />
          <div>
            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fca5a5' }}>
              Financial Reconciliation Warning: {variance} Liters Unaccounted
            </div>
            <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
              Total produced ({totalProduced} L) exceeds sum of commercial sales ({milkSoldLiters} L), domestic ({domesticLiters} L), and calf feeding ({calfLiters} L).
            </div>
          </div>
        </div>
      )}

      {/* Financial KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Commercial Milk Revenue (Sold)</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>PKR {grossMilkRevenue.toLocaleString()}</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>{milkSoldLiters} L @ PKR {milkRatePerLiter}/L</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #c084fc' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Internal Domestic Absorption</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#c084fc' }}>PKR {((domesticLiters * milkRatePerLiter)).toLocaleString()}</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>{domesticLiters} L domestic consumption value</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Calf Milk Investment Cost</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fb923c' }}>PKR {(calfLiters * 115).toLocaleString()}</div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>{calfLiters} L capitalized into calf rearing</div>
        </div>

        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Audit Status</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: isBalanced ? '#34d399' : '#f87171' }}>
            {isBalanced ? 'Balanced' : 'Audit Required'}
          </div>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Variance: {variance} L</div>
        </div>
      </div>

      {/* Ledger Table */}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
              <th style={{ padding: '10px 12px' }}>Transaction Stream</th>
              <th style={{ padding: '10px 12px' }}>Volume (L)</th>
              <th style={{ padding: '10px 12px' }}>Rate / Cost Basis</th>
              <th style={{ padding: '10px 12px' }}>Total Amount (PKR)</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Financial Status</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid #1a2234' }}>
              <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#34d399' }}>Commercial Milk Dispatch (Sold)</td>
              <td style={{ padding: '10px 12px', color: '#fff' }}>{milkSoldLiters} L</td>
              <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>PKR {milkRatePerLiter} / L</td>
              <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#34d399' }}>PKR {grossMilkRevenue.toLocaleString()}</td>
              <td style={{ padding: '10px 12px', textAlign: 'right', color: '#34d399', fontWeight: 'bold' }}>Revenue Realized</td>
            </tr>
            <tr style={{ borderBottom: '1px solid #1a2234' }}>
              <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#c084fc' }}>Household / Domestic Consumption</td>
              <td style={{ padding: '10px 12px', color: '#fff' }}>{domesticLiters} L</td>
              <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>PKR 195 (Opportunity value)</td>
              <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#c084fc' }}>PKR {(domesticLiters * 195).toLocaleString()}</td>
              <td style={{ padding: '10px 12px', textAlign: 'right', color: '#c084fc', fontWeight: 'bold' }}>Internal Non-Billed</td>
            </tr>
            <tr style={{ borderBottom: '1px solid #1a2234' }}>
              <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#fb923c' }}>Calf Nursery Feed Supply</td>
              <td style={{ padding: '10px 12px', color: '#fff' }}>{calfLiters} L</td>
              <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>PKR 115 (Production cost)</td>
              <td style={{ padding: '10px 12px', fontWeight: 'bold', color: '#fb923c' }}>PKR {(calfLiters * 115).toLocaleString()}</td>
              <td style={{ padding: '10px 12px', textAlign: 'right', color: '#fb923c', fontWeight: 'bold' }}>Biological Asset Capitalization</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  );
}
