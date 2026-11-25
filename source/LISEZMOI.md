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

## Hébergement (25 nov. 2026)
- Adresse principale : https://mybestpair.github.io/copilote-tournee/ (GitHub Pages, branche `claude/zealous-turing-4shyoc`, dossier `docs/`) ; elle passe sur le réseau de l'entreprise, contrairement à `workers.dev`.
- Copie de secours : Worker Cloudflare `copilote-tournee` (`build_worker.py`, en-têtes de sécurité complets).
- À chaque mise à jour : régénérer `docs/` avec `build_pwa.py`, pousser, puis redéployer le Worker et la page claude.ai.

## Synchronisation entre appareils (25 nov. 2026)
- Chiffrée de bout en bout : code de jumelage de 20 caractères (≈ 99 bits) créé sur le premier appareil ; HKDF en tire l'adresse de la boîte, le jeton d'accès (le serveur n'en garde que l'empreinte SHA-256) et la clé AES-GCM 256. Données compressées puis chiffrées sur l'appareil.
- Serveur : Worker `copilote-tournee`, route `/api/sync/<id>` (GET / PUT avec numéro de version / DELETE), base D1 `copilote-sync` (table `boxes`), origines autorisées : GitHub Pages et le Worker. Taille maximale ≈ 1,9 Mo.
- Fusion : la dernière modification l'emporte, clé par clé ; si les deux appareils ont modifié la même donnée depuis la dernière synchro (hors réseau), fusion fiche par fiche (tâches, comptes rendus, rendez-vous, visites, remarques, clients, journal, plan du jour). Réglages propres à l'appareil non partagés (délai de verrouillage, carte, mode confidentiel). Photos non synchronisées.
- Déclenchement : à l'ouverture, 3 s après un changement, au retour sur l'application ou du réseau, et chaque minute.
- Limite connue : le réseau de l'entreprise bloque `workers.dev` ; pour le PC du travail, il faudra un nom de domaine (par ex. `sync.mybestpair.fr`) relié au Worker.
