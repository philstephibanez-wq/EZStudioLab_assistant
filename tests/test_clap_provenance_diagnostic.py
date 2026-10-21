"""Non-regression contracts for CLAP provenance differential (read-only)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_clap_provenance import diagnose, digest, changed_paths


def archive(module):
    return {"fields": {"diagnostics_json": {"module_registry": {"modules": [module]}}}}


def revision(module):
    return {"fields": {"comparison_json": {"module_consultations": {
        "results": [{"item_id": "semantic.clap-open-vocabulary",
                     "source_sha256": digest(module)}]}}}}


class ClapForensicTests(unittest.TestCase):
    def test_identical_source(self):
        module = {"id": "semantic.clap-open-vocabulary", "normalized": {"x": 1}}
        result = diagnose(archive(module), revision(module))
        self.assertTrue(result["integrity_complete"])

    def test_mismatch_blocks(self):
        original = {"id": "semantic.clap-open-vocabulary", "normalized": {"x": 1}}
        changed = {"id": original["id"], "normalized": {"x": 2}}
        result = diagnose(archive(changed), revision(original))
        self.assertFalse(result["integrity_complete"])
        self.assertEqual(result["status"], "unexplained_mismatch")

    def test_original_reference_explains_but_does_not_clear_integrity(self):
        original = {"id": "semantic.clap-open-vocabulary", "model": {"path": "secret"}}
        changed = {"id": original["id"], "model": {"path": "[REDACTED]"}}
        result = diagnose(archive(changed), revision(original), original)
        self.assertTrue(result["source_mutation_proven"])
        self.assertFalse(result["integrity_complete"])
        self.assertEqual(result["difference_paths"],
                         [{"path": "$.model.path", "kind": "value_changed"}])
        self.assertNotIn("secret", str(result))

    def test_nested_list_change(self):
        self.assertEqual(changed_paths({"x": [1, 2]}, {"x": [1]}),
                         [{"path": "$.x[1]", "kind": "only_in_archive"}])

    def test_missing_consultation_rejected(self):
        module = {"id": "semantic.clap-open-vocabulary"}
        with self.assertRaisesRegex(ValueError, "clap_consultation_count_invalid"):
            diagnose(archive(module), {"fields": {"comparison_json": {
                "module_consultations": {"results": []}}}})


if __name__ == "__main__":
    unittest.main()
