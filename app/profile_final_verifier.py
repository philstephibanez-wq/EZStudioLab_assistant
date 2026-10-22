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

def _matched_recording_sources(identity, research):
    """A source must be bound to the same artist/title; external research owns matching."""
    title = _clean(identity.get("title"))
    artist = _clean(identity.get("artist"))
    # A heuristic catalog identity may be confirmed by independent source matching.
    # Do not discard a genuine identity-matched recording solely because the
    # original title/artist split was heuristic.
    if not title or not artist:
        return []
    return [s for s in research.get("sources", []) if isinstance(s, dict)
            and s.get("available") is True and s.get("identity_relevant") is True
            and _url(s)]

def _evidence_for_assertion(item, source):
    """Return corroborating recording evidence, never infer absence from missing credit."""
    if source.get("source") != "MusicBrainz":
        return None
    value = _clean(item["value"]).casefold()
    key = item["key"]
    if key.startswith("instrument:"):
        credits = source.get("recording_credits") or []
        for credit in credits:
            if not isinstance(credit, dict) or credit.get("scope") != "recording":
                continue
            instruments = {_clean(v).casefold() for v in credit.get("instruments") or []}
            if value in instruments:
                return ("MusicBrainz — crédits de l'enregistrement", "recording_credit")
    if key == "genre":
        # Explicit recording-level taxonomy only. Artist/release tags are not proof.
        tags = {_clean(t).casefold() for t in source.get("recording_genres") or []}
        if value in tags:
            return ("MusicBrainz — genre de l'enregistrement", "recording_genre")
    if key == "lead_vocal" and value == "présent":
        credits = source.get("recording_credits") or []
        if any(isinstance(c, dict) and c.get("scope")=="recording"
               and c.get("role")=="vocal" and
               not any("backing" in _clean(x).casefold() or
                       "background" in _clean(x).casefold()
                       for x in c.get("instruments") or [])
               for c in credits):
            return ("MusicBrainz — crédit vocal de l'enregistrement", "recording_vocal_credit")
    if key == "backing_vocals" and value == "présent":
        credits = source.get("recording_credits") or []
        if any(isinstance(c, dict) and c.get("scope")=="recording" and
               any("backing vocal" in _clean(x).casefold() or "background vocal" in _clean(x).casefold()
                   for x in c.get("instruments") or [])
               for c in credits):
            return ("MusicBrainz — voix d'accompagnement créditées", "recording_backing_credit")
    return None

def verify_final_values(row, identity, research):
    """One conservative, separately persisted verdict for EVERY final musical assertion.

    Only explicit recording-level evidence can return BON. FAUX requires positive
    contradictory recording evidence and is intentionally not guessed here.
    """
    assertions = final_assertions(row)
    sources = _matched_recording_sources(identity, research)
    result=[]
    for item in assertions:
        decision="non_trouve"
        links=[]
        reference=None
        for source in sources:
            finding=_evidence_for_assertion(item, source)
            if not finding:
                continue
            safe_url=_url(source)
            if not safe_url:
                continue
            decision="bon"
            reference=item["value"]
            links=[{"title":finding[0],"url":safe_url,"evidence_type":finding[1]}]
            break
        result.append({**item,"verdict":decision,"confidence_pct":None,
                       "reference_value":reference,"sources":links,
                       "reason":"Source indépendante concordante" if links else
                                "Référence indépendante suffisante non trouvée"})
    return {"schema":"ezstudio.profile-final-verification.v1",
            "status":"completed","mode":"independent_recording_evidence",
            "verified_at":datetime.now(timezone.utc).isoformat(),
            "assertions":result,"scientific_preset_mutation_allowed":False}
