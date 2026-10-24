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
                      search_status=(result.get("tool_audit") or {}).get("document_search"))
    except Exception as exc:
        report.update(status="failed",exception_type=type(exc).__name__,
                      exception_reason=str(exc)[:120] if isinstance(exc,ValueError) else None)
    report["duration_ms"]=round((time.monotonic()-started)*1000)
    print(json.dumps(report,ensure_ascii=True,allow_nan=False))
    return 0 if report["status"]=="completed" else 1

if __name__=="__main__":
    raise SystemExit(main())
