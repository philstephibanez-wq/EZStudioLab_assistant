## CONTRAT FONDAMENTAL ET INVIOLABLE — MISSION DE L'ASSISTANT

**L'ASSISTANT N'EXPERTISE PAS LAB. IL EXPERTISE UNIQUEMENT LES ITEMS MUSICAUX PRODUITS PAR LAB.**

- Son entrée métier est : identité de la chanson et de l'enregistrement (titre, interprète, version si connue), puis **toutes les assertions musicales finales réellement émises par LAB**, dynamiques et individuelles (instruments compris), jamais une liste fixe de dix items.
- Il découvre par recherche Web ouverte les ressources publiques, scanne chacune pour tous les items, en calcule les ensembles et intersections, puis affine les recherches ; il vérifie l'enregistrement concerné avant tout verdict ; une œuvre originale, une reprise ou une partition arrangée ne prouve pas les caractéristiques d'une autre version.
- Il extrait et recoupe les faits musicaux ; HTML d'abord, OCR pour le texte en image, OMR pour la notation si nécessaire. Il fournit une référence vérifiable, une justification et un niveau de confiance.
- Il juge **chaque item** : BON, FAUX ou NON TROUVÉ lorsque la preuve est insuffisante ; distinguer séparément l'erreur technique. Ne jamais inventer de valeur ni interpréter l'absence de source comme une réfutation.
- Il persiste ses conclusions documentaires pour réutilisation ultérieure, avec identité de l'enregistrement et sources ; aucun résultat n'est présenté comme confirmé si l'identité est incertaine.
- **HORS PÉRIMÈTRE** : expertiser, auditer, diagnostiquer ou expliquer les moteurs, réseaux neuronaux, modules, algorithmes, presets ou versions scientifiques de LAB. L'Assistant n'a pas à connaître comment LAB calcule les valeurs. Ne pas demander de télémétrie scientifique pour décider d'un item musical.
- Le titre peut changer à chaque run : ne jamais figer la mission sur une chanson ou un artiste cités dans le chat. Travailler sur les items réellement reçus pour la chanson courante.
- L'intégration avec LAB est limitée à la transmission des items et au retour des conclusions ; elle n'autorise aucune modification des moteurs scientifiques.

**Toute proposition ou implémentation qui confond contre-expertise des items et expertise du fonctionnement de LAB est hors contrat et doit être rejetée avant publication.**

# AGENTS.md

## SOURCE DE VÉRITÉ GITHUB — PRÉFLIGHT OBLIGATOIRE

- GitHub est la source de contexte persistante, **avant** toute réponse opérationnelle ou modification : consulter les dépôts concernés, `AGENTS.md`, contrats, README, issues/handoffs, décisions, historique Git et changements récents. Ne jamais remplacer une vérification possible par une supposition ou par le souvenir d'un ancien chat.
- Consulter également le dépôt privé `philstephibanez-wq/EZStudio_Run_Reports` pour les rapports existants. Les rapports sont des copies expurgées ; la base MAIN reste autorité pour les résultats métier. Ne jamais prétendre disposer d'un log non publié ni d'une observation temps réel.
- L'accès GitHub direct à l'assistant est autorisé dans ce chantier lorsqu'il est demandé par le mainteneur. Les handoffs plus anciens qui interdisaient une écriture directe sont historiques ; signaler les contradictions et préférer les consignes explicites actuelles du mainteneur sans effacer l'historique.
- Pour chaque chantier, mettre à jour l'issue/handoff concerné : état prouvé, versions et SHA, décisions, limites, risques, tests **exécutés** versus à exécuter, action suivante et conditions de reprise. Ne jamais présenter un test ajouté mais non exécuté comme validé.
- Pour les machines MAIN/XPS, ne demander une commande locale que lorsque les données nécessaires ne sont réellement pas accessibles par GitHub ou les rapports existants. Ne publier aucun secret, jeton, trace HTTP brute, audio ou donnée privée.
- Avant publication, contrôler l'intégralité des contrats applicables et les écarts avec les handoffs ; toute non-conformité est bloquante, pas une remarque facultative.

## PRÉFIXE DE COMMIT ET CONFORMITÉ DE LIVRAISON — OBLIGATOIRE

- Tous les commits, y compris les modifications documentaires et les correctifs, doivent comporter en tête `[vVERSION]`, où `VERSION` correspond exactement à la valeur du fichier canonique dans le même commit. Aucun commit non versionné.
- Corps de message multiligne : `Contexte`, `Modifications`, `Validation`, `Impact`, et `Limites / risques` si nécessaire.
- Chaque commit livré incrémente `VERSION`, même pour les modifications documentaires, tests ou refactorisations ; la validation effectuée et les limites sont indiquées sans exagération.
- Avant toute publication : confirmer fichiers concernés, absence de fichiers temporaires, version, préfixe, messages, vérifications statiques et tests pertinents. Aucun historique partagé n'est réécrit de force.
- Un test CI qui échoue ne bloque pas à lui seul un push direct tant qu'une protection de branche n'impose pas le statut. Ne jamais annoncer un blocage effectif avant sa configuration et sa vérification.

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


### Cycle de release avec compteur de correctifs — décision du mainteneur (23 octobre 2026)

Cette précision prime sur les exemples anciens de suffixes successifs et sur la clause contradictoire qui interdisait de mettre à jour VERSION pour un correctif intermédiaire.

- Ouverture d'une release : `vN.Na(0)` (exemple `v1.7a(0)`).
- Chaque correctif publié : même identifiant de release, compteur incrémenté `vN.Na(1)`, `vN.Na(2)`, etc. Aucun push fonctionnel ne conserve le même numéro.
- Après validation effective de stabilité : suppression du compteur, `vN.Na` (exemple `v1.7a`). Ne pas annoncer la stabilité sans tests et acceptation.
- Release suivante : nouvelle composante mineure et compteur remis à zéro, `vN.N(0)` (exemple `v1.8(0)`), puis `vN.N(1)`, etc. Stabilisation : `vN.N`.
- Le fichier `VERSION` est la source de vérité ; les interfaces affichent version et SHA Git séparément. Le préfixe du message `[vVERSION]` n'altère pas le nom de la version dans le fichier.
- Historique : conserver les anciens commits et leurs SHA, ne jamais réécrire rétroactivement des versions qui n'existaient pas.
- En cas de conflit avec les anciennes clauses, appliquer ce cycle explicite tout en conservant les exigences de tests, de messages descriptifs et de handoff.

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


## CONTRAT DES MESSAGES DE COMMIT — OBLIGATOIRE

Chaque commit publié doit être intelligible sans ouvrir le diff. Rédiger **en français**, avec :

- Format obligatoire du titre : `[vVERSION] type(périmètre): résultat concret`, avec la version identique à `VERSION` dans le même commit ; par exemple `[v1.4a(18)] fix(profile): écarter les comparaisons documentaires invalides`.
- Un **corps de message multiligne** expliquant `Contexte`, `Modifications`, `Validation`, `Impact` et, si nécessaire, `Limites / risques`.
- Dans `Validation`, distinguer explicitement les tests exécutés des tests seulement ajoutés ou non exécutés. Ne jamais affirmer une réussite non constatée.
- Dans `Impact`, indiquer les dépôts ou composants touchés, les éventuels redémarrages/déploiements, et si les modèles, presets scientifiques, données et interfaces sont inchangés.
- Ne pas masquer plusieurs changements fonctionnels indépendants sous un intitulé générique (`fix`, `update`, `VERSION`, `cleanup`).
- **Un commit de livraison cohérent par version**, réunissant code durable, tests et `VERSION`, autant que les outils de publication le permettent. Les commits intermédiaires éventuels doivent eux aussi être descriptifs. Aucun réécriture forcée de l'historique déjà publié.
- Si une contrainte du dépôt exige de modifier `VERSION`, la respecter, y compris pour les livraisons documentaires.

Cette règle s'applique aux contributions humaines, assistants et automatisations sur tous les dépôts du projet.
