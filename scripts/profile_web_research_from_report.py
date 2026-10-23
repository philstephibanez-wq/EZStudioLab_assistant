"""Re-investigate actual PROFILE values from a previous live report.

This read-only path needs no LAB token, retained trace directory, or mocks.
The input must be a previous ezs.live-multisong-preflight.v1 report.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_web_investigator import research_assertions

LABELS={"tempo":"Tempo","meter":"Mesure","key":"Tonalité","genre":"Genre",
        "lead_vocal":"Voix principale","backing_vocals":"Voix d'accompagnement",
        "vocal_harmonies":"Harmonies vocales","choir":"Chœurs"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--previous-report",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    previous=json.loads(Path(args.previous_report).read_text(encoding="utf-8-sig"))
    if previous.get("schema")!="ezs.live-multisong-preflight.v1":
        raise SystemExit("EXPECTED_AUTHENTIC_LAB_MULTISONG_REPORT")
    songs=previous.get("results")
    if not isinstance(songs,list) or len(songs)<2:
        raise SystemExit("REQUIRE_AT_LEAST_TWO_PREVIOUSLY_ANALYZED_SONGS")
    results=[]
    for index,song in enumerate(songs,1):
        title=str(song.get("title") or "").strip()
        artist=str(song.get("artist") or "").strip()
        earlier=song.get("items") or []
        assertions=[]
        for item in earlier:
            key=str(item.get("key") or "").strip()
            value=str(item.get("value") or "").strip()
            if not key or not value:continue
            assertions.append({"key":key,"value":value,
                "label":LABELS.get(key,"Instrument" if key.startswith("instrument:") else key)})
        if not title or not artist or not assertions:
            raise SystemExit("INCOMPLETE_PREVIOUS_LAB_REPORT_SONG_"+str(index))
        print(f"[{index}/{len(songs)}] {artist} — {title}",flush=True)
        investigation=research_assertions(assertions,{"title":title,"artist":artist})
        results.append({"title":title,"artist":artist,"source":"previous_real_lab_report",
            "items":[{"key":item["key"],"value":item["value"],
                "status":item["status"],"query":item.get("query"),
                "reason":item.get("reason"),"references":item["citation_urls"],
                "evidence":item.get("evidence_review"),
                "rejected_irrelevant":item.get("rejected_irrelevant",0)}
                for item in investigation["items"]]})
    destination=Path(args.output)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps({"schema":"ezs.live-multisong-research-replay.v1",
        "results":results},ensure_ascii=False,indent=2),encoding="utf-8")
    print("REPORT="+str(destination.resolve()),flush=True)
    print("SONGS="+str(len(results)),flush=True)
    counts={}
    for song in results:
        for item in song["items"]:
            status=item["status"]
            counts[status]=counts.get(status,0)+1
    print("SEARCH_STATUS="+json.dumps(counts,ensure_ascii=False),flush=True)
    for song in results:
        for item in song["items"]:
            if item["status"]=="error":
                print("SEARCH_ERROR="+song["artist"]+"/"+item["key"]+": "+str(item.get("reason")),flush=True)
    if not any(item["references"] for song in results for item in song["items"]):
        raise SystemExit("SEARCH_PROVIDER_OR_RELEVANCE_FAILED: inspect report item statuses and reasons")

if __name__=="__main__":main()
