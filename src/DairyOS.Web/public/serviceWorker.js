self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key.startsWith('dairyos-')).map((key) => caches.delete(key)));
    await self.registration.unregister();
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  // Intentionally do not intercept requests. In particular, never cache or
  // synthesize API responses that could be mistaken for current farm data.
});
