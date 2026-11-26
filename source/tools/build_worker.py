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
const SEC = { 'X-Content-Type-Options':'nosniff', 'Referrer-Policy':'strict-origin-when-cross-origin', 'Permissions-Policy':'geolocation=(self), microphone=(self), camera=(self)', 'X-Robots-Tag':'noindex', 'X-Frame-Options':'DENY', 'Cross-Origin-Opener-Policy':'same-origin',
  'Strict-Transport-Security':'max-age=31536000',
  'Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline' blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: blob: https://tile.openstreetmap.org; connect-src 'self' https://router.project-osrm.org https://copilote-tournee.studio-conseiller.workers.dev https://data.geopf.fr; worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'none'; object-src 'none'" };
// Synchronisation : le serveur ne garde qu'une boîte chiffrée par l'appareil (clé inconnue ici), protégée par un jeton dont il ne garde que l'empreinte
const ORIGINS = ['https://mybestpair.github.io', 'https://copilote-tournee.studio-conseiller.workers.dev'];
const MAXB = 1900000;
function corsH(req){ const o = req.headers.get('origin'); return o && ORIGINS.includes(o) ? { 'Access-Control-Allow-Origin':o, 'Vary':'Origin', 'Access-Control-Allow-Methods':'GET, PUT, DELETE, OPTIONS', 'Access-Control-Allow-Headers':'content-type, x-sync-token', 'Access-Control-Max-Age':'86400' } : {}; }
async function sha(s){ const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)); return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join(''); }
async function api(req, env, id){
  const H = { 'content-type':'application/json; charset=utf-8', 'cache-control':'no-store', ...SEC, ...corsH(req) };
  const out = (o, status = 200) => new Response(JSON.stringify(o), { status, headers:H });
  if (req.method === 'OPTIONS') return new Response(null, { status:204, headers:H });
  const origin = req.headers.get('origin'); if (origin && !ORIGINS.includes(origin)) return out({ error:'origine refusée' }, 403);
  const tok = req.headers.get('x-sync-token') || ''; if (!/^[a-f0-9]{64}$/.test(tok)) return out({ error:'jeton manquant' }, 401);
  const db = env.DB, row = await db.prepare('SELECT ver, tok, data, updated, fails, until FROM boxes WHERE id = ?').bind(id).first(), th = await sha(tok), now = Date.now();
  if (row && row.until > now) return out({ error:'trop d’essais', retry:Math.ceil((row.until - now) / 1000) }, 429);
  if (row && row.tok !== th){   // mauvais mot de passe : au-delà de 5 essais, attente qui double à chaque échec (1 min, 2 min… 1 h)
    const fails = (row.fails || 0) + 1, until = fails >= 5 ? now + Math.min(3600000, 60000 * 2 ** (fails - 5)) : 0;
    await db.prepare('UPDATE boxes SET fails = ?, until = ? WHERE id = ?').bind(fails, until, id).run();
    return out({ error:'jeton refusé' }, 403);
  }
  if (row && row.fails) await db.prepare('UPDATE boxes SET fails = 0, until = 0 WHERE id = ?').bind(id).run();
  if (req.method === 'GET'){
    if (!row) return out({ ver:0 }, 404);
    const since = +new URL(req.url).searchParams.get('since');
    return since === row.ver ? out({ ver:row.ver, same:true }) : out({ ver:row.ver, data:row.data, updated:row.updated });
  }
  if (req.method === 'DELETE'){ if (row) await db.prepare('DELETE FROM boxes WHERE id = ?').bind(id).run(); return out({ ok:true }); }
  if (req.method === 'PUT'){
    const txt = await req.text(); if (txt.length > MAXB) return out({ error:'trop volumineux' }, 413);
    let b; try { b = JSON.parse(txt); } catch { return out({ error:'format' }, 400); }
    if (typeof b.data !== 'string' || !Number.isInteger(b.ver)) return out({ error:'format' }, 400);
    if (b.newTok !== undefined && !/^[a-f0-9]{64}$/.test(b.newTok)) return out({ error:'format' }, 400);
    if (!row){
      if (b.ver !== 0) return out({ ver:0, conflict:true }, 409);
      await db.prepare('INSERT INTO boxes (id, tok, ver, data, updated) VALUES (?, ?, 1, ?, ?)').bind(id, th, b.data, now).run();
      return out({ ver:1 });
    }
    if (b.ver !== row.ver) return out({ ver:row.ver, conflict:true }, 409);
    const r = b.newTok ? await db.prepare('UPDATE boxes SET ver = ver + 1, data = ?, updated = ?, tok = ? WHERE id = ? AND ver = ?').bind(b.data, now, await sha(b.newTok), id, row.ver).run()
      : await db.prepare('UPDATE boxes SET ver = ver + 1, data = ?, updated = ? WHERE id = ? AND ver = ?').bind(b.data, now, id, row.ver).run();
    if (!r.meta.changes) return out({ conflict:true }, 409);
    return out({ ver:row.ver + 1 });
  }
  return out({ error:'méthode' }, 405);
}
export default {
  async fetch(req, env){
    const url = new URL(req.url);
    const m = url.pathname.match(/^\\/api\\/sync\\/([a-f0-9]{64})$/);
    if (m) { try { return await api(req, env, m[1]); } catch (e) { return new Response(JSON.stringify({ error:'serveur' }), { status:500, headers:{ 'content-type':'application/json', ...SEC, ...corsH(req) } }); } }
    let path = url.pathname === '/' ? '/index.html' : url.pathname;
    const f = FILES[path];
    if (!f || (req.method !== 'GET' && req.method !== 'HEAD')) return new Response('Introuvable', { status:404, headers:{ 'content-type':'text/plain; charset=utf-8', ...SEC } });
    const cache = /\\.(png|json|css)$|^\\/lib\\//.test(path) && path !== '/manifest.webmanifest' ? 'public, max-age=86400' : 'no-cache';
    return new Response(req.method === 'HEAD' ? null : (BIN[path] || f.s), { headers:{ 'content-type':f.t, 'cache-control':cache, ...SEC } });
  }
};
""" % json.dumps(files, ensure_ascii=False)
open(out, 'w', encoding='utf-8').write(js)
print(len(js)//1024, 'Ko')
