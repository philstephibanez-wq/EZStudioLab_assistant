from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from ai_provider import (
    AIProviderConfig,
    DisabledAIProvider,
    LocalAIProvider,
    OpenAIResponsesProvider,
    ai_provider_status,
    build_ai_provider_from_env,
)
from profile_auto_review import enrich_review_payload_with_ai


class V13JAIProviderContract(unittest.TestCase):
    def test_default_provider_is_explicitly_off(self):
        with patch.dict(os.environ, {}, clear=True):
            provider = build_ai_provider_from_env()
            self.assertIsInstance(provider, DisabledAIProvider)
            status = ai_provider_status()
        self.assertEqual(status["provider"], "off")
        self.assertFalse(status["enabled"])
        self.assertEqual(status["shared_model_root"], r"\\EZSTUDIO-MAIN\EZModels")

    def test_openai_missing_key_is_visible_not_silent(self):
        env = {
            "EZSTUDIOLAB_AI_PROVIDER": "openai",
            "EZSTUDIOLAB_OPENAI_MODEL": "gpt-6-luna",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = build_ai_provider_from_env()
            result = provider.review_profile(
                {"run_id": 1, "title": "Song", "artist": "Artist"},
                {"sources": []},
            )
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "openai_api_key_missing")
        self.assertEqual(result["provider"], "openai")

    def test_local_model_must_live_under_main_shared_root(self):
        cfg = AIProviderConfig(
            provider="local",
            shared_model_root=r"\\EZSTUDIO-MAIN\EZModels",
            local_model_path=r"C:\models\forbidden.gguf",
        )
        with self.assertRaises(RuntimeError):
            LocalAIProvider(cfg)

    def test_ai_result_is_advisory_and_never_promotes_preset(self):
        payload = {
            "run_id": 42,
            "revision_key": "profile-42-assistant-auto-v1",
            "reviewer": "assistant-auto",
            "status": "completed",
            "sources": [{"name": "MusicBrainz"}],
            "consensus": {"genre_labels": ["rock"]},
            "comparison": {"genre": {"decision": "match"}},
            "confidence": 0.81,
        }
        ai = {
            "schema": "EZStudioLab_assistant.ai-profile-review.v1",
            "status": "completed",
            "provider": "openai",
            "model": "gpt-6-luna",
            "confidence": 0.88,
            "summary": "Evidence broadly agrees.",
            "dimensions": {
                "genre": {
                    "decision": "match",
                    "confidence": 0.9,
                    "evidence": ["MusicBrainz"],
                    "rationale": "Public genre evidence agrees.",
                }
            },
            "sources": [],
            "response_id": "resp_test",
        }
        enriched = enrich_review_payload_with_ai(payload, ai)
        self.assertEqual(enriched["revision_key"], "profile-42-assistant-ai-v1")
        self.assertEqual(enriched["reviewer"], "assistant-auto+ai")
        self.assertEqual(enriched["comparison"]["genre"]["decision"], "match")
        self.assertTrue(enriched["comparison"]["assistant_ai"]["advisory_only"])
        self.assertFalse(
            enriched["comparison"]["assistant_ai"]["automatic_preset_promotion_allowed"]
        )

    def test_openai_request_can_enable_web_search(self):
        cfg = AIProviderConfig(
            provider="openai",
            model="gpt-6-luna",
            web_search=True,
            timeout_seconds=30,
        )
        provider = OpenAIResponsesProvider(cfg, api_key="test-key")
        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def read(self, limit):
                return json.dumps({
                    "id": "resp_123",
                    "output": [{
                        "type": "message",
                        "content": [{
                            "type": "output_text",
                            "text": json.dumps({
                                "summary": "OK",
                                "confidence": 0.8,
                                "dimensions": {},
                                "sources": [],
                            }),
                        }],
                    }],
                    "usage": {"input_tokens": 10, "output_tokens": 10},
                }).encode("utf-8")

        def fake_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode("utf-8"))
            captured["auth"] = req.headers.get("Authorization")
            return FakeResponse()

        with patch("urllib.request.urlopen", fake_urlopen):
            result = provider.review_profile(
                {"run_id": 1, "title": "Song", "artist": "Artist"},
                {"sources": []},
            )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(captured["body"]["tools"], [{"type": "web_search"}])
        self.assertEqual(captured["auth"], "Bearer test-key")


if __name__ == "__main__":
    unittest.main()
