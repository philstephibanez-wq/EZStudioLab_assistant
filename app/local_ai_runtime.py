from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

ASSISTANT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHARED_MODEL_ROOT = r"\\EZSTUDIO-MAIN\EZModels"
DEFAULT_CACHE_ROOT = ASSISTANT_ROOT / "runtime" / "models-cache"
DEFAULT_RUNTIME_ROOT = ASSISTANT_ROOT / "runtime" / "ai"
DEFAULT_ENDPOINT = "http://127.0.0.1:8720"
DEFAULT_PORT = 8720
DEFAULT_DEVICE = "Vulkan1"

@dataclass(frozen=True)
class LocalAIRuntimeConfig:
    canonical_model: str
    shared_model_root: str
    cache_root: Path
    runtime_root: Path
    endpoint: str
    port: int
    device: str
    gpu_layers: int
    context_size: int
    server_exe: Path

def _relative_model_path(root: str, model: str):
    rt, mt = str(root).strip(), str(model).strip()
    if rt.startswith("\\\\") or "\\" in rt or ":" in rt:
        rp, mp = PureWindowsPath(rt), PureWindowsPath(mt)
    else:
        rp, mp = Path(rt), Path(mt)
    try:
        return mp.relative_to(rp)
    except Exception as exc:
        raise RuntimeError("local_ai_model_must_be_under_shared_model_root") from exc

def config_from_env() -> LocalAIRuntimeConfig:
    canonical = str(os.getenv("EZSTUDIOLAB_LOCAL_AI_MODEL", "")).strip()
    if not canonical:
        raise RuntimeError("local_ai_model_path_required")
    shared = str(os.getenv("EZSTUDIO_SHARED_MODEL_ROOT", DEFAULT_SHARED_MODEL_ROOT)).strip() or DEFAULT_SHARED_MODEL_ROOT
    _relative_model_path(shared, canonical)
    cache_root = Path(str(os.getenv("EZSTUDIOLAB_LOCAL_AI_CACHE_ROOT", "")).strip() or DEFAULT_CACHE_ROOT)
    runtime_root = Path(str(os.getenv("EZSTUDIOLAB_LOCAL_AI_RUNTIME_ROOT", "")).strip() or DEFAULT_RUNTIME_ROOT)
    endpoint = (str(os.getenv("EZSTUDIOLAB_LOCAL_AI_ENDPOINT", DEFAULT_ENDPOINT)).strip() or DEFAULT_ENDPOINT).rstrip("/")
    try: port = int(os.getenv("EZSTUDIOLAB_LOCAL_AI_PORT", str(DEFAULT_PORT)))
    except ValueError: port = DEFAULT_PORT
    try: gpu_layers = int(os.getenv("EZSTUDIOLAB_LOCAL_AI_GPU_LAYERS", "99"))
    except ValueError: gpu_layers = 99
    try: context_size = int(os.getenv("EZSTUDIOLAB_LOCAL_AI_CONTEXT_SIZE", "4096"))
    except ValueError: context_size = 4096
    server_exe = Path(str(os.getenv("EZSTUDIOLAB_LLAMA_SERVER", "")).strip() or runtime_root / "bin" / "llama-server.exe")
    return LocalAIRuntimeConfig(canonical, shared, cache_root, runtime_root, endpoint,
        max(1024, min(65535, port)),
        str(os.getenv("EZSTUDIOLAB_LOCAL_AI_DEVICE", DEFAULT_DEVICE)).strip() or DEFAULT_DEVICE,
        max(0, gpu_layers), max(512, context_size), server_exe)

def local_model_path(config: LocalAIRuntimeConfig) -> Path:
    rel = _relative_model_path(config.shared_model_root, config.canonical_model)
    return config.cache_root / Path(*rel.parts)

def _manifest_path(config): return config.runtime_root / "cache-manifest.json"
def _pid_path(config): return config.runtime_root / "llama-server.pid"

def _read_json(path: Path):
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return {}
    return value if isinstance(value, dict) else {}

def sync_local_model_cache(config: LocalAIRuntimeConfig | None = None) -> dict[str, Any]:
    cfg = config or config_from_env()
    source, target = Path(cfg.canonical_model), local_model_path(cfg)
    if not source.is_file(): raise RuntimeError(f"local_ai_canonical_model_missing:{source}")
    stat, manifest = source.stat(), _read_json(_manifest_path(cfg))
    unchanged = (target.is_file() and target.stat().st_size == stat.st_size
        and manifest.get("canonical_model") == str(source)
        and int(manifest.get("size") or -1) == stat.st_size
        and int(manifest.get("mtime_ns") or -1) == stat.st_mtime_ns)
    if unchanged:
        return {"schema":"EZStudioLab_assistant.local-ai-cache.v1","status":"cached","canonical_model":str(source),"local_model":str(target),"size":stat.st_size,"copied":False}
    target.parent.mkdir(parents=True, exist_ok=True); cfg.runtime_root.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".part"); temp.unlink(missing_ok=True)
    started = time.perf_counter()
    with source.open("rb") as src, temp.open("wb") as dst:
        while True:
            block = src.read(8 * 1024 * 1024)
            if not block: break
            dst.write(block)
        dst.flush(); os.fsync(dst.fileno())
    if temp.stat().st_size != stat.st_size:
        temp.unlink(missing_ok=True); raise RuntimeError("local_ai_cache_size_mismatch")
    temp.replace(target); elapsed = time.perf_counter() - started
    m = {"schema":"EZStudioLab_assistant.local-ai-cache.v1","canonical_model":str(source),"local_model":str(target),"size":stat.st_size,"mtime_ns":stat.st_mtime_ns,"copied_at_epoch":time.time()}
    _manifest_path(cfg).write_text(json.dumps(m, ensure_ascii=True, indent=2), encoding="utf-8", newline="\n")
    return {**m, "status":"copied", "copied":True, "copy_seconds":round(elapsed, 3)}

def _health(endpoint: str, timeout: float = 1.0):
    req = urllib.request.Request(endpoint.rstrip("/") + "/health", headers={"Accept":"application/json"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response: body = response.read(65536)
        payload = json.loads(body.decode("utf-8"))
        ready = bool(isinstance(payload, dict) and (payload.get("ok") is True or str(payload.get("status") or "").casefold() in {"ok","ready"}))
        return ready, payload if isinstance(payload, dict) else {}
    except Exception as exc:
        return False, {"error":f"{type(exc).__name__}:{exc}"[:300]}

def _process_info(pid: int):
    if os.name != "nt": return {"pid":pid,"alive":False}
    script = "$p=Get-CimInstance Win32_Process -Filter \"ProcessId=%d\" -ErrorAction SilentlyContinue;if($null -eq $p){exit 3};[Console]::Out.Write(($p.Name+'|'+$p.CommandLine))" % int(pid)
    kwargs = {"capture_output":True,"text":True,"encoding":"utf-8","errors":"replace","timeout":3}
    if hasattr(subprocess, "CREATE_NO_WINDOW"): kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    p = subprocess.run(["powershell","-NoProfile","-NonInteractive","-Command",script], **kwargs)
    return {"pid":pid,"alive":p.returncode==0,"identity":p.stdout.strip() if p.returncode==0 else None}

def local_ai_status(config: LocalAIRuntimeConfig | None = None):
    cfg = config or config_from_env(); model = local_model_path(cfg)
    try: pid = int(_pid_path(cfg).read_text(encoding="ascii").strip())
    except (OSError, ValueError): pid = None
    proc = _process_info(pid) if pid else {"pid":None,"alive":False}; ready, health = _health(cfg.endpoint)
    return {"schema":"EZStudioLab_assistant.local-ai-runtime-status.v1","hostname":socket.gethostname(),"ready":ready,"endpoint":cfg.endpoint,"device":cfg.device,"canonical_model":cfg.canonical_model,"local_model":str(model),"local_model_present":model.is_file(),"server_exe":str(cfg.server_exe),"server_exe_present":cfg.server_exe.is_file(),"pid":pid,"process_alive":bool(proc.get("alive")),"process_identity":proc.get("identity"),"health":health}

def local_ai_start(config: LocalAIRuntimeConfig | None = None):
    cfg = config or config_from_env(); current = local_ai_status(cfg)
    if current["ready"]: current["status"] = "already_running"; return current
    cache = sync_local_model_cache(cfg); model = Path(cache["local_model"])
    if not cfg.server_exe.is_file(): raise RuntimeError(f"llama_server_missing:{cfg.server_exe}")
    cfg.runtime_root.mkdir(parents=True, exist_ok=True); out = cfg.runtime_root / "llama-server.out.log"; err = cfg.runtime_root / "llama-server.err.log"
    args = [str(cfg.server_exe),"-m",str(model),"-dev",cfg.device,"-ngl",str(cfg.gpu_layers),"-c",str(cfg.context_size),"--host","127.0.0.1","--port",str(cfg.port)]
    flags = 0
    if hasattr(subprocess,"CREATE_NO_WINDOW"): flags |= subprocess.CREATE_NO_WINDOW
    if hasattr(subprocess,"DETACHED_PROCESS"): flags |= subprocess.DETACHED_PROCESS
    with out.open("ab") as stdout, err.open("ab") as stderr:
        proc = subprocess.Popen(args, cwd=cfg.runtime_root, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, creationflags=flags, close_fds=True)
    _pid_path(cfg).write_text(str(proc.pid), encoding="ascii")
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if proc.poll() is not None: raise RuntimeError(f"llama_server_start_failed:exit={proc.returncode}")
        ready, _ = _health(cfg.endpoint, 1.0)
        if ready:
            s = local_ai_status(cfg); s["status"] = "started"; s["cache"] = cache; return s
        time.sleep(.5)
    raise RuntimeError("llama_server_start_timeout")

def local_ai_stop(config: LocalAIRuntimeConfig | None = None):
    cfg = config or config_from_env(); pid_file = _pid_path(cfg)
    try: pid = int(pid_file.read_text(encoding="ascii").strip())
    except (OSError, ValueError): pid = None
    stopped = False
    if pid and os.name == "nt":
        info = _process_info(pid); identity = str(info.get("identity") or "")
        if info.get("alive") and "llama-server.exe" in identity.casefold():
            p = subprocess.run(["taskkill","/PID",str(pid),"/T","/F"], capture_output=True, text=True, encoding="utf-8", errors="replace"); stopped = p.returncode == 0
    pid_file.unlink(missing_ok=True)
    return {"schema":"EZStudioLab_assistant.local-ai-runtime-stop.v1","stopped":stopped,"pid":pid,"ready":_health(cfg.endpoint,.5)[0]}
