# MAIN — restauration de la télémétrie GPU de l'Assistant

Version : `1.6a(148)`. Branche : `assistant-main`.

Le Web Docker smoke ne possède pas `nvidia-smi`, donc l'ancien endpoint `/assistant/gpu/telemetry` répondait HTTP 503. Cette livraison **ne change pas** le runtime IA et **ne traite pas** la file LAB.

Architecture : exporteur Python standard library sur l'hôte MAIN → JSON atomique sous `H:\temp\EZSTUDIO_ASSISTANT_GPU\telemetry.json` → bind-mount **lecture seule** vers `/run/ezstudio-gpu` dans le conteneur Web → endpoint Symfony qui refuse les données absentes, malformées ou vieilles de plus de 12 s.

## Activation contrôlée (sur MAIN)

1. `git pull --ff-only origin assistant-main`.
2. Création du dossier éphémère `H:\temp\EZSTUDIO_ASSISTANT_GPU`. Il peut être purgé : il ne s'agit ni d'une base de données ni de données métier.
3. Diagnostic ponctuel : `python scripts/main_gpu_telemetry.py --output H:/temp/EZSTUDIO_ASSISTANT_GPU/telemetry.json --once`. Vérifier que le JSON porte `available: true`, sans publier le contenu privé des métriques.
4. Lancer l'exporteur périodique par un **mécanisme Windows persistant explicitement autorisé** (la commande sans `--once` s'exécute en boucle jusqu'à son arrêt). Aucun processus ou tâche n'est installé automatiquement par Git.
5. Définir `EZS_MAIN_GPU_TELEMETRY_DIR=H:/temp/EZSTUDIO_ASSISTANT_GPU` pour Compose. Avant une recréation ciblée du seul Web, contrôler les modifications locales et les instances actives ; ne pas utiliser `docker compose down` sur les autres services.
6. Après activation, contrôler `GET http://127.0.0.1:18713/assistant/gpu/telemetry` : HTTP 200 + `available:true` et mesures réelles ; vérifier le passage à HTTP 503 quand le collecteur ne publie plus (anti-métriques périmées). Contrôler la version affichée séparément : les images ne se reconstruisent pas au seul `git pull`.

## Contrats et limites

- Web sans GPU, sans `nvidia-smi`, sans accès au modèle et sans jeton d'analyse.
- Pas d'ouverture de nouveau port HTTP hôte ; aucune transmission de secrets dans le JSON.
- Aucun changement d'Orchestrator, de LAB ni des jobs #181/#182/#185.
- Tests contractuels statiques : `python -m unittest discover -s tests -p test_main_gpu_telemetry_contract.py -v`. **Aucune recette Docker/MAIN n'est revendiquée avant son exécution.**
- Sur Windows, si `nvidia-smi` manque au PATH de l'utilisateur exécutant l'exporteur, la sortie sera indisponible jusqu'à correction de ce chemin ; aucune valeur inventée.

## Handoff

La correction Web ne résout pas l'authentification du vérificateur ni le dispatch musical. Reprendre séparément l'issue Assistant #12 et l'issue Orchestrator #15 sans réclamer les jobs tant que l'API métier n'est pas validée.
