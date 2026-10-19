"""PROFILE recording-credit provenance contract."""
import ast
from pathlib import Path
import unittest
import urllib.parse

ROOT = Path(__file__).resolve().parents[1] / "app"
module = ast.parse((ROOT / "profile_auto_review.py").read_text(encoding="utf-8"))
names = {"_compact", "_recording_credits", "_musicbrainz", "_query"}
functions = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name in names]
if {n.name for n in functions} != names:
    raise RuntimeError("recording_credit_functions_missing")
namespace = {"Any": object, "_NON_CREDIT_ATTRIBUTES": {
    "additional", "guest", "solo", "lead", "rhythm", "background",
    "backing", "live", "session", "featured",
}, "re": __import__("re"), "urllib": __import__("urllib"), "urllib.parse": urllib.parse}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
             str(ROOT / "profile_auto_review.py"), "exec"), namespace)
credits = namespace["_recording_credits"]
lookup = namespace["_musicbrainz"]


class RecordingCreditsContract(unittest.TestCase):
    def test_recording_credit_keeps_provenance_and_instrument(self):
        result = credits([{"target-type": "artist", "type": "instrument",
            "artist": {"name": "Session Musician"},
            "attributes": ["guitar", "guest"]}], "https://musicbrainz.org/recording/123")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["scope"], "recording")
        self.assertEqual(result[0]["instruments"], ["guitar"])
        self.assertEqual(result[0]["source_url"], "https://musicbrainz.org/recording/123")

    def test_musicbrainz_does_not_treat_live_as_instrument(self):
        class FakeBudget:
            max_requests_per_item = 6
        class FakeHttp:
            budget = FakeBudget()
            request_count = 0
            def get_json(self, url, **kwargs):
                self.request_count += 1
                if "recording/?" in url:
                    return {"recordings": [{
                        "id": "rec123", "title": "Aline", "score": 100,
                        "artist-credit": [{"name": "Christophe"}]}]}
                return {"title": "Aline", "relations": [
                    {"target-type": "artist", "type": "instrument",
                     "artist": {"name": "Musician"}, "attributes": ["live", "guitar"]},
                    {"target-type": "artist", "type": "producer",
                     "artist": {"name": "Producer"}, "attributes": ["drums"]},
                ]}
        item = lookup(FakeHttp(), "Aline", "Christophe")
        self.assertEqual(item["instruments"], ["guitar"])
        self.assertEqual(item["recording_credits"][0]["scope"], "recording")
        self.assertNotIn("live", str(item["instruments"]))

    def test_album_relation_or_unrelated_role_not_assumed_track_credit(self):
        result = credits([
            {"target-type": "release", "type": "instrument", "artist": {"name": "X"},
             "attributes": ["drums"]},
            {"target-type": "artist", "type": "producer", "artist": {"name": "Y"},
             "attributes": []},
        ], None)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
