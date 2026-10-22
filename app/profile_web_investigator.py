"""Per-assertion autonomous web research; discovery is never a validated verdict.

Opt-in OpenAI Responses web_search transport. Raw web snippets and model statements
are discovery leads only. Provider citations are returned for a subsequent
first-party evidence verification step; no model output is trusted as proof.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.parse
from profile_final_verifier import final_assertions

def _https_url(value):
    try:
        p=urllib.parse.urlparse(str(value))
        return p.geturl() if p.scheme=="https" and p.hostname and not p.username and not p.password else None
    except Exception:
        return None

def research_each_assertion(row, identity, *, opener=None, api_key=None, model=None):
    assertions=final_assertions(row)
    token=api_key if api_key is not None else os.environ.get("OPENAI_API_KEY","")
    model=model or os.environ.get("EZS_PROFILE_WEB_MODEL","gpt-5.1")
    results=[]
    if not token:
        return {"status":"unavailable","reason":"web_provider_credentials_missing",
                "searched":0,"items":[{"key":a["key"],"value":a["value"],"status":"not_searched"} for a in assertions]}
    opener=opener or urllib.request.urlopen
    title=str(identity.get("title") or "")
    artist=str(identity.get("artist") or "")
    for a in assertions:
        if not title or not artist:
            results.append({"key":a["key"],"value":a["value"],"status":"identity_unavailable"})
            continue
        prompt={"track":{"title":title,"artist":artist},
                "item":{"key":a["key"],"label":a["label"],"lab_value":a["value"]},
                "task":"Independently investigate this exact item on the public web. Search across pertinent source families and document contradictions. Distinguish other covers, releases, recordings and artists. If unpublished, report absence of documentary evidence. Do not infer musical facts from LAB. Respond JSON with summary and evidence_leads only. Cite URLs returned by web tool, not invented URLs."}
        request={"model":model,"tools":[{"type":"web_search"}],
            "instructions":"You are an investigator, not an evaluator. Perform fresh web searches for the named musical track AND the specific assertion. No verdicts. Source-free statements are not proof. Output JSON only.",
            "input":json.dumps(prompt,ensure_ascii=False)}
        req=urllib.request.Request("https://api.openai.com/v1/responses",
            data=json.dumps(request,ensure_ascii=False).encode("utf-8"),
            headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
        try:
            with opener(req,timeout=90) as response:
                envelope=json.loads(response.read(1_000_000).decode("utf-8"))
            output=envelope.get("output") or []
            web_calls=sum(1 for event in output if isinstance(event,dict) and event.get("type")=="web_search_call")
            citations=[]
            text_parts=[]
            for event in output:
                if not isinstance(event,dict):
                    continue
                for part in event.get("content") or []:
                    if not isinstance(part,dict):
                        continue
                    if part.get("type")=="output_text":
                        text_parts.append(str(part.get("text") or "")[:4000])
                        for ann in part.get("annotations") or []:
                            if isinstance(ann,dict) and ann.get("type")=="url_citation":
                                url=_https_url(ann.get("url"))
                                if url and url not in citations:
                                    citations.append(url)
            results.append({"key":a["key"],"value":a["value"],
                "status":"discovered" if web_calls and citations else "unverified",
                "web_calls":web_calls,"citation_urls":citations[:12],
                "investigator_text":" ".join(text_parts)[:3500],
                "eligible_for_verdict":False})
        except Exception as exc:
            results.append({"key":a["key"],"value":a["value"],
                "status":"error","reason":type(exc).__name__,"eligible_for_verdict":False})
    return {"status":"completed","searched":len(results),"items":results,
            "independent_web_investigation":True,"automatic_verdicts":False}
