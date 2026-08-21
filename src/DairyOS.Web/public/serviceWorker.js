const CACHE_NAME = 'dairyos-v1';
const DB_NAME = 'DairyOS_OfflineDB';
const STORE_NAME = 'sync-queue';

// 1. Initialize the Offline Vault (IndexedDB)
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// 2. Save Failed Requests to the Vault
async function saveToVault(requestUrl, payload) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).add({
        url: requestUrl,
        payload: payload,
        timestamp: new Date().getTime()
    });
    console.log('[DairyOS Courier] Network down. Saved to Digital Clipboard.');
}

// 3. Interceptor
self.addEventListener('fetch', (event) => {
    // Only intercept POST requests (saving data)
    if (event.request.method === 'POST' && event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request.clone()).catch(async () => {
                const payload = await event.request.clone().json();
                await saveToVault(event.request.url, payload);
                return new Response(JSON.stringify({ status: 'offline_queued' }), {
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
    }
});
