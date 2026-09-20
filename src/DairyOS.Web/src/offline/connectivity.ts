import { useEffect, useState } from 'react';

export type ConnectivityState = 'ONLINE' | 'OFFLINE';

export function useConnectivity(): ConnectivityState {
  const [state, setState] = useState<ConnectivityState>(
    typeof navigator === 'undefined' || navigator.onLine ? 'ONLINE' : 'OFFLINE',
  );
  useEffect(() => {
    const online = () => setState('ONLINE');
    const offline = () => setState('OFFLINE');
    window.addEventListener('online', online);
    window.addEventListener('offline', offline);
    return () => {
      window.removeEventListener('online', online);
      window.removeEventListener('offline', offline);
    };
  }, []);
  return state;
}
