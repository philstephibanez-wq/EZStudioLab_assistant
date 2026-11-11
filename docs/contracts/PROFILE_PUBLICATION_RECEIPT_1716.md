# PROFILE — accusé local de publication des rapports (Assistant 1.7a16)

## Cause et frontière

Une révision LAB peut être terminée alors que l'export du rapport Assistant vers `EZStudio_Run_Reports` échoue. L'ancien worker écrit un marqueur console `PROFILE_REPORT_ERROR`, mais l'absence de fichier dans `runtime/reports` ne permet pas de distinguer publication absente, erreur ou publication désactivée. Le résumé GitHub reste **une archive différente** du résultat métier stocké par LAB.

## Comportement

- La publication GitHub existante est invoquée **exactement une fois** ; le contrat d'archivage et l'acquittement LAB ne changent pas.
- À la fin de chaque tentative disposant d'une trace, écrire atomiquement un accusé expurgé dans `runtime/reports/profile/run-<id>/trace-<id>.json` sur MAIN ; `runtime/` reste ignoré par Git.
- Champs : schéma, run, identifiant de job, identifiant de trace raccourci, révision, statut `published` / `partial` / `disabled` / `failed`, nom de classe de l'erreur si échec, UTC, archive GitHub autoritative.
- Aucune URL, aucune donnée scientifique, aucun secret, message d'exception, page brute ou donnée d'inférence ne figure dans cet accusé.
- Le rapport **ne certifie aucun verdict musical** et ne remplace pas le dépôt privé des rapports. Un statut `published` atteste seulement le retour « published » de la routine existante.
- Une exception de publication reste levée et journalisée par le worker (`PROFILE_REPORT_ERROR`) ; un échec d'écriture de l'accusé n'est pas traité comme une réussite.
- Si `EZS_PROFILE_TRACE=0` ou si la création de trace échoue, cet accusé n'existe pas : les marqueurs existants demeurent, le cas reste hors du périmètre de cette tranche.
- `/api/profile/verify` reste un circuit distinct, sans insertion artificielle dans le worker historique.

## Impacts et rollback

| Domaine | Avant | Après | Risque / prévention / preuve / retour arrière |
|---|---|---|---|
| Worker Assistant | Appelle `publish_trace` | Enveloppe l'appel sans modifier les résultats | Une seule invocation testée ; restaurer le fichier Python et VERSION via sauvegarde |
| Archive GitHub | Résumé et brut en append-only | Identique | Aucune modification à l'API GitHub ; test mocké ; archives passées intactes |
| Stockage MAIN | Pas d'accusé local contractuel | JSON sous `runtime/reports/profile/` | Écritures atomiques, identifiants contrôlés, aucune suppression ; restauration du code n'efface pas les preuves |
| LAB | Révision et état job inchangés | Identique | Aucun changement LAB / scientifique / preset / IA / service / queue |
| Sécurité | Export expurgé | Accusé expurgé | Pas de messages d'erreur ou données métier ; tests de fuite |

## Validation

Tests unitaires sans réseau et revue des octets SHA de base. La recette MAIN reste obligatoire avant activation. Un service actif peut continuer de charger l'ancien module tant que le processus n'a pas redémarré : **aucun redémarrage automatique**. Le traitement de `final_reviews`, de la vérification d'enregistrement, et de l'affichage « XPS » dans LAB sont des sujets distincts.

## Correctif Windows R1C (avant publication 1.7a16)

Échec démontré sur MAIN : `os.replace()` échoue avec `WinError 17` lorsque le fichier temporaire se trouve sur `H:\temp` et que les tests écrivent dans le `TEMP` utilisateur sur `C:`. La création temporaire est désormais effectuée dans le dossier de l'accusé sous `runtime/reports` (répertoire runtime ignoré par Git), suivie du `fsync`, du remplacement atomique sur le même volume et d'un nettoyage en `finally`. Aucun fichier temporaire ne subsiste en cas de succès. Cette exception technique au placement temporaire sous H:\temp est indispensable pour assurer l'atomicité quel que soit le volume de destination ; elle ne concerne que le fichier transitoire expurgé et ne crée pas de source suivie. La recette R1C vérifie ce placement explicitement.
