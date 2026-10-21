"""R1 evidence-based crosscheck of archived LAB, Qwen and XPS records.

Pure and read-only: no inference, network calls or preset mutation.
"""
from __future__ import annotations
import hashlib
import json
from profile_critical_audit import audit

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()

def crosscheck(lab, revision, xps):
    base=audit(revision)
    run=base["run_id"]
    if (lab.get("schema")!="ezstudio.run-report.v1" or lab.get("producer")!="lab"
        or lab.get("phase")!="profile" or lab.get("run_id")!=run
        or xps.get("schema")!="ezstudio.profile-execution-report.v1"
        or xps.get("run_id")!=run or xps.get("revision_id")!=base["revision_id"]):
        raise ValueError("crosscheck_archive_identity_invalid")
    registry=lab.get("diagnostics",{}).get("module_registry",{}).get("modules")
    records=revision["fields"]["comparison_json"]["module_consultations"]["results"]
    xps_records=xps.get("module_audit",{}).get("records")
    if not isinstance(registry,list) or not isinstance(xps_records,list) or len(registry)!=len(records) or len(xps_records)!=len(records):
        raise ValueError("crosscheck_module_coverage_invalid")
    verified=[]
    for n,(source,review,trace) in enumerate(zip(registry,records,xps_records),1):
        key=review["item_id"]
        if (not isinstance(source,dict) or source.get("id")!=key or trace.get("item_id")!=key
            or review.get("index")!=n or trace.get("index")!=n
            or digest(source)!=review.get("source_sha256") or trace.get("source_sha256")!=review.get("source_sha256")
            or trace.get("status")!=review.get("status")):
            raise ValueError("crosscheck_source_or_provenance_mismatch:"+key)
        verified.append({"module":key,"source_sha256":digest(source),"source_status":source.get("status"),"qwen_status":review["status"],
                         "qwen_request_sha256":trace.get("qwen_request_sha256"),"qwen_response_sha256":trace.get("qwen_response_sha256")})
    tonal=[m for m in registry if str(m["id"]).startswith("tonal.") and m.get("status")=="ok"]
    findings=[]
    tonal_details=[{"module":m["id"],"label":m.get("normalized",{}).get("label"),
                    "confidence":m.get("calibrated",{}).get("confidence"),
                    "calibration_method":m.get("calibrated",{}).get("method"),
                    "calibration_status":m.get("calibrated",{}).get("status")} for m in tonal]
    labels={m["label"] for m in tonal_details}
    if len(tonal_details)>1:
        findings.append({"code":"TONAL_LABEL_AGREEMENT" if len(labels)==1 else "TONAL_LABEL_DISAGREEMENT",
                         "modules":[m["module"] for m in tonal_details],
                         "evidence":tonal_details,
                         "verified_against_scientific_modules":True,
                         "ground_truth_validated":False})
        if len({m["calibration_method"] for m in tonal_details})>1:
            findings.append({"code":"TONAL_CONFIDENCE_HETEROGENEOUS","evidence":tonal_details,
                             "note":"Scores from heterogeneous calibration methods cannot be interpreted as directly comparable probabilities.",
                             "ground_truth_validated":False})
    return {**base,"schema":"ezstudio.profile-crosscheck.r1","scientific_crosscheck_performed":True,
            "crosschecked_module_total":len(verified),"provenance_checks":verified,
            "scientific_findings":findings,"no_preset_mutation":True,
            "crosscheck_sha256":digest({"provenance":verified,"scientific_findings":findings})}
