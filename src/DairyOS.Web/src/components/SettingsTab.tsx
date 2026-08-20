import React, { useState } from 'react';
import { 
  ShieldAlert, CheckCircle2, RotateCcw, Search, Filter, Clock, 
  Award, Building, Users, FileText, Upload, Plus, Save 
} from 'lucide-react';
import { useAlertAudit } from '../context/AlertAuditContext';
import AnimalPassportModal from './AnimalPassportModal';

export default function SettingsTab() {
  const [activeTab, setActiveTab] = useState<'FARM' | 'USERS' | 'DOCS' | 'AUDIT'>('FARM');

  // =======================================================================
  // AUDIT REGISTER STATE (Preserved)
  // =======================================================================
  const { alerts, markResolved, adminReinstate } = useAlertAudit();
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedPassportId, setSelectedPassportId] = useState<string | null>(null);
  const [overrideAlertId, setOverrideAlertId] = useState<string | null>(null);
  const [overrideReason, setOverrideReason] = useState<string>('');

  const handleTriggerReinstate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!overrideAlertId) return;
    adminReinstate(overrideAlertId, 'Ammad Hassan (Admin)', overrideReason || 'Erroneous resolution canceled by manager');
    setOverrideAlertId(null);
    setOverrideReason('');
  };

  const filteredAlerts = alerts.filter(a => {
    const matchesStatus = filterStatus === 'ALL' || a.status === filterStatus;
    const matchesSearch = 
      a.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (a.animalId && a.animalId.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (a.resolvedBy && a.resolvedBy.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  // =======================================================================
  // FARM PROFILE STATE
  // =======================================================================
  const [farmName, setFarmName] = useState('Barki Dairy Farm');
  const [location, setLocation] = useState('Lahore, Punjab, PK');
  const [regNumber, setRegNumber] = useState('LFA-88912-PK');
  const [farmSaved, setFarmSaved] = useState(false);

  const handleSaveFarm = (e: React.FormEvent) => {
    e.preventDefault();
    setFarmSaved(true);
    setTimeout(() => setFarmSaved(false), 2000);
  };

  // =======================================================================
  // USERS & DOCUMENTS MOCK DATA
  // =======================================================================
  const users = [
    { name: 'Ammad Hassan', role: 'Owner / Admin', email: 'ammad@barkidairy.com', status: 'Active' },
    { name: 'Dr. Tariq Mahmood', role: 'Chief Veterinarian', email: 'tariq.vet@barkidairy.com', status: 'Active' },
    { name: 'Salman Masroor Khan', role: 'Farm Manager', email: 'salman@barkidairy.com', status: 'Active' },
  ];

  const documents = [
    { name: 'LFA Commercial Dairy License.pdf', type: 'Compliance', date: '2025-01-15' },
    { name: 'SkyElectric Solar Lease Agreement.pdf', type: 'Contract', date: '2025-07-10' },
    { name: 'Barkat Feed Mill - Annual Supply Contract.pdf', type: 'Contract', date: '2026-02-01' },
    { name: 'Quarterly Vet Inspection Report.pdf', type: 'Medical', date: '2026-07-30' },
  ];

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      
      {/* GLOBAL HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Building size={22} /> System Settings & Administration
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Manage farm profile, user access, compliance documents, and review the security audit ledger.
          </p>
        </div>
      </div>

      {/* SUB-NAVIGATION TABS */}
      <div style={{ display: 'flex', borderBottom: '1px solid #1f2937', marginBottom: '20px' }}>
        <button 
          onClick={() => setActiveTab('FARM')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'FARM' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'FARM' ? '2px solid #38bdf8' : 'none', padding: '10px 16px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
        >
          <Building size={16} /> Farm Profile & Setup
        </button>
        <button 
          onClick={() => setActiveTab('USERS')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'USERS' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'USERS' ? '2px solid #38bdf8' : 'none', padding: '10px 16px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
        >
          <Users size={16} /> User Management
        </button>
        <button 
          onClick={() => setActiveTab('DOCS')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'DOCS' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'DOCS' ? '2px solid #38bdf8' : 'none', padding: '10px 16px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
        >
          <FileText size={16} /> Documents & Compliance
        </button>
        <button 
          onClick={() => setActiveTab('AUDIT')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'AUDIT' ? '#ef4444' : '#94a3b8', border: 'none', borderBottom: activeTab === 'AUDIT' ? '2px solid #ef4444' : 'none', padding: '10px 16px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
        >
          <ShieldAlert size={16} /> Warning Audit Register
        </button>
      </div>

      {/* =====================================================================
          TAB 1: FARM PROFILE & SETUP 
          ===================================================================== */}
      {activeTab === 'FARM' && (
        <div style={{ maxWidth: '600px' }}>
          <form onSubmit={handleSaveFarm} style={{ background: '#111827', border: '1px solid #1f2937', padding: '24px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '15px', color: '#fff', borderBottom: '1px solid #1f2937', paddingBottom: '10px' }}>
              Primary Farm Information
            </h3>
            
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Registered Farm Name</label>
              <input type="text" value={farmName} onChange={e => setFarmName(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }} />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Geographic Location / HQ</label>
              <input type="text" value={location} onChange={e => setLocation(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }} />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Livestock & Dairy Development (LFA) Registration #</label>
              <input type="text" value={regNumber} onChange={e => setRegNumber(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
              {farmSaved ? (
                <span style={{ color: '#34d399', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}><CheckCircle2 size={14}/> Settings Saved</span>
              ) : <span />}
              <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '10px 20px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Save size={16} /> Save Profile
              </button>
            </div>
          </form>
        </div>
      )}

      {/* =====================================================================
          TAB 2: USER MANAGEMENT 
          ===================================================================== */}
      {activeTab === 'USERS' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '15px', color: '#fff' }}>Authorized System Users</h3>
            <button style={{ background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px 16px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Plus size={14}/> Invite New User
            </button>
          </div>
          
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#161f30', borderBottom: '1px solid #1f2937', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '12px 16px' }}>Name</th>
                  <th style={{ padding: '12px 16px' }}>Role / Permission Level</th>
                  <th style={{ padding: '12px 16px' }}>Email</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1a2234' }}>
                    <td style={{ padding: '12px 16px', color: '#fff', fontWeight: 'bold' }}>{u.name}</td>
                    <td style={{ padding: '12px 16px', color: '#38bdf8' }}>{u.role}</td>
                    <td style={{ padding: '12px 16px', color: '#cbd5e1' }}>{u.email}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <span style={{ background: 'rgba(52, 211, 153, 0.2)', color: '#34d399', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>{u.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* =====================================================================
          TAB 3: DOCUMENTS & COMPLIANCE 
          ===================================================================== */}
      {activeTab === 'DOCS' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '15px', color: '#fff' }}>Farm Document Repository</h3>
            <button style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Upload size={14}/> Upload Document
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
            {documents.map((doc, i) => (
              <div key={i} style={{ background: '#111827', border: '1px solid #1f2937', padding: '16px', borderRadius: '8px', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <div style={{ background: '#1e293b', padding: '10px', borderRadius: '8px', color: '#ef4444' }}>
                  <FileText size={24} />
                </div>
                <div>
                  <div style={{ color: '#fff', fontSize: '13px', fontWeight: 'bold', marginBottom: '4px' }}>{doc.name}</div>
                  <div style={{ color: '#94a3b8', fontSize: '11px', display: 'flex', gap: '8px' }}>
                    <span style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px' }}>{doc.type}</span>
                    <span>Added: {doc.date}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =====================================================================
          TAB 4: WARNING AUDIT REGISTER (Restored & Intact)
          ===================================================================== */}
      {activeTab === 'AUDIT' && (
        <div>
          {/* KPI Tiles */}
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

          {/* Controls Bar */}
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

          {/* Audit Register Table */}
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
                          {isReinstated && '🚨 [ADMIN REINSTATED] '} {a.title}
                        </div>
                        <div style={{ fontSize: '10px', color: isReinstated ? '#fca5a5' : '#94a3b8', marginTop: '2px' }}>{a.details}</div>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        {a.animalId ? (
                          <button 
                            onClick={() => setSelectedPassportId(a.animalId!)}
                            style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', textDecoration: 'underline', padding: 0, fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '3px' }}
                          ><Award size={12} /> #{a.animalId}</button>
                        ) : <span style={{ color: '#64748b' }}>System-wide</span>}
                      </td>
                      <td style={{ padding: '10px 12px', color: '#cbd5e1', fontSize: '11px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Clock size={12} color="#94a3b8" /> {a.createdAt}</div>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        {isResolved && (
                          <div style={{ fontSize: '11px', color: '#34d399' }}>
                            <div><strong>Resolved:</strong> {a.resolvedAt}</div>
                            <div style={{ color: '#94a3b8' }}>By: <strong>{a.resolvedBy}</strong> ({a.resolutionNotes})</div>
                          </div>
                        )}
                        {isReinstated && (
                          <div style={{ fontSize: '11px', color: '#f87171' }}>
                            <div><strong>Reinstated:</strong> {a.reinstatedAt}</div>
                            <div>By: <strong>{a.reinstatedBy}</strong></div>
                            <div style={{ fontStyle: 'italic', color: '#fca5a5' }}>Reason: "{a.reinstateReason}"</div>
                          </div>
                        )}
                        {a.status === 'ACTIVE' && (
                          <span style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' }}>PENDING RESOLUTION</span>
                        )}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                        {a.status === 'ACTIVE' && (
                          <button 
                            onClick={() => markResolved(a.id, 'Ammad Hassan', 'Verified on farm')}
                            style={{ background: '#059669', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                          ><CheckCircle2 size={13} /> Mark Resolved</button>
                        )}
                        {a.status === 'RESOLVED' && (
                          <button 
                            onClick={() => setOverrideAlertId(a.id)}
                            style={{ background: '#7f1d1d', border: '1px solid #ef4444', color: '#fca5a5', padding: '5px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                          ><RotateCcw size={13} /> Admin Reinstate</button>
                        )}
                        {isReinstated && (
                          <button 
                            onClick={() => markResolved(a.id, 'Ammad Hassan (Re-Audit)', 'Resolved post admin audit')}
                            style={{ background: '#b91c1c', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                          ><CheckCircle2 size={13} /> Close Reinstated</button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ADMIN OVERRIDE REINSTATE MODAL */}
      {overrideAlertId && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '16px' }}>
          <form onSubmit={handleTriggerReinstate} style={{ background: '#111827', border: '2px solid #ef4444', padding: '24px', borderRadius: '10px', width: '100%', maxWidth: '460px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1f2937', paddingBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <RotateCcw size={18} color="#ef4444" />
                <h3 style={{ margin: 0, color: '#f87171', fontSize: '16px' }}>Admin Reinstatement Override</h3>
              </div>
              <button type="button" onClick={() => setOverrideAlertId(null)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>✕</button>
            </div>
            <p style={{ margin: 0, fontSize: '12px', color: '#cbd5e1' }}>
              You are overturning resolution for Audit Item <strong style={{ color: '#38bdf8' }}>{overrideAlertId}</strong>. This warning will immediately reappear across the Main Dashboard and Operational Modules rendered in <strong style={{ color: '#ef4444' }}>TOTAL RED</strong>.
            </p>
            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Administrative Justification / Reason</label>
              <input type="text" required placeholder="e.g., Erroneously marked resolved before clinical verification" value={overrideReason} onChange={e => setOverrideReason(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '6px' }}>
              <button type="button" onClick={() => setOverrideAlertId(null)} style={{ background: '#1e293b', border: '1px solid #374151', color: '#94a3b8', padding: '7px 14px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}>Cancel</button>
              <button type="submit" style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '7px 16px', borderRadius: '4px', fontWeight: 'bold', fontSize: '11px', cursor: 'pointer' }}>Execute Red Reinstatement</button>
            </div>
          </form>
        </div>
      )}

      {/* PASSPORT MODAL */}
      {selectedPassportId && (
        <AnimalPassportModal animalId={selectedPassportId} onClose={() => setSelectedPassportId(null)} />
      )}

    </div>
  );
}
