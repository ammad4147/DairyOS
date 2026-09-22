import React, { useEffect, useMemo, useState } from 'react';
import { MainAppShell } from '../App';
import HumanOperatorConsole from './HumanOperatorConsole';
import { API_BASE_URL } from '../config/api';
import './HumanAccessGate.css';

const API = API_BASE_URL || '';
const HUMAN_SESSION_KEY = 'dairyos.human.session';
type Person = { id: number; display_name: string; entry_group: string; role: string; pin_set: boolean; active: boolean };
type GateState = 'loading' | 'bootstrap' | 'welcome' | 'pin' | 'management' | 'operator' | 'help' | 'error';
const initials = (name: string) => name.trim().split(/\s+/).slice(0, 2).map(part => part[0]?.toUpperCase() || '').join('');
const accent = (id: number) => [205, 145, 38, 270, 355, 181][Math.abs(id) % 6];

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
  const [wallpaper, setWallpaper] = useState<string | null>(null);

  const load = async () => {
    try {
      const statusResponse = await fetch(`${API}/human-access/status`);
      if (!statusResponse.ok) throw new Error('Unable to resolve DairyOS access state.');
      const status = await statusResponse.json();
      const wallpaperResponse = await fetch(`${API}/settings/welcome-screen`);
      if (wallpaperResponse.ok) {
        const wallpaperPayload = await wallpaperResponse.json();
        setWallpaper(typeof wallpaperPayload.wallpaper === 'string' ? wallpaperPayload.wallpaper : null);
      }
      const existing = sessionStorage.getItem(HUMAN_SESSION_KEY);
      if (existing) {
        const me = await fetch(`${API}/human-access/me`, { headers: { 'X-DairyOS-Human-Session': existing } });
        if (me.ok) {
          const body = await me.json();
          setIdentity(body.identity);
          setState(body.identity?.entry_group === 'MANAGEMENT' ? 'management' : 'operator');
          return;
        }
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
  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const filteredPeople = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return people.filter(person => person.display_name.toLocaleLowerCase().includes(query));
  }, [people, search]);

  const choose = (person: Person) => {
    setSelected(person); setPin(''); setConfirmPin(''); setMessage(''); setState('pin');
  };

  const bootstrap = async (event: React.FormEvent) => {
    event.preventDefault(); setMessage('');
    const response = await fetch(`${API}/human-access/bootstrap`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: name, pin, pin_confirmation: confirmPin }) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) { setMessage(payload.detail || 'Primary Administrator setup failed.'); return; }
    setPin(''); setConfirmPin(''); await load();
  };

  const login = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selected) return;
    setMessage('');
    if (!selected.pin_set) {
      const setup = await fetch(`${API}/human-access/people/${selected.id}/pin/initial`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pin, pin_confirmation: confirmPin }) });
      const setupPayload = await setup.json().catch(() => ({}));
      if (!setup.ok) { setMessage(setupPayload.detail || 'Initial PIN setup failed.'); return; }
    }
    const response = await fetch(`${API}/human-access/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ identity_id: selected.id, pin }) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) { setMessage(payload.detail || 'Unable to authenticate.'); return; }
    sessionStorage.setItem(HUMAN_SESSION_KEY, payload.session_token);
    setIdentity(payload.identity); setPin(''); setConfirmPin('');
    setState(payload.identity?.entry_group === 'MANAGEMENT' ? 'management' : 'operator');
  };

  const logout = async () => {
    const token = sessionStorage.getItem(HUMAN_SESSION_KEY);
    await fetch(`${API}/human-access/logout`, { method: 'POST', headers: token ? { 'X-DairyOS-Human-Session': token } : {} });
    sessionStorage.removeItem(HUMAN_SESSION_KEY); setIdentity(null); setSelected(null); await load();
  };

  if (state === 'management') return <MainAppShell />;
  if (state === 'operator' && identity) return <HumanOperatorConsole identity={identity} onLogout={() => void logout()} />;
  if (state === 'loading') return <WelcomePanel><p>Loading DairyOS access…</p></WelcomePanel>;
  if (state === 'error') return <WelcomePanel><h1>DairyOS access unavailable</h1><p className="welcome-alert">{message}</p></WelcomePanel>;

  if (state === 'bootstrap') return (
    <form onSubmit={bootstrap} className="welcome-screen">
      <div className="welcome-panel-wrap"><div className="welcome-panel">
        <Brand />
        <h1>Set up DairyOS</h1>
        <p>Establish the first Primary Administrator. Do not share the PIN.</p>
        <input aria-label="Administrator name" placeholder="Your name" value={name} onChange={e => setName(e.target.value)} required />
        <input aria-label="Administrator PIN" type="password" inputMode="numeric" maxLength={4} placeholder="Four-digit PIN" value={pin} onChange={e => setPin(e.target.value)} required />
        <input aria-label="Confirm administrator PIN" type="password" inputMode="numeric" maxLength={4} placeholder="Confirm PIN" value={confirmPin} onChange={e => setConfirmPin(e.target.value)} required />
        <button className="welcome-primary" type="submit">Create Primary Administrator</button>
        {message && <p className="welcome-alert" role="alert">{message}</p>}
      </div></div>
    </form>
  );

  if (state === 'help') return <HelpFlow people={people} onBack={() => { setMessage(''); setState('welcome'); }} />;

  if (state === 'pin' && selected) return (
    <form onSubmit={login} className="welcome-screen" style={wallpaper ? { '--welcome-wallpaper': `url("${wallpaper}")` } as React.CSSProperties : undefined}>
      <div className="welcome-panel-wrap"><div className="welcome-panel">
        <Brand />
        <button type="button" className="welcome-link welcome-back" onClick={() => setState('welcome')}>← Choose another person</button>
        <div className="welcome-avatar welcome-selected-avatar" style={{ '--accent': accent(selected.id) } as React.CSSProperties}>{initials(selected.display_name)}</div>
        <h1>{selected.pin_set ? `Welcome back, ${selected.display_name}` : selected.display_name}</h1>
        <p>{selected.pin_set ? 'Enter your PIN to continue.' : 'Create your four-digit PIN to continue.'}</p>
        <input aria-label="PIN" type="password" inputMode="numeric" maxLength={4} placeholder="PIN" value={pin} onChange={e => setPin(e.target.value)} required autoFocus />
        {!selected.pin_set && <input aria-label="Confirm PIN" type="password" inputMode="numeric" maxLength={4} placeholder="Confirm PIN" value={confirmPin} onChange={e => setConfirmPin(e.target.value)} required />}
        <button className="welcome-primary" type="submit">{selected.pin_set ? 'Continue' : 'Create PIN'}</button>
        {message && <p className="welcome-alert" role="alert">{message}</p>}
        <button type="button" className="welcome-link" onClick={() => setState('help')}>Need help? Contact Administrator</button>
      </div></div>
    </form>
  );

  const identityCard = 'welcome-identity-card';
  return (
    <div className="welcome-screen" style={wallpaper ? { '--welcome-wallpaper': `url("${wallpaper}")` } as React.CSSProperties : undefined}>
      <div className="welcome-shell">
        <header className="welcome-top">
          <Brand />
          <div className="welcome-motto" aria-hidden="true">Healthy Animals<br />Productive Farms<br />A Brighter Tomorrow</div>
        </header>

        <main className="welcome-main">
          <h1 className="welcome-title">Welcome to DairyOS</h1>
          <p className="welcome-prompt">Select your name to continue</p>
          <div className="welcome-identity-grid">
            {filteredPeople.map(person => (
              <button type="button" key={person.id} className={identityCard} onClick={() => choose(person)} aria-label={`Continue as ${person.display_name}`}>
                <span className="welcome-avatar" style={{ '--accent': accent(person.id) } as React.CSSProperties}>{initials(person.display_name)}</span>
                <span className="welcome-name">{person.display_name}</span>
              </button>
            ))}
          </div>
          {filteredPeople.length === 0 && <p className="welcome-empty">No matching active identities.</p>}
          <div className="welcome-search-wrap">
            <span className="welcome-search-icon" aria-hidden="true">⌕</span>
            <input className="welcome-search" aria-label="Find your name" placeholder="Find your name..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </main>

        <div className="welcome-bottom">
          <button type="button" className="welcome-help" onClick={() => setState('help')}><strong>Need help?</strong><span>Contact Administrator</span></button>
          <div className="welcome-footer" aria-hidden="true">
            <div className="welcome-farm-mark">⌂ ─ ◇ ─ ⌂</div>
            <div className="welcome-footer-line">BETTER DATA • BETTER DECISIONS • A STRONGER DAIRY FUTURE</div>
          </div>
          <div className="welcome-clock">
            <div className="welcome-clock-date">{clock.toLocaleDateString('en-PK', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })}</div>
            <div className="welcome-clock-time">{clock.toLocaleTimeString('en-PK', { hour: '2-digit', minute: '2-digit' })}</div>
          </div>
        </div>
      </div>
      <svg className="welcome-wave" viewBox="0 0 1600 180" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0 110 C280 45 430 145 720 100 C980 58 1180 112 1600 48 V180 H0Z" fill="rgba(4,31,57,.78)" />
        <path d="M0 140 C310 85 520 160 820 124 C1110 88 1320 130 1600 92 V180 H0Z" fill="rgba(4,22,42,.88)" />
      </svg>
    </div>
  );
}

function Brand() {
  return <div className="welcome-brand"><img src="/dairyos-cow.svg" alt="" aria-hidden="true" /><div className="welcome-brand-copy"><div className="welcome-wordmark">Dairy<span>OS</span></div><div className="welcome-subbrand">FARM MANAGEMENT SYSTEM</div></div></div>;
}

function WelcomePanel({ children }: { children: React.ReactNode }) {
  return <div className="welcome-screen"><div className="welcome-panel-wrap"><div className="welcome-panel"><Brand />{children}</div></div></div>;
}

function HelpFlow({ people, onBack }: { people: Person[]; onBack: () => void }) {
  const [identityId, setIdentityId] = useState('');
  const [missingName, setMissingName] = useState('');
  const [reason, setReason] = useState('Forgot PIN');
  const [detail, setDetail] = useState('');
  const [message, setMessage] = useState('');
  const selectedPerson = people.find(person => String(person.id) === identityId);
  const missing = reason === 'My name is missing';

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const displayName = missing ? missingName.trim() : (selectedPerson?.display_name || '');
    if (!displayName) { setMessage('Select your name or enter the missing name.'); return; }
    const composed = detail.trim() ? `${reason}: ${detail.trim()}` : reason;
    const response = await fetch(`${API}/human-access/help`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: displayName, message: composed }) });
    const payload = await response.json().catch(() => ({}));
    setMessage(response.ok ? 'Your request was recorded for Administrator review.' : (payload.detail || 'Unable to record the request.'));
  };

  return <form onSubmit={submit} className="welcome-screen"><div className="welcome-panel-wrap"><div className="welcome-panel">
    <Brand />
    <button type="button" className="welcome-link welcome-back" onClick={onBack}>← Back</button>
    <h1>Need help accessing DairyOS?</h1>
    {!missing && <select aria-label="Your name" value={identityId} onChange={e => setIdentityId(e.target.value)} required><option value="">Select your name</option>{people.map(person => <option key={person.id} value={person.id}>{person.display_name}</option>)}</select>}
    <select aria-label="Access problem" value={reason} onChange={e => setReason(e.target.value)}>
      <option>Forgot PIN</option><option>Cannot sign in</option><option>My name is missing</option><option>Other access problem</option>
    </select>
    {missing && <input aria-label="Your name" placeholder="Your name" value={missingName} onChange={e => setMissingName(e.target.value)} required />}
    <textarea aria-label="Additional details" placeholder="Additional details (optional)" value={detail} onChange={e => setDetail(e.target.value)} />
    <p>No PIN is reset from this screen. The Administrator will review your request.</p>
    <button className="welcome-primary" type="submit">Send Request</button>
    {message && <p role="status">{message}</p>}
  </div></div></form>;
}
