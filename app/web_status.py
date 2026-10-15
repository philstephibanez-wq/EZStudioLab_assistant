from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from transport import AnalysisApiClient, AnalysisApiError

ROOT = Path(__file__).resolve().parents[1]
INSTALL_ROOT = ROOT.parent
RUNTIME_ROOT = INSTALL_ROOT / "var" / "assistant"

LAB_TIMEOUT_SECONDS = 1.5
SMB_TIMEOUT_SECONDS = 1.5


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _probe_lab(base_url: str, token: str) -> dict:
    result = {
        "transport": "REST",
        "base_url": base_url,
        "endpoint": "/internal/analysis/desktop/hello",
        "reachable": False,
        "authorized": False,
    }

    if not token:
        result["error"] = "analysis_token_missing"
        return result

    try:
        client = AnalysisApiClient(
            base_url=base_url,
            token=token,
            user_agent="EZStudioLab_assistant/web-status",
        )
        response = client.request(
            "POST",
            "/internal/analysis/desktop/hello",
            {
                "schema": "ezstudio.assistant.web-probe.v1",
                "node_id": socket.gethostname(),
                "state": "status_probe",
            },
            timeout=LAB_TIMEOUT_SECONDS,
        )
        state = response.get("state") if isinstance(response, dict) else None
        result["reachable"] = True
        result["authorized"] = bool(
            isinstance(state, dict) and state.get("ok") is True
        )
        result["target"] = (
            response.get("target") if isinstance(response, dict) else None
        )
        result["server_time"] = (
            response.get("server_time") if isinstance(response, dict) else None
        )
        if not result["authorized"]:
            result["error"] = "lab_hello_invalid_response"
    except AnalysisApiError as exc:
        result["error"] = str(exc)[:500]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}:{exc}"[:500]

    return result


def _probe_model_root(model_root: Path) -> dict:
    code = (
        "import os,sys;"
        "raise SystemExit(0 if os.path.exists(sys.argv[1]) else 3)"
    )
    kwargs = {
        "capture_output": True,
        "text": True,
        "timeout": SMB_TIMEOUT_SECONDS,
    }
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    result = {
        "transport": "SMB",
        "root": str(model_root),
        "accessible": False,
        "scope": "AI models only",
    }

    try:
        completed = subprocess.run(
            [sys.executable, "-c", code, str(model_root)],
            **kwargs,
        )
        result["accessible"] = completed.returncode == 0
        if completed.returncode != 0:
            result["error"] = "model_root_unreachable"
    except subprocess.TimeoutExpired:
        result["error"] = "model_root_timeout"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}:{exc}"[:500]

    return result


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    status_file = Path(
        os.getenv(
            "EZSTUDIOLAB_ASSISTANT_STATUS_FILE",
            str(RUNTIME_ROOT / "assistant.status.json"),
        )
    )
    model_root = Path(
        os.getenv(
            "EZSTUDIO_SHARED_MODEL_ROOT",
            r"\\EZSTUDIO-MAIN\EZModels",
        )
    )
    base_url = os.getenv(
        "EZSTUDIOLAB_ASSISTANT_BASE_URL",
        "http://EZSTUDIO-MAIN:8702",
    ).rstrip("/")
    token = os.getenv("EZSTUDIOLAB_ASSISTANT_TOKEN", "").strip()

    runtime = _read_json(status_file)
    lab_rest = _probe_lab(base_url, token)
    models = _probe_model_root(model_root)

    payload = {
        "ok": True,
        "schema": "ezstudio.assistant.web-status.v1",
        "state": runtime.get("state") or "IDLE",
        "activity": runtime.get("activity") or "En attente",
        "hostname": socket.gethostname(),
        "version": version,
        "database": False,
        "persistence_owner": "LAB",
        "dependencies_ok": bool(
            lab_rest.get("reachable")
            and lab_rest.get("authorized")
            and models.get("accessible")
        ),
        "lab_rest": lab_rest,
        "models": models,
        "runtime": {
            "status_file": str(status_file),
            "pid": runtime.get("pid"),
            "job_id": runtime.get("job_id"),
            "phase": runtime.get("phase"),
            "progress": runtime.get("progress"),
        },
    }

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
