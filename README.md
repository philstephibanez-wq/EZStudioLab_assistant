# EZStudioLab_assistant

Nœud assistant distribué d'EZStudioLab.

## État V1C1

V1C1 branche l’assistant sur les endpoints distribués V1C d’`EZStudio_lab` : heartbeat worker capability-aware et interrogation de la file éligible pour ce worker.

Le mode `distributed-probe` est volontairement non destructif : il enregistre/met à jour le worker, publie ses capacités et demande les jobs compatibles. Il ne claim aucun job et ne lance aucune analyse scientifique.

Le mode `distributed-watch` répète ce contrôle sans claim.

## Sécurité

Les jobs historiques restent locaux par défaut. Un job n’est visible dans la file distribuée que si son contrat `request_json` active explicitement `distributed.enabled=true`, avec `input_mode=shared_path` et des `requirements`.

Le claim réel reste désactivé dans la CLI tant que le test réseau XPS ↔ V1C n’est pas validé. Aucun fallback silencieux.

## Gate PROFILE → STEMS

Décisions possibles : `BLOCKED` ou `READY_FOR_STEMS`. La fin d’un batch ne suffit pas à promouvoir PROFILE.

## Contrat V1C1

```powershell
python .\tests\test_EZStudioLab_assistant_v1c1_distributed_probe.py
```

Attendu :

```text
EZStudioLab_assistant_V1C1_DISTRIBUTED_PROBE_CONTRACT_OK
V1C worker heartbeat endpoint wired
Capability-aware eligible queue endpoint wired
No job is claimed by distributed-probe
Scientific execution remains disabled
```
