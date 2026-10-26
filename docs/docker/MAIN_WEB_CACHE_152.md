# MAIN smoke — Symfony cache tmpfs (1.6a(152))

Incident observé sur l'image Web 1.6a(137) : Symfony HTTP 500, exception « Unable to create the cache directory ». Le montage `/opt/ezstudio-assistant/var` est `tmpfs rw,mode=755,uid=33,gid=33`. Un `docker exec` en root sans capacités Linux a échoué à créer un sous-répertoire (Permission denied).

Cette tranche définit `user: "33:33"` pour le **seul** service `assistant-web-smoke`, aligné sur le propriétaire du montage. Ne modifie ni le contrôle GPU antérieur à 148, ni l'Assistant PROFILE, ni CUDA.

## Recette MAIN — préserver les services en cours

1. Vérifier un dépôt propre puis `git pull --ff-only origin assistant-main` et `VERSION = 1.6a(152)`.
2. Utiliser la CLI `H:\\Docker\\Desktop\\resources\\bin\\docker.exe` et valider `docker compose -f docker/main/compose.yaml --profile smoke config --quiet`.
3. Exécuter `python -m unittest discover -s tests -p test_main_web_user_contract.py -v`.
4. Construire uniquement l'image Web : `docker compose -f docker/main/compose.yaml --profile smoke build assistant-web-smoke`. Une construction ne modifie pas le conteneur actif.
5. Pour appliquer le correctif après validation de l'image et accord opérationnel : `docker compose -f docker/main/compose.yaml --profile smoke up -d --no-deps --force-recreate assistant-web-smoke`. Cette opération **recrée** uniquement le Web, avec interruption de son service ; ne l'exécuter qu'en connaissance de cause. Ne jamais utiliser `down` ou `up` sans nom de service.
6. Contrôler `docker exec <web> id`, `docker exec <web> cat VERSION`, HTTP `/` et `/backoffice`, journaux ; en cas de HTTP 500, investiguer la prochaine exception sans modifier CUDA.

Cette correction ne garantit pas l'absence d'autres erreurs applicatives. Aucun jeton métier ni job LAB activé. Conserver les jobs #181/#182/#185.
