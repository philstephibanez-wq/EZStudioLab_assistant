"""Read-only preflight for PROFILE 1.5a. Does not invoke Qwen or claim jobs."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from transport import AnalysisApiClient
from profile_scientific_items import fetch_items
from web_status import _read_dpapi_token, DEFAULT_TOKEN_FILE
from declarative_review import load_review_preset
from profile_module_compact import module_prompt_payload

def check(run_id, api_get):
    payload=fetch_items(run_id,api_get)
    preset,_=load_review_preset("profile")
    system=("Analyse uniquement les résultats du module scientifique fourni, sans prétendre écouter l'audio. "
            "Les scores du moteur sont des hypothèses, pas des faits. Retourne un objet JSON: "
            "status (completed ou abstain), summary, uncertainty, supporting_evidence (liste), conflicting_evidence (liste). "
            "Ne valide aucun preset et indique toute insuffisance de preuves.")
    limit=int(preset["context_max_chars"])
    checks=[]
    for i,item in enumerate(payload["items"],1):
        request={"schema":"ezstudio.profile-module-consultation.v1","run_id":run_id,
          "item_id":item["item_id"],"index":i,"item_total":payload["item_total"],
          "source_sha256":"0"*64,"module":item["module"],
          "instructions":"Consultative musical assessment only. Do not claim audio was heard or promote a preset. Explain uncertainty and contradictory evidence."}
        original=json.dumps(request,ensure_ascii=False,separators=(",",":"),allow_nan=False)
        original_size=max(len(system)+len(original),len(system.encode())+len(original.encode()))
        try:
            _, projection=module_prompt_payload(request,limit,system)
            checks.append({"item_id":item["item_id"],"original_chars":original_size,
                           "prompt_chars":projection["input_chars"],"sample_limit":projection["sample_limit"],
                           "fits":True,"projection":True})
        except ValueError as exc:
            checks.append({"item_id":item["item_id"],"original_chars":original_size,
                           "fits":False,"error":str(exc)})
    return {"run_id":run_id,"item_total":len(checks),"context_max_chars":limit,
            "all_fit":all(x["fits"] for x in checks),"items":checks,
            "no_qwen_inference":True}

def main():
    token=os.environ.get("EZSTUDIOLAB_ASSISTANT_TOKEN","").strip() or _read_dpapi_token(DEFAULT_TOKEN_FILE)
    if not token:raise SystemExit("PREFLIGHT_ERROR token_unavailable")
    api=AnalysisApiClient(os.environ.get("EZSTUDIOLAB_ASSISTANT_BASE_URL","http://EZSTUDIO-MAIN:8702"),token)
    result=check(153,lambda path:api.request("GET",path,timeout=15))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result["all_fit"] or result["item_total"]!=12:raise SystemExit(2)
if __name__=="__main__":main()
