# Inférence CUDA expérimentale MAIN — v1.6a(128)

**Portée** : conteneur indépendant `llama.cpp` CUDA 12, service explicite `cuda-smoke`, écoute loopback `127.0.0.1:18720`. Aucun rattachement à l'Assistant métier, à LAB, au Web 18713, à Caddy ou à l'Orchestrator. La branche `main` (XPS) est protégée ; seule `assistant-main` évolue.

La RTX 2060 a été visible depuis un conteneur NVIDIA CUDA sur MAIN (`nvidia-smi`, 6144 MiB). Cela ne démontre pas la réussite d'une inférence `llama.cpp`. Le modèle existe déjà sur MAIN et doit être choisi explicitement : **aucun téléchargement automatique, aucune copie dans une image, aucun repli silencieux**.

## Préparation sans modifier les services

Dans PowerShell sur MAIN, depuis `H:\EZStudioLab_assistant` :

```powershell
# Exemple à adapter à un dossier déjà existant : ne pas créer de modèle ni choisir un GGUF au hasard.
$env:EZS_ASSISTANT_MODEL_DIR = "H:\CHEMIN_REEL_DU_REPERTOIRE_GGUF"
$env:EZS_ASSISTANT_MODEL_FILE = "NOM_REEL_DU_FICHIER.gguf"
Test-Path (Join-Path $env:EZS_ASSISTANT_MODEL_DIR $env:EZS_ASSISTANT_MODEL_FILE)
Get-NetTCPConnection -State Listen -LocalPort 18720 -ErrorAction SilentlyContinue
docker compose -f docker/main/compose.cuda.yaml --profile cuda-smoke config
```

**Arrêter si le chemin n'existe pas, si le port 18720 est pris, ou si une analyse GPU active ne peut pas être exclue.** Le compose utilise une image officielle `ghcr.io/ggml-org/llama.cpp:server-cuda`, un montage lecture seule du dossier maître MAIN et le périphérique NVIDIA. Le profil isolé doit être explicitement activé. L'image CUDA peut être téléchargée lors du premier `up`.

## Exécution volontaire

```powershell
docker compose -f docker/main/compose.cuda.yaml --profile cuda-smoke up -d llama-cuda-smoke
docker compose -f docker/main/compose.cuda.yaml --profile cuda-smoke ps
docker compose -f docker/main/compose.cuda.yaml --profile cuda-smoke logs --tail 80 llama-cuda-smoke
Invoke-RestMethod http://127.0.0.1:18720/health -TimeoutSec 10
```

Une réponse `loading model` peut précéder `ok` ; un simple conteneur `Up` n'est pas une preuve d'inférence. Après disponibilité, tester une requête OpenAI-compatible avec le modèle connu en contrôlant le retour et la VRAM, **uniquement quand MAIN est idle**. Préserver les traces dans les rapports privés, sans prompt ni contenu protégé dans GitHub.

Arrêt ciblé :

```powershell
docker compose -f docker/main/compose.cuda.yaml --profile cuda-smoke down
```

## Risques et décisions reportées

- CUDA utilise le GPU partagé MAIN ; limiter la simultanéité avec LAB / EZScore. Aucun contrôleur de quota ni verrou de GPU n'est intégré dans cette tranche.
- `--n-gpu-layers 20` et contexte 2048 sont des réglages prudents mais non garantis pour tout GGUF sur RTX 2060 6 Go ; adapter uniquement après mesure.
- Secrets, presets scientifiques, caches et modèles sont exclus de l'image ; accès aux modèles uniquement via bind en lecture seule.
- API non authentifiée sur loopback pour smoke-test uniquement, **jamais exposer au LAN/Internet**.
- Aucune validation réelle `llama.cpp` CUDA sur MAIN n'a encore eu lieu.
