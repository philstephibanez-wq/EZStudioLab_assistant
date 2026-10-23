"""Live-only PROFILE web preflight. No mock, no synthetic music, no network fallback."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_web_investigator import research_each_assertion

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--row-json",required=True,help="Real LAB snapshot: lab.profile.row.json")
    parser.add_argument("--title",required=True)
    parser.add_argument("--artist",required=True)
    options=parser.parse_args()
    data=json.loads(Path(options.row_json).read_text(encoding="utf-8"))
    if not isinstance(data,dict):
        raise SystemExit("INVALID_LAB_ROW")
    result=research_each_assertion(data,{"title":options.title,"artist":options.artist})
    print(json.dumps({"status":result["status"],"searched":result["searched"],
        "items":[{"key":x.get("key"),"status":x.get("status"),"documents_read":sum(d.get("status")=="read" for d in (x.get("documents") or [])),
        "references":len(x.get("citation_urls") or []),"document_verdict":(x.get("evidence_review") or {}).get("verdict"),
        "proposed_verdict":(x.get("evidence_review") or {}).get("proposed_verdict"),
        "source_values":[{"url":z.get("url"),"value":z.get("reference_value")} for z in (x.get("evidence_review") or {}).get("references",[])][:5]}
        for x in result["items"]]},ensure_ascii=False,indent=2))
    if result.get("status")!="completed" or not result.get("searched"):
        raise SystemExit("LIVE_WEB_NOT_OPERATIONAL")
    if not any(x.get("status")=="documents_read" for x in result["items"]):
        raise SystemExit("ZERO_PUBLIC_WEB_DOCUMENTS_READ")
if __name__=="__main__":main()
