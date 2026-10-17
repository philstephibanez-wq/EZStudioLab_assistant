# ⛔ HYGIÈNE DU DÉPÔT — RÈGLE OBLIGATOIRE

Le dépôt doit contenir uniquement des fichiers durables et nécessaires au produit.

Tous les éléments temporaires ou liés à une intervention ponctuelle doivent être créés hors du dépôt sous `H:\temp`.

`H:\temp` peut être purgé régulièrement et sans préavis. Le produit ne doit donc jamais en dépendre.

Avant tout commit/push :
- vérifier `git status --short` ;
- exclure backups, ZIP, logs, dumps, caches, exports et scripts ponctuels ;
- faire un staging ciblé ;
- ne jamais ajouter un fichier temporaire « pour garder une trace ».


## VERSIONING DES LIVRAISONS

Le fichier `VERSION` fait partie des composants durables du produit et doit être versionné intentionnellement.

- Toute livraison poussée doit incrémenter `VERSION`.
- `release` : `MAJOR.MINOR`.
- `fix` : suffixe lettre minuscule sur la release courante (`1.5a`, `1.5b`, ...).
- Le SHA Git est une révision technique séparée et ne remplace jamais la version humaine.
- Un commit destiné au push qui ne met pas à jour `VERSION` est non conforme.

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
