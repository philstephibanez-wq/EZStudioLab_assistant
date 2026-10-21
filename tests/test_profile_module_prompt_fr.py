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

if __name__=="__main__":
    unittest.main()
