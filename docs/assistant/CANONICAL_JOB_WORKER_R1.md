# Consommateur canonique v1.6a(140)

Le composant `runtime.canonical_job_worker` réalise un parcours **à la demande** de la file LAB, sans sous-file: contexte `job_id` → claim `run_id` → tentative de recherche → finish `run_id`.

**Sécurité et vérité métier:** le mode normal `preflight` ne modifie pas le job. `--execute` le réclame puis le clôt en **error**, car le moteur documentaire actuel ne sait pas établir ni persister des verdicts probants. Il n'existe pas encore de parcours qui termine `completed`; ne jamais présenter `error` comme une expertise accomplie. Exception de recherche : tentative de clôture d'erreur ; échec de clôture explicitement signalé. Le composant n'archive pas automatiquement les rapports GitHub et ne se lance pas en tâche permanente. Les traces manuelles vérifiées du job #181 sont archivées séparément dans EZStudio_Run_Reports, commit 94b9857.

```powershell
cd H:\EZStudioLab_assistant
git pull --ff-only origin assistant-main
python -m unittest discover -s tests -p test_canonical_job_worker.py
python -m runtime.canonical_job_worker --job-id 181 --lab-root H:\EZStudio_lab
```

**Ne pas utiliser `--execute` sur #181 tant que l'objectif reste de conserver le job QUEUED pour les futurs essais.** Cette commande transformerait ce job en ERROR et nécessiterait une réactivation contrôlée ultérieure, distincte du simple préflight.

Limites explicites: pas de worker résident, pas de lease/heartbeat, pas d'extraction/validation de preuves, pas de sauvegarde des verdicts et pas d'archivage automatique.
