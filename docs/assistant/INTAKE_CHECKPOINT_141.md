# Raccordement checkpoint intake — Assistant v1.6a(141)

La commande `--record-intake` utilise le **job canonique réel**, sans prétendre avoir exécuté la recherche documentaire : GET contexte (job_id), validation du contrat musical strict, POST checkpoint `intake-v1`, GET journal, puis vérification de la relecture du même événement et du même run_id. Le POST est idempotent : relancer la commande n'ajoute pas d'événement. Aucun claim ou finish ; statut du job inchangé. Le journal est dans SQLite LAB, non une révision musicale. La publication automatique au dépôt privé EZStudio_Run_Reports n'est pas encore raccordée ; l'archive manuelle diagnostique du job #181 existe déjà et demeure distincte.

Commande après tests : `python -m runtime.canonical_job_worker --job-id 181 --lab-root H:\EZStudio_lab --record-intake`. Attendu : `intake_checkpoint_persisted` avec `event_id`, `claimed=false`, `finished=false`.

Important : si un événement `intake-v1` de même job existe avec un autre contenu, LAB renverra conflit idempotent. Cela doit être traité, pas écrasé. Aucun verdict BON/FAUX/NON TROUVÉ n'est établi par ce test. La boucle worker permanente et la recherche fiable restent hors livraison.
