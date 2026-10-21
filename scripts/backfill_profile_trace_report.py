"""Publish an existing, scrubbed XPS PROFILE audit without running Qwen again."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from profile_report import make_report, publish_report

def select_trace(root: Path, run: int, revision: int):
    matches=[]
    for folder in sorted(root.glob(f"run-{run}-*")):
        if not (folder.name.startswith(f"run-{run}-") and re.fullmatch("[0-9a-f]{12}",folder.name.rsplit("-",1)[-1])):
            continue
        timeline=folder/"timeline.jsonl"
        if not timeline.is_file():
            continue
        records=[]
        with timeline.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    data=json.loads(line)
                except ValueError:
                    raise ValueError("invalid_trace_jsonl")
                if isinstance(data,dict):
                    records.append(data)
        revisions=[]
        for event in records:
            if event.get("event") != "lab.submit.response":
                continue
            data=event.get("data")
            if isinstance(data,dict):
                rev=data.get("revision")
                if isinstance(rev,dict) and rev.get("id") == revision and data.get("ok") is True:
                    revisions.append(event)
        module_events=[event for event in records if event.get("event") == "module.review.completed"]
        if len(revisions)==1 and len(module_events)==12:
            matches.append((folder,timeline))
    if len(matches)!=1:
        raise RuntimeError(f"archive_source_not_unique_or_missing:{len(matches)}")
    return matches[0]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",type=int,required=True)
    parser.add_argument("--revision",type=int,required=True)
    parser.add_argument("--trace-root",type=Path,default=Path(os.getenv("EZS_PROFILE_TRACE_ROOT") or r"C:\\temp\\EZS_PROFILE_DEBUG"))
    parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args()
    if args.run<=0 or args.revision<=0:
        parser.error("positive identifiers required")
    folder,timeline=select_trace(args.trace_root,args.run,args.revision)
    trace=type("ArchivedTrace",(),{
        "file":timeline,"run_id":args.run,"trace_id":folder.name.rsplit("-",1)[-1]
    })()
    report=make_report(trace,{"revision":args.revision})
    audit=report.get("module_audit") or {}
    if audit.get("count")!=12:
        raise RuntimeError("incomplete_module_audit")
    if args.dry_run:
        print(f"PROFILE_TRACE_BACKFILL_READY run={args.run} revision={args.revision} modules=12 trace={trace.trace_id}")
    else:
        state=publish_report(report)
        print(f"PROFILE_TRACE_BACKFILL_{state.upper()} run={args.run} revision={args.revision} modules=12")
if __name__=="__main__":
    main()
