import { Cloud, CloudOff, Clock } from 'lucide-react';
import { useConnectivity } from '../offline/connectivity';
import { useEffect, useState } from 'react';
import { usePendingMutations } from '../offline/outboxStatus';

export default function ConnectivityStatus() {
  const { state, lastOnlineAt } = useConnectivity();
  const online = state === 'ONLINE';
  const pending = usePendingMutations();
  const [exportError, setExportError] = useState('');
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1_000);
    return () => window.clearInterval(timer);
  }, []);

  const dateText = new Intl.DateTimeFormat('en-PK', { dateStyle: 'medium' }).format(now);
  const timeText = new Intl.DateTimeFormat('en-PK', { timeStyle: 'short' }).format(now);
  const lastOnlineText = lastOnlineAt
    ? new Intl.DateTimeFormat('en-PK', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(lastOnlineAt))
    : null;
  const shortLastOnlineText = lastOnlineAt
    ? new Intl.DateTimeFormat('en-PK', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(lastOnlineAt))
    : null;
  const statusTitle = online
    ? 'Connected to the DairyOS master server'
    : state === 'CHECKING'
      ? 'Checking connection to the DairyOS master server'
      : `DairyOS master server is unreachable. Last connected: ${lastOnlineText || 'not yet recorded'}`;

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
    <div className="dairyos-connectivity-status" style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2, minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#cbd5e1', fontSize: 9, whiteSpace: 'nowrap' }}>
        <Clock size={11} aria-hidden="true" />
        <span className="dairyos-status-time" title="Device date and time" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', color: '#cbd5e1', fontSize: 8, lineHeight: 1.15, whiteSpace: 'nowrap' }}>
          <time>{dateText}</time>
          <time>{timeText}</time>
        </span>
      </div>
      {!online && state !== 'CHECKING' && <span className="dairyos-last-online" title={`Last connected: ${lastOnlineText || 'not yet recorded'}`} style={{ color: '#cbd5e1', fontSize: 8, whiteSpace: 'nowrap' }}>
        Last connected: {shortLastOnlineText || 'Not yet connected'}
      </span>}
    </div>
    <div role="status" aria-live="polite" title={statusTitle} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 3px', color: online ? '#86efac' : state === 'CHECKING' ? '#bfdbfe' : '#fca5a5', whiteSpace: 'nowrap' }}>
      <span aria-label={state === 'CHECKING' ? 'Checking connection' : online ? 'Connected' : 'Disconnected'} style={{ width: 9, height: 9, borderRadius: '50%', background: online ? '#22c55e' : state === 'CHECKING' ? '#60a5fa' : '#ef4444', boxShadow: `0 0 0 2px ${online ? 'rgba(34,197,94,.18)' : state === 'CHECKING' ? 'rgba(96,165,250,.18)' : 'rgba(239,68,68,.18)'}` }} />
    </div>
    {pending.length > 0 && <details style={{ position: 'relative', color: '#fde68a', fontSize: 10 }}>
      <summary title="Locally stored entries that were not confirmed by the DairyOS server" style={{ cursor: 'pointer', padding: '5px 7px', borderRadius: 5, background: '#713f12', border: '1px solid #92400e', fontWeight: 700, whiteSpace: 'nowrap' }}>
        Review {pending.length}
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
