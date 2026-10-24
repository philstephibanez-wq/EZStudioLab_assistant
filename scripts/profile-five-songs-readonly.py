"""Echantillon de cinq chansons PROFILE LAB, lecture seule.

Source: GET /internal/analysis/desktop/profile/reviews/queue (analyses finies
eligibles pour revision, PAS tout l'historique). Aucune requete POST vers LAB.
Le rapport stdout contient uniquement identifiants, titres, valeurs de duree,
candidats MusicBrainz et relation de duree; jamais token/diagnostics/audio.
"""
from __future__ import annotations
import json
import urllib.error
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

def exclusion_diagnostic(rows):
    """Aggregate eligibility reasons without exposing values or private metrics."""
    reasons={"not_completed":0,"invalid_identifiers":0,"missing_title_or_artist":0,
             "missing_duration":0,"unrecognized_duration":0,"eligible_rows":0}
    duration_keys={}
    for row in rows:
        if not isinstance(row,dict):
            reasons["invalid_identifiers"]+=1
            continue
        if row.get("state")!="done":
            reasons["not_completed"]+=1
            continue
        if type(row.get("run_id")) is not int or type(row.get("song_id")) is not int or row["run_id"]<=0 or row["song_id"]<=0:
            reasons["invalid_identifiers"]+=1
            continue
        if not str(row.get("title") or "").strip() or not str(row.get("artist") or "").strip():
            reasons["missing_title_or_artist"]+=1
            continue
        metrics=row.get("metrics")
        if isinstance(metrics,dict):
            for key in DURATION_KEYS:
                if key in metrics:
                    duration_keys[key]=duration_keys.get(key,0)+1
        duration=_lab_duration(metrics)
        if duration is None:
            reasons["missing_duration"]+=1
        elif not compare_durations({"candidates":[]},duration)["lab_duration_available"]:
            reasons["unrecognized_duration"]+=1
        else:
            reasons["eligible_rows"]+=1
    return {"exclusion_counts":reasons,"known_duration_fields_present":duration_keys,
            "duration_metrics_type_counts":{
                "object":sum(isinstance(r.get("metrics"),dict) for r in rows if isinstance(r,dict)),
                "non_object":sum(not isinstance(r.get("metrics"),dict) for r in rows if isinstance(r,dict))}}

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
        # The queue embeds large diagnostic objects; request a bounded candidate pool.
        # This is a random sample of this pool, NOT a uniform sample of all LAB runs.
        queue_limit=20
        max_response_bytes=32_000_000
        url=BASE+"/internal/analysis/desktop/profile/reviews/queue?"+urllib.parse.urlencode({"limit":queue_limit})
        request=urllib.request.Request(url,headers={
            "X-EZScore-Analysis-Token":token,"Accept":"application/json"},method="GET")
        try:
            with urllib.request.urlopen(request,timeout=20) as response:
                content_type=str(response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                raw=response.read(max_response_bytes+1)
                http_status=response.status
            if len(raw)>max_response_bytes:
                return {"status":"lab_response_too_large","http_status":http_status,
                        "queue_limit":queue_limit,"response_limit_bytes":max_response_bytes,"lab_writes":0}
            if content_type!="application/json" and not content_type.endswith("+json"):
                return {"status":"lab_non_json_response","http_status":http_status,
                        "content_type":content_type[:80],"response_bytes":len(raw),
                        "lab_writes":0}
            try:
                body=json.loads(raw)
            except (json.JSONDecodeError,UnicodeDecodeError):
                return {"status":"lab_invalid_json","http_status":http_status,
                        "content_type":content_type[:80],"response_bytes":len(raw),
                        "lab_writes":0}
        except urllib.error.HTTPError as exc:
            return {"status":"lab_http_error","http_status":exc.code,
                    "content_type":str(exc.headers.get("Content-Type") or "").split(";")[0][:80],
                    "lab_writes":0}
        except Exception as exc:
            return {"status":"lab_read_failed","error_type":type(exc).__name__,"lab_writes":0}
    else:
        body=fetch_queue()
    if not isinstance(body,dict) or not isinstance(body.get("reviews"),list):
        return {"status":"lab_queue_invalid","lab_writes":0}
    # Immediately project the bounded response to minimum metadata; never retain
    # full scientific diagnostics in the test report or send them to MusicBrainz.
    rows=[{k:row.get(k) for k in ("run_id","song_id","state","title","artist","metrics")}
          for row in body["reviews"] if isinstance(row,dict)]
    del body
    diagnostic=exclusion_diagnostic(rows)
    picked=sample(rows)
    report={"schema":"ezstudio.profile.five-song-readonly.v1",
            "status":picked["status"],"sampling_scope":"completed_profiles_in_review_queue",
            "seed":20261024,"queue_count":len(rows),
            "queue_limit":20 if fetch_queue is None else None,
            "eligible_count":picked["eligible_count"],"requested":5,
            "eligibility_diagnostic":diagnostic,
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
