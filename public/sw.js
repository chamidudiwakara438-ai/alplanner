/* AL Planner service worker — caches the app shell. APIs always go to the network. */
const CACHE = 'alplanner-shell-2026-08-13w4';
const SHELL = [
  '/', '/index.html', '/css/style.css',
  '/js/i18n.js', '/js/content.js', '/js/store.js', '/js/sims.js', '/js/app.js',
  '/js/firebase-config.js', '/manifest.json', '/assets/logo.svg',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/.netlify/')) return;
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      if (res.ok && (url.pathname.startsWith('/data/') || url.pathname.startsWith('/js/') || url.pathname.startsWith('/css/'))) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
      }
      return res;
    }).catch(() => caches.match('/index.html')))
  );
});
