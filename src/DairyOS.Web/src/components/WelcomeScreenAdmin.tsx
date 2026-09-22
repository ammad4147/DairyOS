import React, { useState } from 'react';
import { API_BASE_URL } from '../config/api';

const API = API_BASE_URL || '';
const sessionHeaders = () => ({ 'X-DairyOS-Human-Session': sessionStorage.getItem('dairyos.human.session') || '' });

export default function WelcomeScreenAdmin() {
  const [message, setMessage] = useState('');
  const save = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; if (!file) return;
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 1_500_000) { setMessage('Choose a PNG, JPEG, or WebP image up to 1.5 MB.'); return; }
    const reader = new FileReader(); reader.onload = async () => { const response = await fetch(`${API}/settings/welcome-screen`, { method: 'PUT', headers: { ...sessionHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ data_url: reader.result }) }); setMessage(response.ok ? 'Welcome wallpaper saved.' : 'Wallpaper could not be saved.'); }; reader.readAsDataURL(file);
  };
  const clear = async () => { const response = await fetch(`${API}/settings/welcome-screen`, { method: 'PUT', headers: { ...sessionHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ data_url: null }) }); setMessage(response.ok ? 'Default farm wallpaper restored.' : 'Wallpaper could not be cleared.'); };
  return <section><h3>Welcome Screen</h3><p>Optional custom wallpaper. DairyOS falls back to the default farm visual if unavailable.</p><input type="file" accept="image/png,image/jpeg,image/webp" onChange={save} /><button type="button" onClick={() => void clear()}>Restore default</button>{message && <p role="status">{message}</p>}</section>;
}
