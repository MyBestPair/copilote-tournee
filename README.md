# Copilote de tournée

Outil pour commerciaux itinérants : tournées organisées, imprévus gérés, comptes rendus, agenda. Version de test.

- **Utiliser l'application** : la page publiée par GitHub Pages (dossier `docs/`). Sur téléphone, « Ajouter à l'écran d'accueil ».
- **Données** : tout reste sur l'appareil de chaque utilisateur (aucun serveur, aucune base de données). Code de verrouillage avec chiffrement, sauvegardes chiffrées, mode confidentiel.
- **Ce dépôt ne contient jamais de données de clients.** Les fichiers de `exemples/` sont fictifs.

## Organisation
| Élément | Où |
|---|---|
| Site publié (généré) | `docs/` |
| Source de la page | `source/copilote-tournee.html` |
| Fabrication du site | `python3 source/tools/build_pwa.py source/copilote-tournee.html docs docs/communes-fr.json` |
| Notes techniques | `source/LISEZMOI.md` |
| Fichiers de test fictifs | `exemples/` |
