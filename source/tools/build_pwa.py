# Fabrique la version installable (site web + application sur l'écran d'accueil) à partir de la page claude.ai
import json, sys, hashlib, shutil, pathlib
src, out, communes = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
page = open(src, encoding='utf-8').read()
version = hashlib.sha1((page + open(communes, encoding='utf-8').read()[:2000]).encode()).hexdigest()[:10]
head = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0c6a47">
<meta name="description" content="Copilote de tournée : vos tournées de commercial organisées, vos imprévus gérés, vos comptes rendus dictés. Version de test.">
<meta name="robots" content="noindex">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: blob: https://tile.openstreetmap.org; connect-src 'self' https://router.project-osrm.org https://copilote-tournee.studio-conseiller.workers.dev https://data.geopf.fr; worker-src 'self' blob:; base-uri 'self'; form-action 'none'; object-src 'none'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="icon-180.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Copilote">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui,-apple-system,"Segoe UI",sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
"""
tail = """
<script>
// Mise à jour : la nouvelle version s'installe en arrière-plan, un bandeau propose de l'ouvrir
if ('serviceWorker' in navigator) window.addEventListener('load', () => {
  let had = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.register('sw.js').then(reg => {
    document.addEventListener('visibilitychange', () => { if (!document.hidden) reg.update().catch(() => {}); });
  }).catch(() => {});
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!had){ had = true; return; }
    if (document.getElementById('upd')) return;
    const b = document.createElement('div'); b.id = 'upd'; b.className = 'upd-bar'; b.setAttribute('role', 'status');
    b.innerHTML = '<span>Nouvelle version du Copilote disponible.</span><button type="button">Mettre à jour</button>';
    b.querySelector('button').onclick = () => location.reload();
    document.body.appendChild(b);
  });
});
</script>
<style>.upd-bar{position:fixed;left:50%;transform:translateX(-50%);top:calc(env(safe-area-inset-top,0px) + 8px);z-index:50;display:flex;gap:10px;align-items:center;background:#15201b;color:#fff;padding:8px 10px 8px 14px;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.3);font:600 14px system-ui,sans-serif;max-width:calc(100vw - 24px)}.upd-bar button{background:#f2b705;color:#1d1a10;border:0;border-radius:8px;padding:8px 12px;font:inherit;cursor:pointer;min-height:40px}</style>
</body>
</html>
"""
out.mkdir(parents=True, exist_ok=True)
(out / 'index.html').write_text(head + page + tail, encoding='utf-8')
if pathlib.Path(communes).resolve() != (out / 'communes-fr.json').resolve(): shutil.copy(communes, out / 'communes-fr.json')
# Bibliothèques hébergées avec le site (plus d'appel à cdnjs : rien ne dépend d'un serveur tiers)
pkg = pathlib.Path(__file__).resolve().parent.parent / 'pkg'
LIBS = { 'xlsx.full.min.js':'x-xlsx/package/dist/xlsx.full.min.js', 'pdf.min.js':'x-pdfjs/package/build/pdf.min.js', 'pdf.worker.min.js':'x-pdfjs/package/build/pdf.worker.min.js',
  'leaflet.js':'x-leaflet/package/dist/leaflet.js', 'leaflet.css':'x-leaflet/package/dist/leaflet.css' }
(out / 'lib' / 'images').mkdir(parents=True, exist_ok=True)
if pkg.exists():   # sinon, les bibliothèques déjà présentes dans docs/lib sont gardées telles quelles
    for dst, src_ in LIBS.items(): shutil.copy(pkg / src_, out / 'lib' / dst)
    for img in (pkg / 'x-leaflet/package/dist/images').iterdir(): shutil.copy(img, out / 'lib' / 'images' / img.name)
manifest = { "name":"Copilote de tournée", "short_name":"Copilote", "lang":"fr", "start_url":"./", "scope":"./", "display":"standalone",
  "background_color":"#edf1ef", "theme_color":"#0c6a47", "description":"Tournées de commercial organisées, imprévus gérés, comptes rendus dictés.",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png"},{"src":"icon-maskable-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}] }
(out / 'manifest.webmanifest').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
sw = """// Fonctionne sans réseau : l'application et la table des communes sont gardées sur le téléphone ; les mises à jour arrivent à l'ouverture suivante
const CACHE = 'copilote-%s';
const SHELL = ['./', 'index.html', 'communes-fr.json', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'lib/leaflet.js', 'lib/leaflet.css', 'lib/xlsx.full.min.js', 'lib/pdf.min.js', 'lib/pdf.worker.min.js'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  const local = u.origin === location.origin, lib = /fonts\\.(googleapis|gstatic)\\.com/.test(u.host);
  if (!local && !lib) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(e.request, { ignoreSearch: local });
    const net = fetch(e.request).then(r => { if (r.ok || r.type === 'opaque') c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
""" % version
(out / 'sw.js').write_text(sw, encoding='utf-8')
(out / '_headers').write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: geolocation=(self), microphone=(self), camera=(self)\n/sw.js\n  Cache-Control: no-cache\n/index.html\n  Cache-Control: no-cache\n", encoding='utf-8')
print('version', version, '->', out)
