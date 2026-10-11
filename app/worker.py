from __future__ import annotations

import json
import time
from typing import Any

from transport import AnalysisApiClient


def _capability_payload(capabilities: Any, state: str) -> dict[str, Any]:
    return {
        "schema": "ezstudio.distributed.worker-heartbeat.v1",
        "protocol": capabilities.protocol,
        "node_id": capabilities.node_id,
        "hostname": capabilities.hostname,
        "state": state,
        "capabilities": capabilities.to_dict(),
    }


def observe_queue(client: AnalysisApiClient, capabilities: Any) -> dict[str, Any]:
    client.hello(_capability_payload(capabilities, "observing"))
    jobs = client.queue()
    client.heartbeat(_capability_payload(capabilities, "idle" if not jobs else "queue_visible"))
    return {
        "schema": "EZStudioLab_assistant.queue-observation.v1",
        "node_id": capabilities.node_id,
        "mode": "observe_only",
        "claim_enabled": False,
        "reason": "capability_aware_lease_claim_not_yet_available",
        "queue_count": len(jobs),
        "jobs": jobs,
    }


def watch_queue(
    client: AnalysisApiClient,
    capabilities: Any,
    *,
    poll_seconds: float = 5.0,
    iterations: int = 0,
) -> int:
    count = 0
    client.hello(_capability_payload(capabilities, "starting"))
    while True:
        jobs = client.queue()
        client.heartbeat(
            _capability_payload(capabilities, "idle" if not jobs else "queue_visible")
        )
        print(json.dumps({
            "event": "queue_snapshot",
            "node_id": capabilities.node_id,
            "queue_count": len(jobs),
            "claim_enabled": False,
            "jobs": jobs,
        }, ensure_ascii=False), flush=True)

        count += 1
        if iterations > 0 and count >= iterations:
            return 0
        time.sleep(poll_seconds)
