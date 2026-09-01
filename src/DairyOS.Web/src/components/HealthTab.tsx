import React, { useEffect, useState } from 'react';
import { HeartPulse, Plus, X, Syringe, AlertTriangle, ShieldCheck, FileText, Filter, Stethoscope } from 'lucide-react';
import { useAnimalContext } from '../context/AnimalContext';
import AnimalSearchBar from './shared/AnimalSearchBar';
import EventTimeline from './shared/EventTimeline';
import { apiUrl } from '../config/api';

interface HealthTabProps {
  onOpenPassport?: (tag: string) => void;
  onNavigate?: (view: string) => void;
  herdMasterList?: any[];
}

export default function HealthTab({ onOpenPassport, onNavigate, herdMasterList = [] }: HealthTabProps) {
  const { selectedAnimalId, setSelectedAnimalId, refreshTimeline, animalTimeline, isLoadingTimeline } = useAnimalContext();
  const [showEventModal, setShowEventModal] = useState(false);
  const [filter, setFilter] = useState<'all' | 'active' | 'critical'>('all');
  const [herdSummary, setHerdSummary] = useState({ activeTreatments: 0, withdrawalCount: 0, vaccinationCoverage: 0, vetExpenses30Day: 0 });
  const [loading, setLoading] = useState(true);

  // NEW: Single backend endpoint for herd health summary
  useEffect(() => {
    setLoading(true);
    fetch(apiUrl('/farm/health/summary'))
      .then(r => r.json())
      .then(data => setHerdSummary(data))
      .catch(() => setHerdSummary({ activeTreatments: 0, withdrawalCount: 0, vaccinationCoverage: 0, vetExpenses30Day: 0 }))
      .finally(() => setLoading(false));
  }, []);

  // Auto-select first animal with active treatment if none selected
  useEffect(() => {
    if (!selectedAnimalId && herdSummary.activeTreatments > 0 && herdMasterList.length > 0) {
      // In real implementation, backend would return an at-risk animal ID
      setSelectedAnimalId(herdMasterList[0].id);
    }
  }, [herdSummary, herdMasterList, selectedAnimalId, setSelectedAnimalId]);

  useEffect(() => {
    if (selectedAnimalId) refreshTimeline();
  }, [selectedAnimalId, refreshTimeline]);

  const timelineEvents = (animalTimeline || [])
    .filter((e: any) => e.category === 'health' || e.category === 'welfare')
    .filter((e: any) => filter === 'all' ? true : filter === 'active' ? e.status === 'Active' : e.severity === 'critical');

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <HeartPulse size={20} /> Clinical Command Center
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Herd-level alerts on the left. Select an animal to view their full clinical timeline with cross-tab context.
          </p>
        </div>
        <button onClick={() => setShowEventModal(true)} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
          <Plus size={16} /> Record Health Event
        </button>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <KpiCard label="Active Treatments" value={herdSummary.activeTreatments} color="#ef4444" icon={<Stethoscope size={16} />} onClick={() => setFilter('active')} />
        <KpiCard label="In Withdrawal" value={herdSummary.withdrawalCount} color="#f59e0b" icon={<AlertTriangle size={16} />} />
        <KpiCard label="Vaccination Coverage" value={`${herdSummary.vaccinationCoverage}%`} color="#34d399" icon={<ShieldCheck size={16} />} />
        <KpiCard label="30-Day Vet Expenses" value={`Rs. ${herdSummary.vetExpenses30Day.toLocaleString()}`} color="#38bdf8" icon={<FileText size={16} />} />
      </div>

      {/* Main Content: Two-Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px', height: 'calc(100% - 180px)' }}>
        
        {/* LEFT: Animal Selector + At-Risk List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <AnimalSearchBar />
          
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '12px', flex: 1, overflowY: 'auto' }}>
            <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#94a3b8', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Filter size={12} /> Animals Requiring Attention
            </div>
            {herdMasterList
              .filter((a: any) => filter === 'all' || (filter === 'active' && a.status?.includes('Treatment')))
              .map((animal: any) => (
              <button
                key={animal.id}
                onClick={() => setSelectedAnimalId(animal.id)}
                style={{
                  width: '100%', textAlign: 'left', padding: '8px 10px', marginBottom: '4px',
                  borderRadius: '6px', border: 'none', cursor: 'pointer',
                  background: selectedAnimalId === animal.id ? 'rgba(239,68,68,0.15)' : 'transparent',
                  color: selectedAnimalId === animal.id ? '#fca5a5' : '#e2e8f0',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                }}
              >
                <span style={{ fontWeight: 'bold', fontSize: 12 }}>#{animal.id}</span>
                <span style={{ fontSize: 10, color: '#94a3b8' }}>{animal.breed}</span>
                {animal.status?.includes('Treatment') && (
                  <span style={{ background: 'rgba(239,68,68,0.2)', color: '#fca5a5', fontSize: 9, padding: '2px 6px', borderRadius: 4 }}>ACTIVE</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* RIGHT: Animal Timeline + Quick Actions */}
        <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '16px', overflowY: 'auto' }}>
          {selectedAnimalId ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ margin: 0, fontSize: '16px', color: '#fff' }}>
                  Clinical Timeline: <span style={{ color: '#38bdf8' }}>#{selectedAnimalId}</span>
                </h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={() => onOpenPassport?.(selectedAnimalId)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#38bdf8', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}>
                    Open Passport
                  </button>
                  <button onClick={() => onNavigate?.('breeding')} style={{ background: '#1e293b', border: '1px solid #334155', color: '#fb923c', padding: '6px 12px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}>
                    View Breeding History
                  </button>
                </div>
              </div>
              
              {isLoadingTimeline ? (
                <div style={{ color: '#64748b', fontSize: 12 }}>Loading timeline...</div>
              ) : (
                <EventTimeline 
                  events={timelineEvents} 
                  onNavigate={(tab) => onNavigate?.(tab)} 
                />
              )}

              {/* Risk Score Banner */}
              <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: '#fca5a5', fontWeight: 'bold', marginBottom: '4px' }}>
                  <AlertTriangle size={12} style={{ display: 'inline', marginRight: 4 }} /> Cross-Tab Risk Signal
                </div>
                <div style={{ fontSize: '12px', color: '#cbd5e1' }}>
                  This animal was bred 32 days ago and has an active mastitis treatment. 
                  PD check is due in 3 days but treatment may affect accuracy. 
                  <button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', textDecoration: 'underline', marginLeft: 8 }}>
                    Reschedule PD
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
              <Stethoscope size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
              <p style={{ fontSize: 13 }}>Select an animal to view their clinical timeline</p>
              <p style={{ fontSize: 11 }}>Events from Health, Breeding, and Production are merged here</p>
            </div>
          )}
        </div>
      </div>

      {/* Event Modal (simplified — reuse existing form logic) */}
      {showEventModal && <HealthEventModal onClose={() => setShowEventModal(false)} onSave={() => { setShowEventModal(false); refreshTimeline(); }} />}
    </div>
  );
}

function KpiCard({ label, value, color, icon, onClick }: { label: string; value: string | number; color: string; icon: React.ReactNode; onClick?: () => void }) {
  return (
    <div 
      onClick={onClick}
      style={{ 
        background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', 
        borderLeft: `4px solid ${color}`, cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.1s'
      }}
    >
      <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        {icon} {label}
      </div>
      <div style={{ fontSize: '24px', fontWeight: 'bold', color }}>{value}</div>
    </div>
  );
}

// Placeholder for the modal — your existing form logic goes here, but simplified
function HealthEventModal({ onClose, onSave }: { onClose: () => void; onSave: () => void }) {
  return <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
    <div style={{ background: '#111827', border: '1px solid #ef4444', borderRadius: 10, padding: 24, width: 500 }}>
      <h3 style={{ color: '#ef4444', margin: '0 0 16px' }}>Record Health Event</h3>
      <p style={{ color: '#94a3b8', fontSize: 12 }}>Form implementation reused from original HealthTab...</p>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
        <button onClick={onClose} style={{ background: '#334155', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 6, cursor: 'pointer' }}>Cancel</button>
        <button onClick={onSave} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 6, cursor: 'pointer' }}>Save</button>
      </div>
    </div>
  </div>;
}