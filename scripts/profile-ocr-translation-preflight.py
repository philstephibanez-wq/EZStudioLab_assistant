"""XPS read-only OCR + translation preflight: no network document download or LAB.
Does not start jobs. Prints sanitized JSON and does not claim a successful OCR
unless the real Tesseract executable and traineddata are available.
"""
from __future__ import annotations
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from profile_tesseract_runtime import resolve_tesseract, booklet_ocr_enabled
from profile_document_consultation import consult

def check_ocr():
    state=resolve_tesseract()
    if state.get("status")!="ready":
        return {"status":"unavailable","reason":state.get("status"),"executed":False}
    # Text-only Tesseract probe verifies binary and model access, not image recognition.
    # A genuine OCR image test requires an authorized input scan and is a separate gate.
    return {"status":"ready_not_executed","executed":False,"models":"eng+fra"}

def check_translation():
    # Deliberately synthetic; passing only proves a real inference, not accuracy.
    sample={"duration":{"verdict":"non_trouve","reference_value":"English metadata: five minutes",
                        "references":[{"url":"https://example.org/fixture",
                        "reference_value":"English metadata: five minutes",
                        "attribution":"synthetic_unverified"}]}}
    advice=consult({"title":"Synthetic song","artist":"Synthetic artist"},sample)
    return {"status":advice.get("status"),"executed":advice.get("status") in ("completed","abstain"),
            "translation_notes_count":len(advice.get("translation_notes") or []),
            "translation_proven":False,"reason":advice.get("reason"),
            "advisory_only":advice.get("advisory_only"),"promotes_verdict":advice.get("promotes_verdict")}

def main():
    started=time.monotonic()
    ocr=check_ocr()
    translation=check_translation()
    report={"schema":"ezstudio.assistant.ocr-translation-preflight.v1",
            "assistant_version":(ROOT/"VERSION").read_text(encoding="utf-8-sig").strip(),
            "ocr":ocr,"ocr_setting_enabled":booklet_ocr_enabled(),
            "qwen_translation":translation,
            "lab_jobs_created":0,"lab_writes":0,
            "scientific_validation":False,
            "duration_ms":round((time.monotonic()-started)*1000)}
    print(json.dumps(report,ensure_ascii=True,allow_nan=False))
    return 0 if translation["executed"] and translation["advisory_only"] and not translation["promotes_verdict"] else 1

if __name__=="__main__":
    raise SystemExit(main())
