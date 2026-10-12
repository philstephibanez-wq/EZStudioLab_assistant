from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from profile_review import normalize_track_identity, profile_review_queue_snapshot
from preset_guard import evaluate_preset_candidate


class FakeClient:
    def profile_review_queue(self, *, limit=100):
        return [
            {
                "run_id": 12,
                "title": "Breakfast In America - Supertramp",
                "artist": "",
            }
        ][:limit]


class V11AProfileReviewContract(unittest.TestCase):
    def test_identity_normalization_is_explicitly_heuristic(self):
        identity = normalize_track_identity({
            "title": "Breakfast In America - Supertramp",
            "artist": "",
        })
        self.assertEqual(identity["title"], "Breakfast In America")
        self.assertEqual(identity["artist"], "Supertramp")
        self.assertEqual(identity["method"], "title_suffix_heuristic")
        self.assertTrue(identity["requires_verification"])

    def test_queue_snapshot_does_not_execute_review_or_promote(self):
        payload = profile_review_queue_snapshot(FakeClient(), limit=10)
        self.assertEqual(payload["count"], 1)
        self.assertFalse(payload["review_execution_enabled"])
        self.assertFalse(payload["automatic_preset_promotion_enabled"])

    def test_guard_accepts_non_regressive_candidate(self):
        result = evaluate_preset_candidate(
            {"a": 0.70, "b": 0.80, "c": 0.90},
            {"a": 0.72, "b": 0.82, "c": 0.91},
            threshold=0.75,
        )
        self.assertEqual(result["decision"], "CANDIDATE_ACCEPTABLE")
        self.assertFalse(result["automatic_promotion_allowed"])

    def test_guard_rejects_worse_candidate(self):
        result = evaluate_preset_candidate(
            {"a": 0.70, "b": 0.80, "c": 0.90},
            {"a": 0.50, "b": 0.81, "c": 0.91},
            threshold=0.75,
            max_song_regression=0.10,
        )
        self.assertEqual(result["decision"], "REJECT")
        self.assertIn("critical_song_regression", result["reasons"])


if __name__ == "__main__":
    unittest.main()
