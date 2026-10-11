# EZStudioLab_assistant

Nœud assistant distribué d'EZStudioLab.

## Rôle

`EZStudioLab_assistant` exécute les tâches compatibles avec les capacités du nœud, résout les modèles depuis le stockage partagé et applique le protocole distribué défini par `EZStudio_lab`.

Le dépôt ne contient pas les moteurs scientifiques PROFILE / STEMS / CHORDS/N / LYRICS. Le protocole partagé reste dans le dépôt hôte sous `python/ezstudio/distributed`.

## Implantation recommandée

```text
H:\EZStudio_lab\
  python\ezstudio\distributed\
  EZStudioLab_assistant\   <- submodule Git
```

Pour un clone autonome de l'assistant, définir `EZSTUDIOLAB_HOST_REPO` vers le clone d'`EZStudio_lab` qui fournit le protocole partagé.

## Modèles

Le stockage partagé est fourni via `EZSTUDIO_SHARED_MODEL_ROOT`. Le cache local optionnel est fourni via `EZSTUDIOLAB_ASSISTANT_MODEL_CACHE`. Aucun fallback silencieux de modèle n'est autorisé.

## Lancement

```powershell
.\scripts\start-EZStudioLab_assistant.ps1 `
  -Python H:\Python\pythoncore-3.14-64\python.exe `
  -SharedModelRoot \\EZSTUDIO-MAIN\EZModels
```

## Contrat

Depuis la racine du dépôt assistant, lorsque le dépôt est imbriqué dans `EZStudio_lab` :

```powershell
H:\Python\pythoncore-3.14-64\python.exe .\tests\test_EZStudioLab_assistant_v1a1.py
```

Attendu :

```text
EZStudioLab_assistant_SUBMODULE_V1A_CONTRACT_OK
Single root README enforced
Shared protocol remains owned by EZStudio_lab
Scientific pipeline untouched
```
