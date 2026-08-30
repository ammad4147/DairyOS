import React, { createContext, useContext, useEffect, useState } from 'react';
import { getStoredUser } from '../auth';
import { apiUrl } from '../config/api';

export interface AuditAlertItem {
  id: string;
  source: 'MILK_DROP' | 'HEALTH_WITHDRAWAL' | 'BREEDING_HEAT' | 'RECONCILIATION' | 'SYSTEM';
  animalId?: string;
  title: string;
  details: string;
  initialLevel: 'AMBER' | 'RED' | 'INFO';
  currentLevel: 'AMBER' | 'RED' | 'INFO';
  status: 'ACTIVE' | 'RESOLVED' | 'REINSTATED';
  createdAt: string;
  resolvedAt?: string;
  resolvedBy?: string;
  resolutionNotes?: string;
  reinstatedAt?: string;
  reinstatedBy?: string;
  reinstateReason?: string;
}

interface AlertAuditContextType {
  alerts: AuditAlertItem[];
  markResolved: (id: string, operator?: string, notes?: string) => Promise<void>;
  adminReinstate: (id: string, adminName?: string, reason?: string) => Promise<void>;
  reinstateAlert: (id: string, adminName?: string, reason?: string) => Promise<void>;
  activeCount: number;
}

interface FindingPayload {
  finding_id: string;
  source_module?: string;
  subject_type?: string | null;
  subject_id?: string | null;
  severity?: string;
  title?: string;
  detail?: string | null;
  status?: string;
  raised_at?: string | null;
  resolved_at?: string | null;
  resolved_by?: string | null;
  resolution_note?: string | null;
  reinstated_at?: string | null;
  reinstated_by?: string | null;
  reinstate_reason?: string | null;
}

const AlertAuditContext = createContext<AlertAuditContextType | undefined>(undefined);

function mapSource(source?: string): AuditAlertItem['source'] {
  switch ((source || '').toUpperCase()) {
    case 'MILK': return 'MILK_DROP';
    case 'HEALTH': return 'HEALTH_WITHDRAWAL';
    case 'BREEDING': return 'BREEDING_HEAT';
    case 'RECONCILIATION': return 'RECONCILIATION';
    default: return 'SYSTEM';
  }
}

function mapLevel(severity?: string): AuditAlertItem['initialLevel'] {
  switch ((severity || '').toUpperCase()) {
    case 'RED':
    case 'CRITICAL':
    case 'HIGH': return 'RED';
    case 'AMBER':
    case 'MEDIUM': return 'AMBER';
    case 'INFORMATION': return 'INFO';
    default: return 'AMBER';
  }
}

function mapStatus(status?: string): AuditAlertItem['status'] {
  switch ((status || '').toUpperCase()) {
    case 'RESOLVED': return 'RESOLVED';
    case 'REINSTATED': return 'REINSTATED';
    default: return 'ACTIVE';
  }
}

function toAlert(finding: FindingPayload): AuditAlertItem {
  const level = mapLevel(finding.severity);
  return {
    id: finding.finding_id,
    source: mapSource(finding.source_module),
    animalId: finding.subject_id || undefined,
    title: finding.title || 'Operational Finding',
    details: finding.detail || 'Persisted operational finding.',
    initialLevel: level,
    currentLevel: finding.status === 'REINSTATED' ? 'RED' : level,
    status: mapStatus(finding.status),
    createdAt: finding.raised_at || '',
    resolvedAt: finding.resolved_at || undefined,
    resolvedBy: finding.resolved_by || undefined,
    resolutionNotes: finding.resolution_note || undefined,
    reinstatedAt: finding.reinstated_at || undefined,
    reinstatedBy: finding.reinstated_by || undefined,
    reinstateReason: finding.reinstate_reason || undefined,
  };
}

async function loadFindings(): Promise<AuditAlertItem[]> {
  const response = await fetch(apiUrl('/farm/findings'));
  if (!response.ok) throw new Error(`Unable to load operational findings (${response.status})`);
  const payload = await response.json() as { findings?: FindingPayload[] };
  return Array.isArray(payload.findings) ? payload.findings.map(toAlert) : [];
}

export const AlertAuditProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [alerts, setAlerts] = useState<AuditAlertItem[]>([]);

  const refresh = async () => {
    try {
      setAlerts(await loadFindings());
    } catch (error) {
      console.error('DairyOS operational findings load failed:', error);
      setAlerts([]);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const markResolved = async (
    id: string,
    operator = getStoredUser()?.username || 'UI Operator',
    notes = 'Operator marked resolved',
  ) => {
    const response = await fetch(apiUrl(`/farm/findings/${encodeURIComponent(id)}/resolve`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator, resolution_note: notes }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => null) as { detail?: string } | null;
      throw new Error(payload?.detail || `Unable to resolve finding (${response.status})`);
    }
    await refresh();
  };

  const adminReinstate = async (
    id: string,
    adminName = getStoredUser()?.username || 'Administrator',
    reason = 'Administrative reinstatement',
  ) => {
    const response = await fetch(apiUrl(`/farm/findings/${encodeURIComponent(id)}/reinstate`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operator: adminName, reason }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => null) as { detail?: string } | null;
      throw new Error(payload?.detail || `Unable to reinstate finding (${response.status})`);
    }
    await refresh();
  };

  const activeCount = alerts.filter(
    alert => alert.status === 'ACTIVE' || alert.status === 'REINSTATED',
  ).length;

  return (
    <AlertAuditContext.Provider
      value={{
        alerts,
        markResolved,
        adminReinstate,
        reinstateAlert: adminReinstate,
        activeCount,
      }}
    >
      {children}
    </AlertAuditContext.Provider>
  );
};

export const useAlertAudit = () => {
  const context = useContext(AlertAuditContext);
  if (!context) throw new Error('useAlertAudit must be used within an AlertAuditProvider');
  return context;
};
