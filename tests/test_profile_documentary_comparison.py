import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_final_verifier import attach_documentary_findings

class DocumentaryComparison(unittest.TestCase):
    def test_provisional_equal_bpm(self):
        original={"assertions":[{"key":"tempo","value":"136.0 BPM","verdict":"non_trouve"}]}
        research={"items":[{"key":"tempo","evidence_review":{"proposed_verdict":"bon","reference_value":"136.0 BPM","references":[{"url":"https://example.org/track"}]}}]}
        result=attach_documentary_findings(original,research,{"items":[]})
        value=result["assertions"][0]
        self.assertEqual(value["verdict"],"non_trouve")
        self.assertEqual(value["documentary_observation"]["comparison"],"concordant")
        self.assertEqual(value["documentary_observation"]["reference_value"],"136.0 BPM")
        self.assertFalse(value["documentary_observation"]["recording_identity_confirmed"])
        self.assertNotIn("documentary_observation",original["assertions"][0])

    def test_verified_verdict_not_overridden(self):
        result=attach_documentary_findings({"assertions":[{"key":"tempo","verdict":"bon"}]},
                 {"items":[{"key":"tempo","evidence_review":{"proposed_verdict":"faux","reference_value":"110 BPM"}}]}, {"items":[]})
        self.assertEqual(result["assertions"][0]["verdict"],"bon")
        self.assertNotIn("documentary_observation",result["assertions"][0])

    def test_missing_evidence(self):
        result=attach_documentary_findings({"assertions":[{"key":"key","verdict":"non_trouve"}]}, {"items":[]}, {"items":[]})
        self.assertEqual(result["assertions"][0]["documentary_observation"]["comparison"],"indeterminate")

if __name__=="__main__":
    unittest.main()
