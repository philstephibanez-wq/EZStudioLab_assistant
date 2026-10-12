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
- `release` : `MAJOR.MINOR.PATCH`.
- `fix` : suffixe lettre minuscule sur la release courante (`1.5.0a`, `1.5.0b`, ...).
- Le SHA Git est une révision technique séparée et ne remplace jamais la version humaine.
- Un commit destiné au push qui ne met pas à jour `VERSION` est non conforme.
