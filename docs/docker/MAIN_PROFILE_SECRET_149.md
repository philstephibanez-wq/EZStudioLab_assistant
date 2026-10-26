# MAIN PROFILE — étape 1.6a(149)

La révision installe Python 3 dans le Web Docker et sélectionne un lecteur de secret portable.
Sur Windows XPS, le lecteur DPAPI historique est conservé.
Sur Linux MAIN, seul `EZSTUDIOLAB_ASSISTANT_TOKEN_FILE` pointant vers un fichier secret absolu non modifiable par groupe/autres est accepté. Aucun jeton brut en variable d'environnement. Absence de secret : refus d'authentification.

Le Compose actuel reste un **smoke sans secret**, volontairement non habilité au workflow métier. Ne pas ajouter de jeton dans compose.yaml, Dockerfile, Git ou logs. Préparer séparément le montage lecture seule du secret dans un runtime dédié après validation et approbation.

## Contrôles MAIN (sans activation des jobs)

```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin assistant-main
python -m unittest discover -s tests -p "test_main_docker_secret.py" -v
python -m unittest discover -s tests -p "test_profile_verify_push.py" -v
$env:EZS_MAIN_GPU_TELEMETRY_DIR='H:/temp/EZSTUDIO_ASSISTANT_GPU'
docker compose -f docker/main/compose.yaml --profile smoke config --quiet
```

Ne pas reconstruire/redémarrer les conteneurs sur la base de ces seuls tests ; ces commandes ne vérifient pas les endpoints réels. Prochain jalon distinct : Compose cible avec secret Docker non public, test HTTP 401 et test authentifié sans divulgation de jeton, test de retour/persistance LAB et idempotence. Jobs #181, #182 et #185 préservés ; Orchestrator non modifié.

Limites : pas de recette MAIN, pas de preuve musicale indépendante validée, Qwen CUDA pas encore raccordé au flux du Web (loopback propre à chaque conteneur).
