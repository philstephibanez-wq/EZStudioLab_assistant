"""Read-only mirror of the latest LAB-persisted PROFILE documentary review."""
import json
import os
import urllib.request

BASE=os.environ.get("EZSTUDIOLAB_ASSISTANT_BASE_URL","http://EZSTUDIO-MAIN:8702").rstrip("/")
TOKEN=os.environ.get("EZSTUDIOLAB_ASSISTANT_TOKEN","")
def main():
    if not TOKEN:
        print(json.dumps({"ok":False,"error":"token_missing"}));return
    url=BASE+"/internal/analysis/desktop/profile/reviews/latest"
    request=urllib.request.Request(url,headers={"X-EZScore-Analysis-Token":TOKEN,
                                                "Accept":"application/json"})
    try:
        with urllib.request.urlopen(request,timeout=12) as response:
            body=json.load(response)
        item=body.get("item")
        if not isinstance(item,dict):
            print(json.dumps({"ok":True,"state":"no_review"}));return
        revision=item.get("revision") or {}
        comparison=revision.get("comparison") or {}
        verification=comparison.get("final_verification") or {}
        assertions=verification.get("assertions") or []
        by_key={a.get("key"):a for a in assertions if isinstance(a,dict)}
        investigation=(verification.get("web_investigation") or {}).get("items") or []
        local_reviews=(verification.get("local_web_review") or {}).get("items") or []
        ai_by_key={a.get("key"):a for a in local_reviews if isinstance(a,dict)}
        results=[]
        for entry in investigation:
            if not isinstance(entry,dict):continue
            key=entry.get("key")
            a=by_key.get(key,{})
            ai=ai_by_key.get(key,{})
            results.append({"key":key,"value_lab":entry.get("value"),
                "verdict":a.get("verdict") or "non_trouve",
                "reference_value":ai.get("reference_value") or a.get("reference_value"),
                "explanation":ai.get("explanation") or a.get("reason"),
                "sources":[d.get("url") for d in (entry.get("documents") or [])
                           if isinstance(d,dict) and d.get("status")=="read" and d.get("url")],
                "ai_status":ai.get("status")})
        print(json.dumps({"ok":True,"state":"available","run_id":item.get("run_id"),
          "revision_id":revision.get("id"),"status":revision.get("status"),
          "identity_declared":item.get("identity_declared"),"items":results,
          "recording_identity_confirmed":False},ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"ok":False,"error":type(exc).__name__}))
if __name__=="__main__":main()
