from __future__ import annotations

import json
import os
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


class LocalAIProvider(AIReviewProvider):
    provider_name = "local"

    def __init__(self, config: AIProviderConfig) -> None:
        self.config = config
        root = Path(config.shared_model_root)
        model_path = Path(config.local_model_path or "")
        try:
            root_resolved = root.resolve()
            model_resolved = model_path.resolve()
            model_resolved.relative_to(root_resolved)
        except Exception as exc:
            raise RuntimeError("local_ai_model_must_be_under_shared_model_root") from exc
        self.model_path = model_resolved

    def status(self) -> dict[str, Any]:
        return {
            "provider": "local",
            "enabled": False,
            "model": str(self.model_path),
            "shared_model_root": str(self.config.shared_model_root),
            "reason": "local_provider_not_implemented",
        }

    def review_profile(self, row: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema": "EZStudioLab_assistant.ai-profile-review.v1",
            "status": "unavailable",
            "provider": "local",
            "model": str(self.model_path),
            "confidence": 0.0,
            "summary": None,
            "dimensions": {},
            "sources": [],
            "reason": "local_provider_not_implemented",
        }


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
