import React, { useEffect, useState } from 'react';
import { Building, Mail, Save, Sliders, Rocket, RotateCcw } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

interface SettingsTabProps {
  onFarmProfileUpdate?: (profile: { farmName: string; location: string }) => void;
}

type EmailConfig = {
  configured: boolean;
  source?: string;
  sender_email?: string;
  sender_display_name?: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  use_tls?: boolean;
  password_configured?: boolean;
};

type DeploymentStatus = {
  deployed: boolean;
  activated_at?: string | null;
  activated_by?: string | null;
  last_action?: string | null;
  reset_protected: boolean;
};

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

export default function SettingsTab({ onFarmProfileUpdate }: SettingsTabProps) {
  const [activeTab, setActiveTab] = useState<'FARM' | 'STANDARDS' | 'EMAIL' | 'DEPLOYMENT'>('FARM');
  const [farmName, setFarmName] = useState(localStorage.getItem('dairyos_farm_name') || 'Barki Dairy Farm');
  const [location, setLocation] = useState(localStorage.getItem('dairyos_farm_loc') || 'Lahore, Punjab, PK');
  const [timezone, setTimezone] = useState(localStorage.getItem('dairyos_timezone') || 'Asia/Karachi (PKT +05:00)');
  const [operationalDate, setOperationalDate] = useState('');
  const [emailConfig, setEmailConfig] = useState<EmailConfig>({ configured: false });
  const [emailPassword, setEmailPassword] = useState('');
  const [testRecipient, setTestRecipient] = useState('');
  const [deployment, setDeployment] = useState<DeploymentStatus>({ deployed: false, reset_protected: false });
  const [controlPassword, setControlPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const loadEmail = async () => {
    try {
      const response = await fetch(`${API_BASE}/settings/email`);
      if (response.ok) setEmailConfig(await response.json());
    } catch (error) {
      console.error(error);
    }
  };

  const loadSettings = async () => {
    try {
      const response = await fetch(`${API_BASE}/settings`);
      if (!response.ok) return;
      const data = await response.json();
      if (data.timezone) setTimezone(data.timezone);
      if (data.current_operational_date) setOperationalDate(data.current_operational_date);
      if (data.farm_name) setFarmName(data.farm_name);
      if (data.location) setLocation(data.location);
    } catch (error) {
      console.error(error);
    }
  };

  const loadDeployment = async () => {
    try {
      const response = await fetch(`${API_BASE}/settings/deployment`);
      if (response.ok) setDeployment(await response.json());
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    void loadSettings();
    void loadDeployment();
  }, []);

  useEffect(() => {
    if (activeTab === 'EMAIL') void loadEmail();
    if (activeTab === 'DEPLOYMENT') void loadDeployment();
  }, [activeTab]);

  const handleSaveFarm = () => {
    localStorage.setItem('dairyos_farm_name', farmName);
    localStorage.setItem('dairyos_farm_loc', location);
    onFarmProfileUpdate?.({ farmName, location });
    window.dispatchEvent(new Event('storage'));
    setMessage('Farm profile saved successfully.');
  };

  const handleSaveStandards = async () => {
    setError('');
    setMessage('');
    try {
      const timezoneName = timezone.split(' ')[0];
      const response = await fetch(`${API_BASE}/settings/operational`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timezone: timezoneName,
          operational_date_convention: 'FARM_LOCAL_DATE',
          updated_by: 'UI Operator',
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to save operational settings.');
      if (data.timezone) setTimezone(data.timezone);
      if (data.current_operational_date) setOperationalDate(data.current_operational_date);
      localStorage.setItem('dairyos_timezone', timezone);
      setMessage(`Operational settings saved. Current operational date: ${data.current_operational_date || 'unchanged'}.`);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to save operational settings.');
    }
  };

  const executeDeployment = async (action: 'DEPLOY' | 'RESET') => {
    setError('');
    setMessage('');
    const prompt = action === 'DEPLOY'
      ? 'Deploy / activate DairyOS operations for this farm?'
      : 'RESET will clear operational farm data and return DairyOS to pre-deployment state. Continue?';
    if (!window.confirm(prompt)) return;

    try {
      const response = await fetch(
        action === 'DEPLOY' ? `${API_BASE}/settings/deployment/activate` : `${API_BASE}/settings/reset-test-data`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            confirm: action,
            password: controlPassword,
            updated_by: 'UI Operator',
          }),
        },
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `${action} operation failed.`);
      setDeployment(data.deployment || data);
      setControlPassword('');
      setMessage(action === 'DEPLOY' ? 'DairyOS is deployed and operational automation is active.' : 'DairyOS was reset to a pre-deployment zero state.');
    } catch (error) {
      setError(error instanceof Error ? error.message : `${action} operation failed.`);
    }
  };

  const saveEmail = async () => {
    setError('');
    setMessage('');
    try {
      const response = await fetch(`${API_BASE}/settings/email`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...emailConfig,
          smtp_password: emailPassword || undefined,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to save email settings.');
      setEmailConfig(data);
      setEmailPassword('');
      setMessage('DairyOS sender settings saved.');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to save email settings.');
    }
  };

  const sendTest = async () => {
    setError('');
    setMessage('');
    try {
      const response = await fetch(`${API_BASE}/settings/email/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient: testRecipient }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Test email failed.');
      setMessage(`Test email sent to ${data.recipient}.`);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Test email failed.');
    }
  };

  return (
    <div style={{ padding: 24, color: '#fff', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ color: '#38bdf8', marginBottom: 20 }}>System Settings</h2>
      <div style={{ display: 'flex', gap: 20, marginBottom: 20, borderBottom: '1px solid #1f2937', flexWrap: 'wrap' }}>
        <button onClick={() => setActiveTab('FARM')} style={tabStyle(activeTab === 'FARM')}><Building size={13} />Farm Profile</button>
        <button onClick={() => setActiveTab('STANDARDS')} style={tabStyle(activeTab === 'STANDARDS')}><Sliders size={13} />Standards</button>
        <button onClick={() => setActiveTab('EMAIL')} style={tabStyle(activeTab === 'EMAIL')}><Mail size={13} />Email</button>
        <button onClick={() => setActiveTab('DEPLOYMENT')} style={tabStyle(activeTab === 'DEPLOYMENT')}><Rocket size={13} />Deployment</button>
      </div>
      {error && <div style={{ background: '#450a0a', border: '1px solid #7f1d1d', color: '#fecaca', padding: 10, borderRadius: 6, marginBottom: 12, fontSize: 11 }}>{error}</div>}
      {message && <div style={{ background: '#064e3b', border: '1px solid #065f46', color: '#a7f3d0', padding: 10, borderRadius: 6, marginBottom: 12, fontSize: 11 }}>{message}</div>}
      {activeTab === 'FARM' && <div style={{ background: '#111827', padding: 20, borderRadius: 8, maxWidth: 440 }}>
        <label style={label}>Farm Name</label>
        <input value={farmName} onChange={e => setFarmName(e.target.value)} style={field} />
        <label style={label}>Location</label>
        <input value={location} onChange={e => setLocation(e.target.value)} style={field} />
        <button onClick={handleSaveFarm} style={button}><Save size={14} />Save Farm</button>
      </div>}
      {activeTab === 'STANDARDS' && <div style={{ background: '#111827', padding: 20, borderRadius: 8, maxWidth: 440 }}>
        <label style={label}>Timezone</label>
        <select value={timezone} onChange={e => setTimezone(e.target.value)} style={field}>
          <option>Asia/Karachi (PKT +05:00)</option>
          <option>UTC</option>
        </select>
        <div style={{ fontSize: 10, color: '#94a3b8', marginBottom: 10 }}>Authoritative operational date: {operationalDate || 'loading…'}</div>
        <button onClick={() => void handleSaveStandards()} style={button}><Save size={14} />Save Standards</button>
      </div>}
      {activeTab === 'DEPLOYMENT' && <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(320px,420px)', gap: 14, alignItems: 'start' }}>
        <section style={card}>
          <h3 style={title}><Rocket size={14} />Deployment Control</h3>
          <div style={muted}>Deployment is an explicit activation boundary. Configuration and date changes do not start automated findings, catch-up email, or operational alerts before deployment.</div>
          <div style={{ marginTop: 14, padding: 12, background: '#0f172a', borderRadius: 6 }}>
            <div style={{ fontSize: 11, fontWeight: 700 }}>Runtime state</div>
            <div style={{ fontSize: 18, fontWeight: 800, marginTop: 5, color: deployment.deployed ? '#86efac' : '#fbbf24' }}>{deployment.deployed ? 'DEPLOYED / ACTIVE' : 'CONFIGURED / NOT DEPLOYED'}</div>
            <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 5 }}>Last action: {deployment.last_action || 'None recorded'}</div>
          </div>
          <label style={label}>Deployment / Reset password</label>
          <input type="password" value={controlPassword} onChange={e => setControlPassword(e.target.value)} style={field} placeholder="Required for both actions" />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={() => void executeDeployment('DEPLOY')} style={button} disabled={deployment.deployed}><Rocket size={14} />Deploy / Activate</button>
            <button onClick={() => void executeDeployment('RESET')} style={{ ...button, background: '#f97316' }}><RotateCcw size={14} />Reset to Pre-Deployment</button>
          </div>
          {!deployment.reset_protected && <div style={{ marginTop: 10, fontSize: 10, color: '#fca5a5' }}>Deployment controls are unavailable until Reset Protection is configured.</div>}
        </section>
        <section style={card}>
          <h3 style={title}>Safety rules</h3>
          <div style={muted}>Reset clears operational farm data while preserving system/reference configuration. Deploy only activates the existing configured farm; it does not fabricate operational records.</div>
          <div style={{ marginTop: 12, fontSize: 10, color: '#cbd5e1' }}>
            <div>• Password required for every deployment/reset action.</div>
            <div>• Explicit DEPLOY or RESET confirmation required.</div>
            <div>• Automatic date-driven actions remain suppressed until deployment.</div>
          </div>
        </section>
      </div>}
      {activeTab === 'EMAIL' && <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(320px,420px)', gap: 14, alignItems: 'start' }}>
        <section style={card}>
          <h3 style={title}>DairyOS Sender</h3>
          <div style={muted}>All nightly digests and DairyOS-generated email are sent using this identity. Database settings override deployment defaults.</div>
          <label style={label}>From email</label>
          <input type="email" value={emailConfig.sender_email ?? ''} onChange={e => setEmailConfig({ ...emailConfig, sender_email: e.target.value })} style={field} />
          <label style={label}>Display name</label>
          <input value={emailConfig.sender_display_name ?? ''} onChange={e => setEmailConfig({ ...emailConfig, sender_display_name: e.target.value })} style={field} />
          <label style={label}>SMTP host</label>
          <input value={emailConfig.smtp_host ?? ''} onChange={e => setEmailConfig({ ...emailConfig, smtp_host: e.target.value })} style={field} />
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <div><label style={label}>Port</label><input type="number" value={emailConfig.smtp_port ?? 587} onChange={e => setEmailConfig({ ...emailConfig, smtp_port: Number(e.target.value) })} style={field} /></div>
            <div><label style={label}>SMTP username</label><input value={emailConfig.smtp_username ?? ''} onChange={e => setEmailConfig({ ...emailConfig, smtp_username: e.target.value })} style={field} /></div>
          </div>
          <label style={label}>SMTP password {emailConfig.password_configured && '(stored)'}</label>
          <input type="password" value={emailPassword} onChange={e => setEmailPassword(e.target.value)} placeholder={emailConfig.password_configured ? 'Leave blank to keep current password' : ''} style={field} />
          <label style={{ display: 'flex', gap: 7, alignItems: 'center', fontSize: 10, color: '#cbd5e1', marginBottom: 12 }}>
            <input type="checkbox" checked={emailConfig.use_tls !== false} onChange={e => setEmailConfig({ ...emailConfig, use_tls: e.target.checked })} />Use TLS
          </label>
          <button onClick={() => void saveEmail()} style={button}><Mail size={14} />Save Email Settings</button>
        </section>
        <section style={card}>
          <h3 style={title}>Send Test Email</h3>
          <div style={muted}>Verify the SMTP connection immediately rather than waiting for the nightly job.</div>
          <input type="email" placeholder="Test recipient" value={testRecipient} onChange={e => setTestRecipient(e.target.value)} style={field} />
          <button disabled={!testRecipient} onClick={() => void sendTest()} style={button}><Mail size={14} />Send Test</button>
          <div style={{ marginTop: 12, fontSize: 10, color: emailConfig.configured ? '#86efac' : '#fca5a5' }}>{emailConfig.configured ? 'Sender configuration is available.' : 'Sender configuration is not complete.'}</div>
        </section>
      </div>}
    </div>
  );
}

const label: React.CSSProperties = { fontSize: 10, color: '#94a3b8', display: 'block', marginBottom: 4 };
const field: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', color: '#fff', padding: 8, marginBottom: 10, border: '1px solid #334155', borderRadius: 5 };
const button: React.CSSProperties = { background: '#38bdf8', padding: '8px 12px', border: 'none', cursor: 'pointer', fontWeight: 'bold', display: 'inline-flex', alignItems: 'center', gap: 5, borderRadius: 5 };
const card: React.CSSProperties = { background: '#111827', padding: 16, borderRadius: 8, border: '1px solid #1f2937' };
const title: React.CSSProperties = { fontSize: 13, margin: '0 0 10px', display: 'flex', alignItems: 'center', gap: 6 };
const muted: React.CSSProperties = { fontSize: 9, color: '#64748b' };
const tabStyle = (active: boolean): React.CSSProperties => ({ background: 'none', border: 0, color: active ? '#38bdf8' : '#94a3b8', padding: 10, cursor: 'pointer', borderBottom: active ? '2px solid #38bdf8' : '2px solid transparent', display: 'inline-flex', alignItems: 'center', gap: 5 });
