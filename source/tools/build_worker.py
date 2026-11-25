# Emballe le site de test dans un Worker Cloudflare (un seul fichier, offre gratuite)
import json, base64, sys, pathlib, mimetypes
site = pathlib.Path(sys.argv[1]); out = sys.argv[2]
TYPES = { '.css':'text/css; charset=utf-8', '.html':'text/html; charset=utf-8', '.json':'application/json; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.webmanifest':'application/manifest+json; charset=utf-8', '.png':'image/png' }
files = {}
for f in sorted(site.rglob('*')):
    if f.is_dir() or f.name.startswith('_'): continue
    ext, key = f.suffix, '/' + f.relative_to(site).as_posix()
    if ext == '.png': files[key] = { 't':TYPES[ext], 'b64':base64.b64encode(f.read_bytes()).decode() }
    else: files[key] = { 't':TYPES.get(ext, 'application/octet-stream'), 's':f.read_text(encoding='utf-8') }
js = """// Copilote de tournée — version de test. Site statique servi par un Worker (aucune donnée de client ne passe par ici : tout reste sur le téléphone).
const FILES = %s;
const BIN = {};
for (const [k, v] of Object.entries(FILES)) if (v.b64) BIN[k] = Uint8Array.from(atob(v.b64), c => c.charCodeAt(0));
const SEC = { 'X-Content-Type-Options':'nosniff', 'Referrer-Policy':'no-referrer', 'Permissions-Policy':'geolocation=(self), microphone=(self), camera=(self)', 'X-Robots-Tag':'noindex', 'X-Frame-Options':'DENY', 'Cross-Origin-Opener-Policy':'same-origin',
  'Strict-Transport-Security':'max-age=31536000',
  'Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline' blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: blob: https://tile.openstreetmap.org; connect-src 'self' https://router.project-osrm.org; worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'none'; object-src 'none'" };
export default {
  async fetch(req){
    const url = new URL(req.url); let path = url.pathname === '/' ? '/index.html' : url.pathname;
    const f = FILES[path];
    if (!f || (req.method !== 'GET' && req.method !== 'HEAD')) return new Response('Introuvable', { status:404, headers:{ 'content-type':'text/plain; charset=utf-8', ...SEC } });
    const cache = /\\.(png|json|css)$|^\\/lib\\//.test(path) && path !== '/manifest.webmanifest' ? 'public, max-age=86400' : 'no-cache';
    return new Response(req.method === 'HEAD' ? null : (BIN[path] || f.s), { headers:{ 'content-type':f.t, 'cache-control':cache, ...SEC } });
  }
};
""" % json.dumps(files, ensure_ascii=False)
open(out, 'w', encoding='utf-8').write(js)
print(len(js)//1024, 'Ko')
