"""Read-only live Qwen/profile smoke test. No LAB calls, no queue, no persisted review.
Prints a sanitized JSON result; exit nonzero on failure.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from profile_document_consultation import consult

def main():
    start=time.monotonic()
    identity={"title":"Synthetic test title","artist":"Synthetic test artist"}
    reviews={"tempo":{"verdict":"non_trouve","reference_value":"120 BPM",
                      "references":[{"url":"https://example.org/synthetic",
                         "reference_value":"120 BPM",
                         "attribution":"unverified_synthetic_fixture"}]}}
    result=consult(identity,reviews)
    ok=(result.get("status") in ("completed","abstain")
        and result.get("advisory_only") is True
        and result.get("promotes_verdict") is False
        and isinstance(result.get("uncertainty"),str))
    output={"schema":"ezstudio.assistant.profile-live-smoke.v1",
            "ok":bool(ok),"status":result.get("status"),
            "model":result.get("model"),"reason":result.get("reason"),
            "has_summary":bool(result.get("summary")),
            "has_uncertainty":bool(result.get("uncertainty")),
            "translation_notes_count":len(result.get("translation_notes") or []),
            "advisory_only":result.get("advisory_only"),
            "promotes_verdict":result.get("promotes_verdict"),
            "duration_ms":round((time.monotonic()-start)*1000),
            "lab_jobs_created":0,"lab_writes":0,
            "real_model":True,"fixture":"synthetic_unverified"}
    print(json.dumps(output,ensure_ascii=True,allow_nan=False))
    return 0 if ok else 1
if __name__=="__main__":
    raise SystemExit(main())
