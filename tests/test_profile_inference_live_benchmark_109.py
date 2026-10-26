import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_inference_live_benchmark import CASES, INSTRUCTION
from profile_inference_qualification import validate_response
class BenchmarkContract(unittest.TestCase):
    def test_cases_independent_and_multilingual(self):
        self.assertEqual(len(CASES),3)
        self.assertEqual(len(set(c["id"] for c in CASES)),3)
        self.assertTrue(all(c["expected"] for c in CASES))
    def test_exact_quote_enforced(self):
        docs=CASES[0]["documents"]
        bad={"facts":[{"item":"tempo","value":"92 BPM","source_url":docs[0]["url"],"quote":"fabricated"}]}
        self.assertFalse(validate_response(bad,docs)["accepted"])
    def test_exhaustive_instruction(self):
        self.assertIn("all musical facts",INSTRUCTION)
        self.assertIn("studio and live",INSTRUCTION)
if __name__=="__main__":unittest.main()
