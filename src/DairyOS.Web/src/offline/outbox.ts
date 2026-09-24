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

export async function listPendingMutations(): Promise<QueuedMutation[]> {
  const db = await database();
  return new Promise((resolve, reject) => {
    const request = db.transaction(STORE, 'readonly').objectStore(STORE).getAll();
    request.onsuccess = () => { db.close(); resolve((request.result as QueuedMutation[]).sort((a, b) => a.createdAt.localeCompare(b.createdAt))); };
    request.onerror = () => { db.close(); reject(request.error); };
  });
}
