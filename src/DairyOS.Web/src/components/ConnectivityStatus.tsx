import { Cloud, CloudOff } from 'lucide-react';
import { useConnectivity } from '../offline/connectivity';
import { flushOutbox } from '../offline/outbox';
import { usePendingMutationCount } from '../offline/outboxStatus';
import { useState } from 'react';

export default function ConnectivityStatus() {
  const online = useConnectivity() === 'ONLINE';
  const pending = usePendingMutationCount();
  const [syncing, setSyncing] = useState(false);
  const syncNow = async () => {
    if (!online || syncing || pending === 0) return;
    setSyncing(true);
    try {
      await flushOutbox();
    } finally {
      setSyncing(false);
    }
  };
  return (
    <div role="status" aria-live="polite" title={online ? 'Connected to DairyOS host' : 'Offline: entries are saved on this device and will sync when connected'} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 7px', borderRadius: 5, color: online ? '#86efac' : '#fde68a', background: online ? '#14532d' : '#713f12', border: `1px solid ${online ? '#166534' : '#92400e'}`, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>
      {online ? <Cloud size={13} /> : <CloudOff size={13} />}
      {online ? 'Online' : 'Offline'}{pending > 0 ? ` · ${pending} pending` : ''}
      {pending > 0 && <button type="button" onClick={() => void syncNow()} disabled={!online || syncing} aria-label="Sync pending entries now" style={{ border: 0, borderRadius: 3, padding: '2px 4px', fontSize: 9, fontWeight: 700, cursor: online && !syncing ? 'pointer' : 'default', color: '#0f172a', background: online && !syncing ? '#bbf7d0' : '#94a3b8' }}>{syncing ? 'Syncing…' : 'Sync now'}</button>}
    </div>
  );
}
