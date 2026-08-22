import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, RefreshCw, Utensils, Wheat } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

type FinanceRow = {
  id: number;
  transaction_type: string;
  master_category?: string | null;
  sub_category?: string | null;
  custom_specification?: string | null;
  quantity?: number | null;
  unit?: string | null;
  amount: number;
  date?: string | null;
  status?: string | null;
};

type Movement = { item: string; movement_type: string; signed_quantity: number; unit?: string | null };
type FeedItem = { key: string; label: string; unit: string; purchased: number; used: number; balance: number };

const panel: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 12, minWidth: 0 };
const input: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', color: '#fff', border: '1px solid #334155', borderRadius: 5, padding: '7px 8px', fontSize: 11 };
const button = (background: string): React.CSSProperties => ({ background, color: '#fff', border: 0, borderRadius: 5, padding: '8px 10px', fontSize: 10, fontWeight: 800, cursor: 'pointer' });

const normalize = (row: FinanceRow) => {
  const label = `${row.sub_category || row.custom_specification || row.id}${row.custom_specification && row.sub_category ? ` — ${row.custom_specification}` : ''}`;
  return { key: `${label}|${row.unit || 'unit'}`, label, unit: row.unit || 'unit' };
};

export default function FeedTabClean() {
  const [finance, setFinance] = useState<FinanceRow[]>([]);
  const [movements, setMovements] = useState<Movement[]>([]);
  const [selectedItem, setSelectedItem] = useState('');
  const [usageType, setUsageType] = useState<'CONSUMPTION' | 'WASTAGE'>('CONSUMPTION');
  const [usageQty, setUsageQty] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try {
      const [financeRes, movementRes] = await Promise.all([
        fetch(`${API_BASE}/farm/finance-ledger`),
        fetch(`${API_BASE}/farm/feed-inventory/movements?limit=200`),
      ]);
      if (!financeRes.ok) throw new Error('Finance ledger unavailable.');
      const ledger = await financeRes.json();
      const movementData = movementRes.ok ? await movementRes.json() : { movements: [] };
      setFinance(ledger.transactions ?? []);
      setMovements(movementData.movements ?? []);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load Feed data.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, []);

  const purchasedRows = useMemo(() => finance.filter(row => row.transaction_type === 'EXPENSE' && row.master_category === 'FEED' && row.status !== 'VOID' && Number(row.quantity || 0) > 0), [finance]);
  const feedItems = useMemo<FeedItem[]>(() => {
    const grouped = new Map<string, FeedItem>();
    for (const row of purchasedRows) {
      const meta = normalize(row);
      const current = grouped.get(meta.key) || { key: meta.key, label: meta.label, unit: meta.unit, purchased: 0, used: 0, balance: 0 };
      current.purchased += Number(row.quantity || 0);
      grouped.set(meta.key, current);
    }
    for (const movement of movements) {
      if (!['CONSUMPTION', 'WASTAGE', 'ADJUSTMENT', 'TRANSFER'].includes(movement.movement_type)) continue;
      for (const item of grouped.values()) {
        if (item.label === movement.item || item.label.split(' — ')[0] === movement.item) {
          item.used += Math.max(0, -Number(movement.signed_quantity || 0));
          item.balance += Number(movement.signed_quantity || 0);
        }
      }
    }
    return [...grouped.values()].map(item => ({ ...item, balance: Math.max(0, item.purchased + item.balance) }));
  }, [purchasedRows, movements]);

  const current = feedItems.find(item => item.key === selectedItem);

  const recordUsage = async (event: React.FormEvent) => {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      if (!current) throw new Error('Select a purchased feed item.');
      const quantity = Number(usageQty);
      if (!(quantity > 0)) throw new Error('Usage quantity must be greater than zero.');
      let catalog = await fetch(`${API_BASE}/farm/feed-inventory/dashboard`);
      if (catalog.ok) {
        const dashboard = await catalog.json();
        const exists = (dashboard.items || []).some((row: any) => row.item === current.label);
        if (!exists) {
          const create = await fetch(`${API_BASE}/farm/feed-inventory/items`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item: current.label, category: 'FEED', unit: current.unit, reorder_level: 0, active: true }) });
          if (!create.ok) throw new Error('Could not initialize the purchased feed item for usage tracking.');
        }
      }
      const response = await fetch(`${API_BASE}/farm/feed-inventory/movements`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item: current.label, quantity, movement_type: usageType, unit: current.unit, notes: notes || null, recorded_by: 'WEB' }) });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Usage could not be recorded.');
      setMessage(`${usageType === 'CONSUMPTION' ? 'Consumption' : 'Wastage'} recorded for ${current.label}.`);
      setUsageQty(''); setNotes(''); await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to record feed usage.'); }
    finally { setSaving(false); }
  };

  const totalPurchased = feedItems.reduce((sum, item) => sum + item.purchased, 0);
  const totalBalance = feedItems.reduce((sum, item) => sum + item.balance, 0);
  const lowBalance = feedItems.filter(item => item.purchased > 0 && item.balance <= 0);

  return <div style={{ height: '100%', overflowY: 'auto', overflowX: 'hidden', boxSizing: 'border-box', padding: 14, color: '#fff' }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
      <div><div style={{ fontSize: 18, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 7 }}><Wheat size={18} color="#38bdf8" /> Feed & Nutrition</div><div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>Purchases come only from Finance Feed expenses. Usage is tracked here; balance = purchased less operational usage.</div></div>
      <button onClick={() => void load()} style={button('#1e293b')}><RefreshCw size={12} /> Refresh</button>
    </div>

    {error && <div style={{ ...panel, color: '#fecaca', borderColor: '#ef4444', marginBottom: 10, fontSize: 10 }}>{error}</div>}
    {message && <div style={{ ...panel, color: '#bbf7d0', borderColor: '#34d399', marginBottom: 10, fontSize: 10 }}>{message}</div>}

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 8, marginBottom: 10 }}>
      <Metric label="Purchased in Finance" value={`${totalPurchased.toLocaleString()} kg/unit`} accent="#38bdf8" />
      <Metric label="Current Feed Balance" value={`${totalBalance.toLocaleString()} kg/unit`} accent="#34d399" />
      <Metric label="Items Purchased" value={String(feedItems.length)} accent="#f59e0b" />
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.4fr) minmax(280px,.6fr)', gap: 10, alignItems: 'start' }}>
      <section style={panel}>
        <div style={{ fontSize: 12, fontWeight: 800, marginBottom: 8 }}>Feed Purchased in Finance</div>
        {loading ? <div style={{ fontSize: 10, color: '#64748b' }}>Loading finance-linked feed purchases…</div> : feedItems.length === 0 ? <div style={{ padding: 20, textAlign: 'center', color: '#64748b', fontSize: 10 }}>No Feed expenses have been entered in Finance yet.</div> : <div style={{ overflowX: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10, minWidth: 520 }}><thead><tr style={{ color: '#94a3b8', textAlign: 'left', borderBottom: '1px solid #1f2937' }}><th style={{ padding: 7 }}>Feed item</th><th style={{ padding: 7, textAlign: 'right' }}>Purchased</th><th style={{ padding: 7, textAlign: 'right' }}>Used</th><th style={{ padding: 7, textAlign: 'right' }}>Balance</th><th style={{ padding: 7 }}>Unit</th></tr></thead><tbody>{feedItems.map(item => <tr key={item.key} style={{ borderBottom: '1px solid #1a2234' }}><td style={{ padding: 7, fontWeight: 700 }}>{item.label}</td><td style={{ padding: 7, textAlign: 'right', color: '#38bdf8' }}>{item.purchased.toLocaleString()}</td><td style={{ padding: 7, textAlign: 'right', color: '#f59e0b' }}>{item.used.toLocaleString()}</td><td style={{ padding: 7, textAlign: 'right', color: item.balance <= 0 ? '#f87171' : '#34d399', fontWeight: 800 }}>{item.balance.toLocaleString()}</td><td style={{ padding: 7, color: '#94a3b8' }}>{item.unit}</td></tr>)}</tbody></table></div>}
      </section>

      <section style={panel}>
        <div style={{ fontSize: 12, fontWeight: 800, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}><Utensils size={14} color="#34d399" /> Record Feed Usage</div>
        <form onSubmit={recordUsage} style={{ display: 'grid', gap: 7 }}>
          <select required value={selectedItem} onChange={e => setSelectedItem(e.target.value)} style={input}><option value="">Select purchased item…</option>{feedItems.map(item => <option key={item.key} value={item.key}>{item.label}</option>)}</select>
          <select value={usageType} onChange={e => setUsageType(e.target.value as 'CONSUMPTION' | 'WASTAGE')} style={input}><option value="CONSUMPTION">Consumption</option><option value="WASTAGE">Wastage</option></select>
          <input required type="number" min="0.001" step="0.001" placeholder={current ? `Quantity (${current.unit})` : 'Quantity'} value={usageQty} onChange={e => setUsageQty(e.target.value)} style={input} />
          <input placeholder="Notes" value={notes} onChange={e => setNotes(e.target.value)} style={input} />
          <button disabled={saving || !current} type="submit" style={button('#059669')}>{saving ? 'Saving…' : 'Record Usage'}</button>
        </form>
      </section>
    </div>

    {lowBalance.length > 0 && <div style={{ ...panel, marginTop: 10, borderColor: '#f59e0b' }}><div style={{ color: '#f59e0b', fontWeight: 800, fontSize: 11, display: 'flex', alignItems: 'center', gap: 5 }}><AlertTriangle size={12} /> Feed balance needs attention</div><div style={{ color: '#94a3b8', fontSize: 10, marginTop: 4 }}>{lowBalance.map(item => item.label).join(', ')} has no remaining balance from recorded purchases.</div></div>}
  </div>;
}

function Metric({ label, value, accent }: { label: string; value: string; accent: string }) { return <div style={{ ...panel, borderLeft: `4px solid ${accent}` }}><div style={{ fontSize: 8, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800 }}>{label}</div><div style={{ marginTop: 4, fontSize: 16, fontWeight: 800, color: accent }}>{value}</div></div>; }
