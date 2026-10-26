# Correctif v1.6a(124) — réparation syntaxique MAIN

L'installateur v123 publié sur `assistant-main` contient un bloc de sélection de release tronqué et le reste de l'installateur dupliqué ; PowerShell refuse de parser le fichier entier et aucune commande n'est exécutée. Ce correctif remplace le bloc malformé par une expression régulière complète, referme `Where-Object` et `foreach`, retire le second exemplaire du corps et conserve la vérification SHA-256 obligatoire.

Aucun changement de comportement du worker, preset, LAB, Caddy ou modèle. Le mode préflight reste sans modification, `-Apply` reste explicite. **Le parseur PowerShell 5.1 doit être exécuté sur MAIN avant toute installation.**

```powershell
cd H:\EZStudioLab_assistant
git fetch origin
git switch assistant-main
git pull --ff-only origin assistant-main
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\test_main_install_parser_124.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1 -Apply
```

Si un contrôle échoue, aucun démarrage. L'état opérationnel MAIN n'est pas établi par la seule réussite du parsing.
