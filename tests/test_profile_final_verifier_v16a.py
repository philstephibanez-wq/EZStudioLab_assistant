"""V1.6a strict contract: final-value-only independent verification."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"app"))
from profile_final_verifier import final_assertions, verify_final_values

def sample():
    return {"metrics":{"tempo":{"bpm":103.4},"time_signature":{"label":"4/4"},
                       "key":{"label":"F minor"}},
            "diagnostics":{"profile_view":{
                "genre_hierarchy":{"primary":{"genre":"blues"}},
                "instrumentation":{"candidates":[{"label":"electric guitar","support":3},
                                                 {"label":"bass guitar","support":2}]},
                "vocal_profile":{"dimensions":{"lead_vocal":{"decision":"present"},
                               "backing_vocals":{"decision":"possible"},
                               "choir":{"decision":"inconclusive"}}},
                "modules":[{"id":"semantic.clap-open-vocabulary","scores":[0.9]}]}},
            "preset":"SECRET_ENGINE_PRESET", "model":"SECRET_MERT"}
def evidence():
    return {"sources":[{"source":"MusicBrainz","available":True,"identity_relevant":True,
        "url":"https://musicbrainz.org/recording/abc","recording_genres":["blues"],
        "recording_credits":[{"scope":"recording","role":"instrument",
            "instruments":["electric guitar"]},
            {"scope":"recording","role":"vocal","instruments":["lead"]}]}]}
class FinalVerificationV16a(unittest.TestCase):
    def setUp(self):
        self.ident={"title":"Folsom Prison Blues","artist":"Johnny Cash"}
    def test_final_assertions_isolate_engines_and_presets(self):
        from json import dumps
        output=dumps(final_assertions(sample()))
        self.assertNotIn("SECRET_ENGINE_PRESET",output)
        self.assertNotIn("SECRET_MERT",output)
        self.assertNotIn("semantic.clap",output)
        self.assertNotIn("support",output)
    def test_each_final_value_has_own_verdict(self):
        out=verify_final_values(sample(),self.ident,evidence())
        vals={a["key"]:a for a in out["assertions"]}
        self.assertEqual(vals["genre"]["verdict"],"bon")
        self.assertEqual(vals["instrument:0"]["verdict"],"bon")
        self.assertEqual(vals["instrument:1"]["verdict"],"non_trouve")
        self.assertEqual(vals["tempo"]["verdict"],"non_trouve")
        self.assertEqual(vals["meter"]["verdict"],"non_trouve")
        self.assertEqual(vals["key"]["verdict"],"non_trouve")
        self.assertEqual(vals["lead_vocal"]["verdict"],"bon")
        self.assertNotIn("backing_vocals",vals)
        self.assertNotIn("choir",vals)
        self.assertTrue(all(a["confidence_pct"] is None for a in out["assertions"]))
    def test_no_identity_no_evidence(self):
        out=verify_final_values(sample(),{"title":"Folsom Prison Blues","artist":"",
                                          "requires_verification":True},evidence())
        self.assertTrue(all(a["verdict"]=="non_trouve" for a in out["assertions"]))
        self.assertTrue(all(not a["sources"] for a in out["assertions"]))
    def test_unrelated_sources_and_unsafe_urls_rejected(self):
        research={"sources":[{**evidence()["sources"][0],"identity_relevant":False},
                             {**evidence()["sources"][0],"url":"javascript:alert(1)"}]}
        out=verify_final_values(sample(),self.ident,research)
        self.assertTrue(all(a["verdict"]=="non_trouve" for a in out["assertions"]))
    def test_missing_scientific_data_produces_no_fabricated_assertion(self):
        self.assertEqual(final_assertions({"metrics":{},"diagnostics":{}}),[])
if __name__=="__main__":
    unittest.main()
