from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_report import make_report, publish_report


class ProfileReportContract(unittest.TestCase):
    def test_allowlisted_telemetry_without_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "timeline.jsonl"
            data = [
                {"event": "qwen.evidence.sent", "data": {"public_research": {"recording_genres": [], "recording_credits": [], "wikipedia_quotes": [{"extract": "secret prompt"}]}}},
                {"event": "qwen.content.decoded", "data": {"genre": {"rationale": "private"}, "dimensions": {"genre": {}}, "token": "never_export"}},
                {"event": "qwen.validated", "data": {"dimensions": {"genre": {"decision": "not_scored", "reason": "no_verified_external_dimension_evidence", "evidence": []}}}},
            ]
            path.write_text("\n".join(json.dumps(x) for x in data), encoding="utf-8")
            trace = SimpleNamespace(file=path, run_id=153, trace_id="abcdef1234567890")
            report = make_report(trace, {"revision": 39})
            encoded = json.dumps(report)
            self.assertEqual(report["evidence_counts"]["wikipedia_quotes"], 1)
            self.assertNotIn("secret prompt", encoded)
            self.assertNotIn("never_export", encoded)
            self.assertNotIn("private", encoded)
            self.assertEqual(report["dimensions"]["genre"]["decision"], "not_scored")

    def test_disabled_publication_is_safe(self):
        with patch.dict("os.environ", {"EZS_PROFILE_REPORTS_PUBLISH": "0"}):
            self.assertEqual(publish_report({"run_id": 153, "trace_id": "abcdef123456"}), "disabled")


if __name__ == "__main__":
    unittest.main()
