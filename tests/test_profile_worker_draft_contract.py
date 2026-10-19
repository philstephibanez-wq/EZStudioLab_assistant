"""Contract tests for PROFILE worker draft disposition without LAB, network, or Qwen."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runtime" / "profile_ai_requests_worker.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"), filename=str(SOURCE))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "require_completed_ai_review")
module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
scope = {}
exec(compile(module, str(SOURCE), "exec"), scope)
validate = scope["require_completed_ai_review"]


class ProfileWorkerDraftContract(unittest.TestCase):
    def test_five_abstentions_allowed(self):
        dimensions = {name: {"decision": "not_scored", "confidence": None, "reason": "no_external_evidence"}
                      for name in ("genre", "instrumentation", "lead_vocal", "backing_vocals", "choir")}
        self.assertEqual(validate({"status": "completed", "dimensions": dimensions}), dimensions)

    def test_scored_dimension_allowed(self):
        dimensions = {"genre": {"decision": "match", "confidence": 0.8, "evidence": ["source"]}}
        self.assertEqual(validate({"status": "completed", "dimensions": dimensions}), dimensions)

    def test_model_error_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "inference_IA_error"):
            validate({"status": "error", "dimensions": {"genre": {"decision": "not_scored"}}})

    def test_missing_dimensions_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "IA_dimensions_absentes"):
            validate({"status": "completed", "dimensions": {}})

    def test_malformed_dimension_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "IA_dimensions_invalides"):
            validate({"status": "completed", "dimensions": {"genre": {"decision": "hallucinated"}}})


if __name__ == "__main__":
    unittest.main()
