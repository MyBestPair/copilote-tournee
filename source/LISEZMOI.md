# Copilote de tournée — sources de la version de test

- `copilote-tournee.html` : l'application (même fichier pour la page claude.ai et pour le site installable).
- `communes-fr.json` : communes et codes postaux de France → position (GeoNames CC BY 4.0, codes postaux La Poste / Etalab).
- `tools/build_pwa.py` : fabrique le site installable (`site/` : index.html, manifeste, service worker hors connexion).
- `tools/make_icons.js` : icônes de l'application.
- `tools/build_worker.py` : emballe `site/` dans un Worker Cloudflare (offre gratuite).

Mise en ligne (Worker `copilote-tournee`, adresse https://copilote-tournee.studio-conseiller.workers.dev) :
1. `python3 tools/build_pwa.py copilote-tournee.html ../site communes-fr.json`
2. `node tools/make_icons.js ../site`
3. `python3 tools/build_worker.py ../site worker.js`
4. Envoi de `worker.js` par l'API Cloudflare (PUT /accounts/{compte}/workers/scripts/copilote-tournee).

Aucune donnée de client ne passe par le serveur : tout reste dans le navigateur du téléphone.

## Sécurité (25 nov. 2026)
- Mode confidentiel (activé par défaut) : ni IA en ligne, ni dictée, ni carte ou itinéraire en ligne ; seuls les boutons Waze / Maps transmettent une adresse quand on les touche.
- Code de verrouillage : données (localStorage) et photos (IndexedDB) chiffrées en AES-GCM 256, clé tirée du code (PBKDF2-SHA256, 310 000 itérations) ; verrouillage automatique après 1 / 5 / 15 / 30 min ; « Code oublié » = effacement seulement.
- Sauvegardes chiffrées par mot de passe (version 2) ; les anciennes sauvegardes en clair restent lisibles à la restauration.
- « Effacer toutes mes données de cet appareil » (confirmation EFFACER).
- Version installable : bibliothèques (Excel, PDF, carte) hébergées dans `lib/`, en-têtes CSP, X-Frame-Options, HSTS posés par le Worker.
