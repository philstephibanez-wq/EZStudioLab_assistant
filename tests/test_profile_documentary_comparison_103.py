import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_final_verifier import _compare_documentary, attach_documentary_findings

class ItemComparison(unittest.TestCase):
    def test_real_incident(self):
        self.assertEqual(_compare_documentary("duration","6:31","7:12"),"discordant")
        self.assertEqual(_compare_documentary("instrument:0","electric guitar","75 BPM"),"indeterminate")
        self.assertEqual(_compare_documentary("lead_vocal","présent","75 BPM"),"indeterminate")
    def test_valid(self):
        self.assertEqual(_compare_documentary("meter","4/4","4/4"),"concordant")
        self.assertEqual(_compare_documentary("duration","6:31","6:30"),"concordant")
    def test_proposed_vote_does_not_override_real_values(self):
        verification={"assertions":[{"key":"duration","value":"6:31","verdict":"non_trouve"}]}
        web={"items":[{"key":"duration","evidence_review":{"reference_value":"7:12","proposed_verdict":"bon"}}]}
        result=attach_documentary_findings(verification,web,{})
        self.assertEqual(result["assertions"][0]["documentary_observation"]["comparison"],"discordant")
if __name__=="__main__":
    unittest.main()
