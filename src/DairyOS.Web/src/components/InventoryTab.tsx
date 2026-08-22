import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowDown, ArrowUp, PackagePlus, RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const inputStyle: React.CSSProperties = { background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '7px 8px', borderRadius: 5, fontSize: 11, width: '100%', boxSizing: 'border-box' };
const buttonStyle: React.CSSProperties = { background: '#0ea5e9', color: '#fff', border: '1px solid #38bdf8', padding: '7px 10px', borderRadius: 5, fontSize: 10, fontWeight: 800, cursor: 'pointer' };
const panel: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 12 };

type CatalogItem = { id:number; item:string; category:string; unit:string; location?:string|null; reorder_level:number; active:boolean; notes?:string|null; balance?:number; status?:string; transaction_count?:number; last_movement_at?:string|null };
type Movement = { id:number; item:string; movement_type:string; quantity:number; signed_quantity:number; unit?:string|null; location?:string|null; supplier?:string|null; notes?:string|null; recorded_by?:string|null; recorded_at?:string|null };

export default function InventoryTab() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [movements, setMovements] = useState<Movement[]>([]);
  const [item, setItem] = useState('');
  const [category, setCategory] = useState('FEED');
  const [unit, setUnit] = useState('kg');
  const [location, setLocation] = useState('');
  const [reorderLevel, setReorderLevel] = useState('0');
  const [movementType, setMovementType] = useState('PURCHASE');
  const [quantity, setQuantity] = useState('');
  const [supplier, setSupplier] = useState('');
  const [notes, setNotes] = useState('');
  const [sourceFinanceId, setSourceFinanceId] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try {
      const [dashboardRes, movementsRes] = await Promise.all([
        fetch(`${API_BASE}/farm/feed-inventory/dashboard`),
        fetch(`${API_BASE}/farm/feed-inventory/movements?limit=50`),
      ]);
      if (!dashboardRes.ok || !movementsRes.ok) throw new Error('Feed Inventory API unavailable.');
      const dashboard = await dashboardRes.json();
      const movementData = await movementsRes.json();
      setItems(dashboard.items ?? []);
      setMovements(movementData.movements ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load Feed Inventory.');
    } finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, []);

  const filteredItems = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return needle ? items.filter(row => `${row.item} ${row.category} ${row.location ?? ''}`.toLowerCase().includes(needle)) : items;
  }, [items, search]);

  const lowStock = items.filter(row => row.status === 'LOW');
  const totalTracked = items.length;

  const createItem = async (event: React.FormEvent) => {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      const response = await fetch(`${API_BASE}/farm/feed-inventory/items`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item, category, unit, location: location || null, reorder_level: Number(reorderLevel || 0), active: true }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Inventory item could not be created.');
      setMessage(`Added ${data.item}.`); setItem(''); setLocation(''); setReorderLevel('0'); await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to create inventory item.'); }
    finally { setSaving(false); }
  };

  const createMovement = async (event: React.FormEvent) => {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      if (!item) throw new Error('Select an inventory item.');
      const response = await fetch(`${API_BASE}/farm/feed-inventory/movements`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item, quantity: Number(quantity), movement_type: movementType, unit, location: location || null, supplier: supplier || null, notes: notes || null, source_financial_transaction_id: sourceFinanceId ? Number(sourceFinanceId) : null }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail?.message || data.detail || 'Inventory movement could not be recorded.');
      setMessage(`${movementType} recorded for ${item}.`); setQuantity(''); setSupplier(''); setNotes(''); setSourceFinanceId(''); await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to record inventory movement.'); }
    finally { setSaving(false); }
  };

  return <div style={{ padding: 16, color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
      <div><div style={{ fontSize: 20, fontWeight: 800 }}>Feed Inventory</div><div style={{ fontSize: 11, color: '#94a3b8' }}>Stock is derived from the persisted movement ledger; reorder levels live in the item master.</div></div>
      <button onClick={() => void load()} style={{ ...buttonStyle, background: '#1e293b', borderColor: '#334155' }}><RefreshCw size={12} /> Refresh</button>
    </div>

    {error && <div style={{ background: 'rgba(239,68,68,.12)', border: '1px solid #ef4444', color: '#fecaca', padding: 9, borderRadius: 6, marginBottom: 10, fontSize: 11 }}>{error}</div>}
    {message && <div style={{ background: 'rgba(16,185,129,.12)', border: '1px solid #10b981', color: '#a7f3d0', padding: 9, borderRadius: 6, marginBottom: 10, fontSize: 11 }}>{message}</div>}

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 12 }}>
      <div style={{ ...panel, borderLeft: '4px solid #38bdf8' }}><div style={{ fontSize: 9, color: '#94a3b8' }}>TRACKED ITEMS</div><div style={{ fontSize: 20, fontWeight: 800 }}>{totalTracked}</div></div>
      <div style={{ ...panel, borderLeft: '4px solid #f59e0b' }}><div style={{ fontSize: 9, color: '#94a3b8' }}>LOW STOCK</div><div style={{ fontSize: 20, fontWeight: 800, color: lowStock.length ? '#f59e0b' : '#34d399' }}>{lowStock.length}</div></div>
      <div style={{ ...panel, borderLeft: '4px solid #34d399' }}><div style={{ fontSize: 9, color: '#94a3b8' }}>MOVEMENTS SHOWN</div><div style={{ fontSize: 20, fontWeight: 800 }}>{movements.length}</div></div>
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
      <form onSubmit={createItem} style={panel}>
        <div style={{ fontSize: 12, fontWeight: 800, marginBottom: 9, color: '#38bdf8' }}>Add Inventory Item</div>
        <input required placeholder="Item name" value={item} onChange={e => setItem(e.target.value)} style={inputStyle} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginTop: 7 }}>
          <select value={category} onChange={e => setCategory(e.target.value)} style={inputStyle}><option value="FEED">Feed</option><option value="SILAGE">Silage</option><option value="ROUGHAGE">Dry Roughage</option><option value="CONCENTRATE">Commercial Feed / Grain</option><option value="ADDITIVE">Mineral / Additive</option></select>
          <select value={unit} onChange={e => setUnit(e.target.value)} style={inputStyle}><option>kg</option><option>ton</option><option>bag</option><option>litre</option><option>unit</option></select>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginTop: 7 }}>
          <input placeholder="Store / bunker location" value={location} onChange={e => setLocation(e.target.value)} style={inputStyle} />
          <input type="number" min="0" step="0.001" placeholder="Reorder level" value={reorderLevel} onChange={e => setReorderLevel(e.target.value)} style={inputStyle} />
        </div>
        <button disabled={saving} type="submit" style={{ ...buttonStyle, width: '100%', marginTop: 8 }}>{saving ? 'Saving…' : 'Create Item'}</button>
      </form>

      <form onSubmit={createMovement} style={panel}>
        <div style={{ fontSize: 12, fontWeight: 800, marginBottom: 9, color: '#34d399' }}>Record Stock Movement</div>
        <select required value={item} onChange={e => { setItem(e.target.value); const selected = items.find(row => row.item === e.target.value); if (selected) { setUnit(selected.unit); setLocation(selected.location || ''); } }} style={inputStyle}><option value="">Select item…</option>{items.map(row => <option key={row.id} value={row.item}>{row.item}</option>)}</select>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginTop: 7 }}>
          <select value={movementType} onChange={e => setMovementType(e.target.value)} style={inputStyle}><option value="PURCHASE">Purchase</option><option value="RECEIPT">Receipt</option><option value="CONSUMPTION">Consumption</option><option value="TRANSFER">Transfer (+/-)</option><option value="WASTAGE">Wastage</option><option value="ADJUSTMENT">Adjustment (+/-)</option></select>
          <input required type="number" step="0.001" placeholder="Quantity" value={quantity} onChange={e => setQuantity(e.target.value)} style={inputStyle} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginTop: 7 }}>
          <input placeholder="Supplier" value={supplier} onChange={e => setSupplier(e.target.value)} style={inputStyle} />
          <input placeholder="Finance Txn ID (optional)" value={sourceFinanceId} onChange={e => setSourceFinanceId(e.target.value)} style={inputStyle} />
        </div>
        <input placeholder="Notes" value={notes} onChange={e => setNotes(e.target.value)} style={{ ...inputStyle, marginTop: 7 }} />
        <button disabled={saving} type="submit" style={{ ...buttonStyle, width: '100%', marginTop: 8, background: '#059669', borderColor: '#34d399' }}>{saving ? 'Saving…' : 'Record Movement'}</button>
      </form>
    </div>

    <div style={{ ...panel, marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 9 }}><div style={{ fontSize: 12, fontWeight: 800 }}>Live Stock Position</div><input placeholder="Search item…" value={search} onChange={e => setSearch(e.target.value)} style={{ ...inputStyle, width: 240 }} /></div>
      {loading ? <div style={{ color: '#94a3b8', fontSize: 11 }}>Loading persisted inventory…</div> : <div style={{ overflowX: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}><thead><tr style={{ color: '#94a3b8', textAlign: 'left', borderBottom: '1px solid #1f2937' }}><th style={{ padding: 8 }}>Item</th><th style={{ padding: 8 }}>Category</th><th style={{ padding: 8 }}>Location</th><th style={{ padding: 8, textAlign: 'right' }}>Balance</th><th style={{ padding: 8, textAlign: 'right' }}>Reorder</th><th style={{ padding: 8 }}>Status</th></tr></thead><tbody>{filteredItems.map(row => <tr key={row.id} style={{ borderBottom: '1px solid #1a2234' }}><td style={{ padding: 8, fontWeight: 700 }}>{row.item}</td><td style={{ padding: 8, color: '#cbd5e1' }}>{row.category}</td><td style={{ padding: 8, color: '#94a3b8' }}>{row.location || '—'}</td><td style={{ padding: 8, textAlign: 'right', fontWeight: 800 }}>{row.balance?.toLocaleString('en-PK', { maximumFractionDigits: 3 })} {row.unit}</td><td style={{ padding: 8, textAlign: 'right' }}>{row.reorder_level.toLocaleString('en-PK', { maximumFractionDigits: 3 })}</td><td style={{ padding: 8 }}>{row.status === 'LOW' ? <span style={{ color: '#f59e0b', display: 'inline-flex', gap: 4, alignItems: 'center' }}><AlertTriangle size={11} /> LOW</span> : row.status === 'OK' ? <span style={{ color: '#34d399' }}>OK</span> : <span style={{ color: '#64748b' }}>NO THRESHOLD</span>}</td></tr>)}</tbody></table></div>}
    </div>

    {lowStock.length > 0 && <div style={{ ...panel, borderColor: '#f59e0b', marginBottom: 12 }}><div style={{ fontSize: 12, fontWeight: 800, color: '#f59e0b', marginBottom: 8 }}>Reorder Attention</div>{lowStock.map(row => <div key={row.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid #1a2234', fontSize: 11 }}><span>{row.item}</span><span style={{ color: '#f59e0b' }}>{row.balance} {row.unit} available / {row.reorder_level} {row.unit} threshold</span></div>)}</div>}

    <div style={panel}>
      <div style={{ fontSize: 12, fontWeight: 800, marginBottom: 8 }}>Recent Stock Movements</div>
      {movements.length === 0 ? <div style={{ color: '#64748b', fontSize: 11 }}>No persisted stock movements.</div> : movements.map(row => <div key={row.id} style={{ display: 'grid', gridTemplateColumns: '1.4fr .9fr .8fr 1.5fr', gap: 8, padding: '8px 0', borderBottom: '1px solid #1a2234', fontSize: 10 }}><span>{row.item}</span><span style={{ color: '#cbd5e1' }}>{row.movement_type}</span><span style={{ textAlign: 'right', color: row.signed_quantity < 0 ? '#f87171' : '#34d399', display: 'inline-flex', justifyContent: 'flex-end', alignItems: 'center', gap: 3 }}>{row.signed_quantity < 0 ? <ArrowDown size={10} /> : <ArrowUp size={10} />}{Math.abs(row.signed_quantity)} {row.unit || ''}</span><span style={{ color: '#64748b' }}>{row.supplier || row.notes || '—'}</span></div>)}
    </div>
  </div>;
}
