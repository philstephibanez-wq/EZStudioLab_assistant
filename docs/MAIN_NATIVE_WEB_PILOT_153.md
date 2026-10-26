# MAIN — pilote Web Symfony natif Windows 1.6a(153)

**But** : vérifier que l'Assistant Web et la sonde NVIDIA historique fonctionnent nativement sur EZSTUDIO-MAIN, en parallèle de Docker. Il ne s'agit **pas** d'une bascule de production, et aucun service n'est supprimé.

## Architecture
- Web Docker smoke actuel : `http://127.0.0.1:18713` (repli conservé)
- Qwen CUDA Docker : `http://127.0.0.1:18720` (inchangé)
- Pilote Symfony Windows natif : `http://127.0.0.1:18813` (nouveau, loopback uniquement)
- GPU : ancien contrôleur Symfony basé sur `nvidia-smi`, inchangé
- Aucun Caddy, aucune réaffectation de 8712/8713, aucun dispatch vers LAB.

## Recette PowerShell 5.1 (sur MAIN)

```powershell
cd H:\EZStudioLab_assistant
git status --short
git pull --ff-only origin assistant-main
Get-Content .\VERSION
python -m unittest discover -s tests -p test_main_native_contract.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\main-native-web.ps1 -Action Preflight
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\main-native-web.ps1 -Action Start
Invoke-WebRequest http://127.0.0.1:18813/backoffice -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:18813/assistant/gpu/telemetry -UseBasicParsing
```

Les scripts échouent si PHP, les dépendances Composer ou le port libre manquent : **ne pas contourner le préflight**. Les journaux applicatifs temporaires se trouvent sous `H:\temp\EZSTUDIO_ASSISTANT_NATIVE_MAIN`. Si le pilote est concluant, envisager ensuite une configuration supervisée séparée, en maintenant rollback Docker.

Stop ciblé du pilote :
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\main-native-web.ps1 -Action Stop
```

Ne pas relancer automatiquement les jobs #181/#182/#185, ne pas migrer l'Orchestrator et ne pas toucher à CUDA. Les 2 tests statiques ne prouvent pas la recette Windows.
