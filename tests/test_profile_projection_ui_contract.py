import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from profile_module_compact import module_prompt_payload
class ProfileProjectionContract(unittest.TestCase):
 def test_large_vector_is_explicitly_summarized(self):
  req={"item_id":"mert","source_sha256":"a"*64,"module":{"id":"mert","vector":[.1]*30000}}
  body,info=module_prompt_payload(req,6500,"Analyse le module")
  self.assertIn("numeric_vector_summary",body)
  self.assertIn("omitted",body)
  self.assertIn("consultation_is_on_projection",body)
  self.assertLessEqual(info["input_chars"],6500)
 def test_ui_has_observed_progress_not_fake_completion(self):
  template=(ROOT/"templates/dashboard/index.html.twig").read_text(encoding="utf-8")
  self.assertIn("profile_consultation",template)
  self.assertIn("consultation-progress",template)
