# EZStudioLab Assistant — MAIN

L'Assistant opérationnel réside sur **MAIN**, sous `H:\EZStudioLab_assistant`.
La branche de référence pour MAIN est `assistant-main` ; la branche GitHub
`main` historique n'est pas la source de déploiement.

## Exploitation
- Interface locale documentée : `http://127.0.0.1:18713/` ; vérifier sa disponibilité sur MAIN.
- Contrôle explicite de l'inférence IA locale : `scripts/assistant-lifecycle.ps1` avec
  `Preflight`, `Status`, `Start` ou `Stop`. Ce script ne démarre pas toute l'interface Web.
- Les résultats métier sont échangés avec `EZStudio_lab` ; LAB reste propriétaire de leur persistance.
- Les modèles et caches sont administrés sur MAIN suivant les contrats d'exploitation.

Les anciens lanceurs `scripts/start.cmd`, `scripts/start.ps1`,
`scripts/stop.cmd` et `scripts/stop.ps1` **ne doivent pas être recréés**.
Ne démarrer ou arrêter aucun service dans une recette documentaire.

Avant toute modification, lire `AGENTS.md`, `CONTRAT DE DÉVELOPPEMENT.md`
et `docs/assistant/BRANCH_AUTHORITY_166.md`. Les anciennes notes de release
sont des archives historiques et ne sont plus des procédures opérationnelles.
