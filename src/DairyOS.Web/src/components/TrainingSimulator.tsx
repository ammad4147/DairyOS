import { useMemo, useState } from 'react';
import { BookOpenCheck, CheckCircle2, RotateCcw, ShieldCheck } from 'lucide-react';

type Scenario = {
  id: string;
  domain: string;
  title: string;
  situation: string;
  steps: string[];
  expected: string;
  next: string;
  safety: string;
};

const scenarios: Scenario[] = [
  {
    id: 'milk-late-entry',
    domain: 'Milk production',
    title: 'Enter a missed milking after the day has closed',
    situation: 'A real milking was missed during the shift and the operator is entering it later.',
    steps: [
      'Confirm the animal, milking session, and actual event date.',
      'Enter the measured litres once; do not substitute today\'s date.',
      'Save and verify the daily history and animal passport.',
      'Review period totals and any downstream COP or revenue impact.',
    ],
    expected: 'The late entry is retained against its actual operational date and remains identifiable as a completed historical fact.',
    next: 'If the entry is wrong, use the supported amendment path and preserve the original audit history.',
    safety: 'The simulator does not write to live milk records. In production, verify the saved identifier before retrying.',
  },
  {
    id: 'tmr-daily-cost',
    domain: 'Feed and TMR',
    title: 'Review a daily TMR calculation',
    situation: 'A manager wants to understand one day\'s feed cost and consumption.',
    steps: [
      'Select the operational date and active herd population.',
      'Review the effective category formulas and ingredient prices.',
      'Compare calculated kilograms and cost with recorded consumption.',
      'Investigate an unavailable or partial status before using the cost in COP.',
    ],
    expected: 'The daily result explains formula, herd, quantity, price, cost, and status without treating a purchase as consumption.',
    next: 'Use the selected-period calculation only after each required day has valid authority.',
    safety: 'Historical calculations are not rewritten by changing today\'s formula or herd strength.',
  },
  {
    id: 'health-withdrawal',
    domain: 'Health and veterinary',
    title: 'Record treatment and protect milk withdrawal',
    situation: 'A veterinarian has authorised treatment for a milking animal.',
    steps: [
      'Confirm the permanent animal identity and treatment authority.',
      'Record the actual treatment and approved withdrawal instruction.',
      'Check the active withdrawal state before handling milk.',
      'Record withheld milk through the disposition workflow and schedule follow-up.',
    ],
    expected: 'Treatment, withdrawal, non-sale milk, and follow-up remain linked and auditable.',
    next: 'Do not release milk until the authorised withdrawal condition is complete.',
    safety: 'The simulator never diagnoses, prescribes a product or dose, or overrides veterinary or regulatory instructions.',
  },
  {
    id: 'breeding-calving',
    domain: 'Breeding and reproduction',
    title: 'Move from pregnancy confirmation to calving',
    situation: 'A confirmed pregnant animal has now calved.',
    steps: [
      'Review the persisted reproductive chronology.',
      'Record the actual calving event and available offspring details.',
      'Refresh current reproductive state and the animal passport.',
      'Record fresh-cow milk, health, and follow-up events separately.',
    ],
    expected: 'Calving becomes the latest durable fact, the animal is no longer incorrectly shown as pregnant, and prior history remains intact.',
    next: 'Follow the approved post-calving health and breeding-readiness plan.',
    safety: 'A predicted calving date is not an actual calving event; clinical interpretation remains authorised-person work.',
  },
  {
    id: 'finance-reconcile',
    domain: 'Finance and revenue',
    title: 'Reconcile produced, sold, and non-sale milk',
    situation: 'A finance user sees total production higher than sold litres.',
    steps: [
      'Confirm the inclusive operational-date range.',
      'Reconcile valid produced litres with dispositions.',
      'Separate sold, non-sale, withheld, and unallocated litres.',
      'Check sale price, cash, receivable, amendments, and voids.',
    ],
    expected: 'Revenue uses valid sold litres while non-sale and unallocated quantities remain explainable.',
    next: 'Correct the source disposition or sale record, never the displayed total directly.',
    safety: 'Training data is synthetic and in memory; it cannot create finance entries or alter the ledger.',
  },
  {
    id: 'system-health',
    domain: 'Settings and support',
    title: 'Run a safe system-health check',
    situation: 'A supervisor wants readiness evidence before starting operations.',
    steps: [
      'Open the read-only health-check workflow.',
      'Review service, database, configuration, and runtime results.',
      'Capture the timestamp and any failed component.',
      'Escalate failures without resetting or editing the database.',
    ],
    expected: 'Readiness is assessed without changing operational data, database records, or backup artifacts.',
    next: 'Use the support evidence path if a component remains unavailable.',
    safety: 'The simulator has no database connection and the real health check must remain read-only.',
  },
];

export default function TrainingSimulator() {
  const [selectedId, setSelectedId] = useState(scenarios[0].id);
  const [step, setStep] = useState(0);
  const [completed, setCompleted] = useState(false);
  const scenario = useMemo(
    () => scenarios.find(item => item.id === selectedId) ?? scenarios[0],
    [selectedId],
  );

  const selectScenario = (id: string) => {
    setSelectedId(id);
    setStep(0);
    setCompleted(false);
  };

  const advance = () => {
    if (step >= scenario.steps.length - 1) {
      setCompleted(true);
      return;
    }
    setStep(value => value + 1);
  };

  const reset = () => {
    setStep(0);
    setCompleted(false);
  };

  return (
    <section style={{ padding: 18, color: '#f8fafc', maxWidth: 1120, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div>
          <div style={{ color: '#38bdf8', fontSize: 10, fontWeight: 900, letterSpacing: 1 }}>TRAINING SIMULATOR</div>
          <h2 style={{ margin: '4px 0', fontSize: 20 }}>Practice DairyOS workflows safely</h2>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: 11 }}>Guided scenarios use isolated in-memory training state. Nothing is sent to the live DairyOS API.</p>
        </div>
        <div style={{ display: 'inline-flex', gap: 6, alignItems: 'center', color: '#bbf7d0', fontSize: 10, fontWeight: 800 }}><ShieldCheck size={15} /> LIVE DATA PROTECTED</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(230px, .8fr) minmax(0, 1.8fr)', gap: 12, marginTop: 16 }}>
        <aside style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 10 }}>
          <div style={{ color: '#94a3b8', fontSize: 9, fontWeight: 900, textTransform: 'uppercase', marginBottom: 8 }}>Choose a scenario</div>
          <div style={{ display: 'grid', gap: 6 }}>
            {scenarios.map(item => (
              <button key={item.id} type="button" onClick={() => selectScenario(item.id)} style={{ textAlign: 'left', background: selectedId === item.id ? '#0c4a6e' : '#1e293b', color: '#f8fafc', border: selectedId === item.id ? '1px solid #38bdf8' : '1px solid #334155', borderRadius: 6, padding: '9px 10px', cursor: 'pointer' }}>
                <div style={{ fontSize: 9, color: selectedId === item.id ? '#bae6fd' : '#94a3b8', fontWeight: 800 }}>{item.domain}</div>
                <div style={{ marginTop: 3, fontSize: 11, fontWeight: 800 }}>{item.title}</div>
              </button>
            ))}
          </div>
        </aside>

        <article style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center' }}>
            <div>
              <div style={{ color: '#a78bfa', fontSize: 9, fontWeight: 900, textTransform: 'uppercase' }}>{scenario.domain}</div>
              <h3 style={{ margin: '4px 0', fontSize: 17 }}>{scenario.title}</h3>
            </div>
            <button type="button" onClick={reset} title="Restart scenario" aria-label="Restart scenario" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: '#1e293b', color: '#cbd5e1', border: '1px solid #334155', borderRadius: 6, padding: '7px 9px', cursor: 'pointer', fontSize: 10 }}><RotateCcw size={13} /> Restart</button>
          </div>
          <div style={{ marginTop: 10, padding: 10, background: '#0f172a', borderRadius: 6, color: '#cbd5e1', fontSize: 11 }}>{scenario.situation}</div>
          <div style={{ marginTop: 14, display: 'flex', gap: 5, alignItems: 'center' }} aria-label={`Scenario step ${step + 1} of ${scenario.steps.length}`}>
            {scenario.steps.map((_, index) => <span key={index} style={{ height: 5, flex: 1, borderRadius: 5, background: index <= step || completed ? '#38bdf8' : '#334155' }} />)}
          </div>
          {!completed ? (
            <div style={{ marginTop: 14 }}>
              <div style={{ color: '#64748b', fontSize: 9, fontWeight: 900, textTransform: 'uppercase' }}>Step {step + 1}</div>
              <div style={{ marginTop: 5, fontSize: 15, lineHeight: 1.45 }}>{scenario.steps[step]}</div>
              <button type="button" onClick={advance} style={{ marginTop: 15, display: 'inline-flex', alignItems: 'center', gap: 6, background: '#0369a1', color: '#fff', border: 0, borderRadius: 6, padding: '9px 12px', cursor: 'pointer', fontSize: 10, fontWeight: 900 }}>{step === scenario.steps.length - 1 ? 'Complete scenario' : 'Next step'} <BookOpenCheck size={13} /></button>
            </div>
          ) : (
            <div style={{ marginTop: 14, padding: 11, background: '#052e16', border: '1px solid #166534', borderRadius: 7 }}><div style={{ display: 'flex', gap: 6, alignItems: 'center', color: '#bbf7d0', fontWeight: 900, fontSize: 12 }}><CheckCircle2 size={15} /> Scenario complete</div><div style={{ marginTop: 8, fontSize: 11, lineHeight: 1.45 }}>{scenario.expected}</div></div>
          )}
          <div style={{ marginTop: 13, display: 'grid', gap: 8 }}>
            <div style={{ padding: 10, background: '#0f172a', borderRadius: 6 }}><div style={{ color: '#38bdf8', fontSize: 9, fontWeight: 900, textTransform: 'uppercase' }}>What happens next</div><div style={{ marginTop: 4, fontSize: 11, color: '#cbd5e1' }}>{scenario.next}</div></div>
            <div style={{ padding: 10, background: '#1c1917', border: '1px solid #78350f', borderRadius: 6 }}><div style={{ color: '#fbbf24', fontSize: 9, fontWeight: 900, textTransform: 'uppercase' }}>Safety boundary</div><div style={{ marginTop: 4, fontSize: 11, color: '#fde68a' }}>{scenario.safety}</div></div>
          </div>
        </article>
      </div>
    </section>
  );
}
