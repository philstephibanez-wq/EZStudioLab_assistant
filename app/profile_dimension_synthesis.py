"""Advisory-only Qwen synthesis of five PROFILE dimensions from saved LAB/module observations.

No audio, no science engine, no web access, and no external-validation scoring.
"""
from __future__ import annotations
import hashlib
import json
import urllib.request
from ai_provider import _local_profile_evidence
from declarative_review import load_review_preset
from profile_trace import snap

KEYS = ("genre", "instrumentation", "lead_vocal", "backing_vocals", "choir")
CONTRIBUTORS = {
    "genre": ("semantic.clap-open-vocabulary", "semantic.panns-cnn14", "semantic.passt-audioset"),
    "instrumentation": ("semantic.clap-open-vocabulary", "semantic.panns-cnn14", "semantic.passt-audioset"),
    "lead_vocal": ("semantic.clap-open-vocabulary", "semantic.panns-cnn14", "semantic.passt-audioset"),
    "backing_vocals": ("semantic.clap-open-vocabulary", "semantic.panns-cnn14", "semantic.passt-audioset"),
    "choir": ("semantic.clap-open-vocabulary", "semantic.panns-cnn14", "semantic.passt-audioset"),
}
PROMPT = (
    "Tu es un critique musical consultatif, sans accès à l'audio ni au Web. "
    "Tu ne disposes QUE des observations LAB et des avis de moteurs fournis. "
    "Rédige EN FRANÇAIS cinq avis musicaux distincts, un par dimension. "
    "N'invente ni instrument ni genre ni présence de chœurs, n'affirme pas avoir écouté le son. "
    "Distingue observation et inférence : les scores des moteurs sont hétérogènes, non calibrés "
    "entre eux et ne constituent pas des probabilités d'une vérité musicale. "
    "Explique les contradictions si elles existent et les incertitudes ; sinon abstention explicite. "
    "Retourne UNIQUEMENT un objet JSON avec dimensions : genre, instrumentation, lead_vocal, "
    "backing_vocals, choir. Pour chacune : advisory (avis précis et concis en français), "
    "uncertainty (limites en français), contributors (liste d'identifiants des modules réellement transmis). "
    "Ne fournis AUCUN score de validation externe, aucune preuve ou source inventée, aucun changement de preset."
)

def _observations(row, sequential):
    view = _local_profile_evidence(row, {}).get("profile_view", {})
    results = sequential.get("results", [])
    brief = {}
    for item in results:
        name = item.get("item_id")
        assessment = item.get("assessment")
        if name not in CONTRIBUTORS["genre"] or not isinstance(assessment, dict):
            continue
        brief[name] = {
            "status": item.get("status"),
            "summary": str(assessment.get("summary") or "")[:500],
            "uncertainty": str(assessment.get("uncertainty") or "")[:280],
        }
    return {"lab_observations": view, "module_consultations": brief,
            "notice": "Avis consultatifs, pas une écoute ni une validation externe."}

def _validate(value, available):
    dimensions = value.get("dimensions") if isinstance(value, dict) else None
    if not isinstance(dimensions, dict) or set(dimensions) != set(KEYS):
        raise ValueError("dimension_advisory_keys_invalid")
    clean = {}
    for key in KEYS:
        entry = dimensions[key]
        if not isinstance(entry, dict):
            raise ValueError("dimension_advisory_entry_invalid:" + key)
        advisory = entry.get("advisory")
        uncertainty = entry.get("uncertainty")
        contributors = entry.get("contributors")
        if not isinstance(advisory, str) or not advisory.strip() or len(advisory) > 750:
            raise ValueError("dimension_advisory_missing:" + key)
        if not isinstance(uncertainty, str) or not uncertainty.strip() or len(uncertainty) > 500:
            raise ValueError("dimension_uncertainty_missing:" + key)
        if not isinstance(contributors, list) or len(contributors) > 3 or any(
            not isinstance(x, str) or x not in available for x in contributors
        ):
            raise ValueError("dimension_contributors_invalid:" + key)
        clean[key] = {"advisory": advisory.strip(), "uncertainty": uncertainty.strip(),
                      "contributors": list(dict.fromkeys(contributors)),
                      "advisory_only": True}
    return {"schema": "ezstudio.profile-dimension-advisories.v1",
            "status": "completed", "dimensions": clean, "external_validation": False}

def synthesize_dimensions(provider, row, sequential):
    available = {item.get("item_id") for item in sequential.get("results", [])
                 if item.get("status") == "completed"}
    observations = _observations(row, sequential)
    preset, preset_sha = load_review_preset("profile")
    body = {
        "model": "local",
        "messages": [{"role": "system", "content": PROMPT},
                     {"role": "user", "content": json.dumps(observations, ensure_ascii=False)}],
        "temperature": preset["temperature"], "max_tokens": min(1800, preset["max_tokens"]),
        "stream": False, "response_format": {"type": "json_object"},
    }
    # Fail closed if projected evidence exceeds configured MAIN declarative context.
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    if len(encoded) > int(preset["context_max_chars"]):
        return {"status": "abstain", "reason": "dimension_context_over_budget"}
    ready, reason = provider._health()
    if not ready:
        return {"status": "abstain", "reason": reason or "model_unavailable"}
    req = urllib.request.Request(
        provider.endpoint + "/v1/chat/completions", data=encoded,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=max(10., float(provider.config.timeout_seconds))) as response:
            raw = response.read(200_000).decode("utf-8")
        choice = json.loads(raw)["choices"][0]
        snap("qwen.dimension.response_metadata", {"finish_reason": choice.get("finish_reason"), "response_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(), "response_bytes": len(raw.encode("utf-8"))})
        if choice.get("finish_reason") == "length":
            raise ValueError("dimension_inference_truncated")
        parsed = provider._decode_local_json(choice["message"]["content"])
        if isinstance(parsed, dict):
            dim = parsed.get("dimensions")
            snap("qwen.dimension.response_shape", {"root_keys": sorted(str(k) for k in parsed), "dimension_keys": sorted(str(k) for k in dim) if isinstance(dim, dict) else None, "dimension_type": type(dim).__name__})
        outcome = _validate(parsed, available)
        snap("qwen.dimension.synthesis", {"status": "completed", "preset_sha256": preset_sha,
                                           "dimension_keys": list(outcome["dimensions"])})
        return outcome
    except Exception as exc:
        # ValueError messages are our fixed validation codes, not model prose.
        code = str(exc) if isinstance(exc, ValueError) and str(exc).startswith("dimension_") else type(exc).__name__
        snap("qwen.dimension.synthesis", {"status": "abstain", "reason": code})
        return {"schema": "ezstudio.profile-dimension-advisories.v1",
                "status": "abstain", "reason": code, "external_validation": False}
