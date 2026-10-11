# EZStudioLab_assistant

Nœud assistant distribué d'EZStudioLab.

## Rôle

`EZStudioLab_assistant` exécute les tâches auxiliaires compatibles avec les capacités du nœud, observe la file d’analyse, collecte les éléments de contrôle et participe au gate scientifique avant promotion d’une phase.

Le dépôt ne contient pas les moteurs scientifiques PROFILE / STEMS / CHORDS/N / LYRICS. Le protocole partagé reste dans `EZStudio_lab/python/ezstudio/distributed`.

## V1B — contrôle distribué et gate scientifique

V1B ajoute :
- client HTTP léger de l’API d’analyse ;
- `queue` : observation ponctuelle de la file ;
- `watch` : observation périodique + heartbeat ;
- `evaluate-gate` : évaluation déterministe du gate PROFILE → STEMS ;
- politique fail-closed : aucune donnée absente n’est interprétée comme un succès.

### Sécurité du claim

Le endpoint historique `/jobs/claim` prend le premier job disponible et n’est pas capability-aware/lease-aware. V1B **ne l’expose donc volontairement pas**.

Le claim distant restera désactivé tant que le serveur n’offrira pas :
- claim d’un job précis ;
- identité du worker ;
- exigences matérielles/modèles ;
- lease + heartbeat ;
- récupération après expiration du lease.

Cela empêche un XPS 4 Go de prendre aveuglément un job prévu pour une machine plus puissante.

## Gate PROFILE → STEMS

Le passage à STEMS n’est pas déclenché par la simple fin d’un batch.

Le rapport d’entrée du gate doit contenir au minimum :
- Preset/version ;
- couverture du corpus ;
- erreurs modules obligatoires ;
- fallbacks silencieux ;
- dimensions `tempo_meter`, `key`, `tuning`, `semantics`, `vocals_choirs` ;
- régressions bloquantes et anomalies non résolues ;
- couverture de revue externe ;
- comparaison à la baseline.

Décisions possibles :

```text
BLOCKED
READY_FOR_STEMS
```

Aucune auto-promotion opaque.

## Implantation

```text
C:\EZStudio_lab\
  python\ezstudio\distributed\

C:\EZStudioLab_assistant\
  app\
  config\
  scripts\
  tests\
```

Pour un clone autonome de l’assistant, définir `EZSTUDIOLAB_HOST_REPO` vers le clone d’`EZStudio_lab`.

## Modèles

Le stockage partagé est fourni via `EZSTUDIO_SHARED_MODEL_ROOT`. Le cache local optionnel est fourni via `EZSTUDIOLAB_ASSISTANT_MODEL_CACHE`. Aucun fallback silencieux de modèle n’est autorisé.

## Exemples

Capacités :

```powershell
.\scripts\start-EZStudioLab_assistant.ps1 `
  -Python C:\Users\steph\AppData\Local\Programs\Python\Python313\python.exe `
  -HostRepo C:\EZStudio_lab `
  -SharedModelRoot \\EZSTUDIO-MAIN\EZModels `
  -Mode capabilities
```

Observation de file :

```powershell
.\scripts\start-EZStudioLab_assistant.ps1 `
  -Python C:\Users\steph\AppData\Local\Programs\Python\Python313\python.exe `
  -HostRepo C:\EZStudio_lab `
  -SharedModelRoot \\EZSTUDIO-MAIN\EZModels `
  -Mode queue `
  -BaseUrl http://EZSTUDIO-MAIN:<PORT> `
  -Token <TOKEN>
```

Gate :

```powershell
python app\main.py evaluate-gate C:\temp\profile-gate.json
```

## Contrat

```powershell
python .\tests\test_EZStudioLab_assistant_v1b_control_gate.py
```

Attendu :

```text
EZStudioLab_assistant_V1B_CONTROL_GATE_CONTRACT_OK
PROFILE gate is explicit and fail-closed
Historic unsafe claim endpoint is not exposed by V1B
Scientific pipeline untouched
```
