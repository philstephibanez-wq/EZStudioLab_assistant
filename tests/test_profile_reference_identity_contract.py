"""Durable contract: PROFILE Qwen receives only recording-identity-relevant sources."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "app" / "ai_provider.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
required = {"_local_profile_compact", "_local_profile_evidence"}
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in required]
if {node.name for node in functions} != required:
    raise RuntimeError("profile_evidence_functions_missing")
namespace = {}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
             str(SOURCE), "exec"), namespace)
evidence = namespace["_local_profile_evidence"]


class ProfileReferenceIdentityContract(unittest.TestCase):
    def setUp(self):
        self.row = {"run_id": 153, "title": "Aline", "artist": "Christophe",
                    "diagnostics": {"profile_view": {}, "tagging": {}}}

    def test_rejects_unrelated_and_unavailable_sources(self):
        research = {"sources": [
            {"source": "Wikidata", "available": True, "identity_relevant": False,
             "genres": ["hip-hop"], "url": "https://example.com/wrong"},
            {"source": "MusicBrainz", "available": False, "identity_relevant": False},
            {"source": "MusicBrainz", "available": True, "identity_relevant": True,
             "genres": ["chanson"], "url": "https://example.com/correct"},
        ]}
        result = evidence(self.row, research)["public_research"]
        self.assertEqual(result["relevant_source_count"], 1)
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["source"], "MusicBrainz")
        self.assertNotIn("hip-hop", str(result))

    def test_sources_without_explicit_identity_validation_are_not_evidence(self):
        research = {"sources": [{"source": "Wikipedia", "available": True,
                                 "genres": ["rock"]}]}
        result = evidence(self.row, research)["public_research"]
        self.assertEqual(result["relevant_source_count"], 0)
        self.assertEqual(result["sources"], [])


if __name__ == "__main__":
    unittest.main()
