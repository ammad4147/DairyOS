import React, { createContext, useContext, useState } from 'react';

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
  markResolved: (id: string, operator?: string, notes?: string) => void;
  adminReinstate: (id: string, adminName?: string, reason?: string) => void;
  activeCount: number;
}

const AlertAuditContext = createContext<AlertAuditContextType | undefined>(undefined);

export const AlertAuditProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [alerts, setAlerts] = useState<AuditAlertItem[]>([
    {
      id: 'ALT-1001',
      source: 'HEALTH_WITHDRAWAL',
      animalId: 'TD-004',
      title: 'Mandatory Milk Withdrawal Active (Clinical Mastitis)',
      details: 'Milk withholding required for 3 days due to intramammary antibiotic treatment.',
      initialLevel: 'RED',
      currentLevel: 'RED',
      status: 'ACTIVE',
      createdAt: '2026-08-20 06:00:00',
    },
    {
      id: 'ALT-1002',
      source: 'MILK_DROP',
      animalId: 'TD-009',
      title: 'Severe Yield Drop Alert (-34.1% vs Baseline)',
      details: 'Recorded 29.0 L vs expected 44.0 L. Modality 3x Daily.',
      initialLevel: 'RED',
      currentLevel: 'RED',
      status: 'ACTIVE',
      createdAt: '2026-08-20 07:05:00',
    },
    {
      id: 'ALT-1003',
      source: 'MILK_DROP',
      animalId: 'TD-003',
      title: 'Amber Drop Warning (-17.1% vs Baseline)',
      details: 'Recorded 29.0 L vs expected 35.0 L. Ration check recommended.',
      initialLevel: 'AMBER',
      currentLevel: 'AMBER',
      status: 'ACTIVE',
      createdAt: '2026-08-20 06:45:00',
    },
    {
      id: 'ALT-1004',
      source: 'RECONCILIATION',
      title: 'Mass-Balance Variance (11.2 L Unaccounted)',
      details: 'Total produced yield exceeds recorded sales, domestic, and calf feeding logs.',
      initialLevel: 'AMBER',
      currentLevel: 'AMBER',
      status: 'RESOLVED',
      createdAt: '2026-08-19 18:30:00',
      resolvedAt: '2026-08-19 19:15:22',
      resolvedBy: 'Ammad Hassan',
      resolutionNotes: 'Calf bucket 2 entry was delayed. Reconciled after log entry.',
    }
  ]);

  const markResolved = (id: string, operator = 'Ammad Hassan', notes = 'Operator marked resolved') => {
    const now = new Date();
    const timestamp = now.getFullYear() + '-' +
      String(now.getMonth() + 1).padStart(2, '0') + '-' +
      String(now.getDate()).padStart(2, '0') + ' ' +
      now.toLocaleTimeString('en-GB');

    setAlerts(prev => prev.map(item => {
      if (item.id === id) {
        return {
          ...item,
          status: 'RESOLVED',
          resolvedAt: timestamp,
          resolvedBy: operator,
          resolutionNotes: notes
        };
      }
      return item;
    }));
  };

  const adminReinstate = (id: string, adminName = 'Ammad Hassan (Admin)', reason = 'Erroneous resolution override') => {
    const now = new Date();
    const timestamp = now.getFullYear() + '-' +
      String(now.getMonth() + 1).padStart(2, '0') + '-' +
      String(now.getDate()).padStart(2, '0') + ' ' +
      now.toLocaleTimeString('en-GB');

    setAlerts(prev => prev.map(item => {
      if (item.id === id) {
        return {
          ...item,
          status: 'REINSTATED',
          currentLevel: 'RED', // Enforces total red urgency
          reinstatedAt: timestamp,
          reinstatedBy: adminName,
          reinstateReason: reason
        };
      }
      return item;
    }));
  };

  const activeCount = alerts.filter(a => a.status === 'ACTIVE' || a.status === 'REINSTATED').length;

  return (
    <AlertAuditContext.Provider value={{ alerts, markResolved, adminReinstate, activeCount }}>
      {children}
    </AlertAuditContext.Provider>
  );
};

export const useAlertAudit = () => {
  const context = useContext(AlertAuditContext);
  if (!context) throw new Error('useAlertAudit must be used within an AlertAuditProvider');
  return context;
};
