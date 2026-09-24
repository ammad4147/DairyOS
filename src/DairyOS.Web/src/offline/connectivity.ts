import { useEffect, useState } from 'react';
import { apiUrl } from '../config/api';

export type ConnectivityState = 'CHECKING' | 'ONLINE' | 'OFFLINE';

export interface ConnectivityStatusValue {
  state: ConnectivityState;
  lastOnlineAt: string | null;
}

const LAST_ONLINE_KEY = 'dairyos:last-successful-server-contact';
const CHECK_INTERVAL_MS = 30_000;
const CHECK_TIMEOUT_MS = 4_000;

function readLastOnline(): string | null {
  try {
    const value = window.localStorage.getItem(LAST_ONLINE_KEY);
    return value && Number.isFinite(Date.parse(value)) ? value : null;
  } catch {
    return null;
  }
}

export function useConnectivity(): ConnectivityStatusValue {
  const [status, setStatus] = useState<ConnectivityStatusValue>({
    state: 'CHECKING',
    lastOnlineAt: null,
  });

  useEffect(() => {
    let mounted = true;
    let checking = false;
    let lastOnlineAt = readLastOnline();

    const publish = (state: ConnectivityState) => {
      if (mounted) setStatus({ state, lastOnlineAt });
    };

    const checkServer = async () => {
      if (checking || !mounted) return;
      if (!navigator.onLine) {
        publish('OFFLINE');
        return;
      }

      checking = true;
      const controller = new AbortController();
      const timeout = window.setTimeout(
        () => controller.abort(),
        CHECK_TIMEOUT_MS,
      );
      try {
        const response = await fetch(apiUrl('/health'), {
          method: 'GET',
          cache: 'no-store',
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
        const body = await response.json() as { system?: string; status?: string };
        if (body.system !== 'DairyOS' || body.status !== 'healthy') {
          throw new Error('DairyOS server did not report healthy.');
        }
        lastOnlineAt = new Date().toISOString();
        try { window.localStorage.setItem(LAST_ONLINE_KEY, lastOnlineAt); } catch { /* display still works for this app session */ }
        publish('ONLINE');
      } catch {
        publish('OFFLINE');
      } finally {
        window.clearTimeout(timeout);
        checking = false;
      }
    };

    const onNetworkChange = () => {
      if (!navigator.onLine) publish('OFFLINE');
      else void checkServer();
    };
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') void checkServer();
    };

    setStatus({ state: 'CHECKING', lastOnlineAt });
    void checkServer();
    const interval = window.setInterval(() => { void checkServer(); }, CHECK_INTERVAL_MS);
    window.addEventListener('online', onNetworkChange);
    window.addEventListener('offline', onNetworkChange);
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => {
      mounted = false;
      window.clearInterval(interval);
      window.removeEventListener('online', onNetworkChange);
      window.removeEventListener('offline', onNetworkChange);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, []);

  return status;
}
