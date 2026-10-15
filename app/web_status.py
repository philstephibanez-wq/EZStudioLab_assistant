from __future__ import annotations
import json, os, socket
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
INSTALL_ROOT = ROOT.parent
RUNTIME_ROOT = INSTALL_ROOT / "var" / "assistant"
def _read_json(path: Path) -> dict:
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return {}
    return value if isinstance(value, dict) else {}
def main() -> int:
    version=(ROOT/"VERSION").read_text(encoding="utf-8").strip()
    status_file=Path(os.getenv("EZSTUDIOLAB_ASSISTANT_STATUS_FILE", str(RUNTIME_ROOT/"assistant.status.json")))
    model_root=Path(os.getenv("EZSTUDIO_SHARED_MODEL_ROOT", r"\\EZSTUDIO-MAIN\EZModels"))
    runtime=_read_json(status_file)
    payload={
      "ok":True,"schema":"ezstudio.assistant.web-status.v1","state":runtime.get("state") or "IDLE",
      "activity":runtime.get("activity") or "En attente","hostname":socket.gethostname(),"version":version,
      "database":False,"persistence_owner":"LAB",
      "lab_rest":{"base_url":os.getenv("EZSTUDIOLAB_ASSISTANT_BASE_URL","http://EZSTUDIO-MAIN:8702"),"transport":"REST"},
      "models":{"transport":"SMB","root":str(model_root),"accessible":model_root.exists(),"scope":"AI models only"},
      "runtime":{"status_file":str(status_file),"pid":runtime.get("pid"),"job_id":runtime.get("job_id"),"phase":runtime.get("phase"),"progress":runtime.get("progress")}}
    print(json.dumps(payload, ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())
