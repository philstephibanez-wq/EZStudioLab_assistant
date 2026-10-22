import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_recording_disambiguation import duration_from_catalog,choose_candidate

def candidate(id,length):
    return ((1,1,100),{"id":id,"length":length},"Pink Floyd")

class DurationIdentityTests(unittest.TestCase):
    def test_unique_duration_selects_the_recording(self):
        found=choose_candidate([candidate("a",334000),candidate("b",350000)],334200)
        self.assertEqual(found["status"],"duration_match")
        self.assertEqual(found["candidate"][1]["id"],"a")
    def test_same_duration_is_ambiguous(self):
        found=choose_candidate([candidate("a",334000),candidate("b",334050)],334000)
        self.assertEqual(found["status"],"insufficient_duration_margin")
    def test_unknown_duration_abstains(self):
        self.assertEqual(choose_candidate([candidate("a",334000),candidate("b",335000)],None)["status"],"duration_unavailable")
    def test_missing_competitor_length_abstains(self):
        self.assertEqual(choose_candidate([candidate("a",334000),candidate("b",None)],334000)["status"],"incomplete_candidate_durations")
    def test_inconsistent_catalog_duration_abstains(self):
        self.assertIsNone(duration_from_catalog({"duration_ms":334000,"duration_seconds":344}))
    def test_nested_lab_metrics_duration_seconds(self):
        self.assertEqual(duration_from_catalog({"metrics":{"duration_seconds":339.847}}),339847)
    def test_inconsistent_nested_and_top_level_abstains(self):
        self.assertIsNone(duration_from_catalog({"metrics":{"duration_seconds":339.847},"duration_seconds":360}))
    def test_catalog_duration_seconds(self):
        self.assertEqual(duration_from_catalog({"duration_seconds":334.2}),334200)

if __name__=="__main__":
    unittest.main()
