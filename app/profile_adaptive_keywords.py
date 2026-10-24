"""Bounded adaptive keyword discovery, never a scientific or recording-identity verdict."""
from __future__ import annotations
import re
import unicodedata
from profile_public_web import search

STOP={"le","la","les","de","des","du","d","l","un","une","the","a","et"}
def terms(text):
    value=unicodedata.normalize("NFKD",str(text or "").casefold())
    value="".join(c for c in value if not unicodedata.combining(c))
    return [x for x in re.findall(r"[a-z0-9]+",value) if x not in STOP and len(x)>1]

def queries(title,artist_hint=None):
    title_words=terms(title)
    artist_words=terms(artist_hint)
    proposals=[]
    def add(words):
        q=" ".join(words)
        if q and q not in proposals:
            proposals.append(q)
    # Broad combinations are intentionally non-exact, never quoted.
    if len(title_words)>1:
        for name in artist_words:
            add(title_words[-2:]+[name])
    add(title_words)
    if artist_words:
        add(title_words+artist_words[:1])
        add(title_words+artist_words)
    return proposals[:7]

def matching_hits(title,artist_hint=None,*,searcher=search,maximum=4):
    tried=[]
    found=[]
    errors=[]
    seen=set()
    for q in queries(title,artist_hint)[:maximum]:
        tried.append(q)
        try:
            hits=searcher(q,max_results=5)
        except Exception as exc:
            errors.append({"query":q,"error_type":type(exc).__name__})
            continue
        for hit in hits:
            if not isinstance(hit,dict):
                continue
            url=hit.get("url")
            if not isinstance(url,str) or not url.startswith("https://") or url in seen:
                continue
            corpus=set(terms(str(hit.get("title") or "")+" "+str(hit.get("snippet") or "")))
            overlap=len(corpus.intersection(terms(title)))
            if overlap<min(2,len(terms(title))):
                continue
            seen.add(url)
            found.append({"url":url,"title":str(hit.get("title") or "")[:180],
                "title_keyword_overlap":overlap,"artist_hint_matched":bool(
                    set(terms(artist_hint)).intersection(corpus)),
                "identity_verified":False,"evidence_eligible":False})
        if len(found)>=3:
            break
    return {"status":"candidates_found" if found else "search_unavailable" if errors else "no_candidates",
            "queries":tried,"candidates":found[:8],"technical_errors":errors,
            "identity_verified":False,"advisory_only":True}
