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
- release : `MAJOR.MINOR` (ex. `1.5`)
- fix : suffixe lettre minuscule ajouté à la release courante (ex. `1.5a`, `1.5b`, ..., puis `aa`, `ab` si nécessaire)
- nouvelle release : incrément d'une composante numérique selon la portée et suppression du suffixe
- rupture majeure : incrément explicite de `MAJOR`

Règles :
1. chaque push doit obligatoirement modifier `VERSION` ;
2. chaque push doit être classé `release` ou `fix` ;
3. le hash Git n'est jamais la version produit : il est affiché séparément comme `Révision` ;
4. les interfaces et logs doivent distinguer `Version` et `Révision` ;
5. pour EZS_orchestrator, la version DEV est canonique ; la PROD reprend cette version lors du déploiement.

## CONTRAT TRANSVERSAL — UTF-8 ET LISIBILITÉ DES SOURCES

**Obligatoire dans tous les correctifs, scripts d'installation et livraisons.**

- PHP, Twig, Python, JavaScript, CSS, JSON, YAML, Markdown et scripts applicatifs : **UTF-8 sans BOM**. Ne jamais altérer la sémantique d'un fichier lors d'une conversion.
- Respecter le charset UTF-8 sur toute la chaîne : réponse HTTP (`Content-Type`), balise HTML `<meta charset="utf-8">`, sérialisation JSON, stockage et rendu navigateur. Vérifier les caractères accentués **dans l'interface rendue**, pas seulement dans le code source.
- Rejeter les chaînes corrompues (*mojibake*) comme `RÃ©vision`, `Ã©`, `Ã¨`, `â€™`, `Â` en contexte français ; rechercher la cause d'encodage, ne pas appliquer de substitutions aveugles.
- Les templates **Twig doivent rester multilignes, lisibles et structurés** : indentation de 4 espaces par niveau, `{% if %}`, `{% for %}`, `{% block %}`, `{% endif %}` et `{% endfor %}` isolés par ligne, éléments HTML structurels sur des lignes séparées, attributs répartis sur plusieurs lignes si nécessaire.
- Les scripts JS/CSS sources ne sont pas minifiés dans le dépôt ; les artefacts compilés restent distincts. Ne pas reformater massivement les fichiers historiques sans demande explicite ni tests de non-régression.
- Conserver les fins de ligne conformément à `.gitattributes` ; **CRLF/LF n'est pas un diagnostic d'UTF-8**.
- Avant validation : décodage UTF-8 strict sans BOM, contrôle de mojibake, `php -l`, `lint:twig` et tests contractuels pertinents, puis vérification visuelle des libellés français. Aucun simple lint de syntaxe ne vaut validation d'encodage ou de présentation.
- Ce contrat s'applique à tous les dépôts EZScore, EZStudio_lab, EZStudioLab_assistant et EZS_orchestrator, y compris aux contributions des assistants et automatisations.
