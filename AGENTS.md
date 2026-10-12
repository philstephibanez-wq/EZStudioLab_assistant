# AGENTS.md

## ⛔ RÈGLE ABSOLUE — FICHIERS TEMPORAIRES

- Aucun fichier temporaire, test ponctuel, installateur ponctuel, script apply/migrate/preflight/hotfix/rollback, backup, ZIP de livraison, log, dump, cache, export de diagnostic, artefact généré ou fichier intermédiaire ne doit être créé dans ce dépôt.
- Tous ces fichiers doivent être créés sous `H:\temp`.
- `H:\temp` est jetable et peut être purgé sans préavis.
- Le produit ne doit jamais dépendre d'un fichier présent dans `H:\temp`.
- Avant tout staging/commit : vérifier `git status --short`.
- Ne pas utiliser `git add .` ou `git add -A` tant que des fichiers non vérifiés sont présents.

Voir aussi `REPOSITORY_HYGIENE.md`.


## VERSIONING TRANSVERSAL — OBLIGATOIRE

Le dépôt utilise un fichier canonique `VERSION`.

Format :
- release : `MAJOR.MINOR.PATCH` (ex. `1.5.0`)
- fix : suffixe lettre minuscule ajouté à la release courante (ex. `1.5.0a`, `1.5.0b`, ..., puis `aa`, `ab` si nécessaire)
- nouvelle release : incrément d'une composante numérique selon la portée et suppression du suffixe
- rupture majeure : incrément explicite de `MAJOR`

Règles :
1. chaque push doit obligatoirement modifier `VERSION` ;
2. chaque push doit être classé `release` ou `fix` ;
3. le hash Git n'est jamais la version produit : il est affiché séparément comme `Révision` ;
4. les interfaces et logs doivent distinguer `Version` et `Révision` ;
5. pour EZS_orchestrator, la version DEV est canonique ; la PROD reprend cette version lors du déploiement.
