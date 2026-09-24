import { apiUrl } from '../config/api';

const DB_NAME = 'DairyOS_Web_Offline';
const DB_VERSION = 1;
const STORE = 'mutation-outbox';
export const OUTBOX_CHANGED = 'dairyos-outbox-changed';

export type QueuedMutation = {
  id: string;
  endpoint: string;
  payload: unknown;
  createdAt: string;
  attempts: number;
  lastError?: string;
};

function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE, { keyPath: 'id' });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function enqueueMutation(endpoint: string, payload: unknown): Promise<QueuedMutation> {
  const mutation: QueuedMutation = {
    id: crypto.randomUUID(), endpoint, payload, createdAt: new Date().toISOString(), attempts: 0,
  };
  const db = await database();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).add(mutation);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
  window.dispatchEvent(new Event(OUTBOX_CHANGED));
  return mutation;
}

async function pending(): Promise<QueuedMutation[]> {
  const db = await database();
  return new Promise((resolve, reject) => {
    const request = db.transaction(STORE, 'readonly').objectStore(STORE).getAll();
    request.onsuccess = () => { db.close(); resolve((request.result as QueuedMutation[]).sort((a, b) => a.createdAt.localeCompare(b.createdAt))); };
    request.onerror = () => { db.close(); reject(request.error); };
  });
}

async function remove(id: string): Promise<void> {
  const db = await database();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
  window.dispatchEvent(new Event(OUTBOX_CHANGED));
}

async function markFailed(item: QueuedMutation, error: unknown): Promise<void> {
  const db = await database();
  item.attempts += 1;
  item.lastError = error instanceof Error ? error.message : String(error);
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(item);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
  window.dispatchEvent(new Event(OUTBOX_CHANGED));
}

export async function pendingMutationCount(): Promise<number> {
  return (await pending()).length;
}

export async function flushOutbox(): Promise<{ sent: number; remaining: number }> {
  if (!navigator.onLine) return { sent: 0, remaining: (await pending()).length };
  let sent = 0;
  for (const item of await pending()) {
    try {
      const response = await fetch(apiUrl(item.endpoint), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item.payload),
      });
      if (!response.ok) throw new Error(`Sync rejected (${response.status})`);
      await remove(item.id);
      sent += 1;
    } catch (error) {
      await markFailed(item, error);
      break;
    }
  }
  return { sent, remaining: (await pending()).length };
}

export function startOutboxSync(): () => void {
  const sync = () => { void flushOutbox(); };
  window.addEventListener('online', sync);
  const timer = window.setInterval(sync, 60_000);
  sync();
  return () => { window.removeEventListener('online', sync); window.clearInterval(timer); };
}
