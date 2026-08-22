import React, { useEffect, useMemo, useState } from 'react';
import { Wheat, RotateCcw, Lightbulb, Save, Printer, MessageCircle, Info, CheckCircle2, AlertTriangle, X } from 'lucide-react';

const STORAGE_KEY = 'dairyos_coml_tmr_data';

const schema = [
  { name: 'Silage', u: 'kg', step: 0.5, min: 0, max: 60, p: 20, g: false },
  { name: 'Vanda (Concentrate)', u: 'kg', step: 0.5, min: 0, max: 25, p: 100, g: false },
  { name: 'Wheat Straw', u: 'kg', step: 0.5, min: 0, max: 12, p: 20, g: false },
  { name: 'Soybean Meal', u: 'kg', step: 0.25, min: 0, max: 5, p: 180, g: false },
  { name: 'Molasses', u: 'kg', step: 0.25, min: 0, max: 3, p: 85, g: false },
  { name: 'Bypass Fat', u: 'g', step: 25, min: 0, max: 600, p: 480, g: true },
  { name: 'Mineral Mixture', u: 'g', step: 25, min: 0, max: 400, p: 460, g: true },
  { name: 'Meetha Soda', u: 'g', step: 25, min: 0, max: 400, p: 200, g: true },
  { name: 'Anionic Salts (DCAD)', u: 'g', step: 25, min: 0, max: 300, p: 350, g: true },
  { name: 'Toxin Binder', u: 'g', step: 10, min: 0, max: 150, p: 260, g: true },
  { name: 'Lysine / Methionine', u: 'g', step: 5, min: 0, max: 80, p: 4000, g: true },
] as const;

const presets: Record<string, number[]> = {
  early_milking: [22, 9.5, 2.5, 2.5, 1, 400, 200, 200, 0, 50, 30],
  mid_milking: [20, 7, 3.5, 1.5, 0.5, 200, 150, 150, 0, 40, 15],
  late_milking: [16, 5, 4.5, 1, 0.5, 75, 100, 100, 0, 30, 0],
  far_off: [10, 2, 6.5, 0, 0, 0, 100, 0, 0, 30, 0],
  close_up: [12, 3.5, 3.5, 1, 1, 0, 150, 0, 175, 50, 20],
  heifer_growth: [12, 3, 2.5, 0.5, 0, 0, 100, 50, 0, 30, 0],
  calf_starter: [4, 2, 0.5, 0, 0, 0, 40, 0, 0, 20, 0],
};

const stageInfo: Record<string, string> = {
  early_milking: '30–35 L/day target · high energy density',
  mid_milking: '20–25 L/day target · rumen stability focus',
  late_milking: '10–15 L/day target · avoid over-conditioning',
  far_off: 'Dry off · high fibre, low energy',
  close_up: 'Transition diet · negative DCAD',
  heifer_growth: '700–900 g/day gain target · moderate protein',
  calf_starter: '4–8 weeks · rumen development',
};

const adviceStrings: Record<string, string> = {
  early_milking: 'Maximise energy density. Monitor silage DM and pH. Maintain a consistent mixing order.',
  mid_milking: 'Maintain silage quality and rumen stability. Reduce bypass fat as yield declines.',
  late_milking: 'Reduce concentrate gradually and monitor BCS before dry-off.',
  far_off: 'Focus on rumen volume and moderate energy to prevent over-conditioning.',
  close_up: 'Use anionic salts for transition cows and monitor intake and calcium-risk management.',
  heifer_growth: 'Protect skeletal development and target steady growth without over-conditioning.',
  calf_starter: 'Maintain freshness and gradual transition into forage and TMR.',
};

const money = (n: number) => `PKR ${n.toLocaleString('en-PK', { maximumFractionDigits: 0 })}`;

export default function TMRPreparationTool() {
  const [stage, setStage] = useState('early_milking');
  const [herdSize, setHerdSize] = useState(10);
  const [qtys, setQtys] = useState<number[]>([...presets.early_milking]);
  const [prices, setPrices] = useState<number[]>(schema.map(s => s.p));
  const [showAdvice, setShowAdvice] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const data = JSON.parse(raw) as { stage?: string; size?: number; qtys?: number[]; prices?: number[] };
      if (data.stage && presets[data.stage]) setStage(data.stage);
      if (typeof data.size === 'number') setHerdSize(data.size);
      if (Array.isArray(data.qtys) && data.qtys.length === schema.length) setQtys(data.qtys);
      if (Array.isArray(data.prices) && data.prices.length === schema.length) setPrices(data.prices);
    } catch {
      // Ignore malformed local TMR drafts.
    }
  }, []);

  const rows = useMemo(() => schema.map((s, i) => {
    const q = qtys[i] || 0;
    const p = prices[i] || 0;
    const costPerHead = s.g ? (q / 1000) * p : q * p;
    return { ...s, q, p, std: presets[stage][i], costPerHead, batchQty: q * herdSize, modified: q !== presets[stage][i] };
  }), [qtys, prices, stage, herdSize]);

  const headCost = rows.reduce((sum, r) => sum + r.costPerHead, 0);
  const batchCost = headCost * herdSize;
  const batchWeight = rows.reduce((sum, r) => sum + (r.g ? 0 : r.batchQty), 0);

  const updateQty = (index: number, value: number) => setQtys(current => current.map((v, i) => i === index ? value : v));
  const updatePrice = (index: number, value: number) => setPrices(current => current.map((v, i) => i === index ? value : v));

  const reset = () => setQtys([...presets[stage]]);

  const save = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ stage, size: herdSize, qtys, prices }));
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  };

  const whatsApp = () => {
    let text = `*DairyOS TMR Batch Sheet*\n*Stage:* ${stage.replace('_', ' ').toUpperCase()}\n*Animals:* ${herdSize}\n*Batch Weight:* ${Math.round(batchWeight)} KG\n*Cost/Head:* ${money(headCost)}\n\n*Ingredients:*\n`;
    rows.forEach(r => { if (r.q > 0) text += `• ${r.name}: ${r.batchQty.toLocaleString()} ${r.u}\n`; });
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`);
  };

  return (
    <div style={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: 10, overflow: 'hidden' }}>
      <div style={{ padding: 14, borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <h3 style={{ margin: 0, color: '#38bdf8', fontSize: 15, display: 'flex', alignItems: 'center', gap: 7 }}><Wheat size={18} /> TMR Preparation Tool</h3>
          <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: 10 }}>Preparation aid only. TMR output does not automatically alter the official monthly COML.</p>
        </div>
        <div style={{ display: 'flex', gap: 7 }}>
          <button onClick={() => setShowAdvice(true)} style={button('#f59e0b')}><Lightbulb size={12} /> Advisory</button>
          <button onClick={() => window.print()} style={button('#64748b')}><Printer size={12} /> Print</button>
          <button onClick={whatsApp} style={button('#22c55e')}><MessageCircle size={12} /> WhatsApp</button>
        </div>
      </div>

      {showAdvice && (
        <div style={{ padding: 12, background: 'rgba(245,158,11,.08)', borderBottom: '1px solid #f59e0b', color: '#fcd34d', fontSize: 11, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
          <Lightbulb size={14} style={{ flexShrink: 0 }} />
          <div style={{ flex: 1 }}><strong>{stage.replace('_', ' ').toUpperCase()}:</strong> {adviceStrings[stage]}</div>
          <button onClick={() => setShowAdvice(false)} style={{ background: 'none', border: 'none', color: '#fbbf24', cursor: 'pointer' }}><X size={14} /></button>
        </div>
      )}

      <div style={{ padding: 12, display: 'grid', gridTemplateColumns: 'minmax(220px,1fr) 120px auto', gap: 8, alignItems: 'end' }}>
        <label style={labelStyle}>Animal Stage<select value={stage} onChange={e => { setStage(e.target.value); setQtys([...presets[e.target.value]]); }} style={inputStyle}>
          <optgroup label="Milking Cows"><option value="early_milking">Early Lactation</option><option value="mid_milking">Mid Lactation</option><option value="late_milking">Late Lactation</option></optgroup>
          <optgroup label="Dry Cows"><option value="far_off">Far-Off Dry</option><option value="close_up">Close-Up</option></optgroup>
          <optgroup label="Young Stock"><option value="heifer_growth">Growing Heifer</option><option value="calf_starter">Calf Starter</option></optgroup>
        </select><span style={{ marginTop: 4, color: '#38bdf8', fontSize: 9, display: 'flex', gap: 4, alignItems: 'center' }}><Info size={10} /> {stageInfo[stage]}</span></label>
        <label style={labelStyle}>Herd Size<input type="number" min={0} value={herdSize} onChange={e => setHerdSize(Number(e.target.value))} style={inputStyle} /></label>
        <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}><button onClick={reset} style={button('#334155')}><RotateCcw size={12} /> Reset</button><button onClick={save} style={button('#2563eb')}><Save size={12} /> {saved ? 'Saved' : 'Save Draft'}</button></div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 720, fontSize: 10 }}>
          <thead><tr style={{ background: '#111827', color: '#94a3b8', textAlign: 'left' }}><th style={th}>Ingredient</th><th style={th}>Qty/Head</th><th style={th}>Price</th><th style={th}>Batch</th><th style={{ ...th, textAlign: 'right' }}>Cost/Head</th></tr></thead>
          <tbody>{rows.map((r, i) => <tr key={r.name} style={{ borderTop: '1px solid #1f2937' }}><td style={{ ...td, color: r.q > 0 ? '#fff' : '#64748b', fontWeight: 700 }}>{r.name}{r.modified && <span style={{ marginLeft: 5, display: 'inline-block', width: 5, height: 5, borderRadius: '50%', background: '#f59e0b' }} />}</td><td style={td}><div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><input type="number" step={r.step} min={r.min} max={r.max} value={r.q || ''} onChange={e => updateQty(i, Number(e.target.value))} style={{ ...inputStyle, width: 78 }} /><span style={{ color: '#94a3b8' }}>{r.u}</span></div></td><td style={td}><div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><input type="number" min={0} step="0.01" value={r.p} onChange={e => updatePrice(i, Number(e.target.value))} style={{ ...inputStyle, width: 82 }} /><span style={{ color: '#64748b' }}>PKR/kg</span></div></td><td style={{ ...td, color: '#34d399', fontWeight: 700 }}>{r.batchQty ? `${r.batchQty.toLocaleString()} ${r.u}` : '—'}</td><td style={{ ...td, textAlign: 'right', color: '#cbd5e1', fontWeight: 700 }}>{money(r.costPerHead)}</td></tr>)}</tbody>
        </table>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, padding: 12 }}>
        <Summary label="Cost / Head / Day" value={money(headCost)} />
        <Summary label="Group Cost / Day" value={money(batchCost)} />
        <Summary label="Total Batch Weight" value={`${Math.round(batchWeight).toLocaleString()} KG`} />
      </div>
      <div style={{ padding: '0 12px 12px', color: '#64748b', fontSize: 9 }}><CheckCircle2 size={10} style={{ verticalAlign: 'middle', marginRight: 4 }} /> The COML Feed Cost/L value must be entered/locked separately by the operator.</div>
    </div>
  );
}

function button(background: string): React.CSSProperties { return { background, color: '#fff', border: 'none', borderRadius: 5, padding: '7px 10px', fontSize: 10, fontWeight: 800, cursor: 'pointer', display: 'inline-flex', gap: 5, alignItems: 'center' }; }
const inputStyle: React.CSSProperties = { background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '7px 8px', borderRadius: 5, fontSize: 10, boxSizing: 'border-box', width: '100%' };
const labelStyle: React.CSSProperties = { fontSize: 9, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800, display: 'block' };
const th: React.CSSProperties = { padding: 8, fontWeight: 800 };
const td: React.CSSProperties = { padding: 8 };
function Summary({ label, value }: { label: string; value: string }) { return <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 7, padding: 10 }}><div style={{ color: '#94a3b8', fontSize: 9, textTransform: 'uppercase', fontWeight: 800 }}>{label}</div><div style={{ color: '#38bdf8', fontSize: 16, fontWeight: 900, marginTop: 4 }}>{value}</div></div>; }
