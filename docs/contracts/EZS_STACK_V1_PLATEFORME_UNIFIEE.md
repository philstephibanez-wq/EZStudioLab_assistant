# EZS Stack V1 — Plateforme unifiée (MAIN)

## Périmètre
EZS_orchestrator, EZStudio_lab et EZStudioLab_assistant uniquement, sur MAIN. EZScore est différé. Aucune autre machine ne participe à la cible.

## Responsabilités
- Orchestrator : autorité unique de planification, de réservation CPU/GPU, de retry et de suivi technique. Symfony Messenger véhicule des références et notifications asynchrones, pas une seconde réservation.
- LAB : propriétaires des jobs, phases PROFILE/STEMS/CHORDS-N/LYRICS, presets, calculs scientifiques, workers et résultats.
- Assistant : contre-expertise **uniquement des assertions musicales finales de LAB** ; vérifier identité de l'enregistrement, preuves publiques, verdicts BON/FAUX/NON TROUVÉ. Ne jamais expertiser les moteurs ou presets LAB.

## Standard
- Cible PHP 8.5, Symfony 7.4, Twig, Console/Process, REST/JSON versionné, Monolog et Symfony Messenger.
- Python conservé pour les moteurs scientifiques et l'IA, modèles installés sur MAIN. Aucun fallback silencieux.
- Chaque dépôt PHP : PHPUnit 13 si compatible, composer test, configuration PHPUnit, tests unitaires/intégration et non-régression ; pytest pour les composants Python. Toute modification Composer doit mettre à jour le composer.lock reproductible.
- Une version incrémentée par livraison, un commit cohérent avec préfixe [vVERSION], description française et preuves d'exécution. Préflight GitHub et MAIN avant remplacement, UTF-8 sans BOM, git diff --check, aucun temporaire dans le dépôt ; H:\temp réservé aux sauvegardes et interventions ponctuelles.
- Les tests non exécutés ne valent pas validation. Vérifier PHP lint, composer validate, Symfony lint:container, PHPUnit ciblé/complet, pytest pertinent et recette réelle avant activation.

## Flux de queue cible
1. Soumission et accusé de réception sans blocage.
2. Orchestrator réserve la ressource, Messenger transmet l'autorisation idempotente.
3. Le service conserve son worker, sa progression et ses résultats.
4. Succès/échec notifié ; ordonnanceur poursuit les jobs éligibles.
5. Trois tentatives métier au maximum ; distinguer redélivrance technique Messenger et exécution réelle.
6. Silence du worker ou expiration du lease n'est jamais preuve d'arrêt GPU. Ne pas réattribuer une ressource encore occupée ou non vérifiée.
7. Déploiement progressif, sans double autorité de claim : démontrer la parité avec les queues historiques avant bascule.

## Ordre des lots
A. PHPUnit, dépendances et composer.lock de LAB et Assistant, tests MAIN.
B. Messenger durable et recette synthétique dans Orchestrator.
C. Adaptation de LAB sans changement scientifique.
D. Adaptation de l'Assistant sans modification de sa mission.
E. Tests transversaux : panne, notification, progression, retries et non-régression.

## État
Contrat d'architecture uniquement : aucun code, worker, transport Messenger ou nouveau processus activé par ce document. Les tests MAIN restent à réaliser lors de la livraison technique distincte.
