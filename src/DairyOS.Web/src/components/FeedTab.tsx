import { useState } from 'react';
import { Wheat, Plus, DollarSign, Scale, Layers } from 'lucide-react';

interface FeedItem {
  id: string;
  feedName: string;
  category: string;
  purchasedKg: number;
  consumedKg: number;
  costPKR: number;
}

export default function FeedTab() {
  const [feedInventory, setFeedInventory] = useState<FeedItem[]>([
    { id: 'F-1', feedName: 'Corn Silage', category: 'Roughage', purchasedKg: 25000, consumedKg: 18500, costPKR: 450000 },
    { id: 'F-2', feedName: 'Cotton Seed Cake (Vanda)', category: 'Concentrate', purchasedKg: 5000, consumedKg: 3800, costPKR: 280000 },
    { id: 'F-3', feedName: 'Lucerne / Alfalfa Hay', category: 'Roughage', purchasedKg: 4000, consumedKg: 2900, costPKR: 160000 }
  ]);

  const [feedName, setFeedName] = useState('');
  const [category, setCategory] = useState('Roughage');
  const [purchasedKg, setPurchasedKg] = useState('');
  const [costPKR, setCostPKR] = useState('');

  const handleAddFeed = (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedName || !purchasedKg) return;

    const newItem: FeedItem = {
      id: `F-${Date.now().toString().slice(-4)}`,
      feedName,
      category,
      purchasedKg: parseFloat(purchasedKg),
      consumedKg: 0,
      costPKR: parseFloat(costPKR) || 0
    };

    setFeedInventory([newItem, ...feedInventory]);
    setFeedName('');
    setPurchasedKg('');
    setCostPKR('');
  };

  return (
    <div style={{ padding: '20px', color: '#f8fafc', height: 'calc(100vh - 75px)', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '12px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Wheat size={20}/> Feed Inventory & Financial Ledger Integration
          </h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
            Tracks bulk feed purchases (tied to operating expenses), daily consumption volume, and closing balance stock.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '16px' }}>
        
        {/* Add Feed Form */}
        <form onSubmit={handleAddFeed} style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '12px', height: 'fit-content' }}>
          <h3 style={{ margin: '0 0 4px 0', fontSize: '13px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Plus size={15} color="#38bdf8"/> Record Feed Procurement
          </h3>

          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Feed Item Name</label>
            <input type="text" required value={feedName} onChange={e => setFeedName(e.target.value)} placeholder="e.g. Wheat Straw / Silage" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '11px' }}>
              <option value="Roughage">Roughage (Silage, Hay)</option>
              <option value="Concentrate">Concentrate (Vanda, Grains)</option>
              <option value="Minerals">Minerals & Supplements</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Purchased Quantity (Kg)</label>
            <input type="number" required value={purchasedKg} onChange={e => setPurchasedKg(e.target.value)} placeholder="0" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Total Cost (PKR) [Linked to Finance Ledger]</label>
            <input type="number" required value={costPKR} onChange={e => setCostPKR(e.target.value)} placeholder="0.00" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} />
          </div>

          <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '9px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12px' }}>
            <Plus size={15}/> Add to Inventory
          </button>
        </form>

        {/* Inventory Ledger Table showing Bought, Consumed, Balance */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Layers size={15} color="#38bdf8"/> Feed Stock Balance & Financial Linkage
          </h3>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left' }}>
                  <th style={{ padding: '6px' }}>Feed Item</th>
                  <th style={{ padding: '6px', textAlign: 'right' }}>Bought (Kg)</th>
                  <th style={{ padding: '6px', textAlign: 'right' }}>Consumed (Kg)</th>
                  <th style={{ padding: '6px', textAlign: 'right' }}>Balance (Kg)</th>
                  <th style={{ padding: '6px', textAlign: 'right' }}>Financial Cost</th>
                </tr>
              </thead>
              <tbody>
                {feedInventory.map(item => {
                  const balance = item.purchasedKg - item.consumedKg;
                  return (
                    <tr key={item.id} style={{ borderBottom: '1px solid #1a2234' }}>
                      <td style={{ padding: '8px 6px', color: '#e2e8f0', fontWeight: 'bold' }}>
                        {item.feedName}
                        <div style={{ fontSize: '9px', color: '#94a3b8' }}>{item.category}</div>
                      </td>
                      <td style={{ padding: '8px 6px', textAlign: 'right', color: '#38bdf8' }}>{item.purchasedKg.toLocaleString()} Kg</td>
                      <td style={{ padding: '8px 6px', textAlign: 'right', color: '#fb923c' }}>{item.consumedKg.toLocaleString()} Kg</td>
                      <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 'bold', color: balance > 2000 ? '#34d399' : '#f87171' }}>{balance.toLocaleString()} Kg</td>
                      <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 'bold', color: '#fff' }}>PKR {item.costPKR.toLocaleString()}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
