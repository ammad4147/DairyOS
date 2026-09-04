import React, { useEffect, useMemo, useState } from 'react';
import { Building, DatabaseBackup, Mail, Plus, Save, Trash2 } from 'lucide-react';
import { API_BASE_URL } from '../config/api';
import type { NavigationTabId } from '../navigation';
import NavigationVisibilityControl from './NavigationVisibilityControl';

interface SettingsTabProps {
  onFarmProfileUpdate?: (profile: { farmName: string; location: string }) => void;
  hiddenNavigationTabs?: NavigationTabId[];
  onHiddenNavigationTabsChange?: (hiddenTabs: NavigationTabId[]) => void;
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

type Recipient = { id: string; name: string; designation: string; email: string };
type BackupHealth = {
  status?: string;
  last_attempt?: string | null;
  last_successful_backup?: string | null;
  physically_redundant?: boolean;
  degraded_reason?: string | null;
  archive_verified?: boolean;
  monthly_primary?: string | null;
};

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';
const RECIPIENT_KEY = 'dairyos_notification_recipients';
const SMTP_PRESETS: Record<string, { host: string; port: number; tls: boolean }> = {
  'gmail.com': { host: 'smtp.gmail.com', port: 587, tls: true },
  'googlemail.com': { host: 'smtp.gmail.com', port: 587, tls: true },
  'outlook.com': { host: 'smtp-mail.outlook.com', port: 587, tls: true },
  'hotmail.com': { host: 'smtp-mail.outlook.com', port: 587, tls: true },
  'live.com': { host: 'smtp-mail.outlook.com', port: 587, tls: true },
  'office365.com': { host: 'smtp.office365.com', port: 587, tls: true },
  'yahoo.com': { host: 'smtp.mail.yahoo.com', port: 587, tls: true },
  'icloud.com': { host: 'smtp.mail.me.com', port: 587, tls: true },
  'me.com': { host: 'smtp.mail.me.com', port: 587, tls: true },
  'aol.com': { host: 'smtp.aol.com', port: 587, tls: true },
};

const field: React.CSSProperties = {
  width: '100%', boxSizing: 'border-box', background: '#1e293b', color: '#fff', padding: 8,
  marginBottom: 9, border: '1px solid #334155', borderRadius: 5,
};
const label: React.CSSProperties = { fontSize: 10, color: '#94a3b8', display: 'block', marginBottom: 4 };
const button: React.CSSProperties = {
  background: '#0284c7', color: '#fff', padding: '8px 11px', border: 0, borderRadius: 5,
  cursor: 'pointer', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 5,
};
const card: React.CSSProperties = {
  background: '#111827', padding: 15, borderRadius: 8, border: '1px solid #1f2937', minWidth: 0,
};

function loadRecipients(): Recipient[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(RECIPIENT_KEY) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function displayBackupTime(value?: string | null) {
  if (!value) return 'No successful backup recorded yet';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat('en-PK', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function SettingsTab({
  onFarmProfileUpdate,
  hiddenNavigationTabs = [],
  onHiddenNavigationTabsChange,
}: SettingsTabProps) {
  const [activeTab, setActiveTab] = useState<'FARM' | 'EMAIL'>('FARM');
  const [farmName, setFarmName] = useState(localStorage.getItem('dairyos_farm_name') || 'Barki Dairy Farm');
  const [location, setLocation] = useState(localStorage.getItem('dairyos_farm_loc') || 'Lahore, Punjab, PK');
  const [emailConfig, setEmailConfig] = useState<EmailConfig>({ configured: false });
  const [emailPassword, setEmailPassword] = useState('');
  const [testRecipient, setTestRecipient] = useState('');
  const [recipients, setRecipients] = useState<Recipient[]>(loadRecipients());
  const [recipientName, setRecipientName] = useState('');
  const [recipientDesignation, setRecipientDesignation] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const [clock, setClock] = useState(new Date());
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [backupHealth, setBackupHealth] = useState<BackupHealth>({
    status: 'NEVER_RUN', last_successful_backup: null, physically_redundant: false,
  });

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 30000);
    return () => window.clearInterval(timer);
  }, []);

  const localDateTime = useMemo(
    () => new Intl.DateTimeFormat('en-PK', { dateStyle: 'full', timeStyle: 'medium' }).format(clock),
    [clock],
  );

  useEffect(() => {
    void (async () => {
      try {
        const response = await fetch(`${API_BASE}/settings`);
        if (!response.ok) return;
        const data = await response.json();
        if (data.farm_name) setFarmName(data.farm_name);
        if (data.location) setLocation(data.location);
      } catch (loadError) {
        console.error(loadError);
      }
    })();
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetch(`${API_BASE}/backup-health`);
        if (!response.ok) return;
        const data = await response.json();
        if (data?.protection && typeof data.protection === 'object') setBackupHealth(data.protection);
      } catch (loadError) {
        console.error('DairyOS backup health load failed:', loadError);
      }
    };
    void load();
    const timer = window.setInterval(() => void load(), 300000);
    return () => window.clearInterval(timer);
  }, []);

  const loadEmail = async () => {
    setError('');
    try {
      const response = await fetch(`${API_BASE}/settings/email`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to load email settings.');
      setEmailConfig(data);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load email settings.');
    }
  };

  useEffect(() => {
    if (activeTab === 'EMAIL') void loadEmail();
  }, [activeTab]);

  const saveFarm = () => {
    localStorage.setItem('dairyos_farm_name', farmName);
    localStorage.setItem('dairyos_farm_loc', location);
    onFarmProfileUpdate?.({ farmName, location });
    window.dispatchEvent(new Event('storage'));
    setMessage('Farm profile saved.');
  };

  const applyProviderPreset = (email: string) => {
    const domain = email.trim().toLowerCase().split('@')[1] || '';
    const preset = SMTP_PRESETS[domain];
    setEmailConfig(previous => ({
      ...previous,
      sender_email: email,
      smtp_username: email,
      ...(preset ? { smtp_host: preset.host, smtp_port: preset.port, use_tls: preset.tls } : {}),
    }));
    if (preset) setMessage(`SMTP defaults loaded automatically for @${domain}.`);
  };

  const saveEmail = async () => {
    setError(''); setMessage('');
    try {
      const response = await fetch(`${API_BASE}/settings/email`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...emailConfig, smtp_password: emailPassword || undefined }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to save email settings.');
      setEmailConfig(data);
      setEmailPassword('');
      setMessage('DairyOS sender settings saved.');
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save email settings.');
    }
  };

  const sendTest = async () => {
    setError(''); setMessage('');
    try {
      const response = await fetch(`${API_BASE}/settings/email/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient: testRecipient }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Test email failed.');
      setMessage(`Test email sent to ${data.recipient}.`);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : 'Test email failed.');
    }
  };

  const addRecipient = () => {
    const email = recipientEmail.trim();
    if (!recipientName.trim() || !email.includes('@')) {
      setError('Recipient name and valid email are required.');
      return;
    }
    const next = [...recipients, {
      id: `${Date.now()}`,
      name: recipientName.trim(),
      designation: recipientDesignation.trim(),
      email,
    }];
    setRecipients(next);
    localStorage.setItem(RECIPIENT_KEY, JSON.stringify(next));
    setRecipientName(''); setRecipientDesignation(''); setRecipientEmail(''); setError('');
    setMessage('Notification recipient added.');
  };

  const removeRecipient = (id: string) => {
    const next = recipients.filter(recipient => recipient.id !== id);
    setRecipients(next);
    localStorage.setItem(RECIPIENT_KEY, JSON.stringify(next));
  };

  const protectionStatus = String(backupHealth.status || 'NEVER_RUN').toUpperCase();
  const protectionColor = protectionStatus === 'HEALTHY'
    ? '#86efac'
    : protectionStatus === 'DEGRADED' ? '#fde68a' : '#fca5a5';

  return (
    <div style={{ padding: 18, color: '#fff', height: '100%', overflowY: 'auto', boxSizing: 'border-box' }}>
      <h2 style={{ color: '#38bdf8', margin: '0 0 12px' }}>System Settings</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button onClick={() => setActiveTab('FARM')} style={tab(activeTab === 'FARM')}><Building size={13} />Farm & System</button>
        <button onClick={() => setActiveTab('EMAIL')} style={tab(activeTab === 'EMAIL')}><Mail size={13} />Email & Notifications</button>
      </div>
      {error && <div style={{ background: '#450a0a', border: '1px solid #7f1d1d', color: '#fecaca', padding: 8, borderRadius: 6, marginBottom: 8, fontSize: 10 }}>{error}</div>}
      {message && <div style={{ background: '#064e3b', border: '1px solid #065f46', color: '#a7f3d0', padding: 8, borderRadius: 6, marginBottom: 8, fontSize: 10 }}>{message}</div>}

      {activeTab === 'FARM' && (
        <div style={{ display: 'grid', gap: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 12, alignItems: 'start' }}>
            <section style={card}>
              <label style={label}>Farm Name</label><input value={farmName} onChange={event => setFarmName(event.target.value)} style={field} />
              <label style={label}>Location</label><input value={location} onChange={event => setLocation(event.target.value)} style={field} />
              <button onClick={saveFarm} style={button}><Save size={13} />Save Farm</button>
            </section>
            <section style={card}>
              <strong style={{ fontSize: 12 }}>System Date & Time</strong>
              <div style={{ color: '#e2e8f0', marginTop: 8, fontWeight: 800 }}>{localDateTime}</div>
              <div style={{ color: '#94a3b8', fontSize: 10, marginTop: 6 }}>DairyOS operator forms use the computer/browser clock as their default date and time. Forms may still select a different historical date where required.</div>
            </section>
            <section style={{ ...card, borderColor: protectionStatus === 'HEALTHY' ? '#166534' : protectionStatus === 'DEGRADED' ? '#854d0e' : '#7f1d1d' }}>
              <strong style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}><DatabaseBackup size={14} />Farm Data Protection</strong>
              <div style={{ marginTop: 8, fontWeight: 900, color: protectionColor }}>{protectionStatus}</div>
              <div style={{ color: '#e2e8f0', fontSize: 10, marginTop: 6 }}>Last verified backup: {displayBackupTime(backupHealth.last_successful_backup)}</div>
              <div style={{ color: '#94a3b8', fontSize: 10, marginTop: 5 }}>Archive verification: {backupHealth.archive_verified ? 'PASS' : 'Not yet verified'} · Independent physical copy: {backupHealth.physically_redundant ? 'YES' : 'NO'}</div>
              {backupHealth.degraded_reason && <div style={{ color: '#fde68a', fontSize: 9, marginTop: 6 }}>{backupHealth.degraded_reason}</div>}
              <div style={{ color: '#64748b', fontSize: 9, marginTop: 7 }}>DairyOS protects farm history automatically. Rolling backups and monthly archives are managed without operator action.</div>
            </section>
          </div>

          <NavigationVisibilityControl
            hiddenNavigationTabs={hiddenNavigationTabs}
            onHiddenNavigationTabsChange={onHiddenNavigationTabsChange}
            onError={setError}
            onMessage={setMessage}
          />
        </div>
      )}

      {activeTab === 'EMAIL' && (
        <div style={{ display: 'grid', gap: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 12, alignItems: 'start' }}>
            <section style={card}>
              <strong style={{ fontSize: 12 }}>DairyOS Sender</strong>
              <div style={{ color: '#64748b', fontSize: 9, margin: '5px 0 10px' }}>Configured sender details are visible here. Recognized provider settings populate automatically from the sender email domain; a stored password remains secret and is shown only as configured.</div>
              <label style={label}>From Email</label><input type="email" value={emailConfig.sender_email ?? ''} onChange={event => applyProviderPreset(event.target.value)} style={field} />
              <label style={label}>Display Name</label><input value={emailConfig.sender_display_name ?? ''} onChange={event => setEmailConfig({ ...emailConfig, sender_display_name: event.target.value })} style={field} />
              <label style={label}>SMTP Host</label><input value={emailConfig.smtp_host ?? ''} onChange={event => setEmailConfig({ ...emailConfig, smtp_host: event.target.value })} style={field} />
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 7 }}>
                <div><label style={label}>Port</label><input type="number" value={emailConfig.smtp_port ?? 587} onChange={event => setEmailConfig({ ...emailConfig, smtp_port: Number(event.target.value) })} style={field} /></div>
                <div><label style={label}>Username</label><input value={emailConfig.smtp_username ?? ''} onChange={event => setEmailConfig({ ...emailConfig, smtp_username: event.target.value })} style={field} /></div>
              </div>
              <label style={label}>SMTP Password {emailConfig.password_configured && '(stored)'}</label>
              <input type="password" value={emailPassword} onChange={event => setEmailPassword(event.target.value)} placeholder={emailConfig.password_configured ? 'Leave blank to keep current password' : ''} style={field} />
              <label style={{ fontSize: 10, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 9 }}><input type="checkbox" checked={emailConfig.use_tls !== false} onChange={event => setEmailConfig({ ...emailConfig, use_tls: event.target.checked })} />Use TLS</label>
              <button onClick={() => void saveEmail()} style={button}><Save size={13} />Save Sender</button>
            </section>

            <div style={{ display: 'grid', gap: 12 }}>
              <section style={card}>
                <strong style={{ fontSize: 12 }}>Test Email</strong>
                <input type="email" value={testRecipient} onChange={event => setTestRecipient(event.target.value)} placeholder="recipient@example.com" style={{ ...field, marginTop: 8 }} />
                <button disabled={!testRecipient} onClick={() => void sendTest()} style={button}><Mail size={13} />Send Test</button>
              </section>
              <section style={card}>
                <strong style={{ fontSize: 12 }}>Notification Recipients</strong>
                <div style={{ color: '#64748b', fontSize: 9, margin: '5px 0 9px' }}>Name, designation and email entry points for farm notification recipients.</div>
                <input value={recipientName} onChange={event => setRecipientName(event.target.value)} placeholder="Name" style={field} />
                <input value={recipientDesignation} onChange={event => setRecipientDesignation(event.target.value)} placeholder="Designation" style={field} />
                <input type="email" value={recipientEmail} onChange={event => setRecipientEmail(event.target.value)} placeholder="Email address" style={field} />
                <button type="button" onClick={addRecipient} style={button}><Plus size={13} />Add Recipient</button>
                <div style={{ marginTop: 9, display: 'grid', gap: 5 }}>
                  {recipients.map(recipient => (
                    <div key={recipient.id} style={{ display: 'flex', gap: 7, alignItems: 'center', borderTop: '1px solid #1f2937', paddingTop: 6 }}>
                      <div style={{ flex: 1, minWidth: 0 }}><strong style={{ fontSize: 10 }}>{recipient.name}</strong><div style={{ color: '#94a3b8', fontSize: 9 }}>{recipient.designation || 'No designation'} · {recipient.email}</div></div>
                      <button aria-label={`Remove ${recipient.name}`} title={`Remove ${recipient.name}`} onClick={() => removeRecipient(recipient.id)} style={{ background: 'none', border: 0, color: '#fca5a5', cursor: 'pointer' }}><Trash2 size={13} /></button>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const tab = (active: boolean): React.CSSProperties => ({
  background: active ? '#0c4a6e' : '#1e293b', color: '#f8fafc',
  border: active ? '1px solid #38bdf8' : '1px solid #475569', borderRadius: 5,
  padding: '7px 10px', cursor: 'pointer', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 5,
});
