"""Consultative PROFILE module prompt contracts without model execution."""
import ast
import unittest
from pathlib import Path

CODE = (Path(__file__).resolve().parents[1] / "app" / "profile_module_qwen.py").read_text(encoding="utf-8")

class ModulePromptContract(unittest.TestCase):
    def test_prompt_is_french_and_source_bounded(self):
        tree=ast.parse(CODE)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="infer_module")
        assignment=next(n for n in fn.body if isinstance(n,ast.Assign)
                        and any(isinstance(t,ast.Name) and t.id=="prompt" for t in n.targets))
        prompt=ast.literal_eval(assignment.value)
        self.assertIn("en français",prompt)
        self.assertIn("ni écouté",prompt)
        self.assertIn("ni consulté le Web",prompt)
        self.assertIn("calibration",prompt)
        self.assertIn("n'invente aucune source",prompt)
        self.assertIn("ne valide ni ne promeus de preset",prompt)

    def test_existing_json_fields_remain(self):
        for field in ("summary","uncertainty","supporting_evidence","conflicting_evidence"):
            self.assertIn(field,CODE)

    def test_english_diagnostics_and_french_preserved(self):
        from unittest.mock import patch
        import sys
        import types
        # profile_module_qwen imports only local dependencies; avoid runtime integration.
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
        from profile_module_qwen import _english_review
        self.assertTrue(_english_review({"summary":"The module identified beats in the audio.","uncertainty":""}))
        self.assertFalse(_english_review({"summary":"Le module identifie 92,3 battements par minute.","uncertainty":"Score non calibré."}))
        self.assertFalse(_english_review({"summary":"","uncertainty":""}))

    def test_retry_is_bounded_and_abstains(self):
        self.assertIn("for attempt in range(2)",CODE)
        self.assertIn("non_french_model_output",CODE)
        self.assertIn("qwen.module.retry_language",CODE)

if __name__=="__main__":
    unittest.main()
