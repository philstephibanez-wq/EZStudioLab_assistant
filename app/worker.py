from __future__ import annotations
import json,time
from typing import Any
from runtime_status import write_status
from transport import AnalysisApiClient
def _capability_payload(capabilities:Any,state:str)->dict[str,Any]:
    return {"schema":"ezstudio.distributed.worker-heartbeat.v1","protocol":capabilities.protocol,"node_id":capabilities.node_id,"hostname":capabilities.hostname,"state":state,"capabilities":capabilities.to_dict()}
def observe_queue(client,capabilities):
    client.hello(_capability_payload(capabilities,"observing")); jobs=client.queue(); client.heartbeat(_capability_payload(capabilities,"idle" if not jobs else "queue_visible"))
    return {"schema":"EZStudioLab_assistant.queue-observation.v1","node_id":capabilities.node_id,"mode":"observe_only","claim_enabled":False,"reason":"use_distributed_probe_for_capability_aware_queue","queue_count":len(jobs),"jobs":jobs}
def watch_queue(client,capabilities,*,poll_seconds=5.0,iterations=0):
    count=0; client.hello(_capability_payload(capabilities,"starting"))
    while True:
        jobs=client.queue(); client.heartbeat(_capability_payload(capabilities,"idle" if not jobs else "queue_visible")); print(json.dumps({"event":"queue_snapshot","node_id":capabilities.node_id,"queue_count":len(jobs),"claim_enabled":False,"jobs":jobs},ensure_ascii=False),flush=True); count+=1
        if iterations>0 and count>=iterations:return 0
        time.sleep(poll_seconds)
def distributed_probe(client,capabilities,*,limit=100):
    worker_id=str(capabilities.node_id); cap=capabilities.to_dict(); heartbeat=client.distributed_worker_heartbeat(worker_id,cap,state="probing"); jobs=client.distributed_eligible_jobs(worker_id,limit=limit); client.distributed_worker_heartbeat(worker_id,cap,state="idle" if not jobs else "eligible_jobs_visible")
    return {"schema":"EZStudioLab_assistant.distributed-probe.v1","worker_id":worker_id,"claim_enabled":False,"scientific_execution_enabled":False,"heartbeat":heartbeat,"eligible_count":len(jobs),"eligible_jobs":jobs}
def distributed_claim_once(client,capabilities,*,job_id,lease_seconds=60,limit=100):
    worker_id=str(capabilities.node_id); cap=capabilities.to_dict(); client.distributed_worker_heartbeat(worker_id,cap,state="claim_check"); jobs=client.distributed_eligible_jobs(worker_id,limit=limit)
    eligible_ids={int(r["job_id"]) for r in jobs if isinstance(r,dict) and str(r.get("job_id","")).isdigit()}
    if int(job_id) not in eligible_ids:
        client.distributed_worker_heartbeat(worker_id,cap,state="idle"); raise RuntimeError(f"distributed_job_not_currently_eligible:{int(job_id)}")
    claim=client.distributed_claim_job(int(job_id),worker_id,lease_seconds=lease_seconds); lease=claim.get("lease")
    if not isinstance(lease,dict): raise RuntimeError("distributed_claim_missing_lease")
    if str(lease.get("worker_id") or "")!=worker_id: raise RuntimeError("distributed_claim_worker_mismatch")
    lease_token=str(lease.get("lease_token") or "").strip()
    if not lease_token: raise RuntimeError("distributed_claim_missing_lease_token")
    context=client.distributed_context(int(job_id),worker_id,lease_token); client.distributed_worker_heartbeat(worker_id,cap,state="claimed_contract_only")
    return {"schema":"EZStudioLab_assistant.distributed-claim-once.v1","worker_id":worker_id,"job_id":int(job_id),"claim_enabled":True,"scientific_execution_enabled":False,"lease":{"worker_id":worker_id,"lease_token_present":True,"expires_at_epoch":lease.get("expires_at_epoch"),"lease_seconds":lease.get("lease_seconds")},"context_received":isinstance(context,dict),"context":context}
def watch_distributed(client,capabilities,*,poll_seconds=5.0,iterations=0,limit=100):
    count=0; worker_id=str(capabilities.node_id); cap=capabilities.to_dict(); write_status("ONLINE","Démarrage du worker distribué"); client.distributed_worker_heartbeat(worker_id,cap,state="starting")
    try:
        while True:
            write_status("ONLINE","Recherche de job compatible")
            jobs=client.distributed_eligible_jobs(worker_id,limit=limit); state="idle" if not jobs else "eligible_jobs_visible"; heartbeat=client.distributed_worker_heartbeat(worker_id,cap,state=state)
            activity="En veille — aucun job compatible" if not jobs else f"{len(jobs)} job(s) compatible(s) détecté(s)"
            write_status("ONLINE",activity)
            print(json.dumps({"event":"distributed_queue_snapshot","worker_id":worker_id,"claim_enabled":False,"scientific_execution_enabled":False,"eligible_count":len(jobs),"eligible_jobs":jobs,"heartbeat":heartbeat},ensure_ascii=False),flush=True); count+=1
            if iterations>0 and count>=iterations:return 0
            time.sleep(poll_seconds)
    except Exception as exc:
        write_status("ERROR",f"{type(exc).__name__}: {exc}"[:240])
        raise
