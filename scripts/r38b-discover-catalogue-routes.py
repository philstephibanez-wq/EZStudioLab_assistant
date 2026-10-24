"""R38b temporary catalogue route discovery (MAIN, read-only)."""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from pathlib import Path

def routes_for_lab(lab_root, php="php"):
    root=Path(lab_root)
    console=root/"bin"/"console"
    if not console.is_file():
        return {"status":"lab_console_missing","route_candidates":[]}
    cmd=[php,str(console),"debug:router","--format=json","--env=prod","--no-debug"]
    try:
        proc=subprocess.run(cmd,cwd=str(root),capture_output=True,text=True,
                            encoding="utf-8",errors="replace",timeout=40,
                            env={**os.environ,"APP_DEBUG":"0"})
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {"status":"route_discovery_failed","error_type":type(exc).__name__,"route_candidates":[]}
    if proc.returncode:
        return {"status":"route_discovery_failed","returncode":proc.returncode,"route_candidates":[]}
    try:
        data=json.loads(proc.stdout)
    except ValueError:
        return {"status":"invalid_router_json","route_candidates":[]}
    results=[]
    if isinstance(data,dict):
        for name,entry in data.items():
            if not isinstance(entry,dict):
                continue
            path=str(entry.get("path") or "")
            methods=entry.get("methods") or []
            if isinstance(methods,str):
                methods=[methods]
            if re.search(r"song|catalog|analysis|profile",name+" "+path,re.I) and (
                not methods or "GET" in methods or "HEAD" in methods):
                results.append({"name":name,"path":path,"methods":methods})
    return {"status":"ok","route_candidates":results,"read_only":True}

def main(argv=None):
    args=argv or sys.argv[1:]
    if len(args)!=1:
        print("Usage: python scripts/r38b-discover-catalogue-routes.py <MAIN-LAB-repository-path>",file=sys.stderr)
        return 2
    report=routes_for_lab(args[0])
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report["status"]=="ok" else 1

if __name__=="__main__":
    raise SystemExit(main())
