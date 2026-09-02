import React, { useState } from 'react';
import { useAlertAudit } from '../context/AlertAuditContext';
import { ShieldAlert, Search, Filter, RotateCcw, CheckCircle2 } from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';

export default function AuditTab() {
  const { alerts, markResolved, reinstateAlert } = useAlertAudit();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL'); // ALL, ACTIVE, REINSTATED, RESOLVED
  const [overrideAlertId, setOverrideAlertId] = useState<string | null>(null);
  const [overrideReason, setOverrideReason] = useState('');
  const [selectedPassportId, setSelectedPassportId] = useState<string | null>(null);

  const filteredAlerts = alerts.filter(a => {
    const matchesSearch = (a.id + a.title + a.details + a.animalId + a.resolvedBy).toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'ALL' ? true : a.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const handleTriggerReinstate = (e: React.FormEvent) => {
    e.preventDefault();
    if (overrideAlertId && overrideReason) {
      reinstateAlert(overrideAlertId, 'Ammad Hassan (Admin)', overrideReason);
      setOverrideAlertId(null);
      setOverrideReason('');
    }
  };

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={22} /> Warning Audit Register
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Authoritative, tamper-evident security audit log tracking all operational alerts, resolution timestamps, and administrator overrides.
          </p>
        </div>
      </div>

      {/* KPI TILES */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #ef4444' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Active Warnings</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f87171' }}>{alerts.filter(a => a.status === 'ACTIVE').length}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #dc2626' }}>
          <div style={{ fontSize: '10px', color: '#fca5a5' }}>Admin Reinstated</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#ef4444' }}>{alerts.filter(a => a.status === 'REINSTATED').length}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Resolved & Logged</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#34d399' }}>{alerts.filter(a => a.status === 'RESOLVED').length}</div>
        </div>
        <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>Total Ledger Entries</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff' }}>{alerts.length}</div>
        </div>
      </div>

      {/* CONTROLS BAR */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#111827', padding: '10px 14px', borderRadius: '6px', border: '1px solid #1f2937', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '320px' }}>
          <Search size={14} color="#94a3b8" />
          <input
            type="text"
            placeholder="Search by ID, Animal, Title, or Operator..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', width: '100%', outline: 'none' }}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={14} color="#94a3b8" />
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>Filter Audit Status:</span>
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '5px 8px', borderRadius: '4px', fontSize: '11px' }}
          >
            <option value="ALL">All Audit Statuses</option>
            <option value="ACTIVE">Active Warnings</option>
            <option value="REINSTATED">Admin Reinstated</option>
            <option value="RESOLVED">Resolved Entries</option>
          </select>
        </div>
      </div>

      {/* AUDIT TABLE */}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
              <th style={{ padding: '10px 12px' }}>Audit ID</th>
              <th style={{ padding: '10px 12px' }}>Warning Title & Details</th>
              <th style={{ padding: '10px 12px' }}>Animal ID</th>
              <th style={{ padding: '10px 12px' }}>Created Timestamp</th>
              <th style={{ padding: '10px 12px' }}>Resolution / Override Audit Trail</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAlerts.map(a => {
              const isReinstated = a.status === 'REINSTATED';
              const isResolved = a.status === 'RESOLVED';

              return (
                <tr key={a.id} style={{ borderBottom: '1px solid #1a2234', background: isReinstated ? 'rgba(239, 68, 68, 0.18)' : (isResolved ? 'transparent' : 'rgba(251, 191, 36, 0.05)') }}>
                  <td style={{ padding: '10px 12px', fontWeight: 'bold', color: isReinstated ? '#f87171' : '#38bdf8' }}>{a.id}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ fontWeight: 'bold', color: isReinstated ? '#f87171' : (a.currentLevel === 'RED' ? '#f87171' : '#fbbf24') }}>
                      {isReinstated && '🚨 [REINSTATED] '} {a.title}
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>{a.details}</div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    {a.animalId ? (
                      <button
                        onClick={() => setSelectedPassportId(a.animalId!)}
                        style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
                      >
                        #{a.animalId}
                      </button>
                    ) : (
                      <span style={{ color: '#64748b' }}>-</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#cbd5e1' }}>{a.createdAt}</td>
                  <td style={{ padding: '10px 12px' }}>
                    {a.lifecycleEvents.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                        {a.lifecycleEvents.map((event, index) => {
                          const eventColor =
                            event.eventType === 'REINSTATED'
                              ? '#f87171'
                              : event.eventType === 'RESOLVED'
                                ? '#34d399'
                                : event.eventType === 'ACKNOWLEDGED'
                                  ? '#38bdf8'
                                  : '#fbbf24';
                          return (
                            <div
                              key={event.eventId}
                              style={{
                                borderLeft: `2px solid ${eventColor}`,
                                paddingLeft: '7px',
                                fontSize: '10px',
                              }}
                            >
                              <div style={{ color: eventColor, fontWeight: 700 }}>
                                {String(index + 1).padStart(2, '0')} · {event.eventType}
                                {event.linkedEventId
                                  ? ` · linked to event #${event.linkedEventId}`
                                  : ''}
                              </div>
                              <div style={{ color: '#94a3b8' }}>
                                {event.occurredAt}
                                {event.operator ? ` · ${event.operator}` : ''}
                              </div>
                              {event.note && (
                                <div style={{ color: '#cbd5e1' }}>{event.note}</div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '11px' }}>
                        Legacy finding — lifecycle history pending migration.
                      </span>
                    )}
                    {a.status === 'ACTIVE' && (
                      <div style={{ color: '#fbbf24', fontSize: '11px', marginTop: 5 }}>
                        Pending Operator Resolution
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                    {isResolved && (
                      <button
                        onClick={() => setOverrideAlertId(a.id)}
                        style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                      >
                        <RotateCcw size={12} /> Admin Reinstate
                      </button>
                    )}
                    {(a.status === 'ACTIVE' || isReinstated) && (
                      <button
                        onClick={() => {
                          const note = isReinstated
                            ? window.prompt(
                                `Resolution note for reinstated warning #${a.id}:`,
                                '',
                              )
                            : 'Manual Resolution via Audit Tab';
                          if (isReinstated && !note?.trim()) {
                            return;
                          }
                          void markResolved(
                            a.id,
                            'Ammad Hassan (Admin)',
                            note || 'Manual Resolution via Audit Tab',
                          );
                        }}
                        style={{ background: '#059669', color: '#fff', border: 'none', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                      >
                        <CheckCircle2 size={12} /> {isReinstated ? 'Resolve Reinstatement' : 'Resolve'}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ADMIN REINSTATE OVERRIDE MODAL */}
      {overrideAlertId && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #ef4444', borderRadius: '8px', padding: '24px', width: '450px' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <RotateCcw size={18} /> Admin Reinstate Warning #{overrideAlertId}
            </h3>
            <p style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '16px' }}>
              Reopening this warning marks it as active again across all dashboards and registers an immutable administrator override.
            </p>
            <form onSubmit={handleTriggerReinstate}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Reason for Override / Reinstatement</label>
                <textarea
                  required
                  value={overrideReason}
                  onChange={e => setOverrideReason(e.target.value)}
                  placeholder="e.g. Somatic cell count still elevated; resolution premature."
                  style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '8px', borderRadius: '4px', fontSize: '12px', minHeight: '70px', boxSizing: 'border-box' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" onClick={() => setOverrideAlertId(null)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '4px', cursor: 'pointer' }}>
                  Cancel
                </button>
                <button type="submit" style={{ background: '#dc2626', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
                  Confirm Reinstatement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* ANIMAL PASSPORT MODAL */}
      {selectedPassportId && (
        <AnimalPassportModal 
          animalId={selectedPassportId} 
          onClose={() => setSelectedPassportId(null)} 
        />
      )}
    </div>
  );
}
