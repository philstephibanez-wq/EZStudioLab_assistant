# Assistant MAIN 1.6a(155) — lancement manuel Windows, Symfony + Caddy

Le LAB lance Symfony avec un frontal Caddy via son orchestrateur. Pour cette phase **sans Orchestrator**, le pilote Assistant reprend Symfony + Caddy natifs, et conserve la sonde GPU LAB (contrôleur déjà identique à celui du LAB sauf sa route). Aucun service Docker requis pour le Web. L'endpoint d'inférence Qwen devra être migré séparément, avant toute recette PROFILE.

**Ports de recette** : Symfony `127.0.0.1:18813` et Caddy `127.0.0.1:18812`. Ports XPS 8712/8713 intacts. Le pilote reste local à MAIN, sans exposition réseau ni modification de l'Orchestrator.

```powershell
cd H:\EZStudioLab_assistant
git status --short
git pull --ff-only origin assistant-main
Get-Content .\VERSION
python -m unittest discover -s tests -p "test_main_native*.py" -v
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\main-native-caddy.ps1 -Action Preflight
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\main-native-caddy.ps1 -Action Start
curl.exe --noproxy "*" --max-time 20 -sS -w "`nHTTP=%{http_code}`n" http://127.0.0.1:18812/assistant/gpu/telemetry
curl.exe --noproxy "*" --max-time 20 -sS -o NUL -w "HTTP=%{http_code}`n" http://127.0.0.1:18812/backoffice
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\main-native-caddy.ps1 -Action Status
```

Arrêt ciblé du pilote uniquement :
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\main-native-caddy.ps1 -Action Stop
```

**Restrictions** : pas de jobs #181/#182/#185 ; ne pas modifier LAB ni XPS ; ne pas déclarer Qwen natif prêt sans validation du binaire Windows. Aucun automatisme de démarrage ni bascule réseau. Logs dans `H:\temp\EZSTUDIO_ASSISTANT_NATIVE_MAIN`.
