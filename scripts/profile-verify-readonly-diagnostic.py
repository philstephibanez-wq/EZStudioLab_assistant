"""Diagnostic lecture seule de la chaîne XPS PROFILE, sans authentification LAB.

N'envoie aucun résultat à LAB et ne crée aucun job. Le dossier d'essai est
synthétique, malgré un titre public servant à tester la recherche documentaire.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"runtime"))
from profile_verify_push import verify
from profile_assertions_contract import ITEMS

def main():
    payload={"expertise_type":"profile","analysis_id":999999,"preset_id":"diagnostic_synthetique",
             "title":"La fille du Père Noël","artist":"Jacques Dutronc",
             "items":{key:None for key in ITEMS}}
    started=time.monotonic()
    report={"schema":"ezstudio.assistant.profile-readonly-diagnostic.v1",
            "fixture":"synthetic_values_real_public_web","title":"La fille du Père Noël",
            "artist":"Jacques Dutronc","lab_jobs_created":0,"lab_writes":0,
            "scientific_validation":False}
    try:
        result=verify(payload)
        report.update(status="completed",technical_status=result.get("technical_status"),
                      technical_errors=result.get("technical_errors"),
                      item_count=len(result.get("reviews") or {}),
                      consulted_url_count=sum(len(v.get("consulted_urls") or []) for v in result.get("reviews",{}).values()),
                      qwen_status=(result.get("ai_consultation") or {}).get("status"),
                      qwen_error_reason=(result.get("ai_consultation") or {}).get("reason"),
                      qwen_error_code=(result.get("ai_consultation") or {}).get("error_code"),
                      qwen_diagnostic=(result.get("ai_consultation") or {}).get("diagnostic"),
                      search_status=(result.get("tool_audit") or {}).get("document_search"),
                      musicbrainz_status=(result.get("structured_musicbrainz") or {}).get("status"),
                      musicbrainz_recording_candidates=(result.get("structured_musicbrainz") or {}).get("candidates",[]),
                      distinct_source_count=(result.get("documentary_provenance") or {}).get("distinct_source_count"),
                      readable_distinct_count=(result.get("documentary_provenance") or {}).get("readable_distinct_count"),
                      documentary_items={key:{
                          "candidate_count": item.get("candidate_count"),
                          "explicit_reference_count": item.get("explicit_reference_count"),
                          "scientific_verdict":item.get("scientific_verdict"),
                          "recording_identity_verified": False,
                          "top_sources":[{"url":source.get("url"),
                              "source_scope":source.get("source_scope"),
                              "read_status":source.get("read_status")} for source in
                              (item.get("candidate_sources") or [])[:3]]
                      } for key,item in
                      ((result.get("documentary_provenance") or {}).get("items") or {}).items()})
    except Exception as exc:
        report.update(status="failed",exception_type=type(exc).__name__,
                      exception_reason=str(exc)[:120] if isinstance(exc,ValueError) else None)
    report["duration_ms"]=round((time.monotonic()-started)*1000)
    print(json.dumps(report,ensure_ascii=True,allow_nan=False))
    return 0 if report["status"]=="completed" else 1

if __name__=="__main__":
    raise SystemExit(main())
