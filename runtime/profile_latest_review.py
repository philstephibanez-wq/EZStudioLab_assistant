"""Read-only mirror of the latest LAB-persisted PROFILE documentary review."""
import json
import os
import urllib.request
import urllib.parse

BASE=os.environ.get("EZSTUDIOLAB_ASSISTANT_BASE_URL","http://EZSTUDIO-MAIN:8702").rstrip("/")
TOKEN=os.environ.get("EZSTUDIOLAB_ASSISTANT_TOKEN","")
def main():
    if not TOKEN:
        print(json.dumps({"ok":False,"error":"token_missing"}));return
    url=BASE+"/internal/analysis/desktop/profile/reviews/latest"
    selected_run=os.environ.get("EZSTUDIOLAB_PROFILE_RUN_ID", "").strip()
    if selected_run:
        if not selected_run.isdecimal() or int(selected_run) < 1:
            print(json.dumps({"ok":False,"error":"run_id_invalid"}));return
        url += "?"+urllib.parse.urlencode({"run_id":int(selected_run)})
    request=urllib.request.Request(url,headers={"X-EZScore-Analysis-Token":TOKEN,
                                                "Accept":"application/json"})
    try:
        with urllib.request.urlopen(request,timeout=12) as response:
            body=json.load(response)
        item=body.get("item")
        if not isinstance(item,dict):
            print(json.dumps({"ok":True,"state":"no_review"}));return
        print(json.dumps({"ok":True,"state":"available",
          "run_id":item.get("run_id"),
          "analysis_reference":item.get("analysis_reference"),
          "preset_reference":item.get("preset_reference"),
          "revision_id":item.get("review_id"),
          "status":item.get("review_status"),
          "identity_declared":item.get("identity_declared"),
          "items":item.get("items") or [],
          "recording_identity_confirmed":bool(item.get("identity_confirmed"))},
          ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"ok":False,"error":type(exc).__name__}))
if __name__=="__main__":main()
