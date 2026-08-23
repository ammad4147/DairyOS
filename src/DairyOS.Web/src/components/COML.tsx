import React, { useEffect, useMemo, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

export type COMLOutput = {
  milkProduced: number;
  feedTotal: number;
  opexTotal: number;
  feedCostPerLiter: number;
  opexCostPerLiter: number;
  costOfMilkProductionPerLiter: number;
};

interface COMLProps {
  onOutputChange?: (output: COMLOutput) => void;
}

type CostRow = { id: string; item: string; cost: number };
type Group = { label: string; items: string[] };

type StoredMonthlyOutput = COMLOutput & { month: string };

const COML_STORAGE_KEY = 'dairyos_coml_monthly_output';
const COML_EVENT = 'dairyos:coml-output';

const FEED_GROUPS: Group[] = [
  { label: 'Green Fodder & Silage', items: ['Corn / Maize Silage','Alfalfa (Lucerne)','Berseem','Rhodes Grass (Fresh)','Sorghum / Sadabahar','Super Napier / Mott Grass','Rye Grass'] },
  { label: 'Dry Roughages & Hay', items: ['Wheat Straw (Bhoosa)','Rhodes Grass Hay','Alfalfa Hay','Corn Stover'] },
  { label: 'Commercial Feeds & Grains', items: ['Commercial Compound Vanda / Cattle Feed','Flaked Corn / Cracked Maize','Wheat Bran (Choker)','Rice Polish','Barley','Broken Rice'] },
  { label: 'Protein Meals & Cakes', items: ['Canola Meal','Soybean Meal (Hi-Pro)','Mustard Cake (Khal Sarson)','Cottonseed Cake (Khal Banola)','Sunflower Meal','Corn Gluten Meal (30% / 60%)'] },
  { label: 'Minerals, Premixes & Additives', items: ['Dairy Mineral Premix','Di-Calcium Phosphate (DCP)','Bypass Fat / Rumen-Protected Fat','Sodium Bicarbonate (Buffer)','Toxin Binder','Live Yeast / Probiotics','Molasses','Urea','Rock Salt / Mineral Licking Blocks'] },
  { label: 'Custom', items: ['Other'] },
];

const OPEX_GROUPS: Group[] = [
  { label: 'Veterinary & Herd Health', items: ['Routine Vet Fees / Consultation','Vaccinations (FMD, HS, LSD, Anthrax)','Dewormers & Parasiticides','Mastitis Injectables & Intramammary Tubes','Antibiotics & General Medications','Calving & OB Supplies'] },
  { label: 'Breeding & Reproduction', items: ['Semen Straws (Sexed / Conventional)','AI Consumables (Sheaths, Gloves, Lube)','Synchronization Hormones (GnRH, PGF2α)','AI Inseminator Service Charges'] },
  { label: 'Labor & Salaries', items: ['Milker Wages','Feeder / Shed Worker Wages','Supervisor / Farm Manager Salary','Daily / Temporary Labor','Staff Rations & Living Expenses'] },
  { label: 'Utilities & Energy', items: ['Grid Electricity (WAPDA)','Generator Fuel (Diesel / Petrol)','Solar System Maintenance & Inverter Servicing','Water Pumping & Borehole Maintenance'] },
  { label: 'Machinery & Infrastructure', items: ['Milking Machine Liners, Tubes & Oil','Milk Chiller / Cooling Tank Maintenance','Silage Cutter / Feed Mixer Repairs','Tractor Diesel & Servicing','Shed Maintenance & Plumbing Repairs'] },
  { label: 'Dairy Chemicals & Hygiene', items: ['Acid Cleaner (Milkstone Remover)','Alkaline CIP Detergent','Chlorine / Sanitizer','Teat Dip (Pre & Post Dip)','Shed Disinfectants & Lime Powder'] },
  { label: 'Bedding, Logistics & Miscellaneous', items: ['Animal Bedding (Sand, Sawdust, Straw)','Milk Transport & Delivery Fuel','Packaging / Milk Cans','Farm Land Lease / Rent','Accounting & Banking Fees'] },
  { label: 'Custom', items: ['Other'] },
];

const inputStyle: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', border: '1px solid #334155', color: '#fff', borderRadius: 6, padding: '9px 10px', fontSize: 12, outline: 'none' };
const panelStyle: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 16, minWidth: 0 };
const money = (v: number) => `PKR ${v.toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

function TaxonomySelect({ groups, selected, value, onChange, placeholder }: { groups: Group[]; selected: Set<string>; value: string; onChange: (v: string) => void; placeholder: string }) {
  return <select value={value} onChange={e => onChange(e.target.value)} style={inputStyle}>
    <option value="">{placeholder}</option>
    {groups.map(group => {
      const available = group.items.filter(item => !selected.has(item));
      return available.length ? <optgroup key={group.label} label={group.label}>{available.map(item => <option key={item} value={item}>{item}</option>)}</optgroup> : null;
    })}
  </select>;
}

function Rows({ rows, accent, remove }: { rows: CostRow[]; accent: string; remove: (id: string) => void }) {
  if (!rows.length) return <div style={{ marginTop: 12, padding: 18, textAlign: 'center', borderTop: '1px solid #1f2937', color: '#64748b', fontSize: 11 }}>No entries added yet.</div>;
  return <div style={{ marginTop: 12, borderTop: '1px solid #1f2937' }}>{rows.map(row => <div key={row.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: '1px solid #1a2234' }}>
    <div style={{ flex: 1, minWidth: 0, color: '#e2e8f0', fontSize: 11, fontWeight: 700 }}>{row.item}</div>
    <div style={{ color: accent, fontSize: 12, fontWeight: 900, whiteSpace: 'nowrap' }}>{money(row.cost)}</div>
    <button type="button" onClick={() => remove(row.id)} title="Remove entry" style={{ width: 28, height: 28, borderRadius: 5, border: '1px solid #334155', background: '#1e293b', color: '#94a3b8', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}><Trash2 size={12} /></button>
  </div>)}</div>;
}

function Metric({ title, accent, children }: { title: string; accent: string; children: React.ReactNode }) {
  return <div style={{ ...panelStyle, borderLeft: `4px solid ${accent}`, minHeight: 86 }}>
    <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 800 }}>{title}</div>
    <div style={{ fontSize: 19, fontWeight: 900, color: accent, marginTop: 8 }}>{children}</div>
  </div>;
}

function monthKey() {
  return new Date().toISOString().slice(0, 7);
}

function publishMonthlyOutput(output: COMLOutput) {
  const month = monthKey();
  const stored: Record<string, StoredMonthlyOutput> = (() => {
    try {
      return JSON.parse(localStorage.getItem(COML_STORAGE_KEY) || '{}') as Record<string, StoredMonthlyOutput>;
    } catch {
      return {};
    }
  })();

  stored[month] = { month, ...output };
  localStorage.setItem(COML_STORAGE_KEY, JSON.stringify(stored));

  window.dispatchEvent(new CustomEvent(COML_EVENT, { detail: stored[month] }));
}

export default function COML({ onOutputChange }: COMLProps) {
  const [milkProduced, setMilkProduced] = useState('');
  const [feedItem, setFeedItem] = useState('');
  const [feedCostInput, setFeedCostInput] = useState('');
  const [opexItem, setOpexItem] = useState('');
  const [opexCostInput, setOpexCostInput] = useState('');
  const [feedRows, setFeedRows] = useState<CostRow[]>([]);
  const [opexRows, setOpexRows] = useState<CostRow[]>([]);

  const selectedFeed = useMemo(() => new Set(feedRows.map(r => r.item)), [feedRows]);
  const selectedOpex = useMemo(() => new Set(opexRows.map(r => r.item)), [opexRows]);
  const feedTotal = useMemo(() => feedRows.reduce((s, r) => s + r.cost, 0), [feedRows]);
  const opexTotal = useMemo(() => opexRows.reduce((s, r) => s + r.cost, 0), [opexRows]);
  const litres = Math.max(0, Number(milkProduced) || 0);
  const feedPerL = litres > 0 ? feedTotal / litres : 0;
  const opexPerL = litres > 0 ? opexTotal / litres : 0;
  const comlPerL = feedPerL + opexPerL;

  useEffect(() => {
    const output: COMLOutput = {
      milkProduced: litres,
      feedTotal,
      opexTotal,
      feedCostPerLiter: feedPerL,
      opexCostPerLiter: opexPerL,
      costOfMilkProductionPerLiter: comlPerL,
    };

    publishMonthlyOutput(output);
    onOutputChange?.(output);
  }, [onOutputChange, litres, feedTotal, opexTotal, feedPerL, opexPerL, comlPerL]);

  const addFeed = () => {
    const cost = Number(feedCostInput);
    if (!feedItem || !Number.isFinite(cost) || cost < 0) return;
    setFeedRows(rows => [...rows, { id: `feed-${Date.now()}-${Math.random()}`, item: feedItem, cost }]);
    setFeedItem(''); setFeedCostInput('');
  };

  const addOpex = () => {
    const cost = Number(opexCostInput);
    if (!opexItem || !Number.isFinite(cost) || cost < 0) return;
    setOpexRows(rows => [...rows, { id: `opex-${Date.now()}-${Math.random()}`, item: opexItem, cost }]);
    setOpexItem(''); setOpexCostInput('');
  };

  return <div style={{ padding: 20, color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
    <div style={{ marginBottom: 16 }}>
      <h2 style={{ margin: '0 0 4px 0', fontSize: 18, color: '#34d399' }}>Cost of Production/Liter</h2>
      <p style={{ margin: 0, fontSize: 12, color: '#94a3b8' }}>Independent manual cost calculator.</p>
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
      <Metric title="Milk Produced" accent="#38bdf8"><input type="number" min="0" step="0.01" value={milkProduced} onChange={e => setMilkProduced(e.target.value)} placeholder="Litres" style={{ ...inputStyle, marginTop: 7, fontSize: 16, fontWeight: 900 }} /></Metric>
      <Metric title="Feed Cost/Liter" accent="#34d399">{money(feedPerL)}</Metric>
      <Metric title="Operational Expenses/Liter" accent="#f59e0b">{money(opexPerL)}</Metric>
      <Metric title="Cost of Milk Production/Liter" accent="#a78bfa">{money(comlPerL)}</Metric>
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12, alignItems: 'start' }}>
      <section style={panelStyle}>
        <h3 style={{ margin: '0 0 12px', fontSize: 14, color: '#34d399' }}>Feed Cost Calculator</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 120px auto', gap: 8, alignItems: 'end' }}>
          <label style={{ color: '#94a3b8', fontSize: 10, fontWeight: 800, textTransform: 'uppercase' }}>Feed Item<div style={{ marginTop: 5 }}><TaxonomySelect groups={FEED_GROUPS} selected={selectedFeed} value={feedItem} onChange={setFeedItem} placeholder="Select feed item" /></div></label>
          <label style={{ color: '#94a3b8', fontSize: 10, fontWeight: 800, textTransform: 'uppercase' }}>Cost<input type="number" min="0" step="0.01" value={feedCostInput} onChange={e => setFeedCostInput(e.target.value)} placeholder="PKR" style={{ ...inputStyle, marginTop: 5 }} /></label>
          <button type="button" onClick={addFeed} disabled={!feedItem || feedCostInput === ''} style={{ background: '#059669', color: '#fff', border: 'none', borderRadius: 6, padding: '9px 12px', fontSize: 10, fontWeight: 900, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 5, opacity: !feedItem || feedCostInput === '' ? 0.45 : 1 }}><Plus size={12} /> Add</button>
        </div>
        <Rows rows={feedRows} accent="#34d399" remove={id => setFeedRows(rows => rows.filter(r => r.id !== id))} />
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><span style={{ color: '#94a3b8', fontSize: 10, fontWeight: 800, textTransform: 'uppercase' }}>Feed Total</span><span style={{ color: '#34d399', fontSize: 16, fontWeight: 900 }}>{money(feedTotal)}</span></div>
      </section>

      <section style={panelStyle}>
        <h3 style={{ margin: '0 0 12px', fontSize: 14, color: '#f59e0b' }}>Operational Cost Calculator</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 120px auto', gap: 8, alignItems: 'end' }}>
          <label style={{ color: '#94a3b8', fontSize: 10, fontWeight: 800, textTransform: 'uppercase' }}>Operating Expense<div style={{ marginTop: 5 }}><TaxonomySelect groups={OPEX_GROUPS} selected={selectedOpex} value={opexItem} onChange={setOpexItem} placeholder="Select operating expense" /></div></label>
          <label style={{ color: '#94a3b8', fontSize: 10, fontWeight: 800, textTransform: 'uppercase' }}>Cost<input type="number" min="0" step="0.01" value={opexCostInput} onChange={e => setOpexCostInput(e.target.value)} placeholder="PKR" style={{ ...inputStyle, marginTop: 5 }} /></label>
          <button type="button" onClick={addOpex} disabled={!opexItem || opexCostInput === ''} style={{ background: '#d97706', color: '#fff', border: 'none', borderRadius: 6, padding: '9px 12px', fontSize: 10, fontWeight: 900, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 5, opacity: !opexItem || opexCostInput === '' ? 0.45 : 1 }}><Plus size={12} /> Add</button>
        </div>
        <Rows rows={opexRows} accent="#f59e0b" remove={id => setOpexRows(rows => rows.filter(r => r.id !== id))} />
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><span style={{ color: '#94a3b8', fontSize: 10, fontWeight: 800, textTransform: 'uppercase' }}>Operational Total</span><span style={{ color: '#f59e0b', fontSize: 16, fontWeight: 900 }}>{money(opexTotal)}</span></div>
      </section>
    </div>
  </div>;
}
