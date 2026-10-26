# Installation locale MAIN — v1.6a(119)

Objectif: conserver la pile existante (Caddy, PHP, Qwen2.5, guardian, worker PROFILE) et l'installation `H:\EZStudioLab_assistant`. Aucun changement des moteurs LAB ni du worker scientifique.

La branche `archive/xps-remote-v1.6a-118` protège l'ancienne version Git. Le répertoire `runtime/` et `.env.local` sont ignorés par Git: archive Git ≠ sauvegarde complète du runtime.

Prérequis: PowerShell 5.1 sur MAIN, Caddy installé et accessible, partage local `EZModels` contenant Qwen2.5, PHP et Python313, vendor Composer, `.env.local` configuré pour `EZSTUDIOLAB_ASSISTANT_TOKEN` et `EZSTUDIOLAB_REVIEW_PRESET_PATH` (chemin UNC vers preset existant), distribution complète et compatible de llama.cpp existante. Aucune nouvelle IA ni téléchargement de modèle.

Commandes administrateur:

```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin main
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1
# Choisir le chemin REEL d'un llama-server.exe deja installe, puis :
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1 -Apply -LlamaServer 'CHEMIN_REEL\llama-server.exe'
# Quand configuration et ressources sont validees :
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-main.ps1 -Apply -Start
```

La commande sans `-Apply` ne modifie rien. `-Apply` prepare une jonction `C:\EZStudioLab_assistant` vers H: pour le chemin absolu du worker, une jonction du modele vers le chemin physique du partage SMB, copie le binaire existant et les DLL presentes dans son dossier et cree un lanceur PROFILE prive dans `runtime/` lorsqu'il manque. Ne remplace pas un lanceur existant. Aucune edition de sources versionnees. La pile ne demarre qu'avec `-Start`.

Limites: le parseur de `.env.local` traite les valeurs literales simples et ne prend pas en charge l'expansion dotenv; les secrets doivent etre valides localement sans impression. Le preset doit etre fourni. Le binaire llama.cpp peut requerir d'autres DLL; l'installateur ne garantit pas un serveur sain. Le contexte 24576 peut saturer RAM/VRAM sur MAIN: ne demarrer qu'avec budget ressources LAB libre. L'operation doit etre verifiee par tests d'integration sur MAIN; aucun fonctionnement reel n'est revendique a la publication.
