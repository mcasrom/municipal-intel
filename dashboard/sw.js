const VERSION = 'municipal-v1';
const CACHE = VERSION + "-20260824c";
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './og-municipal.png',
  './data/catalogo.json',
  './data/series.json',
  './data/rankings.json',
  './data/lorca_intel.json',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  // los datos pueden actualizarse (cron): network-first para JSON
  if (url.pathname.startsWith('/data/')) {
    e.respondWith(
      fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }
  // app shell y páginas: cache-first con revalidación en background
  e.respondWith(
    caches.match(e.request).then((hit) => {
      const fallback = hit || caches.match('./');
      const network = fetch(e.request).then((res) => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => fallback);
      return hit || network;
    })
  );
});
