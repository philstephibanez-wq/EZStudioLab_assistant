# Décommissionnement de l'ancien hôte — références actives R1

## Décision
L'Assistant fonctionne sur MAIN. Les quatre anciens lanceurs start/stop sont interdits.
Cette tranche met à jour les instructions actives, l'exemple de configuration
et les commentaires trompeurs **sans modifier les instructions exécutables**.

## Préservation
Les champs historiques `raw_xps_requests_archived`, les paramètres `--xps`,
les variables `xps_records`, les archives de runs, les noms de branches et les
documents de releases restent intacts. Une migration des schémas nécessiterait
un autre contrat, des tests de lecture et un plan de rollback.
Les anciens tests de démarrage incompatibles avec l'architecture courante ne
sont ni masqués ni supprimés.

## Impacts avant / après
Avant : README pointait vers un hôte supprimé et un lanceur inexistant ;
certaines docstrings situaient encore le runtime sur cet hôte.
Après : les consignes décrivent MAIN et les exemples ne pointent plus vers
la machine retirée ; aucun processus, service, port, job, token, moteur ou preset
n'est reconfiguré. Risque : confondre données historiques et opérationnelles.
Prévention : conservation des contrats de données et des anciens rapports.
Tests : contrôles statiques ciblés et revue du diff ; recette réelle sur MAIN
à effectuer après réconciliation des versions.

## Dépendance de publication
R2 PROFILE `1.7a14` est appliqué mais non publié localement sur MAIN,
au HEAD Git `daa28f4664b57743d5d7f439485a89e8da0d56b9`.
Ce nettoyage `1.7a15` est préparé séparément depuis ce HEAD ; **ne pas
fusionner dans assistant-main ni lancer git pull avant la réconciliation R2**.
Rollback : revert du commit de nettoyage après protection des changements
locaux ; aucun reset forcé, suppression d'archive ou redémarrage implicite.
