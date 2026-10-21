"""R1 scientific crosscheck of three existing private reports, without Qwen."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_scientific_crosscheck import crosscheck

def read_json(path):
    raw=Path(path).read_bytes()
    if raw.startswith((b"\xff\xfe",b"\xfe\xff")):
        return json.loads(raw.decode("utf-16"))
    return json.loads(raw.decode("utf-8-sig"))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--lab",required=True)
    parser.add_argument("--revision",required=True)
    parser.add_argument("--xps",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    result=crosscheck(read_json(args.lab),read_json(args.revision),read_json(args.xps))
    output=Path(args.output)
    if output.exists():raise RuntimeError("output_exists")
    if not output.parent.is_dir():raise RuntimeError("output_parent_missing")
    output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if not result["integrity_complete"]:
        print("PROFILE_SCIENTIFIC_CROSSCHECK_INCOMPLETE",result["run_id"],result["revision_id"],"verified",result["crosschecked_module_total"],"unverified",result["unverified_module_total"],"blocking",",".join(result["blocking_source_mismatches"]))
        raise SystemExit(2)
    print("PROFILE_SCIENTIFIC_CROSSCHECK_OK",result["run_id"],result["revision_id"],result["crosschecked_module_total"],"findings",len(result["scientific_findings"]))
if __name__=="__main__":main()
