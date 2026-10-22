import sys
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_dimension_synthesis import KEYS, _validate, _observations, synthesize_dimensions

class DimensionSynthesisContract(unittest.TestCase):
    def test_five_distinct_advisories_with_bounded_contributors(self):
        available={"semantic.clap-open-vocabulary","semantic.panns-cnn14"}
        dimensions={name:{"advisory":"Hypothèse consultative "+name,
                          "uncertainty":"Preuves indépendantes insuffisantes",
                          "contributors":["semantic.clap-open-vocabulary"]} for name in KEYS}
        result=_validate({"dimensions":dimensions},available)
        self.assertEqual(set(result["dimensions"]),set(KEYS))
        self.assertTrue(result["external_validation"] is False)
        self.assertTrue(all(v["advisory_only"] for v in result["dimensions"].values()))

    def test_forged_contributor_rejected(self):
        data={"dimensions":{name:{"advisory":"À vérifier","uncertainty":"Non calibré",
                                  "contributors":["invented.engine"]} for name in KEYS}}
        with self.assertRaisesRegex(ValueError,"dimension_contributors_invalid"):
            _validate(data,set())

    def test_missing_dimension_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"dimension_advisory_keys_invalid"):
            _validate({"dimensions":{}},set())

    def test_only_existing_module_consultations_enter_prompt(self):
        row={"title":"Test", "artist":"Test", "diagnostics":{}}
        sequential={"results":[
            {"item_id":"semantic.clap-open-vocabulary","status":"completed",
             "assessment":{"summary":"Genre proposé","uncertainty":"Non calibré"}},
            {"item_id":"embedding.mert-95m","status":"completed",
             "assessment":{"summary":"Unrelated","uncertainty":""}}]}
        result=_observations(row,sequential)
        self.assertIn("semantic.clap-open-vocabulary",result["module_consultations"])
        self.assertNotIn("embedding.mert-95m",result["module_consultations"])
        self.assertNotIn("audio",result.keys())

    def test_invalid_json_isolated_per_dimension_and_five_calls(self):
        from types import SimpleNamespace
        import json
        import profile_dimension_synthesis as m
        class Provider:
            endpoint="http://127.0.0.1:8720"
            config=SimpleNamespace(timeout_seconds=10)
            def _health(self): return (True, None)
            def _decode_local_json(self, raw): return json.loads(raw)
        class Response:
            def __init__(self, index): self.index=index
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n):
                content = '{"bad":true}' if self.index==1 else json.dumps({
                    "advisory":"Hypothèse consultative",
                    "uncertainty":"Non calibré",
                    "contributors":[]})
                return json.dumps({"choices":[{"finish_reason":"stop",
                    "message":{"content":content}}]}).encode("utf-8")
        calls=[]
        def urlopen(req,timeout):
            calls.append(req)
            return Response(len(calls))
        preset={"temperature":0.1,"max_tokens":3072,"context_max_chars":16000}
        with patch.object(m,"load_review_preset",return_value=(preset,"digest")), patch.object(m.urllib.request,"urlopen",side_effect=urlopen), patch.object(m,"snap"):
            out=synthesize_dimensions(Provider(),{"diagnostics":{}},{"results":[]})
        self.assertEqual(len(calls),5)
        self.assertEqual(out["status"],"partial")
        self.assertEqual(set(out["dimensions"]),set(KEYS))
        self.assertEqual(out["dimension_statuses"]["genre"],"dimension_advisory_missing")
        self.assertEqual(out["dimension_statuses"]["instrumentation"],"completed")
        self.assertFalse(out["external_validation"])

    def test_single_dimension_rejects_forged_module(self):
        from profile_dimension_synthesis import _single_dimension
        with self.assertRaisesRegex(ValueError,"dimension_contributors_invalid"):
            _single_dimension({"advisory":"Sensible", "uncertainty":"Inconnu",
                 "contributors":["faux.moteur"]}, "genre", set())

if __name__=="__main__":
    unittest.main()
