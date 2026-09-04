import React, { useEffect, useState } from 'react';
import { KeyRound, Save } from 'lucide-react';
import { API_BASE_URL } from '../config/api';
import { NAVIGATION_TABS, normalizeHiddenNavigationTabs } from '../navigation';
import type { NavigationTabId } from '../navigation';

interface NavigationVisibilityControlProps {
  hiddenNavigationTabs: NavigationTabId[];
  onHiddenNavigationTabsChange?: (hiddenTabs: NavigationTabId[]) => void;
  onError: (message: string) => void;
  onMessage: (message: string) => void;
}

type CredentialStatus = {
  username: string;
  setup_required: boolean;
  recovery_configured: boolean;
};

type CredentialMode = 'LOGIN' | 'SETUP' | 'RECOVER';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';
const NAV_AUTH_KEY = 'dairyos_navigation_access_token';
const field: React.CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  background: '#1e293b',
  color: '#fff',
  padding: 8,
  border: '1px solid #334155',
  borderRadius: 5,
};
const label: React.CSSProperties = {
  fontSize: 10,
  color: '#94a3b8',
  display: 'block',
  marginBottom: 4,
};
const button: React.CSSProperties = {
  background: '#0284c7',
  color: '#fff',
  padding: '8px 11px',
  border: 0,
  borderRadius: 5,
  cursor: 'pointer',
  fontWeight: 800,
  display: 'inline-flex',
  alignItems: 'center',
  gap: 5,
};
const card: React.CSSProperties = {
  background: '#111827',
  padding: 15,
  borderRadius: 8,
  border: '1px solid #7c3aed',
  minWidth: 0,
};

export default function NavigationVisibilityControl({
  hiddenNavigationTabs,
  onHiddenNavigationTabsChange,
  onError,
  onMessage,
}: NavigationVisibilityControlProps) {
  const [navigationToken, setNavigationToken] = useState(
    () => sessionStorage.getItem(NAV_AUTH_KEY) || '',
  );
  const [navigationDraft, setNavigationDraft] = useState<NavigationTabId[]>(
    normalizeHiddenNavigationTabs(hiddenNavigationTabs),
  );
  const [credentialStatus, setCredentialStatus] = useState<CredentialStatus>({
    username: 'admin',
    setup_required: false,
    recovery_configured: false,
  });
  const [credentialMode, setCredentialMode] = useState<CredentialMode>('LOGIN');
  const [adminUsername, setAdminUsername] = useState('admin');
  const [adminPassword, setAdminPassword] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [recoveryCode, setRecoveryCode] = useState('');
  const [issuedRecoveryCode, setIssuedRecoveryCode] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setNavigationDraft(normalizeHiddenNavigationTabs(hiddenNavigationTabs));
  }, [hiddenNavigationTabs]);

  const loadCredentialStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/settings/navigation-credentials`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Unable to load administrator credential status.');
      const next = payload as CredentialStatus;
      setCredentialStatus(next);
      setAdminUsername(next.username || 'admin');
      if (next.setup_required) setCredentialMode('SETUP');
      else setCredentialMode(current => current === 'SETUP' ? 'LOGIN' : current);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to load administrator credential status.');
    }
  };

  useEffect(() => {
    void loadCredentialStatus();
  }, []);

  const clearPasswordFields = () => {
    setAdminPassword('');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setRecoveryCode('');
  };

  const validateNewPassword = () => {
    if (newPassword.length < 12) throw new Error('Administrator password must be at least 12 characters long.');
    if (newPassword !== confirmPassword) throw new Error('New password and confirmation do not match.');
  };

  const authenticateNavigation = async () => {
    setBusy(true);
    onError('');
    onMessage('');
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: adminUsername, password: adminPassword }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.access_token) throw new Error(payload.detail || 'Authentication failed.');
      const token = String(payload.access_token);
      const permissionsResponse = await fetch(`${API_BASE}/authz/permissions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const permissions = await permissionsResponse.json();
      if (
        !permissionsResponse.ok
        || !Array.isArray(permissions.permissions)
        || !permissions.permissions.includes('settings.navigation')
      ) {
        throw new Error('This account cannot change navigation visibility.');
      }
      sessionStorage.setItem(NAV_AUTH_KEY, token);
      setNavigationToken(token);
      setCurrentPassword(adminPassword);
      setAdminPassword('');
      onMessage(`Navigation visibility unlocked for ${payload.user?.username || adminUsername}.`);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Authentication failed.');
    } finally {
      setBusy(false);
    }
  };

  const setupInitialPassword = async () => {
    setBusy(true);
    onError('');
    onMessage('');
    try {
      validateNewPassword();
      const response = await fetch(`${API_BASE}/settings/navigation-credentials/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: adminUsername, new_password: newPassword }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Unable to set the administrator password.');
      setIssuedRecoveryCode(String(payload.recovery_code || ''));
      setCredentialMode('LOGIN');
      setAdminPassword(newPassword);
      setNewPassword('');
      setConfirmPassword('');
      await loadCredentialStatus();
      onMessage('Initial administrator password set. Save the one-time recovery code shown below.');
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to set the administrator password.');
    } finally {
      setBusy(false);
    }
  };

  const recoverPassword = async () => {
    setBusy(true);
    onError('');
    onMessage('');
    try {
      validateNewPassword();
      const response = await fetch(`${API_BASE}/settings/navigation-credentials/recover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: adminUsername,
          recovery_code: recoveryCode,
          new_password: newPassword,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Unable to recover the administrator password.');
      setIssuedRecoveryCode(String(payload.recovery_code || ''));
      setCredentialMode('LOGIN');
      setAdminPassword(newPassword);
      setNewPassword('');
      setConfirmPassword('');
      setRecoveryCode('');
      onMessage('Administrator password recovered. The recovery code has been rotated; save the new one shown below.');
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to recover the administrator password.');
    } finally {
      setBusy(false);
    }
  };

  const lockNavigation = () => {
    sessionStorage.removeItem(NAV_AUTH_KEY);
    setNavigationToken('');
    clearPasswordFields();
    onMessage('Navigation visibility controls locked.');
  };

  const navigationFetch = async (url: string, init: RequestInit = {}) => {
    const token = navigationToken || sessionStorage.getItem(NAV_AUTH_KEY) || '';
    const headers = new Headers(init.headers || {});
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const response = await fetch(url, { ...init, headers });
    if (response.status === 401 || response.status === 403) {
      sessionStorage.removeItem(NAV_AUTH_KEY);
      setNavigationToken('');
      throw new Error('Administrator authentication is required to change navigation visibility.');
    }
    return response;
  };

  const setNavigationVisible = (tabId: NavigationTabId, visible: boolean) => {
    setNavigationDraft(current => (
      visible
        ? current.filter(id => id !== tabId)
        : normalizeHiddenNavigationTabs([...current, tabId])
    ));
  };

  const saveNavigation = async () => {
    onError('');
    onMessage('');
    try {
      const response = await navigationFetch(`${API_BASE}/settings/navigation`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hidden_tabs: navigationDraft }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Unable to save navigation visibility.');
      const hidden = normalizeHiddenNavigationTabs(payload?.navigation?.hidden_tabs);
      setNavigationDraft(hidden);
      onHiddenNavigationTabsChange?.(hidden);
      onMessage('Navigation visibility saved. Hidden tabs remain fully operational.');
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to save navigation visibility.');
    }
  };

  const changePassword = async () => {
    setBusy(true);
    onError('');
    onMessage('');
    try {
      validateNewPassword();
      if (!currentPassword) throw new Error('Current administrator password is required.');
      const response = await navigationFetch(`${API_BASE}/auth/me/password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Unable to change the administrator password.');
      setCurrentPassword(newPassword);
      setNewPassword('');
      setConfirmPassword('');
      onMessage('Administrator password changed.');
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to change the administrator password.');
    } finally {
      setBusy(false);
    }
  };

  const rotateRecoveryCode = async () => {
    setBusy(true);
    onError('');
    onMessage('');
    try {
      const response = await navigationFetch(`${API_BASE}/settings/navigation-credentials/recovery-code`, {
        method: 'POST',
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Unable to generate a recovery code.');
      setIssuedRecoveryCode(String(payload.recovery_code || ''));
      setCredentialStatus(current => ({ ...current, recovery_configured: true }));
      onMessage('New administrator recovery code generated. Save it now; it is displayed only in this session.');
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to generate a recovery code.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section style={card}>
      <strong style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
        <KeyRound size={14} />Navigation Visibility
      </strong>
      <div style={{ color: '#94a3b8', fontSize: 9, margin: '5px 0 10px' }}>
        Password-protected farm-wide display control. Hiding a tab removes only its top navigation button; its module, API, background work, calculations and records remain active.
      </div>

      {issuedRecoveryCode && (
        <div style={{ background: '#172554', border: '1px solid #3b82f6', borderRadius: 5, padding: 9, marginBottom: 10 }}>
          <div style={{ color: '#bfdbfe', fontSize: 9, fontWeight: 800 }}>ONE-TIME RECOVERY CODE — SAVE SECURELY</div>
          <code style={{ display: 'block', color: '#fff', fontSize: 11, marginTop: 5, wordBreak: 'break-all' }}>{issuedRecoveryCode}</code>
          <button type="button" onClick={() => setIssuedRecoveryCode('')} style={{ ...button, background: '#334155', marginTop: 7 }}>Dismiss after saving</button>
        </div>
      )}

      {!navigationToken && credentialMode === 'SETUP' && (
        <div>
          <div style={{ color: '#fde68a', fontSize: 10, marginBottom: 8 }}>
            No administrator password has been set. Create the initial password before Navigation Visibility can be unlocked.
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 7, alignItems: 'end' }}>
            <div><label style={label}>Username</label><input value={adminUsername} disabled style={field} /></div>
            <div><label style={label}>New Password</label><input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} style={field} /></div>
            <div><label style={label}>Confirm Password</label><input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} style={field} /></div>
            <button type="button" disabled={busy || !newPassword || !confirmPassword} onClick={() => void setupInitialPassword()} style={button}>{busy ? 'Saving…' : 'Set Initial Password'}</button>
          </div>
        </div>
      )}

      {!navigationToken && credentialMode === 'LOGIN' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 7, alignItems: 'end' }}>
            <div><label style={label}>Username</label><input value={adminUsername} onChange={e => setAdminUsername(e.target.value)} style={field} /></div>
            <div><label style={label}>Password</label><input type="password" value={adminPassword} onChange={e => setAdminPassword(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') void authenticateNavigation(); }} style={field} /></div>
            <button type="button" disabled={busy || !adminUsername || !adminPassword} onClick={() => void authenticateNavigation()} style={button}>{busy ? 'Authenticating…' : 'Unlock'}</button>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 7 }}>
            <button type="button" disabled={!credentialStatus.recovery_configured} onClick={() => { clearPasswordFields(); setCredentialMode('RECOVER'); }} style={{ ...button, background: '#475569', opacity: credentialStatus.recovery_configured ? 1 : 0.55 }}>
              Recover / Reset Password
            </button>
          </div>
          {!credentialStatus.recovery_configured && <div style={{ color: '#64748b', fontSize: 9, textAlign: 'right', marginTop: 4 }}>No recovery code is configured yet. Unlock once and generate one.</div>}
        </div>
      )}

      {!navigationToken && credentialMode === 'RECOVER' && (
        <div>
          <div style={{ color: '#cbd5e1', fontSize: 10, marginBottom: 8 }}>
            Enter the saved recovery code and choose a new administrator password. Recovery is accepted only from the local DairyOS computer.
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7 }}>
            <div><label style={label}>Recovery Code</label><input value={recoveryCode} onChange={e => setRecoveryCode(e.target.value)} style={field} /></div>
            <div><label style={label}>New Password</label><input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} style={field} /></div>
            <div><label style={label}>Confirm Password</label><input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} style={field} /></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 7, marginTop: 8 }}>
            <button type="button" onClick={() => { clearPasswordFields(); setCredentialMode('LOGIN'); }} style={{ ...button, background: '#475569' }}>Back</button>
            <button type="button" disabled={busy || !recoveryCode || !newPassword || !confirmPassword} onClick={() => void recoverPassword()} style={button}>{busy ? 'Recovering…' : 'Recover Password'}</button>
          </div>
        </div>
      )}

      {navigationToken && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: 7 }}>
            {NAVIGATION_TABS.map(item => (
              <label key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 7, background: '#1e293b', border: '1px solid #334155', padding: '8px 10px', borderRadius: 5, fontSize: 10 }}>
                <input type="checkbox" checked={!navigationDraft.includes(item.id)} onChange={e => setNavigationVisible(item.id, e.target.checked)} />
                <span>Show {item.label}</span>
              </label>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginTop: 10 }}>
            <button type="button" onClick={lockNavigation} style={{ ...button, background: '#475569' }}>Lock</button>
            <button type="button" onClick={() => void saveNavigation()} style={button}><Save size={13} />Save Navigation</button>
          </div>

          <div style={{ borderTop: '1px solid #334155', marginTop: 12, paddingTop: 10 }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: '#cbd5e1', marginBottom: 7 }}>Administrator Password & Recovery</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 7, alignItems: 'end' }}>
              <div><label style={label}>Current Password</label><input type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} style={field} /></div>
              <div><label style={label}>New Password</label><input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} style={field} /></div>
              <div><label style={label}>Confirm Password</label><input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} style={field} /></div>
              <button type="button" disabled={busy || !currentPassword || !newPassword || !confirmPassword} onClick={() => void changePassword()} style={button}>Change Password</button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 7 }}>
              <button type="button" disabled={busy} onClick={() => void rotateRecoveryCode()} style={{ ...button, background: '#475569' }}>
                {credentialStatus.recovery_configured ? 'Rotate Recovery Code' : 'Generate Recovery Code'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
