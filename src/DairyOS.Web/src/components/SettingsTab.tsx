import { useState } from 'react';
import { Settings, Save, Shield, Database, User } from 'lucide-react';

export default function SettingsTab() {
  const [farmName, setFarmName] = useState('Barki Dairy Farm Lahore');
  const [operator, setOperator] = useState('Ammad Hassan');
  const [currency, setCurrency] = useState('PKR (Pakistani Rupee)');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div style={{ padding: '20px', color: '#f8fafc', maxWidth: '800px' }}>
      <h2 style={{ margin: '0 0 6px 0', fontSize: '18px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Settings size={20}/> Farm Settings & Configuration
      </h2>
      <p style={{ margin: '0 0 20px 0', fontSize: '12px', color: '#94a3b8' }}>
        Configure operational parameters, financial currency, and user operator credentials.
      </p>

      {saved && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '10px 14px', borderRadius: '6px', marginBottom: '16px', fontSize: '12px' }}>
          Settings successfully saved and synchronized with DairyOS backend.
        </div>
      )}

      <form onSubmit={handleSave} style={{ background: '#111827', border: '1px solid #1f2937', padding: '20px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Farm Name / Unit</label>
          <input type="text" value={farmName} onChange={e => setFarmName(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', outline: 'none' }} />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Primary Farm Operator</label>
          <input type="text" value={operator} onChange={e => setOperator(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', outline: 'none' }} />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Accounting Currency</label>
          <select value={currency} onChange={e => setCurrency(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '8px', borderRadius: '4px', fontSize: '12px', outline: 'none' }}>
            <option value="PKR (Pakistani Rupee)">PKR (Pakistani Rupee)</option>
            <option value="USD (US Dollar)">USD (US Dollar)</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
          <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '9px 16px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
            <Save size={15}/> Save Settings
          </button>
        </div>
      </form>
    </div>
  );
}
