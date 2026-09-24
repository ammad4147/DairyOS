import React, { useEffect, useMemo, useRef, useState } from 'react';
import { MainAppShell } from '../App';
import { clearUncertainWriteMarkers } from '../api/farmEntryClient';
import HumanOperatorConsole from './HumanOperatorConsole';
import { API_BASE_URL } from '../config/api';
import './HumanAccessGate.css';

const API = API_BASE_URL || '';
const HUMAN_SESSION_KEY = 'dairyos.human.session';
const HUMAN_ACCESS_CHANNEL = 'dairyos.human-access';
const HUMAN_ACCESS_TAB_ID = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
type Person = { id: number; display_name: string; workspace: string; role: string; pin_set: boolean; active: boolean };
type GateState = 'loading' | 'bootstrap' | 'welcome' | 'pin' | 'management' | 'operator' | 'error';
const initials = (name: string) => name.trim().split(/\s+/).slice(0, 2).map(part => part[0]?.toUpperCase() || '').join('');

export default function HumanAccessGate() {
  const [state, setState] = useState<GateState>('loading');
  const [identity, setIdentity] = useState<Person | null>(null);
  const [people, setPeople] = useState<Person[]>([]);
  const [selected, setSelected] = useState<Person | null>(null);
  const [name, setName] = useState('');
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [message, setMessage] = useState('');
  const [search, setSearch] = useState('');
  const [clock, setClock] = useState(new Date());
  const logoutRef = useRef<(notifyOtherTabs?: boolean) => Promise<void>>(async () => {});

  const routeIdentity = (person: Person) => {
    setIdentity(person);
    setState(person.workspace === 'MANAGEMENT' ? 'management' : 'operator');
  };

  const load = async () => {
    try {
      const statusResponse = await fetch(`${API}/human-access/status`);
      if (!statusResponse.ok) throw new Error('Unable to resolve DairyOS access state.');
      const status = await statusResponse.json();
      const existing = sessionStorage.getItem(HUMAN_SESSION_KEY);
      if (existing) {
        const me = await fetch(`${API}/human-access/me`, { headers: { 'X-DairyOS-Human-Session': existing } });
        if (me.ok) { const body = await me.json(); routeIdentity(body.identity); return; }
        sessionStorage.removeItem(HUMAN_SESSION_KEY);
      }
      if (status.bootstrap_required) { setState('bootstrap'); return; }
      const response = await fetch(`${API}/human-access/people`);
      if (!response.ok) throw new Error('Unable to load active DairyOS identities.');
      const payload = await response.json();
      setPeople((payload.people || []).filter((person: Person) => person.active !== false));
      setState('welcome');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'DairyOS access initialization failed.');
      setState('error');
    }
  };

  useEffect(() => { void load(); }, []);
  useEffect(() => { const timer = window.setInterval(() => setClock(new Date()), 1000); return () => window.clearInterval(timer); }, []);

  const filteredPeople = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return people.filter(person => person.display_name.toLocaleLowerCase().includes(query));
  }, [people, search]);

  const choose = (person: Person) => { setSelected(person); setPin(''); setConfirmPin(''); setMessage(''); setState('pin'); };

  const bootstrap = async (event: React.FormEvent) => {
    event.preventDefault(); setMessage('');
    const response = await fetch(`${API}/human-access/bootstrap`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: name, pin, pin_confirmation: confirmPin }) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) { setMessage(payload.detail || 'Primary Administrator setup failed.'); return; }
    setPin(''); setConfirmPin(''); await load();
  };

  const login = async (event: React.FormEvent) => {
    event.preventDefault(); if (!selected) return; setMessage('');
    if (!selected.pin_set) { setMessage('Ask the Primary Administrator to initialize your PIN.'); return; }
    const response = await fetch(`${API}/human-access/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ identity_id: selected.id, pin }) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) { setMessage(payload.detail || 'Unable to authenticate.'); return; }
    sessionStorage.setItem(HUMAN_SESSION_KEY, payload.session_token);
    setPin(''); setConfirmPin(''); routeIdentity(payload.identity);
  };

  const logout = async (notifyOtherTabs = true) => {
    const token = sessionStorage.getItem(HUMAN_SESSION_KEY);
    try {
      await fetch(`${API}/human-access/logout`, { method: 'POST', headers: token ? { 'X-DairyOS-Human-Session': token } : {} });
    } catch {
      // End this browser session locally even when the server cannot be reached.
    } finally {
      if (notifyOtherTabs && typeof BroadcastChannel !== 'undefined') {
        try {
          const channel = new BroadcastChannel(HUMAN_ACCESS_CHANNEL);
          channel.postMessage({ type: 'logout', sender: HUMAN_ACCESS_TAB_ID });
          channel.close();
        } catch {
          // Local logout must complete even if peer-tab notification is unavailable.
        }
      }
      clearUncertainWriteMarkers();
      sessionStorage.removeItem(HUMAN_SESSION_KEY); setIdentity(null); setSelected(null); await load();
    }
  };
  logoutRef.current = logout;

  useEffect(() => {
    if (typeof BroadcastChannel === 'undefined') return;
    const channel = new BroadcastChannel(HUMAN_ACCESS_CHANNEL);
    const onMessage = (event: MessageEvent) => {
      if (event.data?.type === 'logout' && event.data.sender !== HUMAN_ACCESS_TAB_ID) {
        void logoutRef.current(false);
      }
    };
    channel.addEventListener('message', onMessage);
    return () => {
      channel.removeEventListener('message', onMessage);
      channel.close();
    };
  }, []);

  if (state === 'management') return <MainAppShell />;
  if (state === 'operator' && identity) return <HumanOperatorConsole identity={identity} onLogout={() => void logout()} />;
  if (state === 'loading') return <WelcomePanel><p>Loading DairyOS access…</p></WelcomePanel>;
  if (state === 'error') return <WelcomePanel><h1>DairyOS access unavailable</h1><p className="welcome-alert">{message}</p></WelcomePanel>;

  if (state === 'bootstrap') return <form onSubmit={bootstrap} className="welcome-screen"><div className="welcome-panel-wrap"><div className="welcome-panel">
    <Brand /><h1>Set up DairyOS</h1><p>Establish the first Primary Administrator. Do not share the PIN.</p>
    <input aria-label="Administrator name" placeholder="Your name" value={name} onChange={e => setName(e.target.value)} required />
    <input aria-label="Administrator PIN" type="password" inputMode="numeric" maxLength={4} placeholder="Four-digit PIN" value={pin} onChange={e => setPin(e.target.value)} required />
    <input aria-label="Confirm administrator PIN" type="password" inputMode="numeric" maxLength={4} placeholder="Confirm PIN" value={confirmPin} onChange={e => setConfirmPin(e.target.value)} required />
    <button className="welcome-primary" type="submit">Create Primary Administrator</button>{message && <p className="welcome-alert" role="alert">{message}</p>}
  </div></div></form>;

  if (state === 'pin' && selected) return <form onSubmit={login} className="welcome-screen"><div className="welcome-panel-wrap"><div className="welcome-panel">
    <Brand /><button type="button" className="welcome-link welcome-back" onClick={() => setState('welcome')}>← Choose another person</button>
    <div className="welcome-selected-initials">{initials(selected.display_name)}</div>
    <h1>{selected.pin_set ? `Welcome back, ${selected.display_name}` : selected.display_name}</h1>
    <p>{selected.pin_set ? 'Enter your PIN to continue.' : 'Ask the Primary Administrator to initialize your PIN before signing in.'}</p>
    {selected.pin_set && <><input aria-label="PIN" type="password" inputMode="numeric" maxLength={4} placeholder="PIN" value={pin} onChange={e => setPin(e.target.value)} required autoFocus /><button className="welcome-primary" type="submit">Continue</button></>}
    {message && <p className="welcome-alert" role="alert">{message}</p>}
  </div></div></form>;

  const count = filteredPeople.length;
  const gridClass = count <= 4 ? 'welcome-identity-grid welcome-identity-grid-balanced' : 'welcome-identity-grid';
  return <div className="welcome-screen"><div className="welcome-shell">
    <header className="welcome-top"><Brand /><Clock value={clock} /></header>
    <main className="welcome-main">
      <h1 className="welcome-title">Welcome to DairyOS</h1><p className="welcome-prompt">Select your name to continue</p>
      <div className={gridClass}>{filteredPeople.map(person => <button type="button" key={person.id} className="welcome-identity-card" onClick={() => choose(person)} aria-label={`Continue as ${person.display_name}`}><span className="welcome-initials">{initials(person.display_name)}</span><span className="welcome-name">{person.display_name}</span></button>)}</div>
      {count === 0 && <p className="welcome-empty">No matching active identities.</p>}
      <input className="welcome-search" aria-label="Find your name" placeholder="Find your name..." value={search} onChange={e => setSearch(e.target.value)} />
    </main>
    <div className="welcome-footer">BETTER DATA • BETTER DECISIONS • A STRONGER DAIRY FUTURE</div>
  </div></div>;
}

function Brand() { return <div className="welcome-brand"><div className="welcome-wordmark">Dairy<span>OS</span></div><div className="welcome-subbrand">FARM MANAGEMENT SYSTEM</div></div>; }
function Clock({ value }: { value: Date }) { return <div className="welcome-clock"><div>{value.toLocaleDateString('en-PK',{weekday:'long',day:'2-digit',month:'long',year:'numeric'})}</div><strong>{value.toLocaleTimeString('en-PK',{hour:'2-digit',minute:'2-digit'})}</strong></div>; }
function WelcomePanel({ children }: { children: React.ReactNode }) { return <div className="welcome-screen"><div className="welcome-panel-wrap"><div className="welcome-panel"><Brand />{children}</div></div></div>; }
