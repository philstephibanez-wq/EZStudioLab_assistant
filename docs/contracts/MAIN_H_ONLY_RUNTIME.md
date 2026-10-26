# MAIN H: — v1.6a(121)

Le runtime Assistant est deploye sous `H:\EZStudioLab_assistant`; le worker deduit sa racine de son fichier, sans jonction C:. Caddy partage le binaire canonique `H:\Caddy\caddy.exe` mais dispose de sa configuration/son port d'administration propre (2022). Les modeles restent sur le partage EZModels, sans duplication; une jonction sous runtime/models-cache permet au script de demarrage de les trouver.

L'installateur `scripts/install-main.ps1` est **lecture seule par defaut**. Avec `-Apply`, il utilise l'API des releases officielles ggml-org/llama.cpp pour identifier exactement l'archive Windows x64 CPU, exige un `digest=sha256` publie et controle les octets recus. Il installe l'executable et les DLL voisines sous H:, les ZIP et extractions etant exclusivement sous H:\temp; il cree un lanceur prive PROFILE sous runtime/ uniquement si absent. Aucun appel payant, aucune acquisition GGUF. S'il manque un checksum, refuse l'installation. CPU plutot que GPU pour eviter de reserver la VRAM des analyses LAB. Avant toute ecriture les prerequis, ports et valeurs de configuration privees sont verifies (non affichees). Les scripts ne garantissent ni la validite du token ni la possibilite de charger un contexte 24576 sous la RAM disponible.

Commandes PowerShell sur MAIN :

```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin main
python .\tests\test_main_h_only_121.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1 -Apply
# Puis, seulement apres validation des ressources LAB :
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1 -Apply -Start
```

Validation Windows de syntaxe PowerShell et execution reelle restent a faire sur MAIN. Aucun changement des calculs LAB, des preuves musicales ou des presets. La branche archive/xps-remote-v1.6a-118 demeure intacte.
