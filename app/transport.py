from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class AnalysisApiError(RuntimeError):
    pass


class AnalysisApiClient:
    """Small read-mostly client for the EZStudio analysis API.

    V1B deliberately does not expose claim/complete/fail methods. The historic
    claim endpoint selects the first queued job without worker capability or
    lease semantics; a 4 GB node must not claim work blindly.
    """

    def __init__(self, base_url: str, token: str, user_agent: str = "EZStudioLab_assistant/1B"):
        self.base_url = str(base_url).rstrip("/")
        self.token = str(token)
        self.user_agent = user_agent

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        body = None
        headers = {
            "Accept": "application/json",
            "X-EZScore-Analysis-Token": self.token,
            "User-Agent": self.user_agent,
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                if int(response.status) == 204 or not raw:
                    return {}
                parsed = json.loads(raw.decode("utf-8"))
                if not isinstance(parsed, dict):
                    raise AnalysisApiError(f"invalid_json_object:{path}")
                return parsed
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AnalysisApiError(f"HTTP {exc.code} {path}: {detail[:500]}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise AnalysisApiError(f"{path}: {type(exc).__name__}:{exc}") from exc

    def queue(self) -> list[dict[str, Any]]:
        payload = self.request("GET", "/internal/analysis/desktop/jobs/queue")
        jobs = payload.get("jobs") or []
        if not isinstance(jobs, list):
            raise AnalysisApiError("queue_jobs_not_list")
        return [row for row in jobs if isinstance(row, dict)]

    def hello(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/internal/analysis/desktop/hello", payload)

    def heartbeat(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/internal/analysis/desktop/heartbeat", payload)
