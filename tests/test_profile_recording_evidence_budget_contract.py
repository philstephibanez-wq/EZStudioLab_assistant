"""Contract: verified recording credits remain in reduced Qwen context."""
import ast
import json
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "app" / "ai_provider.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in
             {"_local_profile_compact", "_local_profile_budget"}]
namespace = {"json": json}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
             str(SOURCE), "exec"), namespace)


class EvidenceBudgetContract(unittest.TestCase):
    def test_credits_survive_reduction(self):
        evidence = {
            "identity": {"title": "Aline", "artist": "Christophe"},
            "profile_view": {
                "genre": {"primary": {"genre": "chanson"}},
                "instrumentation": {"candidates": [{"label": "guitar"}]},
                "vocals": {"dimensions": {"lead_vocal": {"decision": "present"}}},
                "debug": "x" * 20000,
            },
            "public_research": {
                "recording_credits": [{"musician": "Session Musician",
                    "instruments": ["guitar"], "scope": "recording"}],
                "sources": [{"source": "MusicBrainz", "identity_relevant": True}],
            },
        }
        value = json.loads(namespace["_local_profile_budget"](
            evidence, "prompt", max_chars=3500))
        self.assertTrue(value["context_reduction"]["active"])
        self.assertEqual(value["public_research"]["recording_credits"][0]["musician"],
                         "Session Musician")
        self.assertIn("vocals", value["profile_view"])

    def test_missing_credits_not_invented(self):
        evidence = {"identity": {"title": "Aline"}, "profile_view": {"genre": {}},
                    "public_research": {"sources": []}}
        value = json.loads(namespace["_local_profile_budget"](
            evidence, "prompt", max_chars=3500))
        self.assertNotIn("recording_credits", value["public_research"])


if __name__ == "__main__":
    unittest.main()
