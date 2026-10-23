"""Bounded, consultative Qwen reasoning over SOURCE-DERIVED public evidence.
No audio access, no scientific validation, no rights to promote evidence.
"""
from __future__ import annotations
import json
import re
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
        content=str(choice["message"].get("content") or "").strip()
        if not content:
            raise ValueError("empty_advisory")
        try:
            message=json.loads(content)
        except json.JSONDecodeError:
            fenced=re.fullmatch(r"```(?:json)?\s*(\{.*\})\s*```",content,re.I|re.S)
            if not fenced:
                raise ValueError("invalid_json_advisory")
            message=json.loads(fenced.group(1))
        if not isinstance(message,dict):
            raise ValueError("invalid_advisory_object")
        raw_status=message.get("status")
        # LLM "confirmed" never means recording identity is confirmed.
        if raw_status in ("completed","abstain"):
            status=raw_status
        elif isinstance(raw_status,str):
            status="abstain"
        elif isinstance(message.get("summary"),str) or isinstance(message.get("uncertainty"),str):
            status="abstain"
        else:
            raise ValueError("invalid_advisory_status")
        summary=str(message.get("summary") or "").strip()
        uncertainty=str(message.get("uncertainty") or "").strip()
        if not summary and not uncertainty:
            raise ValueError("empty_advisory_fields")
        # An ordinal label (low/medium/high) is not a documented uncertainty.
        if uncertainty.casefold() in ("low","medium","high","faible","moyen","eleve","élevé"):
            uncertainty="Niveau qualitatif genere sans justification documentaire : "+uncertainty
            status="abstain"
        notes=message.get("translation_notes")
        if isinstance(notes,str):
            notes=[notes] if notes.strip() else []
        elif not isinstance(notes,list):
            notes=[]
        return {"status":status,"model":str(output.get("model") or "local"),
                "summary":summary[:2000],
                "uncertainty":uncertainty[:1000],
                "translation_notes":[str(x)[:400] for x in notes[:8]],
                "advisory_only":True,"promotes_verdict":False,"raw_status":raw_status}
    except Exception as exc:
        return {"status":"error","reason":type(exc).__name__,"advisory_only":True,
                "promotes_verdict":False}
