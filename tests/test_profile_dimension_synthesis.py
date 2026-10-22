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

    def test_invalid_model_shape_returns_coded_abstention_without_claiming_success(self):
        from types import SimpleNamespace
        import json
        import profile_dimension_synthesis as m
        class Provider:
            endpoint="http://127.0.0.1:8720"
            config=SimpleNamespace(timeout_seconds=10)
            def _health(self): return (True, None)
            def _decode_local_json(self, raw): return json.loads(raw)
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n): return json.dumps({"choices":[{"finish_reason":"stop","message":{"content":'{"dimensions":{}}'}}]}).encode("utf-8")
        preset={"temperature":0.1,"max_tokens":3072,"context_max_chars":16000}
        snapshots=[]
        with patch.object(m,"load_review_preset",return_value=(preset,"digest")), patch.object(m.urllib.request,"urlopen",return_value=Response()), patch.object(m,"snap",side_effect=lambda *a:snapshots.append(a)):
            out=synthesize_dimensions(Provider(),{"diagnostics":{}},{"results":[]})
        self.assertEqual(out["status"],"abstain")
        self.assertEqual(out["reason"],"dimension_advisory_keys_invalid")
        self.assertTrue(any(name=="qwen.dimension.response_shape" for name,_ in snapshots))
        self.assertNotIn("dimensions",out)

if __name__=="__main__":
    unittest.main()
