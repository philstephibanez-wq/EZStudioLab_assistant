"""R38d temporary five-song catalogue sampler; not the Assistant workflow.
SQLite is read-only. History is stored outside Git and written only with --commit.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from profile_catalogue_rotation import choose_unseen, load_history, commit_history

spec=importlib.util.spec_from_file_location("r38c_inventory",ROOT/"scripts"/"r38c-main-catalogue-inventory.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Confirmed song IDs from the previous two documentary campaigns.
PREVIOUSLY_TESTED={13,21,22,29,44,28,31,54,55,56}

def prepare(database,history):
    catalogue=module.inventory(database)
    used=load_history(history) | PREVIOUSLY_TESTED
    selection=choose_unseen(
        [s for s in catalogue["songs"] if s["state"]=="done"],used,5)
    return catalogue,selection,used

def main(argv=None):
    parser=argparse.ArgumentParser(description="Temporary five-new-songs documentary sample (not production workflow)")
    parser.add_argument("database",help="Explicit MAIN LAB SQLite database path")
    parser.add_argument("--history",required=True,help="Absolute history JSON path OUTSIDE Git repositories")
    parser.add_argument("--commit",action="store_true",help="Reserve these five song IDs in history")
    args=parser.parse_args(argv)
    hist=Path(args.history).resolve()
    if not hist.is_absolute() or ROOT==hist or ROOT in hist.parents:
        parser.error("history_must_be_outside_assistant_repository")
    catalogue,selection,used=prepare(args.database,hist)
    report={"schema":"ezstudio.assistant.r38d-sample.v1",
            "status":selection["status"],"sampling_only":True,
            "permanent_workflow_changed":False,"lab_writes":0,
            "lab_jobs_created":0,"catalogue_songs":catalogue["total_songs"],
            "analyzed_songs":catalogue["analyzed_songs"],
            "previously_tested_minimum":len(PREVIOUSLY_TESTED),
            "unseen_count":selection["unseen_count"],
            "selection":selection["selected"],
            "history_committed":False}
    if args.commit and selection["status"]=="selected":
        commit_history(hist,used,[s["song_id"] for s in selection["selected"]])
        report["history_committed"]=True
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if selection["status"]=="selected" else 1

if __name__=="__main__":
    raise SystemExit(main())
