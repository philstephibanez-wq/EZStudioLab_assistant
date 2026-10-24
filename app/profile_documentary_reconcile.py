"""Documentary reconciliation: lexical corroboration is not a verified recording."""
from __future__ import annotations
from difflib import SequenceMatcher
from profile_adaptive_keywords import terms

def _similar(a,b):
    x=" ".join(terms(a)); y=" ".join(terms(b))
    if not x or not y:
        return False
    if x==y:
        return True
    # Order of first/last name may be inverted; spelling tolerance is conservative.
    return SequenceMatcher(None," ".join(sorted(x.split()))," ".join(sorted(y.split()))).ratio()>=0.78

def reconcile(title,artist_hint,web,recordings):
    evidence=[]
    for hit in web.get("candidates",[])[:8]:
        name=str(hit.get("title") or "")
        has_title=len(set(terms(title)) & set(terms(name)))>=min(2,len(set(terms(title))))
        if not has_title:
            continue
        evidence.append({"url":hit.get("url"),"artist_hint_supported":bool(artist_hint and
                         _similar(artist_hint,name)),"source_kind":"search_snippet_only"})
    artist_candidates=sorted({a for rec in recordings for a in rec.get("artist_candidates",[])
                              if isinstance(a,str) and a.strip()})
    matched=[a for a in artist_candidates if artist_hint and _similar(artist_hint,a)]
    return {"status":"hypotheses_only","work_title_supported_by_snippets":bool(evidence),
            "artist_hint":artist_hint,"musicbrainz_artist_matches":matched,
            "musicbrainz_other_artists":[a for a in artist_candidates if a not in matched],
            "documentary_links":evidence[:8],
            "work_identity_verified":False,"performer_identity_verified":False,
            "recording_identity_verified":False}
