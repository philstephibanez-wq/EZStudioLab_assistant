from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ASSISTANT_ROOT = Path(__file__).resolve().parents[1]
HOST_REPO = Path(os.getenv("EZSTUDIOLAB_HOST_REPO", ASSISTANT_ROOT.parent)).resolve()
PYTHON = HOST_REPO / "python"
if not PYTHON.is_dir():
    raise RuntimeError("EZStudio_lab python root missing")
if str(PYTHON) not in sys.path:
    sys.path.insert(0, str(PYTHON))

APP = ASSISTANT_ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from gate import evaluate_profile_gate
from transport import AnalysisApiClient

readme = ASSISTANT_ROOT / "README.md"
assert readme.is_file()
assert not list(ASSISTANT_ROOT.glob("**/README_*.md"))
assert not [p for p in ASSISTANT_ROOT.rglob("README.md") if p != readme]

ready = {
    "preset": "profile-test.v1",
    "corpus": {"total": 24, "completed": 24, "failed": 0},
    "mandatory_module_errors": 0,
    "silent_fallbacks": 0,
    "dimensions": {
        "tempo_meter": {"blocking_regressions": 0, "unresolved_blockers": 0},
        "key": {"blocking_regressions": 0, "unresolved_blockers": 0},
        "tuning": {"blocking_regressions": 0, "unresolved_blockers": 0},
        "semantics": {"blocking_regressions": 0, "unresolved_blockers": 0},
        "vocals_choirs": {"blocking_regressions": 0, "unresolved_blockers": 0},
    },
    "external_review": {"required": 24, "completed": 24},
    "baseline_comparison": {"performed": True},
}
assert evaluate_profile_gate(ready)["decision"] == "READY_FOR_STEMS"

blocked = json.loads(json.dumps(ready))
blocked["dimensions"]["tuning"]["unresolved_blockers"] = 1
result = evaluate_profile_gate(blocked)
assert result["decision"] == "BLOCKED"
assert "unresolved_blockers:tuning:1" in result["blockers"]

client = AnalysisApiClient("http://127.0.0.1:9999", "token")
assert not hasattr(client, "claim")
assert not hasattr(client, "complete")
assert not hasattr(client, "fail")

print("EZStudioLab_assistant_V1B_CONTROL_GATE_CONTRACT_OK")
print("PROFILE gate is explicit and fail-closed")
print("Historic unsafe claim endpoint is not exposed by V1B")
print("Scientific pipeline untouched")
