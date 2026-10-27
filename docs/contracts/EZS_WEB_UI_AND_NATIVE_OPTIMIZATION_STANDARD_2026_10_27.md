# EZS — Standard transversal interfaces web et optimisation native (2026-10-27)

## Décision d'architecture
- Interfaces web de l'écosystème : **Twig + Bootstrap 5 + jQuery** pour une base graphique et des interactions cohérentes. Langue française ; navigation, formulaires, tableaux, états, accessibilité et responsivité standardisés.
- Les pages existantes restent opérationnelles. Migration incrémentale, composants visuels testés, **aucune substitution globale du CSS, JS ou markup sans audit de compatibilité**.
- JavaScript : jQuery est la bibliothèque transversale de référence pour DOM, événements et AJAX. Pas de deuxième couche Stimulus ou framework SPA par défaut. Utiliser les API REST canoniques, pas de chemins parallèles.
- CSS : Bootstrap 5 est le framework graphique standard ; **jQuery n'est pas une bibliothèque CSS**. Les surcharges spécifiques sont limitées, nommées et isolées ; ne pas casser les écrans historiques.
- Versions : versions épinglées et chargées une seule fois par page ; vérifier explicitement les plugins existants avant convergence de versions. Les composants LAB possèdent déjà jQuery 4.0.0/jQuery UI, tandis que l'Assistant possède jQuery 3.7.1 : ne pas effectuer de mise à jour aveugle.
- Dépendances : préférer à terme des fichiers statiques locaux versionnés et vérifiés plutôt qu'une dépendance CDN impérative en production. Tester fonctionnement hors ligne/Caddy, politiques CSP et intégrité de fichiers.
- Sécurité : ne jamais exposer de token technique au JavaScript public. Les API protégées restent protégées côté serveur ; opérations modifiant l'état : contrôles d'autorisation, CSRF adapté et journalisation.
- Optimisations natives : **C** ou bibliothèques natives uniquement après profilage, benchmark et non-régression (fonctionnel/scientifique). Réutiliser des bibliothèques éprouvées avant d'écrire une DLL ; audit FFI et gestion de mémoire si employés.
- Orchestrator V2 : PHP 8.5 / Symfony modulaire, Twig, REST, Messenger et Scheduler selon besoin, Caddy et zéro Python **après bascule vérifiée**. Ne pas ajouter de CLI/worker redondants. Aucun lancement php -S ou tâche Windows.
- LAB conserve Python pour les calculs scientifiques ; l'Assistant reste limité à la contre-expertise des assertions musicales de LAB lors de sa première phase.
- Nettoyage obligatoire : une fois chaque module migré et validé, supprimer dans la **même livraison** les CSS, JS, templates, endpoints, CLI et Python legacy effectivement remplacés. Ne jamais supprimer avant preuve de parité et tests de non-régression.

## Critères de validation pour chaque interface
1. Même langage visuel Bootstrap, navigation accessible, responsive, écrans existants fonctionnels.
2. Une seule version jQuery réellement chargée par page ; aucun conflit avec jQuery UI ou scripts métier.
3. Fetch/AJAX vers API authentifiée sans fuite de secret, erreurs et délais gérés.
4. Tests DEV puis bascule contrôlée ; aucune modification des moteurs scientifiques.
5. Contrôle de nettoyage et hygiène Git : pas de fichiers temporaires ni doublons conservés.
