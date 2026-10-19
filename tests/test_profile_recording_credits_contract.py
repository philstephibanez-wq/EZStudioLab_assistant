"""PROFILE recording-credit provenance contract."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "app"
module = ast.parse((ROOT / "profile_auto_review.py").read_text(encoding="utf-8"))
names = {"_compact", "_recording_credits"}
functions = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name in names]
if {n.name for n in functions} != names:
    raise RuntimeError("recording_credit_functions_missing")
namespace = {"Any": object, "_NON_CREDIT_ATTRIBUTES": {
    "additional", "guest", "solo", "lead", "rhythm", "background",
    "backing", "live", "session", "featured",
}, "re": __import__("re")}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
             str(ROOT / "profile_auto_review.py"), "exec"), namespace)
credits = namespace["_recording_credits"]


class RecordingCreditsContract(unittest.TestCase):
    def test_recording_credit_keeps_provenance_and_instrument(self):
        result = credits([{"target-type": "artist", "type": "instrument",
            "artist": {"name": "Session Musician"},
            "attributes": ["guitar", "guest"]}], "https://musicbrainz.org/recording/123")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["scope"], "recording")
        self.assertEqual(result[0]["instruments"], ["guitar"])
        self.assertEqual(result[0]["source_url"], "https://musicbrainz.org/recording/123")

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
