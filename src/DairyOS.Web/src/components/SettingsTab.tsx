import React, { useState } from 'react';
import { Building, Sliders, Save } from 'lucide-react';

export default function SettingsTab() {
  const [activeTab, setActiveTab] = useState<'FARM' | 'STANDARDS'>('FARM');

  // State initialization
  const [farmName, setFarmName] = useState(localStorage.getItem('dairyos_farm_name') || 'Barki Dairy Farm');
  const [location, setLocation] = useState(localStorage.getItem('dairyos_farm_loc') || 'Lahore, Punjab, PK');
  const [timezone, setTimezone] = useState(localStorage.getItem('dairyos_timezone') || 'Asia/Karachi (PKT +05:00)');

  const handleSaveFarm = () => {
    localStorage.setItem('dairyos_farm_name', farmName);
    localStorage.setItem('dairyos_farm_loc', location);
    window.dispatchEvent(new Event('storage'));
    alert('Farm profile saved successfully.');
  };

  const handleSaveStandards = () => {
    localStorage.setItem('dairyos_timezone', timezone);
    alert('Standards saved successfully.');
  };

  return (
    <div style={{ padding: '24px', color: '#fff', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ color: '#38bdf8', marginBottom: '20px' }}>System Settings</h2>
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', borderBottom: '1px solid #1f2937' }}>
        <button onClick={() => setActiveTab('FARM')} style={{ background: 'none', border: 'none', color: activeTab === 'FARM' ? '#38bdf8' : '#94a3b8', padding: '10px', cursor: 'pointer', borderBottom: activeTab === 'FARM' ? '2px solid #38bdf8' : 'none' }}>Farm Profile</button>
        <button onClick={() => setActiveTab('STANDARDS')} style={{ background: 'none', border: 'none', color: activeTab === 'STANDARDS' ? '#38bdf8' : '#94a3b8', padding: '10px', cursor: 'pointer', borderBottom: activeTab === 'STANDARDS' ? '2px solid #38bdf8' : 'none' }}>Standards</button>
      </div>

      {activeTab === 'FARM' && (
        <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', maxWidth: '400px' }}>
          <label style={{ fontSize: '11px', color: '#94a3b8' }}>Farm Name</label>
          <input value={farmName} onChange={e => setFarmName(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', padding: '8px', marginBottom: '15px', border: '1px solid #334155' }} />
          <label style={{ fontSize: '11px', color: '#94a3b8' }}>Location</label>
          <input value={location} onChange={e => setLocation(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', padding: '8px', marginBottom: '15px', border: '1px solid #334155' }} />
          <button onClick={handleSaveFarm} style={{ background: '#38bdf8', padding: '8px 16px', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}><Save size={14} style={{marginRight: 5}}/> Save Farm</button>
        </div>
      )}

      {activeTab === 'STANDARDS' && (
        <div style={{ background: '#111827', padding: '20px', borderRadius: '8px', maxWidth: '400px' }}>
          <label style={{ fontSize: '11px', color: '#94a3b8' }}>Timezone</label>
          <select value={timezone} onChange={e => setTimezone(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', padding: '8px', marginBottom: '15px', border: '1px solid #334155' }}>
            <option>Asia/Karachi (PKT +05:00)</option>
            <option>UTC</option>
          </select>
          <button onClick={handleSaveStandards} style={{ background: '#38bdf8', padding: '8px 16px', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}><Save size={14} style={{marginRight: 5}}/> Save Standards</button>
        </div>
      )}
    </div>
  );
}
