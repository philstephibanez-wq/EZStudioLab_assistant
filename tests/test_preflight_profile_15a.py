import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from preflight_profile_15a import check
class ContextPreflightContract(unittest.TestCase):
 def test_over_budget_is_detected_without_qwen(self):
  payload={"schema":"ezstudio.profile-scientific-items.r1","run_id":153,"item_total":1,
   "coverage":{"registry_total":1,"returned":1,"complete_for_registry":True},
   "items":[{"index":1,"item_id":"a","source_pointer":"/diagnostics/module_registry/modules/0",
             "module":{"id":"a","extra":"x"*50000}}]}
  result=check(153,lambda p:payload)
  self.assertFalse(result["all_fit"])
  self.assertTrue(result["no_qwen_inference"])
