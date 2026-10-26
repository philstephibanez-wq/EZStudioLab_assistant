# Queue pass canonique v1.6a(143)

Commande `python -m runtime.canonical_queue_pass --lab-root H:\EZStudio_lab` : **prévisualisation en lecture seule** de tous les jobs QUEUED. `--execute` est volontairement distinct et opère réellement les transitions claim/finish via `runtime.canonical_job_worker.consume`, en séquence, isolant les erreurs par job. Le moteur documentaire n'est pas fiable : **chaque job exécuté pourra passer en ERROR**. Ne pas utiliser `--execute` sur #181 et #182 si l'on veut conserver leurs essais QUEUED. Aucune valeur musicale n'est confirmée ni persistée par cette commande ; aucun `completed`. Ce n'est pas un service permanent ni une file parallèle. Les limites lease, reprise de running, recherche fiable, persistance des verdicts et archive auto demeurent ouvertes.

Recette : `python -m unittest discover -s tests -p test_canonical_queue_pass.py` et `python -m runtime.canonical_queue_pass --lab-root H:\EZStudio_lab` ; ne pas ajouter `--execute` pendant la recette.
