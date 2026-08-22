import React from 'react';
import { useAlertAudit } from '../context/AlertAuditContext';
import { X, ShieldAlert } from 'lucide-react';

export default function AlertModal({ onClose }: { onClose: () => void }) {
  const { alerts, markResolved } = useAlertAudit();
  
  return (
    <div style={{ position: 'fixed', top: 0, right: 0, width: '420px', height: '100vh', background: '#0f172a', borderLeft: '1px solid #1f2937', zIndex: 9999, display: 'flex', flexDirection: 'column', boxShadow: '-10px 0 25px rgba(0,0,0,0.5)' }}>
      
      {/* Header (Fixed) */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid #1e293b', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38bdf8' }}>
          <ShieldAlert size={20} />
          <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 'bold' }}>System Audit & Alerts</h2>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={20} /></button>
      </div>

      {/* Scrollable Content Container */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {alerts.map((alert) => (
          <div key={alert.id} style={{ background: '#111827', padding: '14px', borderRadius: '8px', borderLeft: '4px solid ' + (alert.status === 'ACTIVE' ? '#ef4444' : '#34d399'), border: '1px solid #1f2937', flexShrink: 0 }}>
            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff', marginBottom: '4px' }}>{alert.title}</div>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px' }}>Source: <strong>{alert.source}</strong> | Status: <span style={{ color: alert.status === 'ACTIVE' ? '#f87171' : '#34d399' }}>{alert.status}</span></div>
            <p style={{ fontSize: '12px', color: '#cbd5e1', margin: '0 0 10px 0' }}>{alert.details}</p>
            {alert.status === 'ACTIVE' && (
              <button 
                onClick={() => markResolved(alert.id, 'Operator', 'Resolved via Alert Bell')}
                style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                Mark Resolved
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
