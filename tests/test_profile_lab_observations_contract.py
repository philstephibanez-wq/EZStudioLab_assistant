from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_lab_observations import describe_lab_profile, attach_lab_observations

class ProfileLabObservationsContract(unittest.TestCase):
    def test_evidence_absence_does_not_hide_lab_signals(self):
        row = {"diagnostics":{"profile_view":{
            "genre_hierarchy":{"primary":{"genre":"singer-songwriter"}},
            "instrumentation":{"candidates":[{"label":"guitar","source_count":2}]},
            "vocal_profile":{"dimensions":{"backing_vocals":{"decision":"possible"}}}}}}
        review = {"summary":"Validation externe : 0/5.", "coverage":{"scored_count":0}}
        result = attach_lab_observations(review, row)
        self.assertIn("guitar (2 moteurs)", result["summary"])
        self.assertIn("voix d'accompagnement : possible", result["summary"])
        self.assertIn("0/5", result["summary"])
        self.assertEqual(result["coverage"]["scored_count"], 0)
        self.assertEqual(review["summary"], "Validation externe : 0/5.")

    def test_empty_profile_never_fabricates(self):
        self.assertIn("aucune donnée structurée", describe_lab_profile({}))
        self.assertNotIn("guitar", describe_lab_profile({}))

    def test_bounded_untrusted_labels(self):
        row = {"diagnostics":{"profile_view":{"instrumentation":{"candidates":[{"label":"x"*3000}]}}}}
        self.assertLess(len(describe_lab_profile(row)), 1300)
