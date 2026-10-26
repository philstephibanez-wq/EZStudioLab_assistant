# Accueil canonique Assistant MAIN — v1.6a(135)

L'interface MAIN est accessible directement à `http://127.0.0.1:18713/`. `/backoffice` reste un alias, et l'écran historique XPS non raccordé est conservé à `/historique` pour consultation seulement. Aucun ancien endpoint XPS n'est sollicité par l'accueil MAIN.

Recette MAIN : pull assistant-main ; reconstruire/recréer **seulement le Web** via compose smoke, garder Qwen CUDA actif ; contrôler `/`, `/backoffice`, `/historique` et `/api/backoffice/inference`. Aucun changement des analyses LAB, Orchestrator, PROD ou modèles.
