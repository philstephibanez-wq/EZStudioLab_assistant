from __future__ import annotations
import os, sys
from pathlib import Path
ASSISTANT_ROOT = Path(__file__).resolve().parents[1]
HOST_REPO = Path(os.getenv("EZSTUDIOLAB_HOST_REPO", ASSISTANT_ROOT.parent)).resolve()
PYTHON = HOST_REPO / "python"
if not PYTHON.is_dir(): raise RuntimeError("EZStudio_lab python root missing")
if str(PYTHON) not in sys.path: sys.path.insert(0, str(PYTHON))
APP = ASSISTANT_ROOT / "app"
if str(APP) not in sys.path: sys.path.insert(0, str(APP))
from transport import AnalysisApiClient
from worker import distributed_probe
class FakeCapabilities:
    protocol="ezstudio.distributed.v1"; node_id="EZStudioLab_assistant-EZSTUDIO-XPS"; hostname="EZSTUDIO-XPS"
    def to_dict(self): return {"protocol":self.protocol,"node_id":self.node_id,"hostname":self.hostname,"cuda_available":True,"max_vram_mb":4096,"ram_total_mb":16118}
class FakeClient(AnalysisApiClient):
    def __init__(self): self.calls=[]
    def request(self, method, path, payload=None, *, timeout=10.0):
        self.calls.append((method,path,payload))
        if path.endswith("/distributed/workers/heartbeat"): return {"schema":"ezstudio.distributed.worker-heartbeat.v1","worker_id":payload["worker_id"],"state":payload["state"]}
        if path.endswith("/distributed/jobs/eligible"): return {"schema_version":"ezstudio.distributed.jobs.v1","jobs":[]}
        raise AssertionError(f"unexpected_request:{method}:{path}")
client=FakeClient(); payload=distributed_probe(client, FakeCapabilities())
assert payload["worker_id"]=="EZStudioLab_assistant-EZSTUDIO-XPS"
assert payload["claim_enabled"] is False and payload["scientific_execution_enabled"] is False and payload["eligible_count"]==0
paths=[c[1] for c in client.calls]
assert paths==["/internal/analysis/desktop/distributed/workers/heartbeat","/internal/analysis/desktop/distributed/jobs/eligible","/internal/analysis/desktop/distributed/workers/heartbeat"]
assert not hasattr(client,"claim") and not hasattr(client,"complete") and not hasattr(client,"fail")
for name in ("distributed_claim_job","distributed_lease_heartbeat","distributed_context","distributed_progress","distributed_complete","distributed_cancelled","distributed_fail"): assert hasattr(client,name),name
print("EZStudioLab_assistant_V1C1_DISTRIBUTED_PROBE_CONTRACT_OK")
print("V1C worker heartbeat endpoint wired")
print("Capability-aware eligible queue endpoint wired")
print("No job is claimed by distributed-probe")
print("Scientific execution remains disabled")
