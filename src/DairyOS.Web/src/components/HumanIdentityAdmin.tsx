import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config/api';

type Person = { id: number; display_name: string; entry_group: string; role: string; active: boolean; pin_set: boolean };
const API = API_BASE_URL || '';

export default function HumanIdentityAdmin() {
  const [people, setPeople] = useState<Person[]>([]);
  const [name, setName] = useState('');
  const [group, setGroup] = useState('MILK_OPERATOR');
  const [message, setMessage] = useState('');
  const [initialPins, setInitialPins] = useState<Record<number, string>>({});

  const load = async () => {
    const response = await fetch(`${API}/human-access/people`);
    const payload = await response.json();
    setPeople(payload.people || []);
  };
  useEffect(() => { void load(); }, []);

  const create = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage('');
    const response = await fetch(`${API}/human-access/people`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name: name, entry_group: group }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) { setMessage(payload.detail || 'Unable to create person.'); return; }
    setName('');
    setMessage('Person created. Initialize their PIN below before they sign in.');
    await load();
  };

  const setInitialPin = async (person: Person) => {
    const pin = initialPins[person.id] || '';
    const response = await fetch(`${API}/human-access/people/${person.id}/pin/initial`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin, pin_confirmation: pin }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) { setMessage(payload.detail || 'Unable to initialize PIN.'); return; }
    setInitialPins(current => ({ ...current, [person.id]: '' }));
    setMessage(`Initial PIN initialized for ${person.display_name}. Provide it privately; the operator can change it after signing in.`);
    await load();
  };

  const toggle = async (person: Person) => {
    const response = await fetch(`${API}/human-access/people/${person.id}/active?active=${!person.active}`, { method: 'PATCH' });
    const payload = await response.json().catch(() => ({}));
    setMessage(response.ok ? `${person.display_name} ${!person.active ? 'activated' : 'deactivated'}.` : (payload.detail || 'Unable to update identity.'));
    await load();
  };

  return <section style={{ background: '#111827', padding: 15, borderRadius: 8, border: '1px solid #1f2937' }}>
    <h3 style={{ marginTop: 0 }}>Operator Access</h3>
    <form onSubmit={create} style={{ display: 'grid', gridTemplateColumns: '1fr 180px auto', gap: 8, alignItems: 'end' }}>
      <label style={label}>Person name<input required value={name} onChange={event => setName(event.target.value)} style={field} /></label>
      <label style={label}>Entry group<select value={group} onChange={event => setGroup(event.target.value)} style={field}><option value="MANAGEMENT">DAIRYOS MANAGEMENT</option><option value="MILK_OPERATOR">MILK OPERATOR</option><option value="ACCOUNTS_OPERATOR">ACCOUNTS OPERATOR</option></select></label>
      <button type="submit" style={button}>Add Person</button>
    </form>
    {message && <p role="status">{message}</p>}
    <div style={{ marginTop: 12, display: 'grid', gap: 6 }}>{people.map(person => <div key={person.id} style={{ display: 'grid', gridTemplateColumns: '1fr 150px 150px minmax(180px, auto) auto', gap: 8, padding: 8, background: '#1e293b', borderRadius: 5, fontSize: 11, alignItems: 'center' }}>
      <span>{person.display_name}</span><span>{person.entry_group}</span><span>{person.role}</span>
      {person.pin_set ? <span>PIN SET</span> : <label style={label}>Initial PIN<input aria-label={`Initial PIN for ${person.display_name}`} type="password" inputMode="numeric" maxLength={4} pattern="[0-9]{4}" required value={initialPins[person.id] || ''} onChange={event => setInitialPins(current => ({ ...current, [person.id]: event.target.value }))} style={field} /><button type="button" onClick={() => void setInitialPin(person)} style={button}>Set Initial PIN</button></label>}
      <button type="button" onClick={() => void toggle(person)} style={button}>{person.active ? 'Deactivate' : 'Activate'}</button>
    </div>)}</div>
  </section>;
}

const field: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', color: '#fff', padding: 8, border: '1px solid #334155', borderRadius: 5 };
const label: React.CSSProperties = { fontSize: 10, color: '#94a3b8', display: 'block' };
const button: React.CSSProperties = { background: '#0284c7', color: '#fff', padding: '8px 11px', border: 0, borderRadius: 5, cursor: 'pointer', fontWeight: 800 };
