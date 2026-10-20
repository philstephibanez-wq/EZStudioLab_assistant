from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from ai_provider import LocalAIProvider

class ProfileAdvisoryContract(unittest.TestCase):
    def test_unverified_comment_retained_without_scoring(self):
        result = LocalAIProvider._validate_local_result(
            {"summary": "Possible guitare acoustique.", "confidence": 0.91,
             "dimensions": {"genre": {"decision": "match", "confidence": .9,
                  "evidence": [{"source":"MusicBrainz","scope":"recording",
                     "source_url":"https://musicbrainz.org/recording/x","genre":"pop"}]}}},
            model="qwen", sent_evidence={"public_research":{"recording_genres":[]}})
        self.assertEqual(result["coverage"]["scored_count"], 0)
        self.assertEqual(result["dimensions"]["genre"]["decision"], "not_scored")
        self.assertIsNone(result["confidence"])
        self.assertIn("NON VÉRIFIÉE", result["summary"])
        self.assertIn("guitare acoustique", result["summary"])
        self.assertLess(len(result["summary"]), 1000)
    def test_no_fabricated_hypothesis_when_missing(self):
        result = LocalAIProvider._validate_local_result(
            {"dimensions": {}}, model="qwen", sent_evidence={})
        self.assertNotIn("Hypothèse Qwen", result["summary"])
        self.assertEqual(result["coverage"]["scored_count"], 0)
