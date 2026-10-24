"""Read-only documentary OCR acceptance on a public Supertramp release booklet.
Run only on XPS by explicit command. No LAB, no stems, no DB writes.
"""
from __future__ import annotations
import json
import sys
import time
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from profile_physical_documents import discover_release_documents, inspect_scans_with_local_ocr
from profile_tesseract_runtime import booklet_ocr_enabled

RELEASE="076b6a39-4dcf-4a51-9daa-a0cc6d048c53"
TRACK="Breakfast in America"
class PublicHTTP:
    request_count=0
    class budget:
        max_requests_per_item=2
    def get_json(self,url,retries=0):
        if url != "https://coverartarchive.org/release/"+RELEASE:
            raise ValueError("unexpected_url")
        self.request_count+=1
        req=urllib.request.Request(url,headers={"User-Agent":"EZStudioLab_assistant/1.6 (public research)"})
        with urllib.request.urlopen(req,timeout=12) as response:
            return json.loads(response.read(1_000_000))

def run():
    start=time.monotonic()
    report={"schema":"ezstudio.assistant.real-document-ocr.v1",
            "release_url":"https://musicbrainz.org/release/"+RELEASE,
            "track_title":TRACK,"release_identity_confirmed":False,
            "recording_identity_confirmed":False,"advisory_only":True,
            "lab_jobs_created":0,"lab_writes":0,
            "scans_discovered":0,"scans_tested":0,"ocr_status":"not_executed",
            "source_type":"public_release_booklet"}
    try:
        docs=discover_release_documents(PublicHTTP(),[RELEASE])
        booklets=[d for d in docs if "booklet" in d.get("types",[])]
        report["scans_discovered"]=len(booklets)
        if not booklet_ocr_enabled():
            report["ocr_status"]="disabled"
        elif not booklets:
            report["ocr_status"]="no_booklet_found"
        else:
            result=inspect_scans_with_local_ocr(booklets,TRACK,max_scans=2)
            report["ocr_status"]=result["status"]
            report["scans_tested"]=len(result["scans"])
            report["scan_results"]=[{"status":s.get("status"),
                "document_url":s.get("document_url"),
                "credit_candidates":s.get("credit_candidates",[]),
                "evidence_eligible":False} for s in result["scans"]]
    except Exception as exc:
        report["ocr_status"]="error"
        report["error_type"]=type(exc).__name__
    report["duration_ms"]=int((time.monotonic()-start)*1000)
    print(json.dumps(report,ensure_ascii=True,allow_nan=False))
    return 0 if report["ocr_status"]=="completed" and report["scans_tested"]>0 else 1
if __name__=="__main__":
    raise SystemExit(run())
