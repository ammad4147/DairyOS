import { Cloud, CloudOff } from 'lucide-react';
import { useConnectivity } from '../offline/connectivity';

export default function ConnectivityStatus() {
  const online = useConnectivity() === 'ONLINE';
  return (
    <div role="status" aria-live="polite" title={online ? 'Connected to DairyOS host' : 'Offline: new entries cannot be saved until the DairyOS host is reachable'} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 7px', borderRadius: 5, color: online ? '#86efac' : '#fde68a', background: online ? '#14532d' : '#713f12', border: `1px solid ${online ? '#166534' : '#92400e'}`, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>
      {online ? <Cloud size={13} /> : <CloudOff size={13} />}
      {online ? 'Online' : 'Offline'}
    </div>
  );
}
