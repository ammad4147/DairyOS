import React, { useState } from 'react';
import FinanceTab from './FinanceTab';
import MilkTab from './MilkTab';
import ReportingTab from './ReportingTab';

type Props = { identity: { display_name: string; role: string; entry_group: string }; onLogout: () => void };

/** Human operator entry point using the same authoritative domain forms as Management. */
export default function HumanOperatorConsole({ identity, onLogout }: Props) {
  const milk = identity.entry_group === 'MILK_OPERATOR';
  const [view, setView] = useState<'domain' | 'reports'>('domain');
  return (
    <div style={shell}>
      <header style={header}>
        <div><h1>{milk ? 'Milk Operator' : 'Accounts Operator'}</h1><div>{identity.display_name} · {identity.role}</div></div>
        <div style={actions}>
          {!milk && <button type="button" onClick={() => setView(view === 'reports' ? 'domain' : 'reports')} style={button}>{view === 'reports' ? 'Back to Accounts' : 'RECONCILIATION & AUDIT STATEMENTS'}</button>}
          <button type="button" onClick={onLogout} style={button}>Logout</button>
        </div>
      </header>
      {view === 'reports' ? <ReportingTab /> : milk ? <MilkTab operatorMode /> : <FinanceTab />}
    </div>
  );
}

const shell: React.CSSProperties = { minHeight: '100vh', background: '#0b0f19', color: '#f8fafc', fontFamily: 'sans-serif', padding: 24, boxSizing: 'border-box' };
const header: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, marginBottom: 24 };
const actions: React.CSSProperties = { display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' };
const button: React.CSSProperties = { background: '#0284c7', color: '#fff', border: 0, borderRadius: 6, padding: '10px 12px', fontWeight: 800, cursor: 'pointer' };
