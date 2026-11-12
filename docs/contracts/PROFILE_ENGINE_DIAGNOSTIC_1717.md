# PROFILE — journal moteur par moteur, Assistant 1.7a17

## Objectif et périmètre

Ajouter une couche **opérationnelle**, sans nouveau calcul de verdict musical, dans le worker `runtime/profile_ai_requests_worker.py`. Les appels existants restent identiques, dans le même ordre, sans nouvelle requête, aucun repli ni changement de preset. Les exceptions continuent d'être propagées.

Un appel exécuté produit `profile.engine.start` et `profile.engine.end` dans `timeline.jsonl`. La fin de l'expertise crée `profile.engine.summary` avant `trace.finish`, avec un instantané JSON. Les événements et états par assertion sont automatiquement pris en charge par le publisher brut GitHub **existant** vers `EZStudio_Run_Reports/diagnostics/assistant/profile/...`, dont le Twig `/diagnostic/profile/raw` permet la lecture après publication. Aucune tentative autonome GitHub, aucun secret ni message d'exception ne sont transmis par cette instrumentation.

Une copie expurgée du résumé est conservée dans `runtime/reports/profile/run-<run_id>/execution-<trace12>.json`, même en cas d'échec du transport GitHub. Le rapport GitHub reste autoritatif ; **le résumé local ne prétend pas qu'une publication a réussi** et contient `remote_archive_status=not_yet_attempted`. Le reçu de publication 1.7a16 reste indépendant et indique `published/partial/disabled/failed`. La publication ne peut pas être garantie tant que l'erreur du run #155 n'a pas été corrigée.

## Étapes observées

- `identity_resolver` (uniquement si artiste absent), `recording_duration` ;
- `public_source_research`, `review_payload_builder`, `independent_verifier` ;
- `assertion_web_investigator`, `local_ai_document_review`, `documentary_verdict_merger` ;
- `documentary_payload_enricher`, `ai_draft_payload_enricher`, `lab_revision_submit`.

Pour chaque appel : moteur logique, run, job, horodatages UTC, durée en ms, `RUNNING` puis `OK`/`DEGRADED`/`FAILED`/`SKIPPED`, code de raison strictement contrôlé, nom de classe d'exception seulement. `SKIPPED` signifie uniquement que le résultat de ce moteur indique explicitement `not_configured`/`unavailable`/`disabled`, **pas** que la phase a été sautée par hypothèse. Le nombre d'étapes dépend du chemin d'exécution, aucune liste fixe de moteurs actifs n'est inventée. Les investigations par assertion ainsi que les revues IA locales par assertion consignent identifiant, état, nombre de documents et **durée réelle en millisecondes**. Les synthèses existantes peuvent contenir des durées `not_instrumented_per_item` si aucun chronomètre interne n’a été disponible, sans inventer de mesure. Les moteurs importés mais non invoqués ne sont pas étiquetés « exécutés ».

## Limites et sécurité

- L'instrumentation enregistre les appels de haut niveau et chaque assertion documentaire/IA locale, **pas encore chaque requête HTTP/page interne** ; les détails déjà présents dans les snapshots métiers restent disponibles, et les appels internes pourront être instrumentés séparément avec des tests.
- Une erreur de génération de résumé est marquée `PROFILE_ENGINE_DIAG_ERROR=<stage>:<class>` sans changer la décision musicale ni l'acquittement LAB. Les tests unitaires valident les états, les durées, les exceptions, le fichier local et la prévention des fuites. Ils ne valident pas l'authentification du worker auprès de GitHub et ne remplacent pas une recette avec vrai job.
- Le `Diagnostic brut PROFILE` Twig ne lit pas les échecs locaux : la consultation hors GitHub nécessitera une extension du contrôleur, distincte de cette instrumentation.
- L'emplacement par défaut des traces a été corrigé précédemment sur MAIN vers `H:\temp\EZS_PROFILE_DEBUG` ; la variable `EZS_PROFILE_TRACE_ROOT` reste prioritaire. Cette livraison **ne touche pas** à `app/profile_trace.py`.
- Les traces et résumés sous `runtime/` demeurent ignorés par Git ; le fichier temporaire atomique est créé sur le même volume que sa destination.
- Pour un transfert vers `EZStudio_Run_Reports`, le publisher existant doit terminer la publication et vérifier la relecture GitHub. **Ne pas déclarer « envoyé » sur la seule présence du fichier local.**

## Vérification

12 tests `unittest` pour le module (Windows, volume local, fournisseur non configuré, exceptions expurgées, résultat identique, contexte sans fuite). `INSTALL.py` vérifie le HEAD, le périmètre Git, la compilation et les octets installés. `preflight` lecture seule, `apply` avec backup, `recipe`, `rollback`. Aucun commit, push, service ni job dans l'installateur.
