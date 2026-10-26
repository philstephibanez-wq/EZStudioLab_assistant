# MAIN local preset — v1.6a(122)

Le preset de révision Assistant existant est sous `H:\EZStudio_lab\presets\assistant\profile-baseline-1.json`. Sa lecture locale est autorisée *exclusivement* pour ce chemin canonique sur Windows ; les autres chemins locaux restent refusés. La validation du schéma, les bornes, le contrôle UTF-8 et les contrats de preuve restent inchangés. Sur l'ancienne installation distante, l'UNC explicite reste autorisé.

Sur MAIN, `scripts/install-main.ps1` choisit ce chemin local par défaut seulement si aucune valeur `EZSTUDIOLAB_REVIEW_PRESET_PATH` n'est définie dans `.env.local`. Toute valeur explicite existante reste prioritaire, avec contrôle d'existence. Le lanceur privé du worker applique le même défaut si nécessaire. Aucun changement du contenu du preset, des comptes SMB ou des ACL. Aucun token affiché.

Validation : tests à exécuter sur MAIN, y compris parse PowerShell, test statique et chargement du preset ; aucun démarrage ni inférence réelle revendiqué.

```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin main
python .\tests\test_main_local_preset_122.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1 -Apply
```
