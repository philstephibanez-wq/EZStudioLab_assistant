"""Echantillon de cinq chansons PROFILE LAB, lecture seule.

Source: GET /internal/analysis/desktop/profile/reviews/queue (analyses finies
eligibles pour revision, PAS tout l'historique). Aucune requete POST vers LAB.
Le rapport stdout contient uniquement identifiants, titres, valeurs de duree,
candidats MusicBrainz et relation de duree; jamais token/diagnostics/audio.
"""
from __future__ import annotations
import json
import os
import random
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from web_status import DEFAULT_TOKEN_FILE, _read_dpapi_token
from profile_musicbrainz_structured import discover_recordings
from profile_recording_reconciliation import compare_durations

BASE=os.getenv("EZSTUDIOLAB_ASSISTANT_BASE_URL","http://EZSTUDIO-MAIN:8702").rstrip("/")
DURATION_KEYS=("duration_seconds","duration_s","duration")
def _lab_duration(metrics):
    if not isinstance(metrics,dict):return None
    for name in DURATION_KEYS:
        value=metrics.get(name)
        if value is not None and not isinstance(value,(bool,dict,list)):
            return value
    return None

def sample(rows, *, seed=20261024, number=5):
    # Highest run per song, fully completed, with identity and usable duration.
    by_song={}
    for row in rows:
        if not isinstance(row,dict) or row.get("state")!="done":
            continue
        run=row.get("run_id")
        song=row.get("song_id")
        if type(run) is not int or type(song) is not int or run<=0 or song<=0:
            continue
        if not str(row.get("title") or "").strip() or not str(row.get("artist") or "").strip():
            continue
        duration=_lab_duration(row.get("metrics"))
        if compare_durations({"candidates":[]},duration)["lab_duration_available"] is not True:
            continue
        if song not in by_song or run>by_song[song]["run_id"]:
            by_song[song]={"run_id":run,"song_id":song,"title":str(row["title"])[:150],
                           "artist":str(row["artist"])[:150],"duration":duration}
    eligible=sorted(by_song.values(),key=lambda x:x["song_id"])
    if len(eligible)<number:
        return {"status":"insufficient_eligible_profiles","eligible_count":len(eligible),
                "required":number,"songs":[]}
    return {"status":"selected","eligible_count":len(eligible),"required":number,
            "songs":random.Random(seed).sample(eligible,number)}

def execute(*, fetch_queue=None, discover=discover_recordings):
    token=(os.getenv("EZSTUDIOLAB_ASSISTANT_TOKEN") or "").strip() or _read_dpapi_token(DEFAULT_TOKEN_FILE)
    if fetch_queue is None and not token:
        return {"status":"token_missing","lab_writes":0}
    if fetch_queue is None:
        url=BASE+"/internal/analysis/desktop/profile/reviews/queue?"+urllib.parse.urlencode({"limit":500})
        request=urllib.request.Request(url,headers={
            "X-EZScore-Analysis-Token":token,"Accept":"application/json"},method="GET")
        try:
            with urllib.request.urlopen(request,timeout=20) as response:
                body=json.loads(response.read(5_000_000))
        except Exception as exc:
            return {"status":"lab_read_failed","error_type":type(exc).__name__,"lab_writes":0}
    else:
        body=fetch_queue()
    if not isinstance(body,dict) or not isinstance(body.get("reviews"),list):
        return {"status":"lab_queue_invalid","lab_writes":0}
    picked=sample(body["reviews"])
    report={"schema":"ezstudio.profile.five-song-readonly.v1",
            "status":picked["status"],"sampling_scope":"completed_profiles_in_review_queue",
            "seed":20261024,"queue_count":len(body["reviews"]),
            "eligible_count":picked["eligible_count"],"requested":5,
            "lab_writes":0,"lab_jobs_created":0,"identity_verified":False,
            "scientific_validation":False,"songs":[]}
    if picked["status"]!="selected":return report
    for song in picked["songs"]:
        catalogue=discover(song["title"],song["artist"])
        reconciliation=compare_durations(catalogue,song["duration"])
        report["songs"].append({
            "run_id":song["run_id"],"song_id":song["song_id"],
            "title":song["title"],"artist":song["artist"],
            "lab_duration_seconds":reconciliation["candidates"][0]["lab_duration_seconds"]
                if reconciliation["candidates"] else
                compare_durations({"candidates":[{"duration_ms":None}]},song["duration"])["candidates"][0]["lab_duration_seconds"],
            "catalogue_status":catalogue.get("status"),
            "recording_candidates":reconciliation["candidates"],
            "identity_verified":False})
    report["status"]="completed" if all(
        song["catalogue_status"]=="completed" for song in report["songs"]) else "partial"
    return report

def main():
    try:out=execute()
    except Exception as exc:
        out={"status":"diagnostic_failed","error_type":type(exc).__name__,"lab_writes":0}
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out.get("status")=="completed" else 1

if __name__=="__main__":raise SystemExit(main())
