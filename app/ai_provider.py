from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any

DEFAULT_SHARED_MODEL_ROOT = r"\\EZSTUDIO-MAIN\EZModels"
DEFAULT_OPENAI_MODEL = "gpt-6-luna"


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str = "off"
    model: str = DEFAULT_OPENAI_MODEL
    web_search: bool = False
    timeout_seconds: float = 60.0
    shared_model_root: str = DEFAULT_SHARED_MODEL_ROOT
    local_model_path: str | None = None
    local_cache_root: str | None = None
    local_endpoint: str = "http://127.0.0.1:8720"


class AIReviewProvider:
    provider_name = "off"

    def status(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "enabled": False, "model": None}

    def review_profile(self, row: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema": "EZStudioLab_assistant.ai-profile-review.v1",
            "status": "disabled",
            "provider": self.provider_name,
            "model": None,
            "confidence": 0.0,
            "summary": None,
            "dimensions": {},
            "sources": [],
        }


class DisabledAIProvider(AIReviewProvider):
    provider_name = "off"


class DisabledAIProviderWithReason(DisabledAIProvider):
    def __init__(self, reason: str, *, provider: str = "off") -> None:
        self.reason = reason
        self.provider_name = provider

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "enabled": False,
            "model": None,
            "reason": self.reason,
        }

    def review_profile(self, row: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
        payload = super().review_profile(row, research)
        payload["status"] = "unavailable"
        payload["provider"] = self.provider_name
        payload["reason"] = self.reason
        return payload


# PROFILE_LOCAL_CONTEXT_BUDGET_R1
# Deterministic reduction of LAB evidence. No model-generated claims or invented sources.
def _local_profile_compact(value, *, depth=0, max_depth=4, list_limit=8, text_limit=450):
    if depth > max_depth:
        return None
    if isinstance(value, str):
        return value[:text_limit] + (" [truncated]" if len(value) > text_limit else "")
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_local_profile_compact(v, depth=depth + 1, max_depth=max_depth,
                 list_limit=list_limit, text_limit=text_limit) for v in value[:list_limit]]
    if isinstance(value, dict):
        return {str(k): _local_profile_compact(v, depth=depth + 1, max_depth=max_depth,
                list_limit=list_limit, text_limit=text_limit)
                for k, v in list(value.items())[:30]
                if not str(k).startswith("_")}
    return str(value)[:text_limit]


def _local_profile_evidence(row, research):
    """PROFILE_EVIDENCE_R3B: an evidence-aware, bounded view of actual LAB paths.

    This is a view for the AI reviewer, not a replacement for scientific output.
    Unverified labels and score ranks are not independent reference evidence.
    """
    def obj(value):
        return value if isinstance(value, dict) else {}

    def short(value, limit=75):
        return value[:limit] if isinstance(value, str) else value if isinstance(value, (bool, int, float)) else None

    def pick(value, keys):
        data = obj(value)
        return {key: short(data[key]) for key in keys if key in data and short(data[key]) is not None}

    def labels(items, limit=3):
        return [pick(item, ('label', 'score', 'score_type', 'decision', 'support', 'source_score', 'rank_consensus'))
                for item in (items if isinstance(items, list) else [])[:limit] if isinstance(item, dict)]

    diag = obj(row.get('diagnostics'))
    profile = obj(diag.get('profile_view'))
    tagging = obj(diag.get('tagging'))
    genre = obj(profile.get('genre_hierarchy'))
    instrumentation = obj(profile.get('instrumentation'))
    vocals = obj(profile.get('vocal_profile'))
    dims = obj(vocals.get('dimensions'))
    musical = {
        'genre': {
            'status': short(genre.get('status')),
            'primary': pick(genre.get('primary'), ('genre_family', 'genre', 'subgenre', 'source_label', 'source_score', 'source_score_type')),
            'candidates': [pick(x, ('genre', 'genre_family', 'source_score')) for x in genre.get('candidates', [])[:3] if isinstance(x, dict)],
            'tagging': labels(tagging.get('genre'), 3),
        },
        'instrumentation': {
            'status': short(instrumentation.get('status')),
            'candidates': [pick(x, ('label', 'support', 'source_count', 'decision', 'rank_consensus'))
                           for x in instrumentation.get('candidates', [])[:5] if isinstance(x, dict)],
            'tagging': labels(tagging.get('instrumentation'), 4),
        },
        'vocals': {
            'status': short(vocals.get('status')),
            'dimensions': {
                key: {
                    **pick(dims.get(key), ('decision', 'engine_support', 'calibrated')),
                    'evidence': [pick(x, ('module', 'label', 'score', 'score_type', 'role'))
                                 for x in obj(dims.get(key)).get('evidence', [])[:2] if isinstance(x, dict)],
                }
                for key in ('lead_vocal', 'backing_vocals', 'vocal_harmonies', 'choir')
                if key in dims
            },
            'tagging': labels(tagging.get('voice'), 3),
        },
    }
    research = obj(research)
    # Explicitly keep reference metadata if present, but never raw website bodies.
    refs = {}
    for key in ('identity', 'genres', 'genre_labels', 'instruments', 'instrumentation', 'vocals', 'matches', 'references', 'sources'):
        value = research.get(key)
        if isinstance(value, list):
            refs[key] = [_local_profile_compact(x, max_depth=2, list_limit=2, text_limit=90)
                         for x in value[:2]]
        elif isinstance(value, dict):
            refs[key] = _local_profile_compact(value, max_depth=2, list_limit=2, text_limit=90)
    return {
        'identity': {key: short(row.get(key), 100) for key in ('title', 'artist', 'run_id')},
        'profile_view': musical,
        'public_research': refs,
        'evidence_notice': 'LAB results are predictions, not independent proof. Compare only if reliable public evidence is explicit. Otherwise choose not_scored.',
    }


def _local_profile_budget(evidence, system_prompt, *, max_chars=6500):
    # PROFILE_LOCAL_CONTEXT_BUDGET_R2: progressively bound only the copy sent to AI.
    # Prefer identity and structured music features over expansive diagnostic records.
    # A character/UTF-8 bound is conservative, not a tokenizer-based guarantee.
    def pack(value):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    def fits(value):
        raw = pack(value)
        return (len(raw) + len(system_prompt) <= max_chars and
                len(raw.encode("utf-8")) + len(system_prompt.encode("utf-8")) <= max_chars)

    if fits(evidence):
        return pack(evidence)

    identity = evidence.get("identity") or {}
    profile = evidence.get("profile_view") or {}
    research = evidence.get("public_research") or {}
    if not isinstance(profile, dict):
        profile = {}
    if not isinstance(research, dict):
        research = {}

    # Filtering by *meaningful field names*, not unbounded insertion order.
    # Preserve data already in the LAB payload; never fabricate a missing value.
    profile_priority = (
        "genre", "genres", "genre_labels", "instrumentation", "instruments",
        "lead_vocal", "lead_vocals", "backing_vocals", "choir", "vocals",
        "tempo", "bpm", "meter", "key", "rhythm", "semantic", "clap",
    )
    research_priority = (
        "identity", "genres", "genre_labels", "instruments", "instrumentation",
        "vocals", "matches", "references", "sources", "warnings",
    )
    selected_profile = {key: profile[key] for key in profile_priority if key in profile}
    selected_research = {key: research[key] for key in research_priority if key in research}
    notice = "Evidence truncated for local context; omissions must be not_scored."

    for depth, elements, text in ((3, 4, 180), (2, 3, 120), (2, 2, 80), (1, 1, 55)):
        candidate = {
            "identity": _local_profile_compact(identity, max_depth=2, list_limit=3, text_limit=120),
            "profile_view": _local_profile_compact(selected_profile, max_depth=depth, list_limit=elements, text_limit=text),
            "public_research": _local_profile_compact(selected_research, max_depth=depth, list_limit=elements, text_limit=text),
            "evidence_notice": notice,
        }
        if fits(candidate):
            return pack(candidate)

    # Fail closed rather than silently removing all evidence.
    raise ValueError("context_budget_exceeded")

class LocalAIProvider(AIReviewProvider):
    provider_name = "local"

    def __init__(self, config: AIProviderConfig) -> None:
        self.config = config
        self.canonical_model_path = str(config.local_model_path or "").strip()
        if not self.canonical_model_path:
            raise RuntimeError("local_ai_model_path_required")
        if not _is_model_under_root(config.shared_model_root, self.canonical_model_path):
            raise RuntimeError("local_ai_model_must_be_under_shared_model_root")
        cache_root = str(config.local_cache_root or "").strip() or str(Path(__file__).resolve().parents[1] / "runtime" / "models-cache")
        self.cache_root = cache_root
        relative = _model_relative_path(config.shared_model_root, self.canonical_model_path)
        self.model_path = str(Path(cache_root) / Path(*relative.parts))
        self.endpoint = str(config.local_endpoint or "http://127.0.0.1:8720").rstrip("/")

    def _health(self) -> tuple[bool, str | None]:
        req = urllib.request.Request(self.endpoint + "/health", headers={"Accept":"application/json"}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=min(3.0, max(1.0, float(self.config.timeout_seconds)))) as response:
                body = response.read(65536)
            payload = json.loads(body.decode("utf-8"))
            if isinstance(payload, dict):
                status = str(payload.get("status") or "").casefold()
                if status in {"ok","ready"} or payload.get("ok") is True:
                    return True, None
            return False, "local_ai_health_not_ready"
        except Exception as exc:
            return False, f"{type(exc).__name__}:{exc}"[:300]

    def status(self) -> dict[str, Any]:
        ready, reason = self._health()
        return {"provider":"local","enabled":ready,"model":self.model_path,"canonical_model":self.canonical_model_path,"cache_root":self.cache_root,"endpoint":self.endpoint,"shared_model_root":str(self.config.shared_model_root),"reason":reason}

    @staticmethod
    def _decode_local_json(content: str) -> dict[str, Any]:
        text = str(content or "").strip()
        if not text:
            raise ValueError("local_ai_content_missing")

        try:
            value = json.loads(text)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

        fenced = re.fullmatch(
            r"```(?:json)?\s*(\{.*\})\s*```",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if fenced:
            value = json.loads(fenced.group(1))
            if isinstance(value, dict):
                return value

        start = text.find("{")
        if start >= 0:
            value, _end = json.JSONDecoder().raw_decode(text[start:])
            if isinstance(value, dict):
                return value

        raise ValueError("local_ai_json_object_required")

    @staticmethod
    def _normalize_local_dimensions(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            # PROFILE_EVIDENCE_R3A: canonical singular key; reject conflicting aliases.
            normalized = dict(value)
            if "lead_vocals" in normalized:
                alias = normalized.pop("lead_vocals")
                if "lead_vocal" in normalized and normalized["lead_vocal"] != alias:
                    raise ValueError("ai_profile_review_lead_vocal_alias_conflict")
                normalized["lead_vocal"] = alias
            return normalized
        if not isinstance(value, list):
            raise ValueError("ai_profile_review_dimensions_object_required")

        known = {
            "genre",
            "instrumentation",
            "lead_vocal",
            "backing_vocals",
            "choir",
        }
        normalized: dict[str, Any] = {}
        for item in value:
            if not isinstance(item, dict):
                raise ValueError("ai_profile_review_dimensions_list_item_object_required")
            keys = [key for key in item if key in known]
            if len(keys) != 1:
                raise ValueError("ai_profile_review_dimension_name_required")
            name = keys[0]
            decision = item.get(name)
            if decision not in {"match", "mismatch", "uncertain", "not_scored"}:
                raise ValueError("ai_profile_review_dimension_decision_invalid")
            normalized[name] = {
                "decision": decision,
                "confidence": item.get("confidence"),
                "evidence": item.get("evidence"),
                "rationale": item.get("rationale"),
            }
        return normalized

    @staticmethod
    def _validate_local_result(value: Any, *, model: str) -> dict[str, Any]:
        if not isinstance(value, dict): raise ValueError("ai_profile_review_json_object_required")
        confidence = value.get("confidence", 0.0)
        if not isinstance(confidence, (int,float)): raise ValueError("ai_profile_review_confidence_required")
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0: raise ValueError("ai_profile_review_confidence_out_of_range")
        dimensions = LocalAIProvider._normalize_local_dimensions(value.get("dimensions"))
        summary = value.get("summary")
        if summary is not None and not isinstance(summary, str): raise ValueError("ai_profile_review_summary_string_required")
        sources = value.get("sources") if isinstance(value.get("sources"), list) else []
        return {"schema":"EZStudioLab_assistant.ai-profile-review.v1","status":"completed","provider":"local","model":model,"confidence":round(confidence,3),"summary":summary.strip() if isinstance(summary,str) else None,"dimensions":dimensions,"sources":[x for x in sources if isinstance(x,dict)][:20]}

    def review_profile(self, row: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
        ready, reason = self._health()
        if not ready:
            return {"schema":"EZStudioLab_assistant.ai-profile-review.v1","status":"unavailable","provider":"local","model":self.model_path,"confidence":0.0,"summary":None,"dimensions":{},"sources":[],"reason":reason or "local_ai_server_unavailable"}
        profile_view = (((row.get("diagnostics") or {}).get("profile_view")) if isinstance(row.get("diagnostics"),dict) else {}) or {}
        evidence = _local_profile_evidence(row, research)
        system_prompt = "You are the PROFILE review engine for EZStudioLab Assistant. Assess the LAB PROFILE analysis against supplied public evidence. Never modify or promote a scientific preset. Distinguish evidence from inference. Return ONLY one valid JSON object with keys summary, confidence, dimensions, sources. confidence must be a NUMBER from 0.0 to 1.0, never a word such as High or Low. dimensions MUST be a JSON OBJECT keyed only by genre, instrumentation, lead_vocal, backing_vocals and choir, never a list. Each dimension value MUST be an object with keys decision, confidence, evidence, rationale. decision is match, mismatch, uncertain, or not_scored. sources MUST be a JSON array. Do not use Markdown fences. Do not invent facts or sources."
        try:
            evidence_json = _local_profile_budget(evidence, system_prompt)
        except ValueError as exc:
            return {"schema":"EZStudioLab_assistant.ai-profile-review.v1","status":"error","provider":"local","model":self.model_path,"confidence":0.0,"summary":None,"dimensions":{},"sources":[],"reason":str(exc)}
        body = {"model":"local","messages":[{"role":"system","content":system_prompt},{"role":"user","content":evidence_json}],"temperature":0.1,"max_tokens":1200,"stream":False}
        req = urllib.request.Request(self.endpoint + "/v1/chat/completions", data=json.dumps(body,ensure_ascii=False).encode("utf-8"), headers={"Content-Type":"application/json","Accept":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=max(10.0,float(self.config.timeout_seconds))) as response:
                envelope = json.loads(response.read(2_000_000).decode("utf-8"))
            choices = envelope.get("choices") if isinstance(envelope,dict) else None
            if not isinstance(choices,list) or not choices: raise ValueError("local_ai_choices_missing")
            finish_reason = choices[0].get("finish_reason")
            if finish_reason == "length":
                raise ValueError("local_ai_output_truncated")
            message = choices[0].get("message") if isinstance(choices[0],dict) else None
            content = message.get("content") if isinstance(message,dict) else None
            if not isinstance(content,str) or not content.strip(): raise ValueError("local_ai_content_missing")
            value = self._decode_local_json(content)
            return self._validate_local_result(value, model=self.model_path)
        except urllib.error.HTTPError as exc:
            return {"schema":"EZStudioLab_assistant.ai-profile-review.v1","status":"error","provider":"local","model":self.model_path,"confidence":0.0,"summary":None,"dimensions":{},"sources":[],"reason":("local_ai_http_400_context_possible" if int(getattr(exc,'code',0)) == 400 else f"local_ai_http_{int(getattr(exc,'code',0))}")}
        except Exception as exc:
            return {"schema":"EZStudioLab_assistant.ai-profile-review.v1","status":"error","provider":"local","model":self.model_path,"confidence":0.0,"summary":None,"dimensions":{},"sources":[],"reason":f"{type(exc).__name__}:{exc}"[:500]}


class OpenAIResponsesProvider(AIReviewProvider):
    provider_name = "openai"

    def __init__(
        self,
        config: AIProviderConfig,
        *,
        api_key: str | None = None,
        endpoint: str = "https://api.openai.com/v1/responses",
    ) -> None:
        self.config = config
        self.api_key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
        self.endpoint = endpoint

    def status(self) -> dict[str, Any]:
        return {
            "provider": "openai",
            "enabled": bool(self.api_key),
            "model": self.config.model,
            "web_search": bool(self.config.web_search),
            "api_key_configured": bool(self.api_key),
        }

    @staticmethod
    def _extract_output_text(payload: dict[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        parts: list[str] = []
        for item in payload.get("output") or []:
            if not isinstance(item, dict):
                continue
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    continue
                if content.get("type") == "output_text":
                    value = content.get("text")
                    if isinstance(value, str) and value.strip():
                        parts.append(value.strip())
        return "\n".join(parts).strip()

    @staticmethod
    def _validate_result(
        value: Any,
        *,
        model: str,
        response_id: str | None,
        usage: Any,
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("ai_profile_review_json_object_required")
        confidence = value.get("confidence", 0.0)
        if not isinstance(confidence, (int, float)):
            raise ValueError("ai_profile_review_confidence_required")
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("ai_profile_review_confidence_out_of_range")
        dimensions = value.get("dimensions")
        if not isinstance(dimensions, dict):
            raise ValueError("ai_profile_review_dimensions_object_required")
        summary = value.get("summary")
        if summary is not None and not isinstance(summary, str):
            raise ValueError("ai_profile_review_summary_string_required")
        sources = value.get("sources")
        if not isinstance(sources, list):
            sources = []
        return {
            "schema": "EZStudioLab_assistant.ai-profile-review.v1",
            "status": "completed",
            "provider": "openai",
            "model": model,
            "confidence": round(confidence, 3),
            "summary": summary.strip() if isinstance(summary, str) else None,
            "dimensions": dimensions,
            "sources": [x for x in sources if isinstance(x, dict)][:20],
            "response_id": response_id,
            "usage": usage if isinstance(usage, dict) else {},
        }

    def review_profile(self, row: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            return {
                "schema": "EZStudioLab_assistant.ai-profile-review.v1",
                "status": "unavailable",
                "provider": "openai",
                "model": self.config.model,
                "confidence": 0.0,
                "summary": None,
                "dimensions": {},
                "sources": [],
                "reason": "openai_api_key_missing",
            }

        profile_view = (
            ((row.get("diagnostics") or {}).get("profile_view"))
            if isinstance(row.get("diagnostics"), dict)
            else {}
        ) or {}
        evidence = {
            "identity": {
                "title": row.get("title"),
                "artist": row.get("artist"),
                "run_id": row.get("run_id"),
            },
            "profile_view": profile_view,
            "public_research": research,
        }
        instructions = (
            "You are the PROFILE review engine for EZStudioLab Assistant. "
            "Assess the LAB PROFILE analysis against the supplied public evidence. "
            "Never modify or promote a scientific preset. Distinguish evidence from inference. "
            "Return ONLY one valid JSON object with keys: summary (string), confidence (0..1), "
            "dimensions (object), sources (array). dimensions should contain genre, instrumentation, "
            "lead_vocal, backing_vocals and choir when evidence permits. Each dimension should use "
            "decision, confidence, evidence and rationale. Use decision values match, mismatch, "
            "uncertain, or not_scored. Do not invent facts or sources."
        )
        request_payload: dict[str, Any] = {
            "model": self.config.model,
            "instructions": instructions,
            "input": json.dumps(evidence, ensure_ascii=False, separators=(",", ":")),
        }
        if self.config.web_search:
            request_payload["tools"] = [{"type": "web_search"}]

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                req,
                timeout=max(10.0, float(self.config.timeout_seconds)),
            ) as response:
                body = response.read(2_000_000)
            envelope = json.loads(body.decode("utf-8"))
            if not isinstance(envelope, dict):
                raise ValueError("openai_response_object_required")
            text = self._extract_output_text(envelope)
            if not text:
                raise ValueError("openai_response_output_text_missing")
            value = json.loads(text)
            return self._validate_result(
                value,
                model=self.config.model,
                response_id=str(envelope.get("id")) if envelope.get("id") is not None else None,
                usage=envelope.get("usage"),
            )
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read(4096).decode("utf-8", errors="replace")
            except Exception:
                pass
            return {
                "schema": "EZStudioLab_assistant.ai-profile-review.v1",
                "status": "error",
                "provider": "openai",
                "model": self.config.model,
                "confidence": 0.0,
                "summary": None,
                "dimensions": {},
                "sources": [],
                "reason": f"openai_http_{int(getattr(exc, 'code', 0))}",
                "detail": detail[:1000],
            }
        except Exception as exc:
            return {
                "schema": "EZStudioLab_assistant.ai-profile-review.v1",
                "status": "error",
                "provider": "openai",
                "model": self.config.model,
                "confidence": 0.0,
                "summary": None,
                "dimensions": {},
                "sources": [],
                "reason": f"{type(exc).__name__}:{exc}"[:500],
            }


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "")).strip().casefold()
    if not raw:
        return bool(default)
    return raw in {"1", "true", "yes", "on"}


def _model_relative_path(root: str, model: str):
    from pathlib import PureWindowsPath
    rt, mt = str(root).strip(), str(model).strip()
    if rt.startswith("\\\\") or "\\" in rt or ":" in rt:
        rp, mp = PureWindowsPath(rt), PureWindowsPath(mt)
    else:
        rp, mp = Path(rt), Path(mt)
    try:
        return mp.relative_to(rp)
    except Exception as exc:
        raise RuntimeError("local_ai_model_must_be_under_shared_model_root") from exc

def _is_model_under_root(root: str, model: str) -> bool:
    try:
        _model_relative_path(root, model); return True
    except Exception:
        return False

def config_from_env() -> AIProviderConfig:
    provider = str(os.getenv("EZSTUDIOLAB_AI_PROVIDER", "off")).strip().casefold()
    if provider not in {"off", "openai", "local"}:
        raise RuntimeError(f"unsupported_ai_provider:{provider}")
    model = str(os.getenv("EZSTUDIOLAB_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    try:
        timeout = float(os.getenv("EZSTUDIOLAB_AI_TIMEOUT_SECONDS", "60"))
    except ValueError:
        timeout = 60.0
    return AIProviderConfig(
        provider=provider,
        model=model,
        web_search=_env_bool("EZSTUDIOLAB_OPENAI_WEB_SEARCH", False),
        timeout_seconds=max(10.0, min(180.0, timeout)),
        shared_model_root=(
            str(os.getenv("EZSTUDIO_SHARED_MODEL_ROOT", DEFAULT_SHARED_MODEL_ROOT)).strip()
            or DEFAULT_SHARED_MODEL_ROOT
        ),
        local_model_path=(str(os.getenv("EZSTUDIOLAB_LOCAL_AI_MODEL", "")).strip() or None),
        local_cache_root=(str(os.getenv("EZSTUDIOLAB_LOCAL_AI_CACHE_ROOT", "")).strip() or None),
        local_endpoint=(
            str(os.getenv("EZSTUDIOLAB_LOCAL_AI_ENDPOINT", "http://127.0.0.1:8720")).strip()
            or "http://127.0.0.1:8720"
        ),
    )


def build_ai_provider_from_env() -> AIReviewProvider:
    config = config_from_env()
    if config.provider == "off":
        return DisabledAIProvider()
    if config.provider == "openai":
        return OpenAIResponsesProvider(config)
    if not config.local_model_path:
        return DisabledAIProviderWithReason("local_ai_model_path_required", provider="local")
    try:
        return LocalAIProvider(config)
    except Exception as exc:
        return DisabledAIProviderWithReason(f"{type(exc).__name__}:{exc}", provider="local")


def ai_provider_status() -> dict[str, Any]:
    provider = build_ai_provider_from_env()
    status = provider.status()
    status["schema"] = "EZStudioLab_assistant.ai-provider-status.v1"
    status["shared_model_root"] = config_from_env().shared_model_root
    return status
