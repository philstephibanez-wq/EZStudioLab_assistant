"""R2: sequential, evidence-bounded consultative reviews, one existing LAB job.

Does not claim, enqueue or finalize jobs. The caller owns canonical queue lifecycle.
"""
from __future__ import annotations
import hashlib
import json
import time
from profile_scientific_items import fetch_items

def examine_modules(run_id, api_get, infer, *, on_progress=None, on_record=None):
    payload=fetch_items(run_id,api_get)
    total=payload["item_total"]
    if total == 0:
        raise ValueError("empty_scientific_module_registry")
    results=[]
    for index,item in enumerate(payload["items"],1):
        module=item["module"]
        source_hash=hashlib.sha256(json.dumps(module,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()
        request={"schema":"ezstudio.profile-module-consultation.v1","run_id":run_id,
                 "item_id":item["item_id"],"index":index,"item_total":total,
                 "source_sha256":source_hash,"module":module,
                 "instructions":"Consultative musical assessment only. Do not claim audio was heard or promote a preset. Explain uncertainty and contradictory evidence."}
        if on_progress:on_progress(index-1,total,item["item_id"])
        start=time.perf_counter()
        answer=infer(request)
        if not isinstance(answer,dict):
            raise ValueError("module_review_invalid:"+item["item_id"])
        status=answer.get("status")
        if status not in ("completed","abstain"):
            raise RuntimeError("module_inference_failed:"+item["item_id"]+":"+str(status))
        record={"item_id":item["item_id"],"index":index,"source_sha256":source_hash,
                "status":status,"assessment":answer,"duration_ms":round((time.perf_counter()-start)*1000)}
        if on_record:on_record(request,record)
        results.append(record)
        if on_progress:on_progress(index,total,item["item_id"])
    return {"schema":"ezstudio.profile-sequential-consultation.v1","run_id":run_id,
            "item_total":total,"examined":len(results),"complete":len(results)==total,
            "advisory_only":True,"results":results}
