import React, { createPortal, useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AlertAuditProvider } from './context/AlertAuditContext';
import { installAuthenticatedFetch } from './auth';

installAuthenticatedFetch();

type MonthlyComlOutput = {
  month: string;
  costOfMilkProductionPerLiter: number;
};

const COML_STORAGE_KEY = 'dairyos_coml_monthly_output';
const COML_EVENT = 'dairyos:coml-output';

function currentMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

function readCurrentComlOutput(): MonthlyComlOutput | null {
  try {
    const raw = localStorage.getItem(COML_STORAGE_KEY);
    if (!raw) return null;

    const entries = JSON.parse(raw) as Record<string, MonthlyComlOutput>;
    const entry = entries[currentMonth()];

    if (!entry || !Number.isFinite(Number(entry.costOfMilkProductionPerLiter))) {
      return null;
    }

    return {
      month: entry.month,
      costOfMilkProductionPerLiter: Number(entry.costOfMilkProductionPerLiter),
    };
  } catch {
    return null;
  }
}

function ComlDashboardBox() {
  const [target, setTarget] = useState<HTMLElement | null>(null);
  const [output, setOutput] = useState<MonthlyComlOutput | null>(() => readCurrentComlOutput());

  useEffect(() => {
    const findTarget = () => {
      const rows = document.querySelectorAll<HTMLElement>('.cmd-card .stat-row');
      const candidate = Array.from(rows).find((row) => {
        const title = row.previousElementSibling;
        return title instanceof HTMLElement && title.textContent?.includes('Milk Production & Farm Yield');
      });

      if (!candidate) return;

      candidate.style.gridTemplateColumns = 'repeat(5,minmax(0,1fr))';
      setTarget(candidate);
    };

    findTarget();

    const observer = new MutationObserver(findTarget);
    observer.observe(document.body, { childList: true, subtree: true });

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const refresh = () => setOutput(readCurrentComlOutput());
    window.addEventListener(COML_EVENT, refresh);
    window.addEventListener('storage', refresh);

    return () => {
      window.removeEventListener(COML_EVENT, refresh);
      window.removeEventListener('storage', refresh);
    };
  }, []);

  if (!target) return null;

  const monthLabel = output?.month
    ? new Date(`${output.month}-01T00:00:00`).toLocaleDateString('en-PK', {
        month: 'short',
        year: 'numeric',
      })
    : new Date().toLocaleDateString('en-PK', {
        month: 'short',
        year: 'numeric',
      });

  return createPortal(
    <div style={{ background: '#1e293b', padding: 6, borderRadius: 6, minWidth: 0 }}>
      <div style={{ fontSize: 8, color: '#94a3b8' }}>Cost of Milk Production/Liter</div>
      <div style={{ fontSize: 13, fontWeight: 900, color: '#a78bfa', marginTop: 2 }}>
        PKR {(output?.costOfMilkProductionPerLiter ?? 0).toLocaleString('en-PK', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}
      </div>
      <div style={{ fontSize: 7, color: '#64748b', marginTop: 2 }}>{monthLabel}</div>
    </div>,
    target,
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AlertAuditProvider>
      <App />
      <ComlDashboardBox />
    </AlertAuditProvider>
  </React.StrictMode>,
);
