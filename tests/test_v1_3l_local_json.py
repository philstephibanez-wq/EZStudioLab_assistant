from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from ai_provider import LocalAIProvider


class LocalAIJson13L(unittest.TestCase):
    def test_fenced_json(self):
        raw = "\n".join([
            "```json",
            '{"summary":"ok","confidence":1,"dimensions":{},"sources":[]}',
            "```",
        ])
        value = LocalAIProvider._decode_local_json(raw)
        self.assertEqual("ok", value["summary"])

    def test_prefixed_json(self):
        raw = "\n".join([
            "Result:",
            '{"summary":"ok","confidence":0.9,"dimensions":{},"sources":[]}',
            "Done.",
        ])
        value = LocalAIProvider._decode_local_json(raw)
        self.assertEqual(0.9, value["confidence"])

    def test_observed_qwen_dimensions_list_normalizes(self):
        dimensions = LocalAIProvider._normalize_local_dimensions([
            {
                "genre": "match",
                "confidence": 1,
                "evidence": "rock",
                "rationale": "same label",
            },
            {
                "instrumentation": "match",
                "confidence": 1,
                "evidence": "guitar bass drums",
                "rationale": "same instruments",
            },
        ])
        self.assertEqual("match", dimensions["genre"]["decision"])
        self.assertEqual("match", dimensions["instrumentation"]["decision"])

    def test_observed_qwen_payload_validates(self):
        raw = "\n".join([
            "```json",
            "{",
            '  "summary": "The LAB profile analysis matches the public research evidence.",',
            '  "confidence": 1,',
            '  "dimensions": [',
            '    {"genre": "match", "confidence": 1, "evidence": "genre confirmed", "rationale": "same label"},',
            '    {"instrumentation": "match", "confidence": 1, "evidence": "instruments confirmed", "rationale": "same instruments"}',
            "  ]",
            "}",
            "```",
        ])
        decoded = LocalAIProvider._decode_local_json(raw)
        result = LocalAIProvider._validate_local_result(decoded, model="test.gguf")
        self.assertEqual("completed", result["status"])
        self.assertEqual("match", result["dimensions"]["genre"]["decision"])
        self.assertEqual([], result["sources"])

    def test_invalid_decision_rejected(self):
        with self.assertRaisesRegex(ValueError, "dimension_decision_invalid"):
            LocalAIProvider._normalize_local_dimensions([{"genre": "yes"}])


if __name__ == "__main__":
    unittest.main()
