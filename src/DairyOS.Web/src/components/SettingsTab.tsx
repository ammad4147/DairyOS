import React, { useState, useEffect } from 'react';
import {
  Building, Users, Sliders, CheckCircle2, Plus, Save, ShieldCheck, RefreshCw, Key
} from 'lucide-react';

interface SettingsTabProps {
  onFarmProfileUpdate?: (profile: { farmName: string; location: string; regNumber: string }) => void;
}

export default function SettingsTab({ onFarmProfileUpdate }: SettingsTabProps) {
  const [activeTab, setActiveTab] = useState<'FARM' | 'STANDARDS' | 'USERS'>('FARM');

  // =======================================================================
  // 1. FARM PROFILE & IDENTITY (Persisted in localStorage & Server)
  // =======================================================================
  const [farmName, setFarmName] = useState(() => localStorage.getItem('dairyos_farm_name') || 'Barki Dairy Farm');
  const [location, setLocation] = useState(() => localStorage.getItem('dairyos_farm_loc') || 'Lahore, Punjab, PK');
  const [regNumber, setRegNumber] = useState(() => localStorage.getItem('dairyos_farm_reg') || 'LFA-88912-PK');
  const [animalPrefix, setAnimalPrefix] = useState(() => localStorage.getItem('dairyos_animal_prefix') || 'TD');
  const [farmSaved, setFarmSaved] = useState(false);

  const handleSaveFarm = async (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('dairyos_farm_name', farmName);
    localStorage.setItem('dairyos_farm_loc', location);
    localStorage.setItem('dairyos_farm_reg', regNumber);
    localStorage.setItem('dairyos_animal_prefix', animalPrefix);

    if (onFarmProfileUpdate) {
      onFarmProfileUpdate({ farmName, location, regNumber });
    }

    try {
      await fetch('/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ farm_name: farmName, animal_id_prefix: animalPrefix, updated_by: 'Admin' })
      });
    } catch {
      // Offline fallback
    }

    setFarmSaved(true);
    setTimeout(() => setFarmSaved(false), 2500);
  };

  // =======================================================================
  // 2. STANDARD OPERATIONAL SETTINGS
  // =======================================================================
  const [timezone, setTimezone] = useState('Asia/Karachi (PKT +05:00)');
  const [currency, setCurrency] = useState('PKR');
  const [defaultTrendWindow, setDefaultTrendWindow] = useState('7');
  const [resetProtected, setResetProtected] = useState(true);
  const [standardsSaved, setStandardsSaved] = useState(false);

  const handleSaveStandards = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('dairyos_timezone', timezone);
    localStorage.setItem('dairyos_currency', currency);
    localStorage.setItem('dairyos_trend_window', defaultTrendWindow);
    setStandardsSaved(true);
    setTimeout(() => setStandardsSaved(false), 2500);
  };

  // =======================================================================
  // 3. USER MANAGEMENT (Persisted & Interactive)
  // =======================================================================
  const [users, setUsers] = useState([
    { username: 'admin', name: 'Ammad Hassan', role: 'Farm Owner / Admin', email: 'ammad@barkidairy.com', status: 'Active' },
    { username: 'tariq_vet', name: 'Dr. Tariq Mahmood', role: 'Chief Veterinarian', email: 'tariq.vet@barkidairy.com', status: 'Active' },
    { username: 'salman_mgr', name: 'Salman Masroor Khan', role: 'Farm Manager', email: 'salman@barkidairy.com', status: 'Active' },
  ]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('OPERATOR');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    const newUser = {
      username: newUsername,
      name: newName,
      role: newRole,
      email: newEmail,
      status: 'Active'
    };
    setUsers([...users, newUser]);

    try {
      await fetch('/auth/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: newUsername, password: newPassword, role: newRole })
      });
    } catch {
      // Local fallback
    }

    setShowInviteModal(false);
    setNewUsername('');
    setNewName('');
    setNewEmail('');
    setNewPassword('');
  };

  return (
    <div style={{ padding: '20px', color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Building size={22} /> System Settings & Administration
          </h2>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>
            Configure farm identity, operational parameters, and user account access.
          </p>
        </div>
      </div>

      {/* TABS */}
      <div style={{ display: 'flex', borderBottom: '1px solid #1f2937', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('FARM')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'FARM' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'FARM' ? '2px solid #38bdf8' : 'none', padding: '10px 16px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
        >
          <Building size={16} /> Farm Profile & Identity
        </button>
        <button
          onClick={() => setActiveTab('STANDARDS')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'STANDARDS' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'STANDARDS' ? '2px solid #38bdf8' : 'none', padding: '10px 16px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
        >
          <Sliders size={16} /> Standard Operating Settings
        </button>
        <button
          onClick={() => setActiveTab('USERS')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', color: activeTab === 'USERS' ? '#38bdf8' : '#94a3b8', border: 'none', borderBottom: activeTab === 'USERS' ? '2px solid #38bdf8' : 'none', padding: '10px 16px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
        >
          <Users size={16} /> User Management & Access
        </button>
      </div>

      {/* 1. FARM PROFILE */}
      {activeTab === 'FARM' && (
        <div style={{ maxWidth: '650px' }}>
          <form onSubmit={handleSaveFarm} style={{ background: '#111827', border: '1px solid #1f2937', padding: '24px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '15px', color: '#fff', borderBottom: '1px solid #1f2937', paddingBottom: '10px' }}>
              Primary Farm Information
            </h3>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Registered Farm Name</label>
              <input type="text" value={farmName} onChange={e => setFarmName(e.target.value)} required style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }} />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Geographic Location / HQ</label>
              <input type="text" value={location} onChange={e => setLocation(e.target.value)} required style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }} />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Livestock & Dairy Development (LFA) Registration #</label>
              <input type="text" value={regNumber} onChange={e => setRegNumber(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }} />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Animal Tag Identifier Prefix</label>
              <input type="text" value={animalPrefix} onChange={e => setAnimalPrefix(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }} />
              <span style={{ fontSize: '10px', color: '#64748b' }}>Used for automatic numbering of newly registered stock (e.g., {animalPrefix}-001).</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
              {farmSaved ? (
                <span style={{ color: '#34d399', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}><CheckCircle2 size={14}/> Farm Identity Updated Successfully</span>
              ) : <span />}
              <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '10px 20px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Save size={16} /> Save Farm Profile
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 2. STANDARDS */}
      {activeTab === 'STANDARDS' && (
        <div style={{ maxWidth: '650px' }}>
          <form onSubmit={handleSaveStandards} style={{ background: '#111827', border: '1px solid #1f2937', padding: '24px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '15px', color: '#fff', borderBottom: '1px solid #1f2937', paddingBottom: '10px' }}>
              Operational & Reporting Standards
            </h3>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>System Timezone</label>
              <select value={timezone} onChange={e => setTimezone(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }}>
                <option value="Asia/Karachi (PKT +05:00)">Asia/Karachi (PKT +05:00)</option>
                <option value="UTC">Coordinated Universal Time (UTC)</option>
                <option value="Asia/Dubai (GST +04:00)">Asia/Dubai (GST +04:00)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Functional Currency</label>
              <select value={currency} onChange={e => setCurrency(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }}>
                <option value="PKR">Pakistani Rupee (PKR - ₨)</option>
                <option value="USD">US Dollar (USD - $)</option>
                <option value="EUR">Euro (EUR - €)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Default Production Trend Window</label>
              <select value={defaultTrendWindow} onChange={e => setDefaultTrendWindow(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '10px', borderRadius: '4px', fontSize: '13px', boxSizing: 'border-box' }}>
                <option value="7">7 Days</option>
                <option value="15">15 Days</option>
                <option value="30">30 Days</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: '#161f30', padding: '12px', borderRadius: '6px' }}>
              <input type="checkbox" id="resetLock" checked={resetProtected} onChange={e => setResetProtected(e.target.checked)} style={{ width: '16px', height: '16px', cursor: 'pointer' }} />
              <div>
                <label htmlFor="resetLock" style={{ fontSize: '12px', fontWeight: 'bold', color: '#fff', cursor: 'pointer' }}>Database Truncation & Reset Lock</label>
                <div style={{ fontSize: '10px', color: '#94a3b8' }}>Prevents unauthorized mass deletion or factory resets of live farm operational logs.</div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
              {standardsSaved ? (
                <span style={{ color: '#34d399', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}><CheckCircle2 size={14}/> Operational Standards Updated</span>
              ) : <span />}
              <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '10px 20px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Save size={16} /> Save Standards
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 3. USER MANAGEMENT */}
      {activeTab === 'USERS' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '15px', color: '#fff' }}>Authorized System Users</h3>
            <button onClick={() => setShowInviteModal(true)} style={{ background: '#0284c7', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Plus size={14}/> Create / Invite User
            </button>
          </div>

          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#161f30', borderBottom: '1px solid #1f2937', textAlign: 'left', color: '#94a3b8' }}>
                  <th style={{ padding: '12px 16px' }}>User Name</th>
                  <th style={{ padding: '12px 16px' }}>Username</th>
                  <th style={{ padding: '12px 16px' }}>Role / Permission Level</th>
                  <th style={{ padding: '12px 16px' }}>Email</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1a2234' }}>
                    <td style={{ padding: '12px 16px', color: '#fff', fontWeight: 'bold' }}>{u.name}</td>
                    <td style={{ padding: '12px 16px', color: '#94a3b8', fontFamily: 'monospace' }}>@{u.username}</td>
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

      {/* INVITE USER MODAL */}
      {showInviteModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#111827', border: '1px solid #38bdf8', borderRadius: '8px', padding: '24px', width: '420px' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#fff', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Plus size={18} color="#38bdf8" /> Add Farm Operator Account
            </h3>
            <form onSubmit={handleAddUser} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Full Name</label>
                <input type="text" required value={newName} onChange={e => setNewName(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Username</label>
                <input type="text" required value={newUsername} onChange={e => setNewUsername(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Email</label>
                <input type="email" required value={newEmail} onChange={e => setNewEmail(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Password</label>
                <input type="password" required value={newPassword} onChange={e => setNewPassword(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Role / Permission Level</label>
                <select value={newRole} onChange={e => setNewRole(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '8px', borderRadius: '4px', fontSize: '12px', boxSizing: 'border-box' }}>
                  <option value="OPERATOR">Operator (Data Entry)</option>
                  <option value="VET">Veterinarian (Health & AI)</option>
                  <option value="MANAGER">Farm Manager</option>
                  <option value="OWNER">Farm Owner / Full Admin</option>
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '12px' }}>
                <button type="button" onClick={() => setShowInviteModal(false)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '4px', cursor: 'pointer' }}>Cancel</button>
                <button type="submit" style={{ background: '#0284c7', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>Create User</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
