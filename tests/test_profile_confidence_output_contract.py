"""Qwen dimension confidence: never auto-fill missing evidence or score."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "app" / "ai_provider.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_profile_ai_coverage"]
namespace = {}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
             str(SOURCE), "exec"), namespace)
coverage = namespace["_profile_ai_coverage"]


class ConfidenceOutputContract(unittest.TestCase):
    def test_missing_dimension_confidence_abstains(self):
        result = coverage({"genre": {"decision": "match", "evidence": ["source-specific credit"]}})
        self.assertEqual(result["scored_count"], 0)
        self.assertEqual(result["dimensions"]["genre"]["decision"], "not_scored")

    def test_missing_external_evidence_abstains(self):
        result = coverage({"instrumentation": {"decision": "match", "confidence": .9, "evidence": []}})
        self.assertEqual(result["scored_count"], 0)

    def test_dimension_confidence_required_individually(self):
        result = coverage({
            "genre": {"decision": "match", "confidence": .8, "evidence": ["verified recording genre reference"]},
            "instrumentation": {"decision": "match", "evidence": ["uncorroborated guitar"]},
        })
        self.assertEqual(result["scored_count"], 1)
        self.assertEqual(result["dimensions"]["genre"]["confidence"], .8)
        self.assertEqual(result["dimensions"]["instrumentation"]["decision"], "not_scored")


if __name__ == "__main__":
    unittest.main()
