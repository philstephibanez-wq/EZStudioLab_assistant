"""Nested Qwen vocals parsing must not invent vocal evidence."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "app" / "ai_provider.py"
module = ast.parse(ROOT.read_text(encoding="utf-8"))
provider = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == "LocalAIProvider")
normalize = next(n for n in provider.body if isinstance(n, ast.FunctionDef) and n.name == "_normalize_local_dimensions")
namespace = {"Any": object}
exec(compile(ast.fix_missing_locations(ast.Module(body=[normalize], type_ignores=[])), str(ROOT), "exec"), namespace)
normalize = namespace["_normalize_local_dimensions"]


class NestedVocalsContract(unittest.TestCase):
    def test_nested_explicit_dimensions(self):
        value = {"genre": {"decision": "not_scored"},
                 "vocals": {"lead_vocal": {"decision": "match", "confidence": 0.8, "evidence": ["credited singer"]},
                            "backing_vocals": {"decision": "uncertain"},
                            "choir": {"decision": "not_scored"}}}
        result = normalize(value)
        self.assertEqual(result["lead_vocal"]["decision"], "match")
        self.assertEqual(result["lead_vocal"]["confidence"], 0.8)
        self.assertEqual(result["choir"]["decision"], "not_scored")

    def test_generic_vocals_do_not_create_evidence(self):
        result = normalize({"vocals": {"decision": "match", "confidence": 0.99, "evidence": ["vocals"]}})
        for key in ("lead_vocal", "backing_vocals", "choir"):
            self.assertEqual(result[key]["decision"], "not_scored")

    def test_duplicate_explicit_key_abstains(self):
        result = normalize({"lead_vocal": {"decision": "match"},
                            "vocals": {"lead_vocal": {"decision": "mismatch"}}})
        self.assertEqual(result["lead_vocal"]["decision"], "not_scored")
        self.assertEqual(result["lead_vocal"]["reason"], "duplicate_dimension_in_model_output")


if __name__ == "__main__":
    unittest.main()
