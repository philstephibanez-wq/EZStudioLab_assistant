"""Real multi-song PROFILE web + OCR preflight. No fixtures or synthetic music.

Manifest JSON array: [{"row_json":"C:\\\\path\\\\real.row.json","title":"...","artist":"..."}].
Every row must be exported from a genuine LAB run.
"""
from __future__ import annotations
import argparse,json,sys,os,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_auto_review import research_public_sources,NetworkBudget
from profile_web_investigator import research_each_assertion
from profile_review import normalize_track_identity

def main():
    parser=argparse.ArgumentParser()
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest",help="JSON array of real LAB runs and actual artist/title pairs")
    source.add_argument("--trace-root",help="Recursively discover authentic LAB row snapshots")
    parser.add_argument("--max-songs",type=int,default=3)
    parser.add_argument("--output",required=True,help="Diagnostic JSON output, never a product verdict")
    args=parser.parse_args()
    if args.manifest:
        manifest_path=Path(args.manifest)
        if not manifest_path.is_file():
            raise SystemExit("MANIFEST_NOT_FOUND: "+str(manifest_path))
        entries=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    else:
        requested=Path(args.trace_root)
        candidates=[requested,Path(tempfile.gettempdir())/"EZS_PROFILE_DEBUG",
            Path.home()/"AppData"/"Local"/"Temp"/"EZS_PROFILE_DEBUG",
            Path("H:/temp/EZS_PROFILE_DEBUG"),
            Path("C:/temp/EZS_PROFILE_DEBUG")]
        roots=[]
        for candidate in candidates:
            if candidate.is_dir() and candidate not in roots:
                roots.append(candidate)
        if not roots:
            raise SystemExit("NO_REAL_TRACE_ROOT_FOUND: checked "+", ".join(str(p) for p in candidates))
        print("TRACE_ROOTS="+", ".join(str(p) for p in roots),flush=True)
        entries=[]
        seen=set()
        paths=[]
        for root in roots:
            paths.extend(root.rglob("*lab.profile.row.json"))
        paths=sorted(set(paths),key=lambda p:p.stat().st_mtime,reverse=True)
        for path in paths:
            try:
                row=json.loads(path.read_text(encoding="utf-8-sig"))
                if not isinstance(row,dict):continue
                normalized=normalize_track_identity(row)
                title=str(normalized.get("title") or "").strip()
                artist=str(normalized.get("artist") or "").strip()
                if not title or not artist:continue
                key=(title.casefold(),artist.casefold())
                if key in seen:continue
                seen.add(key)
                entries.append({"row_json":str(path),"title":title,"artist":artist})
            except (OSError,ValueError,TypeError):
                continue
            if len(entries)>=args.max_songs:break
        print("DISCOVERED_REAL_SONGS="+str(len(entries)),flush=True)
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
