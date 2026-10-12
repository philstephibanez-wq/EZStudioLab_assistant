from __future__ import annotations
import os,sys
from pathlib import Path
ASSISTANT_ROOT=Path(__file__).resolve().parents[1]
HOST_REPO=Path(os.getenv("EZSTUDIOLAB_HOST_REPO",ASSISTANT_ROOT.parent)).resolve()
PYTHON=HOST_REPO/"python"
if not PYTHON.is_dir(): raise RuntimeError("EZStudio_lab python root missing")
if str(PYTHON) not in sys.path: sys.path.insert(0,str(PYTHON))
APP=ASSISTANT_ROOT/"app"
if str(APP) not in sys.path: sys.path.insert(0,str(APP))
from transport import AnalysisApiClient
from worker import distributed_claim_once
class C:
    protocol="ezstudio.distributed.v1"; node_id="EZStudioLab_assistant-EZSTUDIO-XPS"; hostname="EZSTUDIO-XPS"
    def to_dict(self): return {"protocol":self.protocol,"node_id":self.node_id,"hostname":self.hostname,"cuda_available":True,"max_vram_mb":4096,"ram_total_mb":16118,"models":[]}
class F(AnalysisApiClient):
    def __init__(self,eligible=True): self.calls=[]; self.eligible=eligible
    def request(self,method,path,payload=None,*,timeout=10.0):
        self.calls.append((method,path,payload))
        if path.endswith("/distributed/workers/heartbeat"): return {"worker_id":payload["worker_id"],"state":payload["state"]}
        if path.endswith("/distributed/jobs/eligible"): return {"jobs":[{"job_id":42,"kind":"profile"}] if self.eligible else []}
        if path.endswith("/distributed/jobs/42/claim"): return {"job_id":42,"lease":{"worker_id":payload["worker_id"],"lease_token":"secret","expires_at_epoch":9999999999,"lease_seconds":60}}
        if path.endswith("/distributed/jobs/42/context"): assert payload["lease_token"]=="secret"; return {"job":{"id":42},"lease":{"worker_id":payload["worker_id"],"expires_at_epoch":9999999999}}
        raise AssertionError(path)
c=F(); r=distributed_claim_once(c,C(),job_id=42,lease_seconds=60,limit=100)
assert r["job_id"]==42 and r["claim_enabled"] is True and r["scientific_execution_enabled"] is False
assert r["lease"]["lease_token_present"] is True and "lease_token" not in r["lease"] and r["context_received"] is True
paths=[x[1] for x in c.calls]
assert paths==["/internal/analysis/desktop/distributed/workers/heartbeat","/internal/analysis/desktop/distributed/jobs/eligible","/internal/analysis/desktop/distributed/jobs/42/claim","/internal/analysis/desktop/distributed/jobs/42/context","/internal/analysis/desktop/distributed/workers/heartbeat"]
c2=F(False)
try: distributed_claim_once(c2,C(),job_id=42)
except RuntimeError as e: assert str(e)=="distributed_job_not_currently_eligible:42"
else: raise AssertionError("ineligible job accepted")
assert not any(x[1].endswith("/claim") for x in c2.calls)
print("EZStudioLab_assistant_V1C2_CLAIM_ONCE_CONTRACT_OK")
print("Explicit job_id required")
print("Eligibility rechecked immediately before claim")
print("Lease token validated but not emitted")
print("Scientific execution remains disabled")
