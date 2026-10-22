"""Live-only PROFILE web preflight. No mock, no synthetic music, no network fallback."""
from __future__ import annotations
import argparse, json, os, sys
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
    if not os.environ.get("OPENAI_API_KEY","").strip():
        raise SystemExit("WEB_PROVIDER_NOT_CONFIGURED: OPENAI_API_KEY absent in this session; no web calls performed")
    result=research_each_assertion(data,{"title":options.title,"artist":options.artist})
    print(json.dumps({"status":result["status"],"searched":result["searched"],
        "items":[{"key":x.get("key"),"status":x.get("status"),"web_calls":x.get("web_calls",0),
        "references":len(x.get("citation_urls") or []),"proposed_verdict":(x.get("assessment") or {}).get("proposed_verdict")}
        for x in result["items"]]},ensure_ascii=False,indent=2))
    if result.get("status")!="completed" or not result.get("searched"):
        raise SystemExit("LIVE_WEB_NOT_OPERATIONAL")
    if not any(x.get("web_calls",0)>0 for x in result["items"]):
        raise SystemExit("ZERO_REAL_WEB_CALLS")
if __name__=="__main__":main()
