"""Qwen consultatif sur un module scientifique, jamais une écoute audio."""
import json
import urllib.request
from declarative_review import load_review_preset
from profile_trace import snap

def infer_module(provider, request):
    ready, reason=provider._health()
    if not ready: return {"status":"error","reason":reason or "model_unavailable"}
    preset,digest=load_review_preset("profile")
    prompt=("Analyse uniquement les résultats du module scientifique fourni, sans prétendre écouter l'audio. "
            "Les scores du moteur sont des hypothèses, pas des faits. Retourne un objet JSON: "
            "status (completed ou abstain), summary, uncertainty, supporting_evidence (liste), conflicting_evidence (liste). "
            "Ne valide aucun preset et indique toute insuffisance de preuves.")
    content=json.dumps(request,ensure_ascii=False,separators=(",",":"),allow_nan=False)
    bound=int(preset["context_max_chars"])
    if max(len(prompt)+len(content),len(prompt.encode())+len(content.encode()))>bound:
        return {"status":"error","reason":"module_context_over_budget","required_chars":len(content)}
    body={"model":"local","messages":[{"role":"system","content":prompt},{"role":"user","content":content}],
          "temperature":preset["temperature"],"max_tokens":preset["max_tokens"],"stream":False,
          "response_format":{"type":"json_object"}}
    snap("qwen.module.request",{"item_id":request["item_id"],"body":body,"preset_sha256":digest})
    req=urllib.request.Request(provider.endpoint+"/v1/chat/completions",data=json.dumps(body,ensure_ascii=False).encode(),
        headers={"Content-Type":"application/json","Accept":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=max(10.,float(provider.config.timeout_seconds))) as response:
            raw=response.read(2_000_000).decode("utf-8")
        snap("qwen.module.response",{"item_id":request["item_id"],"raw":raw})
        choice=json.loads(raw)["choices"][0]
        if choice.get("finish_reason")=="length":return {"status":"error","reason":"output_truncated"}
        parsed=provider._decode_local_json(choice["message"]["content"])
        if not isinstance(parsed,dict) or parsed.get("status") not in ("completed","abstain"):
            return {"status":"error","reason":"invalid_model_response"}
        return {"status":parsed["status"],"summary":str(parsed.get("summary") or "")[:2000],
                "uncertainty":str(parsed.get("uncertainty") or "")[:1000],
                "supporting_evidence":parsed.get("supporting_evidence") if isinstance(parsed.get("supporting_evidence"),list) else [],
                "conflicting_evidence":parsed.get("conflicting_evidence") if isinstance(parsed.get("conflicting_evidence"),list) else [],
                "model":str(provider.model_path),"preset_sha256":digest}
    except Exception as exc:
        snap("qwen.module.error",{"item_id":request["item_id"],"type":type(exc).__name__,"message":str(exc)[:200]})
        return {"status":"error","reason":type(exc).__name__}
