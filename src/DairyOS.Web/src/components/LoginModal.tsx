import React, { useState } from 'react';
import { Lock, User, ShieldCheck, AlertCircle, ArrowRight } from 'lucide-react';
import { saveUser } from '../auth';
import { API_BASE_URL } from '../config/api';

interface LoginModalProps {
  onLoginSuccess: (user: { username: string; role: string; fullName: string; permissions: string[] }) => void;
}

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

export default function LoginModal({ onLoginSuccess }: LoginModalProps) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('dairyos');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const finishLogin = async (data: any, fallbackUsername = username) => {
    const authenticated = data?.user ?? data ?? {};
    const authenticatedUsername = String(authenticated.username || fallbackUsername);
    const role = String(authenticated.role || '').toUpperCase();
    if (!role) throw new Error('Authenticated account did not return a role.');

    let permissions: string[] = [];
    try {
      const token = localStorage.getItem('dairyos_token');
      const response = await fetch(`${API_BASE}/authz/permissions`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (response.ok) {
        const payload = await response.json();
        permissions = Array.isArray(payload.permissions) ? payload.permissions : [];
      } else if (response.status === 401) {
        throw new Error('Authentication token was not accepted while loading permissions.');
      }
    } catch {
      permissions = [];
    }

    const userObj = {
      username: authenticatedUsername,
      role,
      // Do not infer a person's identity from a username. The backend remains
      // authoritative for the authenticated account and role.
      fullName: authenticated.fullName || authenticated.display_name || authenticatedUsername,
      permissions,
    };
    saveUser(userObj);
    onLoginSuccess(userObj);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) throw new Error('Invalid credentials. Check username or password.');
      const data = await response.json();
      localStorage.setItem('dairyos_token', data.access_token || '');
      await finishLogin(data);
    } catch {
      localStorage.removeItem('dairyos_token');
      setError('Unable to authenticate with DairyOS server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'radial-gradient(circle at 50% 30%, #1e293b 0%, #0b0f19 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, fontFamily: 'sans-serif' }}>
      <div style={{ width: '400px', background: '#111827', border: '1px solid #1f2937', borderRadius: '12px', padding: '32px', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)' }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ width: '54px', height: '54px', borderRadius: '12px', background: '#0284c7', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold', fontSize: '20px', marginBottom: '12px' }}>DOS</div>
          <h1 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#fff', fontWeight: 'bold' }}>DairyOS Enterprise</h1>
          <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Dairy Farm Operating System</p>
        </div>
        {error && <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', padding: '10px 12px', borderRadius: '6px', fontSize: '11px', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}><AlertCircle size={15} color="#ef4444" /><span>{error}</span></div>}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Username</label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}><User size={15} color="#64748b" style={{ position: 'absolute', left: '12px' }} /><input type="text" value={username} onChange={e => setUsername(e.target.value)} required style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px 12px 10px 36px', borderRadius: '6px', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }} /></div>
          </div>
          <div>
            <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Password</label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}><Lock size={15} color="#64748b" style={{ position: 'absolute', left: '12px' }} /><input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px 12px 10px 36px', borderRadius: '6px', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }} /></div>
          </div>
          <button type="submit" disabled={loading} style={{ background: '#0284c7', color: '#fff', border: 'none', padding: '12px', borderRadius: '6px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginTop: '8px', opacity: loading ? 0.7 : 1 }}>{loading ? 'Authenticating...' : 'Sign In to Farm System'} <ArrowRight size={15} /></button>
        </form>
        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '10px', color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}><ShieldCheck size={13} color="#34d399" /><span>Role-based access control active</span></div>
      </div>
    </div>
  );
}
