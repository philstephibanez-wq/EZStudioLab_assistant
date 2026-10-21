"""Read-only end-to-end scientific module probe; never claims an AI job."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_scientific_items import fetch_items, describe_items
from transport import AnalysisApiClient
from web_status import _read_dpapi_token, DEFAULT_TOKEN_FILE

def probe(run_id, client):
    payload=fetch_items(run_id,lambda path:client.request("GET",path,timeout=15))
    result=describe_items(payload)
    result["coverage"]=payload["coverage"]
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run",type=int,default=153)
    args=p.parse_args()
    token=os.environ.get("EZSTUDIOLAB_ASSISTANT_TOKEN","").strip() or _read_dpapi_token(DEFAULT_TOKEN_FILE)
    if not token:
        p.error("analysis_token_unavailable")
    base=os.environ.get("EZSTUDIOLAB_ASSISTANT_BASE_URL","http://EZSTUDIO-MAIN:8702")
    client=AnalysisApiClient(base,token,user_agent="EZStudioLab_assistant/profile-items-probe")
    result=probe(args.run,client)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
