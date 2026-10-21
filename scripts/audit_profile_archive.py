"""Run a read-only audit against an existing local report."""
import argparse
import json
import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"app"))
from profile_critical_audit import audit
p=argparse.ArgumentParser()
p.add_argument("--archive",required=True)
p.add_argument("--output",required=True)
args=p.parse_args()
result=audit(json.loads(pathlib.Path(args.archive).read_text(encoding="utf-8")))
out=pathlib.Path(args.output)
if out.exists():raise RuntimeError("output_exists")
if not out.parent.is_dir():raise RuntimeError("output_parent_missing")
out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PROFILE_AUDIT_OK",result["run_id"],result["revision_id"],result["module_total"])
