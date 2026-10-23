"""Real multi-song PROFILE web + OCR preflight. No fixtures or synthetic music.

Manifest JSON array: [{"row_json":"C:\\\\path\\\\real.row.json","title":"...","artist":"..."}].
Every row must be exported from a genuine LAB run.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_auto_review import research_public_sources,NetworkBudget
from profile_web_investigator import research_each_assertion

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",required=True,help="JSON array of real LAB runs and actual artist/title pairs")
    parser.add_argument("--output",required=True,help="Diagnostic JSON output, never a product verdict")
    args=parser.parse_args()
    entries=json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
    if not isinstance(entries,list) or len(entries)<2:raise SystemExit("REQUIRE_AT_LEAST_TWO_REAL_SONGS")
    results=[]
    for index,entry in enumerate(entries,1):
        if not isinstance(entry,dict):raise SystemExit("INVALID_MANIFEST_ENTRY")
        rowpath=Path(entry.get("row_json") or "")
        title=str(entry.get("title") or "").strip()
        artist=str(entry.get("artist") or "").strip()
        if not rowpath.is_file() or not title or not artist:raise SystemExit("INVALID_REAL_ROW_OR_IDENTITY")
        row=json.loads(rowpath.read_text(encoding="utf-8-sig"))
        if not isinstance(row,dict):raise SystemExit("INVALID_LAB_ROW")
        identity={"title":title,"artist":artist}
        print(f"[{index}/{len(entries)}] {artist} — {title}",flush=True)
        try:
            source_research=research_public_sources(identity,NetworkBudget())
            investigation=research_each_assertion(row,identity,source_research=source_research)
            results.append({"title":title,"artist":artist,"row_json":str(rowpath),
                "search_status":investigation["status"],
                "ocr":investigation["ocr_audit"],
                "items":[{"key":item.get("key"),"value":item.get("value"),
                    "status":item.get("status"),
                    "references":item.get("citation_urls",[]),
                    "evidence":item.get("evidence_review"),
                    "ocr_scans":item.get("ocr_scans",[])}
                    for item in investigation["items"]]})
        except Exception as exc:
            results.append({"title":title,"artist":artist,"error_type":type(exc).__name__,
                            "error":str(exc)[:200]})
    Path(args.output).write_text(json.dumps({"schema":"ezs.live-multisong-preflight.v1",
                        "results":results},ensure_ascii=False,indent=2),encoding="utf-8")
    print("REPORT="+str(Path(args.output).resolve()))
    print("SONGS="+str(len(results))+" ERRORS="+str(sum("error_type" in x for x in results)))
    if any("error_type" in x for x in results):raise SystemExit("LIVE_MULTI_SONG_PARTIAL_FAILURE")

if __name__=="__main__":main()
