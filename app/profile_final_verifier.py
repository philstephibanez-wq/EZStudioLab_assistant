"""Independent verification of LAB final musical assertions only.

The verifier never receives, imports or inspects scientific module outputs.
Evidence comes exclusively from identity-matched recording-scoped references.
"""
from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import urlparse

DECISIONS = {"bon", "faux", "non_trouve"}
UNKNOWN = {"", "possible", "inconclusive", "unknown", "unavailable", "undetermined", "not_scored", "non déterminé"}
INSTRUMENT_ALIASES = {
    "guitar": "guitar", "electric guitar": "electric guitar",
    "acoustic guitar": "acoustic guitar", "bass guitar": "bass guitar",
    "piano": "piano", "organ": "organ", "drums": "drums",
    "drum kit": "drums", "violin": "violin", "cello": "cello",
    "trumpet": "trumpet", "saxophone": "saxophone",
}
def _clean(value):
    return str(value or "").strip()
def _valid(value):
    return bool(_clean(value)) and _clean(value).casefold() not in UNKNOWN
def _url(source):
    url = source.get("url")
    if not isinstance(url, str):
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    return url

def final_assertions(row):
    """Explicit allowlist: absolutely no raw diagnostic/module/preset leaves this boundary."""
    view = (row.get("diagnostics") or {}).get("profile_view") or {}
    metrics = row.get("metrics") or {}
    vox = (view.get("vocal_profile") or {}).get("dimensions") or {}
    out = []
    def put(key, label, value):
        if _valid(value):
            out.append({"key":key,"label":label,"value":_clean(value)})
    bpm = (metrics.get("tempo") or {}).get("bpm")
    if isinstance(bpm, (int, float)) and not isinstance(bpm, bool) and 20 <= bpm <= 350:
        put("tempo", "Tempo", f"{bpm:.1f} BPM")
    meter = metrics.get("time_signature") or {}
    put("meter","Mesure",meter.get("label") or meter.get("suggested_label"))
    put("key","Tonalité",(view.get("tonal") or {}).get("label") or (metrics.get("key") or {}).get("label"))
    put("genre","Genre musical",((view.get("genre_hierarchy") or {}).get("primary") or {}).get("genre"))
    for i, item in enumerate((view.get("instrumentation") or {}).get("candidates") or []):
        if isinstance(item, dict) and _valid(item.get("label")):
            put("instrument:"+str(i),"Instrument",item["label"])
    for key,label in (("lead_vocal","Voix principale"),("backing_vocals","Voix d'accompagnement"),
                      ("vocal_harmonies","Harmonies vocales"),("choir","Chœurs")):
        decision = (vox.get(key) or {}).get("decision")
        if decision in ("present","detected"):
            put(key,label,"présent")
        elif decision == "absent":
            put(key,label,"absent")
    return out

def verify_final_values(row, identity, research):
    """Conservative deterministic verdicts: never convert absence of reference to FAUX."""
    assertions = final_assertions(row)
    sources = [s for s in research.get("sources", []) if isinstance(s,dict)
               and s.get("available") is True and s.get("identity_relevant") is True and _url(s)]
    result=[]
    for item in assertions:
        key,value = item["key"],item["value"]
        decision="non_trouve"; links=[]; reference=None
        for source in sources:
            # A recording-level credit can establish presence, never absence.
            if not key.startswith("instrument:") or source.get("source") != "MusicBrainz":
                continue
            target = _clean(value).casefold()
            credits = source.get("recording_credits") or []
            found = any(
                isinstance(credit,dict) and credit.get("scope")=="recording"
                and any(_clean(v).casefold()==target for v in credit.get("instruments") or [])
                for credit in credits
            )
            if found:
                decision="bon"; reference=value
                links=[{"title":"MusicBrainz — crédit de l'enregistrement","url":_url(source),
                        "evidence_type":"recording_performer_credit"}]
                break
        result.append({**item,"verdict":decision,"confidence_pct":None,
                       "reference_value":reference,"sources":links})
    return {"schema":"ezstudio.profile-final-verification.v1",
            "status":"completed","mode":"independent_recording_evidence",
            "verified_at":datetime.now(timezone.utc).isoformat(),
            "assertions":result,"scientific_preset_mutation_allowed":False}
