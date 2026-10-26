import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_model_comparator import compare,endpoint_port

class ComparatorTests(unittest.TestCase):
    def test_reject_non_loopback(self):
        for url in ("http://example.org:8730","https://127.0.0.1:8730","http://127.0.0.1:8730/remote"):
            with self.assertRaises(ValueError):endpoint_port(url)
    def test_accept_candidate_port(self):
        self.assertEqual(endpoint_port("http://127.0.0.1:8730"),8730)
    def test_same_corpus_metrics(self):
        def mock(endpoint,model,docs):
            from profile_inference_live_benchmark import CASES
            case=next(c for c in CASES if c["documents"]==docs)
            return {"facts":[{"item":f["item"],"value":f["value"],"source_url":docs[0]["url"],"quote":docs[0]["text"]}
                for f in case["expected"]]},1.0
        r=compare([("baseline","http://127.0.0.1:8720","local"),
                   ("candidate","http://127.0.0.1:8730","local")],mock)
        self.assertEqual(len(r["comparisons"]),2)
        self.assertEqual(r["comparisons"][0]["completed"],3)
        self.assertFalse(r["production_modified"])
    def test_failures_not_presented_as_success(self):
        def fail(endpoint,model,docs):raise RuntimeError("unavailable")
        r=compare([("candidate","http://127.0.0.1:8730","local")],fail)
        self.assertFalse(r["comparisons"][0]["valid_comparison"])
        self.assertEqual(r["comparisons"][0]["completed"],0)
if __name__=="__main__":unittest.main()
