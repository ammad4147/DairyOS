import { Cloud, CloudOff } from 'lucide-react';
import { useConnectivity } from '../offline/connectivity';
import { useState } from 'react';
import { usePendingMutations } from '../offline/outboxStatus';

export default function ConnectivityStatus() {
  const online = useConnectivity() === 'ONLINE';
  const pending = usePendingMutations();
  const [exportError, setExportError] = useState('');

  const exportPending = () => {
    try {
      const contents = JSON.stringify({
        exported_at: new Date().toISOString(),
        status: 'LOCAL_ONLY_NOT_CONFIRMED_DELIVERED',
        notice: 'These entries were stored in this browser and were not confirmed as received by the DairyOS server. Review each entry in DairyOS before manually re-entering it.',
        entries: pending,
      }, null, 2);
      const url = URL.createObjectURL(new Blob([contents], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `dairyos-local-unsent-entries-${new Date().toISOString().replaceAll(':', '-')}.json`;
      link.click();
      URL.revokeObjectURL(url);
      setExportError('');
    } catch {
      setExportError('Export failed. The locally stored entries remain on this device.');
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
    <div role="status" aria-live="polite" title={online ? 'Connected to DairyOS host' : 'Offline: new entries cannot be saved until the DairyOS host is reachable'} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 7px', borderRadius: 5, color: online ? '#86efac' : '#fde68a', background: online ? '#14532d' : '#713f12', border: `1px solid ${online ? '#166534' : '#92400e'}`, fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>
      {online ? <Cloud size={13} /> : <CloudOff size={13} />}
      {online ? 'Online' : 'Offline'}
    </div>
    {pending.length > 0 && <details style={{ position: 'relative', color: '#fde68a', fontSize: 10 }}>
      <summary style={{ cursor: 'pointer', padding: '5px 7px', borderRadius: 5, background: '#713f12', border: '1px solid #92400e', fontWeight: 700, whiteSpace: 'nowrap' }}>
        {pending.length} local entr{pending.length === 1 ? 'y' : 'ies'} need review
      </summary>
      <div style={{ position: 'absolute', top: 28, right: 0, width: 'min(360px, calc(100vw - 24px))', padding: 12, borderRadius: 7, background: '#111827', border: '1px solid #92400e', color: '#e2e8f0', whiteSpace: 'normal', boxShadow: '0 12px 24px rgba(0,0,0,.45)' }}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>Stored on this device; delivery was never confirmed.</div>
        <div style={{ color: '#cbd5e1', marginBottom: 9 }}>Export these records, then check the DairyOS register before entering any again. Exporting does not send or remove them.</div>
        <button type="button" onClick={exportPending} style={{ cursor: 'pointer', padding: '5px 8px', borderRadius: 4, color: '#fff', background: '#334155', border: '1px solid #64748b', fontSize: 10 }}>Export local entries (JSON)</button>
        {exportError && <div role="alert" style={{ color: '#fca5a5', marginTop: 6 }}>{exportError}</div>}
        <ol style={{ maxHeight: 150, overflowY: 'auto', paddingLeft: 20, marginBottom: 0 }}>
          {pending.map((item) => <li key={item.id} style={{ marginTop: 5 }}>
            <div>{item.endpoint} · {new Date(item.createdAt).toLocaleString()}</div>
            <pre style={{ maxHeight: 60, overflow: 'auto', fontSize: 9, color: '#cbd5e1', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(item.payload, null, 2)}</pre>
          </li>)}
        </ol>
      </div>
    </details>}
    </div>
  );
}
