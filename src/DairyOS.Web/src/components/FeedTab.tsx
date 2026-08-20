import React, { useState, useEffect } from 'react';
import { 
  Wheat, RotateCcw, Lightbulb, Save, Printer, MessageCircle, 
  Info, CheckCircle2, AlertTriangle, X, Database, TrendingDown, 
  Activity, Layers 
} from 'lucide-react';

// ─── TMR Data Schema & Presets ──────────────────────────────────────────────
const schema = [
  { name: "Silage",              u: "kg", step: 0.5,  min: 0, max: 60,  p: 20,   g: false },
  { name: "Vanda (Concentrate)", u: "kg", step: 0.5,  min: 0, max: 25,  p: 100,  g: false },
  { name: "Wheat Straw",         u: "kg", step: 0.5,  min: 0, max: 12,  p: 20,   g: false },
  { name: "Soybean Meal",        u: "kg", step: 0.25, min: 0, max: 5,   p: 180,  g: false },
  { name: "Molasses",            u: "kg", step: 0.25, min: 0, max: 3,   p: 85,   g: false },
  { name: "Bypass Fat",          u: "g",  step: 25,   min: 0, max: 600, p: 480,  g: true  },
  { name: "Mineral Mixture",     u: "g",  step: 25,   min: 0, max: 400, p: 460,  g: true  },
  { name: "Meetha Soda",         u: "g",  step: 25,   min: 0, max: 400, p: 200,  g: true  },
  { name: "Anionic Salts (DCAD)",u: "g",  step: 25,   min: 0, max: 300, p: 350,  g: true  },
  { name: "Toxin Binder",        u: "g",  step: 10,   min: 0, max: 150, p: 260,  g: true  },
  { name: "Lysine / Methionine", u: "g",  step: 5,    min: 0, max: 80,  p: 4000, g: true  }
];

const presets: Record<string, number[]> = {
  early_milking: [22, 9.5, 2.5, 2.5, 1.0, 400, 200, 200,   0,  50,  30],
  mid_milking:   [20, 7.0, 3.5, 1.5, 0.5, 200, 150, 150,   0,  40,  15],
  late_milking:  [16, 5.0, 4.5, 1.0, 0.5,  75, 100, 100,   0,  30,   0],
  far_off:       [10, 2.0, 6.5,   0,   0,   0, 100,   0,   0,  30,   0],
  close_up:      [12, 3.5, 3.5, 1.0, 1.0,   0, 150,   0, 175,  50,  20],
  heifer_growth: [12, 3.0, 2.5, 0.5,   0,   0, 100,  50,   0,  30,   0],
  calf_starter:  [ 4, 2.0, 0.5,   0,   0,   0,  40,   0,   0,  20,   0]
};

const stageInfo: Record<string, string> = {
  early_milking:  "30–35 L/day target · High energy density · Peak stress period",
  mid_milking:    "20–25 L/day target · Rumen stability focus · Monitor BCS",
  late_milking:   "10–15 L/day target · Steaming up phase · Avoid over-conditioning",
  far_off:        "Dry off · High fibre, low energy · Prevent obesity pre-calving",
  close_up:       "Transition diet · DCAD negative · No Meetha Soda with anionic salts",
  heifer_growth:  "700–900 g/day gain target · Moderate protein · Avoid over-feeding",
  calf_starter:   "4–8 weeks · Rumen development · Fresh mix only — discard after 6 hrs"
};

const adviceStrings: Record<string, string> = {
  early_milking: "High-Yield Strategy: Maximise energy density. Bypass Fat and rumen-protected amino acids reduce liver stress during the negative energy balance phase. Silage quality is paramount — check DM and pH. Mixing order: Straw → Silage → Vanda → SBM → Additives → Molasses.",
  mid_milking:   "Stability Strategy: Maintain high silage quality. Monitor rumen fill and cud chewing — at least 60% of resting cows should be ruminating. Reduce Bypass Fat as milk yield declines.",
  late_milking:  "Conditioning Strategy: Begin steaming up if yield justifies it. Monitor BCS — do not let cows exceed 3.5 at dry-off. Reduce concentrate gradually over 2 weeks.",
  far_off:       "Rest Strategy: Focus on rumen volume with high straw. Limit energy to prevent obesity, which causes difficult calvings and fatty liver. Anionic salts are not needed at this stage.",
  close_up:      "Transition Strategy: Anionic Salts are essential to lower DCAD and prevent milk fever. REMOVE Meetha Soda — it directly antagonises anionic salts. Add Molasses to mask bitterness. Target DCAD of −50 to −100 mEq/kg DM.",
  heifer_growth: "Development Strategy: Target 700–900 g/day growth. Over-conditioning at this stage causes lifelong production losses. Mineral mix critical for skeletal development.",
  calf_starter:  "Development Strategy: Freshness is critical — mould destroys rumen papillae development. Mix only what is eaten within 6 hours. Transition to TMR gradually after 8 weeks."
};

export default function FeedTab() {
  const [stage, setStage] = useState<string>('early_milking');
  const [herdSize, setHerdSize] = useState<number>(10);
  const [qtys, setQtys] = useState<number[]>([...presets.early_milking]);
  const [prices, setPrices] = useState<number[]>(schema.map(s => s.p));
  
  const [showModal, setShowModal] = useState<boolean>(false);
  const [saveNotify, setSaveNotify] = useState<boolean>(false);

  // Load from LocalStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('dairyos_tmr_data');
      if (saved) {
        const d = JSON.parse(saved);
        if (d.stage && d.qtys && d.prices) {
          setStage(d.stage);
          setHerdSize(d.size);
          setQtys(d.qtys);
          setPrices(d.prices);
        }
      }
    } catch (e) {
      console.warn("Could not load TMR data");
    }
  }, []);

  const handleLoadTemplate = (selectedStage: string) => {
    setStage(selectedStage);
    setQtys([...presets[selectedStage]]);
  };

  const handleReset = () => { setQtys([...presets[stage]]); };

  const handleSave = () => {
    const data = { stage, size: herdSize, qtys, prices };
    localStorage.setItem('dairyos_tmr_data', JSON.stringify(data));
    setSaveNotify(true);
    setTimeout(() => setSaveNotify(false), 3000);
  };

  const handleQtyChange = (index: number, val: number) => {
    const newQtys = [...qtys];
    newQtys[index] = val;
    setQtys(newQtys);
  };

  const handlePriceChange = (index: number, val: number) => {
    const newPrices = [...prices];
    newPrices[index] = val;
    setPrices(newPrices);
  };

  let headSum = 0;
  let totalWeight = 0;

  const rowData = schema.map((s, i) => {
    const q = qtys[i] || 0;
    const p = prices[i] || 0;
    const std = presets[stage][i];
    const isModified = q !== std;
    const costPerHead = s.g ? (q / 1000) * p : q * p;
    headSum += costPerHead;
    const batchQty = q * herdSize;
    if (!s.g) totalWeight += batchQty;
    return { ...s, q, p, isModified, costPerHead, batchQty, std };
  });

  const groupTotal = headSum * herdSize;

  const handleWhatsApp = () => {
    let t = `*TMR BATCH SHEET*\n*Stage:* ${stage.replace('_', ' ').toUpperCase()}\n*Animals:* ${herdSize}\n*Batch Weight:* ${Math.round(totalWeight)} KG\n*Cost/Head:* Rs. ${Math.round(headSum)}\n\n*Ingredients:*\n`;
    rowData.forEach((r) => { if (r.q > 0) t += `• ${r.name}: ${r.batchQty.toLocaleString()} ${r.u}\n`; });
    t += `\n_DairyOS – TMR Manager_`;
    window.open(`https://wa.me/?text=${encodeURIComponent(t)}`);
  };

  const formatPKR = (num: number) => num.toLocaleString('en-PK', { maximumFractionDigits: 0 });

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box', position: 'relative' }}>
      <style>{`
        @media print {
          body { background: white !important; color: black !important; }
          .no-print { display: none !important; }
          .print-header { color: black !important; }
          input, select { border: none !important; background: transparent !important; color: black !important; -webkit-appearance: none; }
          table { border: 1px solid #ccc; }
          th { background: #f1f5f9 !important; color: black !important; }
          td { border-bottom: 1px solid #ccc !important; }
        }
      `}</style>

      {/* =========================================================================
          SECTION 1: FEED & NUTRITION OPERATIONS (Restored Core Dashboard)
          ========================================================================= */}
      <div className="no-print" style={{ marginBottom: '40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={22} /> Feed & Nutrition Operations
            </h2>
            <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
              Track inventory, daily consumption, and active group rations.
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '20px' }}>
          {/* Inventory Overview */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '3px solid #34d399' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}><Database size={16} color="#34d399" /> Silage Bunker Status</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#34d399' }}>180 <span style={{ fontSize: '12px', color: '#94a3b8' }}>Tons Remaining</span></div>
            <div style={{ marginTop: '8px', background: '#1e293b', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: '45%', height: '100%', background: '#34d399' }}></div>
            </div>
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '6px' }}>Est. depletion in 42 days at current feed rate.</div>
          </div>

          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '3px solid #f59e0b' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}><Database size={16} color="#f59e0b" /> Vanda / Concentrate Stock</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>4,250 <span style={{ fontSize: '12px', color: '#94a3b8' }}>KG Remaining</span></div>
            <div style={{ marginTop: '8px', background: '#1e293b', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: '25%', height: '100%', background: '#f87171' }}></div>
            </div>
            <div style={{ fontSize: '10px', color: '#fca5a5', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}><AlertTriangle size={10} /> Low stock warning: Reorder soon.</div>
          </div>

          {/* Daily Metric */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', borderLeft: '3px solid #38bdf8' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}><Activity size={16} color="#38bdf8" /> Daily Feed Distribution</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#38bdf8' }}>1,850 <span style={{ fontSize: '12px', color: '#94a3b8' }}>KG Fed Today</span></div>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '8px', display: 'flex', justifyContent: 'space-between' }}>
              <span>Target: 1,900 KG</span>
              <span style={{ color: '#f87171', display: 'flex', alignItems: 'center', gap: '2px' }}><TrendingDown size={12} /> -2.6%</span>
            </div>
          </div>
        </div>
      </div>

      <hr className="no-print" style={{ border: 'none', borderTop: '2px dashed #1f2937', marginBottom: '30px' }} />

      {/* =========================================================================
          SECTION 2: TMR LIFE-CYCLE MANAGER (New Tool)
          ========================================================================= */}

      {/* ADVISORY MODAL */}
      {showModal && (
        <div className="no-print" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '16px' }}>
          <div style={{ background: '#111827', border: '1px solid #f59e0b', borderRadius: '12px', width: '100%', maxWidth: '600px', display: 'flex', flexDirection: 'column', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(245, 158, 11, 0.1)' }}>
              <h3 style={{ margin: 0, color: '#f59e0b', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Lightbulb size={18} /> Advisory: {stage.replace('_', ' ').toUpperCase()}
              </h3>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', color: '#f59e0b', cursor: 'pointer' }}><X size={20} /></button>
            </div>
            <div style={{ padding: '20px', color: '#cbd5e1', fontSize: '13px', lineHeight: '1.6' }}>
              <p style={{ marginBottom: '16px' }} dangerouslySetInnerHTML={{ __html: adviceStrings[stage].replace(/: /g, ': </b>').replace(/Strategy/g, '<b>Strategy') }} />
              <ul style={{ margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px', color: '#94a3b8' }}>
                <li><b>Mixing Order:</b> Straw → Silage → Vanda / SBM → Dry additives → Molasses last.</li>
                <li><b>Mix Time:</b> 3–5 minutes after last ingredient.</li>
                <li><b>Quality Check:</b> No visible sorting after 2 hours. Offer fresh within 1 hr of milking.</li>
                <li><b>Dry Matter:</b> Adjust silage quantity if DM changes &gt;2% between batches.</li>
              </ul>
              <div style={{ marginTop: '20px', fontSize: '11px', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(245, 158, 11, 0.1)', padding: '10px', borderRadius: '6px' }}>
                <AlertTriangle size={14} /> These are industry-standard starting points. Adjust based on on-farm milk records, BCS, and ration analysis results.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* HEADER SECTION */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', borderBottom: '1px solid #1f2937', paddingBottom: '20px', flexWrap: 'wrap', gap: '20px' }}>
        <div>
          <h2 className="print-header" style={{ margin: '0 0 6px 0', fontSize: '20px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Wheat size={22} /> TMR Life-Cycle Manager
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Updated: {new Date().toLocaleDateString('en-PK', { day:'numeric', month:'short', year:'numeric' })}</p>
            <span style={{ background: 'rgba(52, 211, 153, 0.15)', color: '#34d399', border: '1px solid #34d399', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle2 size={12}/> Defaults = HF Industry Standard
            </span>
          </div>
        </div>

        <div className="no-print" style={{ display: 'flex', gap: '15px', background: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flexGrow: 1, minWidth: '220px' }}>
            <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#94a3b8', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Animal Stage</label>
            <select 
              value={stage} 
              onChange={e => handleLoadTemplate(e.target.value)} 
              style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '6px', fontSize: '14px', fontWeight: 'bold', cursor: 'pointer', outline: 'none' }}
            >
              <optgroup label="Milking Cows">
                <option value="early_milking">Early Lactation (0–70 DIM)</option>
                <option value="mid_milking">Mid Lactation (70–200 DIM)</option>
                <option value="late_milking">Late Lactation (200–305 DIM)</option>
              </optgroup>
              <optgroup label="Dry Cows">
                <option value="far_off">Far-Off Dry (&gt;21d pre-calving)</option>
                <option value="close_up">Close-Up (last 21d pre-calving)</option>
              </optgroup>
              <optgroup label="Young Stock">
                <option value="heifer_growth">Growing Heifer</option>
                <option value="calf_starter">Calf Starter</option>
              </optgroup>
            </select>
            <div style={{ fontSize: '10px', color: '#38bdf8', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}><Info size={12}/> {stageInfo[stage]}</div>
          </div>
          <div>
            <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#94a3b8', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>Herd Size</label>
            <input 
              type="number" 
              value={herdSize === 0 ? '' : herdSize} 
              onChange={e => setHerdSize(Number(e.target.value))} 
              min="0" 
              style={{ width: '80px', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '6px', fontSize: '14px', fontWeight: 'bold', textAlign: 'center' }} 
            />
          </div>
        </div>
      </div>

      {/* ACTION BAR */}
      <div className="no-print" style={{ display: 'flex', gap: '10px', marginBottom: '20px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
        {saveNotify && <span style={{ color: '#34d399', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px', marginRight: 'auto' }}><CheckCircle2 size={16}/> Configuration Saved</span>}
        <button onClick={handleReset} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: '#94a3b8', border: '1px solid #334155', padding: '8px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
          <RotateCcw size={14}/> Reset to Standard
        </button>
        <button onClick={() => setShowModal(true)} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#f59e0b', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
          <Lightbulb size={14}/> Advisory
        </button>
        <button onClick={handleSave} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#2563eb', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
          <Save size={14}/> Save
        </button>
        <button onClick={() => window.print()} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#64748b', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
          <Printer size={14}/> Print
        </button>
        <button onClick={handleWhatsApp} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#22c55e', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
          <MessageCircle size={14}/> WhatsApp
        </button>
      </div>

      {/* DATA TABLE */}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflowX: 'auto', marginBottom: '24px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#0f172a', borderBottom: '1px solid #1f2937' }}>
              <th style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase' }}>Ingredient</th>
              <th style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase' }}>Qty / Head</th>
              <th className="no-print" style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase' }}>Price / KG</th>
              <th style={{ padding: '12px 16px', color: '#10b981', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', background: 'rgba(16, 185, 129, 0.1)', textAlign: 'center' }}>Batch Load ({herdSize} Head)</th>
              <th style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', textAlign: 'right' }}>Cost / Head</th>
            </tr>
          </thead>
          <tbody>
            {rowData.map((row, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #1a2234', background: row.q > 0 ? 'transparent' : 'rgba(15, 23, 42, 0.5)' }}>
                <td style={{ padding: '12px 16px', fontWeight: 'bold', color: row.q > 0 ? '#fff' : '#64748b' }}>
                  {row.name}
                  {row.isModified && <span className="no-print" style={{ display: 'inline-block', width: '6px', height: '6px', background: '#f59e0b', borderRadius: '50%', marginLeft: '8px', verticalAlign: 'middle' }} title="Modified from standard HF preset" />}
                </td>
                <td style={{ padding: '8px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input 
                      type="number" 
                      value={row.q === 0 ? '' : row.q} 
                      onChange={e => handleQtyChange(i, Number(e.target.value))}
                      step={row.step} min={row.min} max={row.max}
                      style={{ width: '70px', background: '#1e293b', color: row.isModified ? '#f59e0b' : '#38bdf8', border: '1px solid #334155', padding: '6px 8px', borderRadius: '4px', fontSize: '13px', fontWeight: 'bold' }} 
                    />
                    <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 'bold' }}>{row.u}</span>
                  </div>
                </td>
                <td className="no-print" style={{ padding: '8px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input 
                      type="number" 
                      value={row.p} 
                      onChange={e => handlePriceChange(i, Number(e.target.value))}
                      style={{ width: '70px', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '6px 8px', borderRadius: '4px', fontSize: '13px' }} 
                    />
                    <span style={{ fontSize: '11px', color: '#64748b' }}>/ kg</span>
                  </div>
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'center', background: 'rgba(16, 185, 129, 0.05)', color: row.batchQty > 0 ? '#34d399' : '#475569', fontWeight: 'bold', borderLeft: '2px solid rgba(16, 185, 129, 0.2)', borderRight: '2px solid rgba(16, 185, 129, 0.2)' }}>
                  {row.batchQty > 0 ? `${row.batchQty.toLocaleString()} ${row.u}` : '—'}
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 'bold', color: row.costPerHead > 0 ? '#cbd5e1' : '#475569' }}>
                  Rs. {formatPKR(row.costPerHead)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* FOOTER STATS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '20px', borderRadius: '8px', borderLeft: '4px solid #38bdf8' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#94a3b8', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>Cost / Head / Day</span>
          <span style={{ fontSize: '28px', fontWeight: 'bold', color: '#38bdf8', fontFamily: 'monospace' }}>Rs. {formatPKR(headSum)}</span>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '20px', borderRadius: '8px', borderLeft: '4px solid #34d399' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#94a3b8', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>Group Cost / Day</span>
          <span style={{ fontSize: '28px', fontWeight: 'bold', color: '#34d399', fontFamily: 'monospace' }}>Rs. {formatPKR(groupTotal)}</span>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '20px', borderRadius: '8px', borderLeft: '4px solid #f59e0b' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#94a3b8', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>Total Batch Weight</span>
          <span style={{ fontSize: '28px', fontWeight: 'bold', color: '#f59e0b', fontFamily: 'monospace' }}>{formatPKR(totalWeight)} <span style={{ fontSize: '14px' }}>KG</span></span>
        </div>
      </div>

    </div>
  );
}
