from __future__ import annotations

import json
import time
from typing import Any

from transport import AnalysisApiClient


def _capability_payload(capabilities: Any, state: str) -> dict[str, Any]:
    return {"schema": "ezstudio.distributed.worker-heartbeat.v1", "protocol": capabilities.protocol, "node_id": capabilities.node_id, "hostname": capabilities.hostname, "state": state, "capabilities": capabilities.to_dict()}


def observe_queue(client: AnalysisApiClient, capabilities: Any) -> dict[str, Any]:
    client.hello(_capability_payload(capabilities, "observing"))
    jobs = client.queue()
    client.heartbeat(_capability_payload(capabilities, "idle" if not jobs else "queue_visible"))
    return {"schema": "EZStudioLab_assistant.queue-observation.v1", "node_id": capabilities.node_id, "mode": "observe_only", "claim_enabled": False, "reason": "use_distributed_probe_for_capability_aware_queue", "queue_count": len(jobs), "jobs": jobs}


def watch_queue(client: AnalysisApiClient, capabilities: Any, *, poll_seconds: float = 5.0, iterations: int = 0) -> int:
    count = 0
    client.hello(_capability_payload(capabilities, "starting"))
    while True:
        jobs = client.queue()
        client.heartbeat(_capability_payload(capabilities, "idle" if not jobs else "queue_visible"))
        print(json.dumps({"event": "queue_snapshot", "node_id": capabilities.node_id, "queue_count": len(jobs), "claim_enabled": False, "jobs": jobs}, ensure_ascii=False), flush=True)
        count += 1
        if iterations > 0 and count >= iterations: return 0
        time.sleep(poll_seconds)


def distributed_probe(client: AnalysisApiClient, capabilities: Any, *, limit: int = 100) -> dict[str, Any]:
    worker_id = str(capabilities.node_id)
    cap = capabilities.to_dict()
    heartbeat = client.distributed_worker_heartbeat(worker_id, cap, state="probing")
    jobs = client.distributed_eligible_jobs(worker_id, limit=limit)
    client.distributed_worker_heartbeat(worker_id, cap, state="idle" if not jobs else "eligible_jobs_visible")
    return {"schema": "EZStudioLab_assistant.distributed-probe.v1", "worker_id": worker_id, "claim_enabled": False, "scientific_execution_enabled": False, "heartbeat": heartbeat, "eligible_count": len(jobs), "eligible_jobs": jobs}


def watch_distributed(client: AnalysisApiClient, capabilities: Any, *, poll_seconds: float = 5.0, iterations: int = 0, limit: int = 100) -> int:
    count = 0
    worker_id = str(capabilities.node_id)
    cap = capabilities.to_dict()
    client.distributed_worker_heartbeat(worker_id, cap, state="starting")
    while True:
        jobs = client.distributed_eligible_jobs(worker_id, limit=limit)
        state = "idle" if not jobs else "eligible_jobs_visible"
        heartbeat = client.distributed_worker_heartbeat(worker_id, cap, state=state)
        print(json.dumps({"event": "distributed_queue_snapshot", "worker_id": worker_id, "claim_enabled": False, "eligible_count": len(jobs), "eligible_jobs": jobs, "heartbeat": heartbeat}, ensure_ascii=False), flush=True)
        count += 1
        if iterations > 0 and count >= iterations: return 0
        time.sleep(poll_seconds)
