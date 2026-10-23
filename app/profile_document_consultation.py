"""Bounded, consultative Qwen reasoning over SOURCE-DERIVED public evidence.
No audio access, no scientific validation, no rights to promote evidence.
"""
from __future__ import annotations
import json
import os
import urllib.request

ENDPOINT = "http://127.0.0.1:8720"

def consult(identity, reviews, *, transport=None):
    """Return structured advisory insight; never mutate reviews/verdicts."""
    entries=[]
    for key, row in reviews.items():
        refs=[{"url":r.get("url"),"value":r.get("reference_value"),
               "attribution":r.get("attribution")} for r in row.get("references",[])[:3]]
        entries.append({"item":key,"lab_verdict":row.get("verdict"),
                        "external_candidate":row.get("reference_value"),
                        "references":refs})
    prompt={"identity":{"title":str(identity.get("title") or "")[:200],
                        "artist":str(identity.get("artist") or "")[:200]},
            "observations":entries}
    system=("Tu es un lecteur documentaire musical, pas un moteur de validation scientifique. "
            "Reponds exclusivement en francais sous JSON avec les champs status, summary, "
            "uncertainty et translation_notes (liste). Tu n'as pas ecoute l'audio, "
            "ni fait de recherches Web, ni effectue d'OCR. "
            "Les propositions documentaires ne prouvent pas l'identite de l'enregistrement. "
            "Ne produis aucun verdict bon/faux et n'invente aucune source. "
            "Si une reference est dans une autre langue, propose une traduction francaise "
            "en signalant qu'elle est generee par IA, non certifiee.")
    body={"model":"local","stream":False,"temperature":0,"max_tokens":350,
          "response_format":{"type":"json_object"},"messages":[
          {"role":"system","content":system},
          {"role":"user","content":json.dumps(prompt,ensure_ascii=True,allow_nan=False)[:9000]}]}
    raw=json.dumps(body,ensure_ascii=True).encode("ascii")
    request=urllib.request.Request(ENDPOINT+"/v1/chat/completions",data=raw,
                headers={"Content-Type":"application/json"},method="POST")
    try:
        if transport is None:
            with urllib.request.urlopen(request,timeout=45) as response:
                output=json.loads(response.read(500_000))
        else:
            output=transport(request)
        choice=output["choices"][0]
        if choice.get("finish_reason")=="length":
            raise ValueError("generation_truncated")
        message=json.loads(choice["message"]["content"])
        if not isinstance(message,dict) or message.get("status") not in ("completed","abstain"):
            raise ValueError("invalid_advisory")
        notes=message.get("translation_notes")
        return {"status":message["status"],"model":str(output.get("model") or "local"),
                "summary":str(message.get("summary") or "")[:2000],
                "uncertainty":str(message.get("uncertainty") or "")[:1000],
                "translation_notes":[str(x)[:400] for x in notes[:8]] if isinstance(notes,list) else [],
                "advisory_only":True,"promotes_verdict":False}
    except Exception as exc:
        return {"status":"error","reason":type(exc).__name__,"advisory_only":True,
                "promotes_verdict":False}
