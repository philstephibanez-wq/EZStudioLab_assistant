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
    if (lab.get("schema")!="ezstudio.diagnostics.main.v1" or lab.get("producer")!="lab"
        or lab.get("phase")!="profile" or lab.get("run_id")!=run
        or lab.get("fields",{}).get("id")!=run or lab.get("fields",{}).get("item")!="profile"
        or xps.get("schema")!="ezstudio.profile-execution-report.v1"
        or xps.get("run_id")!=run or xps.get("revision_id")!=base["revision_id"]):
        raise ValueError("crosscheck_archive_identity_invalid")
    registry=lab.get("fields",{}).get("diagnostics_json",{}).get("module_registry",{}).get("modules")
    records=revision["fields"]["comparison_json"]["module_consultations"]["results"]
    xps_records=xps.get("module_audit",{}).get("records")
    if not isinstance(registry,list) or not isinstance(xps_records,list) or len(registry)!=len(records) or len(xps_records)!=len(records):
        raise ValueError("crosscheck_module_coverage_invalid")
    # A privacy-redacted archive cannot reproduce a source hash exactly.
    # Report such modules as unverified; do not accept a hash mismatch as valid.
    redactions=lab.get("redactions",[])
    if not isinstance(redactions,list):
        raise ValueError("crosscheck_redactions_invalid")
    redacted_modules=set()
    for entry in redactions:
        path=entry.get("field","") if isinstance(entry,dict) else ""
        if path.startswith("$.diagnostics_json.module_registry.modules[].raw.audioset_scores."):
            redacted_modules.update(
                m["id"] for m in registry
                if isinstance(m,dict) and isinstance(m.get("raw"),dict)
                and isinstance(m["raw"].get("audioset_scores"),dict)
                and any(v=="[REDACTED_SECRET_OR_BINARY]" for v in m["raw"]["audioset_scores"].values())
            )
    verified=[]
    for n,(source,review,trace) in enumerate(zip(registry,records,xps_records),1):
        key=review["item_id"]
        if (not isinstance(source,dict) or source.get("id")!=key or trace.get("item_id")!=key
            or review.get("index")!=n or trace.get("index")!=n
            or trace.get("source_sha256")!=review.get("source_sha256")
            or trace.get("status")!=review.get("status")):
            raise ValueError("crosscheck_source_or_provenance_mismatch:"+key)
        observed=digest(source)
        matched=observed==review.get("source_sha256")
        if not matched and key not in redacted_modules:
            raise ValueError("crosscheck_source_or_provenance_mismatch:"+key)
        verified.append({"module":key,"source_sha256":observed,
                         "original_source_sha256":review["source_sha256"],
                         "source_hash_verified":matched,
                         "unverified_reason":None if matched else "privacy_redaction_in_archived_module",
                         "source_status":source.get("status"),"qwen_status":review["status"],
                         "qwen_request_sha256":trace.get("qwen_request_sha256"),
                         "qwen_response_sha256":trace.get("qwen_response_sha256")})
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
            "crosschecked_module_total":sum(1 for item in verified if item["source_hash_verified"]),
            "unverified_module_total":sum(1 for item in verified if not item["source_hash_verified"]),
            "provenance_checks":verified,
            "scientific_findings":findings,"no_preset_mutation":True,
            "crosscheck_sha256":digest({"provenance":verified,"scientific_findings":findings})}
