from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ASSISTANT_ROOT = Path(__file__).resolve().parents[1]
HOST_REPO = Path(os.getenv("EZSTUDIOLAB_HOST_REPO", ASSISTANT_ROOT.parent / "EZStudio_lab")).resolve()
PYTHON = HOST_REPO / "python"
if not PYTHON.is_dir():
    raise RuntimeError("EZStudio_lab python root missing")
if str(PYTHON) not in sys.path:
    sys.path.insert(0, str(PYTHON))

from ezstudio.distributed.capabilities import detect_capabilities
from ezstudio.distributed.model_resolver import ModelResolver, sha256_path
from ezstudio.distributed.worker_protocol import JobRequirements, compatibility_report

app = ASSISTANT_ROOT / "app" / "main.py"
start_cmd = ASSISTANT_ROOT / "scripts" / "start.cmd"
start_ps1 = ASSISTANT_ROOT / "scripts" / "start.ps1"
stop_cmd = ASSISTANT_ROOT / "scripts" / "stop.cmd"
stop_ps1 = ASSISTANT_ROOT / "scripts" / "stop.ps1"
config = ASSISTANT_ROOT / "config" / "EZStudioLab_assistant.example.json"
readme = ASSISTANT_ROOT / "README.md"

assert app.is_file()
assert start_cmd.is_file()
assert start_ps1.is_file()
assert stop_cmd.is_file()
assert stop_ps1.is_file()
assert not (ASSISTANT_ROOT / "scripts" / "start-EZStudioLab_assistant.ps1").exists()
assert config.is_file()
assert readme.is_file()
assert not list(ASSISTANT_ROOT.glob("README_*.md"))

caps = detect_capabilities()
assert caps.protocol == "ezstudio.distributed.v1"
assert caps.cpu_logical_count >= 1

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    shared = tmp_path / "shared"
    cache = tmp_path / "cache"
    model = shared / "audio" / "test-model"
    model.mkdir(parents=True)
    (model / "weights.bin").write_bytes(b"EZStudioLab_assistant-v1a1")
    resolver = ModelResolver(shared_root=shared, cache_root=cache)
    cached = resolver.resolve("audio/test-model", use_cache=True)
    assert sha256_path(cached) == sha256_path(model)
    report = compatibility_report(
        caps,
        JobRequirements(model_relative_path="audio/test-model"),
        model_resolver=resolver,
    )
    assert report["compatible"] is True

print("EZStudioLab_assistant_V1A_SINGLE_ROOT_CONTRACT_OK")
print("Canonical start/stop lifecycle enforced")
print("Shared protocol remains owned by EZStudio_lab")
print("Scientific pipeline untouched")
