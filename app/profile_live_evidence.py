"""Conservative evidence comparison from live, retrieved public documents.

No generated reference, no simulated provider, no automatic scientific correction.
Only explicit measurements in pages mentioning the target title and artist.
"""
from __future__ import annotations
import re
from profile_musical_facts import evaluate_reference

def _norm(s):
    return re.sub(r"[^a-z0-9]+"," ",str(s).casefold()).strip()

def _reference_value(key,text):
    patterns={
        "tempo":r"\b(?:tempo|bpm)\s*[:=\-]?\s*(\d{2,3}(?:[.,]\d+)?)\s*(?:bpm)?\b|\b(\d{2,3}(?:[.,]\d+)?)\s*bpm\b",
        "meter":r"\b(?:time signature|meter|metre)\s*[:=\-]?\s*(\d{1,2}/\d{1,2})\b",
        "key":r"\b(?:musical key|key signature|key)\s*[:=\-]?\s*([A-G](?:#|b)?\s+(?:major|minor))\b"
    }
    pattern=patterns.get(key)
    if not pattern:return None
    values=[]
    for match in re.finditer(pattern,text,re.I):
        value=next((v for v in match.groups() if v),None)
        if value:
            value=value.replace(",",".").strip()
            if key=="tempo":
                if not 20<=float(value)<=350:continue
                value=value+" BPM"
            values.append(value)
    distinct={v.casefold():v for v in values}
    return next(iter(distinct.values())) if len(distinct)==1 else None

def evaluate_live_documents(assertion, identity, documents):
    """One credible explicit reference suffices; multiple disagreeing references abstain."""
    key=assertion["key"]
    title=_norm(identity.get("title"))
    artist=_norm(identity.get("artist"))
    accepted=[]
    for doc in documents:
        if doc.get("status")!="read":continue
        text=str(doc.get("text") or "")
        compact=_norm(text[:18000])
        if not title or not artist or title not in compact or artist not in compact:
            continue
        reference=_reference_value(key,text)
        if not reference:continue
        candidate={"source":"PublicWeb","url":doc["url"],"fact_scope":"recording",
                   "musical_facts":{key:{"explicit":True,"value":reference,"url":doc["url"]}}}
        finding=evaluate_reference(assertion,candidate)
        if finding:
            accepted.append({"url":doc["url"],"reference_value":reference,"verdict":finding["verdict"]})
    if not accepted:
        return {"verdict":"non_trouve","references":[],"reason":"Aucune mesure explicite et attribuable au titre et à l'artiste dans les pages lues"}
    conclusions={entry["verdict"] for entry in accepted}
    values={entry["reference_value"].casefold() for entry in accepted}
    if len(conclusions)!=1 or len(values)!=1:
        return {"verdict":"non_trouve","references":accepted,
                "reason":"Références contradictoires ou insuffisantes pour trancher"}
    return {"verdict":accepted[0]["verdict"],"references":accepted,
            "reference_value":accepted[0]["reference_value"],
            "reason":"Valeur explicite relevée dans "+str(len(accepted))+" page(s) attribuée(s) au titre et artiste ; attribution à la version exacte à confirmer"}
