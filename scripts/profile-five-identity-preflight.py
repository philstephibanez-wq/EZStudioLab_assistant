"""Five PROFILE identity candidates, strictly documentary; never enqueue or write LAB."""
from __future__ import annotations
import json
import os
import random
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from web_status import DEFAULT_TOKEN_FILE, _read_dpapi_token
from profile_recording_reconciliation import compare_durations
from profile_musicbrainz_structured import discover_recordings

BASE=os.getenv("EZSTUDIOLAB_ASSISTANT_BASE_URL","http://EZSTUDIO-MAIN:8702").rstrip("/")
MAX_BYTES=32_000_000
SEED=20261024

def fetch_rows():
    token=(os.getenv("EZSTUDIOLAB_ASSISTANT_TOKEN") or "").strip() or _read_dpapi_token(DEFAULT_TOKEN_FILE)
    if not token:
        raise RuntimeError("token_missing")
    req=urllib.request.Request(BASE+"/internal/analysis/desktop/profile/reviews/queue?limit=20",
        headers={"X-EZScore-Analysis-Token":token,"Accept":"application/json"},method="GET")
    with urllib.request.urlopen(req,timeout=25) as res:
        if not str(res.headers.get("Content-Type") or "").lower().startswith("application/json"):
            raise ValueError("lab_non_json")
        raw=res.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ValueError("lab_response_too_large")
    data=json.loads(raw)
    if not isinstance(data,dict) or not isinstance(data.get("reviews"),list):
        raise ValueError("lab_queue_invalid")
    return [{k:item.get(k) for k in ("run_id","song_id","title","artist","state","metrics")}
            for item in data["reviews"] if isinstance(item,dict)]

def select_five(rows,number=5,seed=SEED):
    by_song={}
    for item in rows:
        if item.get("state")!="done" or type(item.get("run_id")) is not int or type(item.get("song_id")) is not int:
            continue
        run,song=item["run_id"],item["song_id"]
        if run<=0 or song<=0 or not str(item.get("title") or "").strip():
            continue
        metrics=item.get("metrics")
        duration=None
        if isinstance(metrics,dict):
            for key in ("duration_seconds","duration_s","duration"):
                if metrics.get(key) is not None:
                    duration=metrics[key]
                    break
        if not compare_durations({"candidates":[]},duration)["lab_duration_available"]:
            continue
        if song not in by_song or run>by_song[song]["run_id"]:
            by_song[song]={"run_id":run,"song_id":song,"title":str(item["title"])[:150],
                           "catalogue_artist":str(item.get("artist") or "")[:120],"duration":duration}
    eligible=sorted(by_song.values(),key=lambda item:item["song_id"])
    return eligible,random.Random(seed).sample(eligible,number) if len(eligible)>=number else []

def parse_filename_identity(raw):
    """Conservative interpretation of filename labels; never identity evidence."""
    original=" ".join(str(raw or "").split())
    parts=[p.strip() for p in re.split(r"\s+-\s+",original) if p.strip()]
    if not parts:
        return {"search_title":"","artist_hint":None,"annotations":[]}
    first=parts[0]
    year=re.search(r"\s*\((?:19|20)\d{2}\)\s*$",first)
    annotations=[]
    if year:
        annotations.append(year.group().strip())
        first=first[:year.start()].strip()
    artist=None
    for part in parts[1:]:
        if re.fullmatch(r"\d{2,3}\s*bpm",part,re.I) or re.fullmatch(r"[A-G](?:#|b)?(?:maj|min|m)?",part,re.I):
            annotations.append(part)
        elif re.fullmatch(r"\((?:19|20)\d{2}\)",part):
            annotations.append(part)
        elif artist is None:
            artist=part
        else:
            annotations.append(part)
    if artist:
        artist_year=re.search(r"\s*\((?:19|20)\d{2}\)\s*$",artist)
        if artist_year:
            annotations.append(artist_year.group().strip())
            artist=artist[:artist_year.start()].strip()
        artist=re.sub(r"\s*\([A-Z]\)\s*$","",artist).strip()
    return {"search_title":first,"artist_hint":artist or None,"annotations":annotations}

def discover_by_title(title,*,transport=None):
    # Title-only candidates are hypotheses, not identification of a recording.
    import re
    cleaned=re.sub(r'["\\\\]',' ',title.strip())[:140]
    query='recording:"'+cleaned+'"'
    url="https://musicbrainz.org/ws/2/recording/?"+urllib.parse.urlencode({"query":query,"fmt":"json","limit":5})
    req=urllib.request.Request(url,headers={
        "Accept":"application/json","User-Agent":"EZStudioLabAssistant/1.6 (documentary-identity-preflight)"})
    try:
        if transport:
            body=transport(req)
        else:
            with urllib.request.urlopen(req,timeout=12) as res:
                body=json.loads(res.read(200000))
        if not isinstance(body,dict) or not isinstance(body.get("recordings"),list):
            return {"status":"invalid_response","candidates":[]}
        candidates=[]
        for rec in body["recordings"][:5]:
            if not isinstance(rec,dict):
                continue
            mid=rec.get("id")
            if not isinstance(mid,str) or not re.fullmatch(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}",mid):
                continue
            if str(rec.get("title") or "").strip().casefold()!=title.strip().casefold():
                continue
            artists=[]
            for credit in rec.get("artist-credit") or []:
                if isinstance(credit,dict):
                    name=credit.get("name") or (credit.get("artist") or {}).get("name")
                    if isinstance(name,str) and name.strip():
                        artists.append(name.strip()[:120])
            candidates.append({"url":"https://musicbrainz.org/recording/"+mid,
                               "artist_credit":artists,"duration_ms":rec.get("length")
                                   if type(rec.get("length")) is int else None})
        return {"status":"completed","candidates":candidates}
    except Exception as exc:
        return {"status":"unavailable","error_type":type(exc).__name__,"candidates":[]}

def execute(*,rows=None,discover=discover_by_title):
    if rows is None:
        try:
            rows=fetch_rows()
        except Exception as exc:
            return {"schema":"ezstudio.profile.identity-five-preflight.v1",
                    "status":"lab_read_failed","error_type":type(exc).__name__,
                    "lab_writes":0,"lab_jobs_created":0}
    eligible,picked=select_five(rows)
    report={"schema":"ezstudio.profile.identity-five-preflight.v1",
            "status":"selected" if picked else "insufficient_eligible_profiles",
            "sampling_scope":"current_lab_review_queue_only",
            "seed":SEED,"queue_count":len(rows),"eligible_count":len(eligible),
            "requested":5,"lab_writes":0,"lab_jobs_created":0,"identity_verified":False,
            "scientific_validation":False,"songs":[]}
    for item in picked:
        parsed=parse_filename_identity(item["title"])
        # Search normalized title without treating the filename artist as authoritative.
        catalogue=discover(parsed["search_title"])
        comparison=compare_durations(catalogue,item["duration"])
        candidates=[]
        for source,c in zip(catalogue.get("candidates",[]),comparison["candidates"]):
            candidates.append({"url":c["url"],"artist_candidates":source.get("artist_credit",[]),
                               "duration_relation":c["duration_relation"],
                               "duration_difference_seconds":c["difference_seconds"],
                               "identity_verified":False})
        report["songs"].append({"run_id":item["run_id"],"song_id":item["song_id"],
                                "title":item["title"],"catalogue_artist":item["catalogue_artist"] or None,
                                "search_title":parsed["search_title"],
                                "artist_hint_unverified":parsed["artist_hint"],
                                "filename_annotations":parsed["annotations"],
                                "documentary_status":catalogue.get("status"),
                                "recording_candidates":candidates,
                                "identity_verified":False,"lab_duration_available":True})
    if picked:
        report["status"]="documentary_candidates_only"
    return report

def main():
    result=execute()
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["status"]=="documentary_candidates_only" else 1

if __name__=="__main__":
    raise SystemExit(main())
