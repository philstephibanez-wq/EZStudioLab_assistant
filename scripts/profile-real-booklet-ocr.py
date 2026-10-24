"""Read-only documentary OCR acceptance on a public Supertramp release booklet.
Run only on XPS by explicit command. No LAB, no stems, no DB writes.
"""
from __future__ import annotations
import json
import argparse
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

def run(*, start=0, max_pages=2):
    start_time=time.monotonic()
    report={"schema":"ezstudio.assistant.real-document-ocr.v1",
            "release_url":"https://musicbrainz.org/release/"+RELEASE,
            "track_title":TRACK,"release_identity_confirmed":False,
            "recording_identity_confirmed":False,"advisory_only":True,
            "lab_jobs_created":0,"lab_writes":0,
            "scans_discovered":0,"scans_tested":0,"ocr_status":"not_executed",
            "source_type":"public_release_booklet",
            "source_selection":"release_booklet_only; web credits must be checked separately",
            "source_priorities":[{"source":"MusicBrainz","purpose":"recording-scoped credits and identifiers","verification":"not_performed"},
              {"source":"Cover Art Archive","purpose":"printed booklet credits","verification":"ocr_candidates_only"}],
            "page_offset":start,"max_pages":max_pages}
    try:
        docs=discover_release_documents(PublicHTTP(),[RELEASE])
        booklets=[d for d in docs if "booklet" in d.get("types",[])]
        report["scans_discovered"]=len(booklets)
        if not booklet_ocr_enabled():
            report["ocr_status"]="disabled"
        elif not booklets:
            report["ocr_status"]="no_booklet_found"
        else:
            scans=[]
            selected=booklets[max(0,start):max(0,start)+max(0,min(max_pages,12))]
            for offset in range(0,len(selected),2):
                batch=inspect_scans_with_local_ocr(selected[offset:offset+2],TRACK,max_scans=2)
                scans.extend(batch.get("scans",[]))
            report["ocr_status"]="completed" if scans else "no_scans_processed"
            report["scans_tested"]=len(scans)
            report["scan_results"]=[{"status":item.get("status"),
                "document_url":item.get("document_url"),
                "credit_candidates":item.get("credit_candidates",[]),
                "ocr_diagnostic":item.get("ocr_diagnostic"),
                "evidence_eligible":False} for item in scans]
    except Exception as exc:
        report["ocr_status"]="error"
        report["error_type"]=type(exc).__name__
    report["duration_ms"]=int((time.monotonic()-start_time)*1000)
    print(json.dumps(report,ensure_ascii=True,allow_nan=False))
    return 0 if report["ocr_status"]=="completed" and report["scans_tested"]>0 else 1
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--start",type=int,default=0)
    parser.add_argument("--max-pages",type=int,default=2)
    args=parser.parse_args()
    raise SystemExit(run(start=args.start,max_pages=args.max_pages))
