"""Conservative MAIN-only GGUF acquisition; no XPS cache or server changes.

Run without --download for read-only preflight. Explicit --download writes
only to the existing MAIN share; demands an upstream SHA256 declaration.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import urllib.request

REPO="unsloth/Qwen3-1.7B-GGUF"
FILE="Qwen3-1.7B-Q4_K_M.gguf"
ROOT=r"\\EZSTUDIO-MAIN\EZModels"
API="https://huggingface.co/api/models/"+REPO+"/tree/main"
SOURCE="https://huggingface.co/"+REPO+"/resolve/main/"+FILE

def resolve_integrity_head(url=SOURCE):
    """Xet files often omit lfs.sha256 in the model tree; resolve HEAD exposes the actual content ETag."""
    request=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"EZStudioLab-assistant-model-preflight"})
    with urllib.request.urlopen(request,timeout=30) as response:
        headers=response.headers
        sha=str(headers.get("X-Linked-Etag") or headers.get("ETag") or "").strip('"').lower()
        size=int(headers.get("X-Linked-Size") or headers.get("Content-Length") or 0)
    if not re.fullmatch(r"[0-9a-f]{64}",sha) or size<=500_000_000:
        raise RuntimeError("UPSTREAM_XET_SHA256_UNAVAILABLE")
    return size,sha

def metadata(fetch=None,integrity=None):
    if fetch is None:
        def fetch(url):
            with urllib.request.urlopen(url,timeout=25) as response:
                return json.load(response)
    entries=fetch(API)
    matches=[x for x in entries if x.get("path")==FILE]
    if len(matches)!=1:raise RuntimeError("MODEL_FILE_NOT_FOUND")
    entry=matches[0]
    size=int(entry.get("size") or 0)
    sha=str((entry.get("lfs") or {}).get("sha256") or "").lower()
    if not re.fullmatch(r"[0-9a-f]{64}",sha):
        head_size,sha=(integrity or resolve_integrity_head)()
        if head_size!=size:raise RuntimeError("UPSTREAM_SIZE_MISMATCH")
    if not (size>500_000_000 and re.fullmatch(r"[0-9a-f]{64}",sha)):
        raise RuntimeError("UPSTREAM_SIZE_OR_SHA256_UNAVAILABLE")
    return {"repository":REPO,"file":FILE,"size":size,"sha256":sha,"source":SOURCE}

def dest(root):
    # On Windows a UNC share root is an anchor: Path.name is empty.
    canonical=PureWindowsPath(ROOT)
    candidate=PureWindowsPath(str(root))
    if str(candidate).rstrip("\\\\/").casefold()!=str(canonical).rstrip("\\\\/").casefold():
        raise ValueError("MAIN_MODEL_SHARE_REQUIRED")
    return Path(root)/"assistant"/"bench"/"qwen3-1.7b-q4_k_m"/FILE

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def preflight(root=ROOT,fetch=None):
    info=metadata(fetch)
    target=dest(root)
    if not target.parents[2].is_dir():raise RuntimeError("MAIN_SHARE_UNAVAILABLE")
    usage=shutil.disk_usage(target.parents[2])
    status="exists" if target.exists() else "missing"
    if status=="exists":
        status="verified" if target.stat().st_size==info["size"] and sha256(target)==info["sha256"] else "invalid_existing_file"
    if usage.free<info["size"]*2 and status=="missing":raise RuntimeError("INSUFFICIENT_MAIN_FREE_SPACE")
    return info,target,status

def download(info,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    part=target.with_name(target.name+".part")
    if target.exists():raise RuntimeError("REFUSE_OVERWRITE_EXISTING")
    if part.exists():raise RuntimeError("PARTIAL_FILE_EXISTS_CHECK_MANUALLY")
    req=urllib.request.Request(info["source"],headers={"User-Agent":"EZStudioLab-assistant-model-preflight"})
    try:
        with urllib.request.urlopen(req,timeout=90) as response,open(part,"xb") as output:
            h=hashlib.sha256()
            total=0
            while True:
                data=response.read(4*1024*1024)
                if not data:break
                output.write(data);h.update(data);total+=len(data)
        if total!=info["size"] or h.hexdigest()!=info["sha256"]:
            raise RuntimeError("DOWNLOAD_SHA256_MISMATCH")
        os.replace(part,target)
    except Exception:
        if part.exists():part.unlink()
        raise

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--download",action="store_true",help="explicitly download the candidate to MAIN only")
    args=p.parse_args()
    info,target,status=preflight()
    print(json.dumps({"candidate":info["repository"],"filename":info["file"],
      "size_bytes":info["size"],"expected_sha256":info["sha256"],
      "target_on_main":str(target),"status":status,"production_unchanged":True},
      ensure_ascii=False,indent=2))
    if status=="verified":return
    if status=="invalid_existing_file":raise RuntimeError("EXISTING_MODEL_INVALID_NO_OVERWRITE")
    if args.download:
        download(info,target)
        print("MODEL_ON_MAIN_SHA256_VERIFIED")
    else:print("PREFLIGHT_ONLY_NO_DOWNLOAD")
if __name__=="__main__":main()
