// Fonctionne sans réseau : l'application et la table des communes sont gardées sur le téléphone ; les mises à jour arrivent à l'ouverture suivante
const CACHE = 'copilote-5cf0ccbd5c';
const SHELL = ['./', 'index.html', 'communes-fr.json', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'lib/leaflet.js', 'lib/leaflet.css', 'lib/xlsx.full.min.js', 'lib/pdf.min.js', 'lib/pdf.worker.min.js'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  const local = u.origin === location.origin, lib = /fonts\.(googleapis|gstatic)\.com/.test(u.host);
  if (!local && !lib) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(e.request, { ignoreSearch: local });
    const net = fetch(e.request).then(r => { if (r.ok || r.type === 'opaque') c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
