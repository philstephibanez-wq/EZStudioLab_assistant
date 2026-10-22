import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_sequential_review import examine_modules
class SequentialContract(unittest.TestCase):
 def payload(self):
  return {"schema":"ezstudio.profile-scientific-items.r1","run_id":153,"item_total":3,
          "coverage":{"registry_total":3,"returned":3,"complete_for_registry":True},
          "items":[{"item_id":str(i),"index":i+1,"source_pointer":"/diagnostics/module_registry/modules/"+str(i),
                    "module":{"id":str(i),"normalized":{"scores":[i]}}} for i in range(3)]}
 def test_all_modules_sequential_one_job_no_side_effects(self):
  events=[];requests=[];calls=[]
  def inference(x):
   requests.append(x)
   return {"status":"abstain","reason":"no_evidence"}
  output=examine_modules(153,lambda p:calls.append(p) or self.payload(),inference,
                         on_progress=lambda *x:events.append(x))
  self.assertEqual(len(requests),3)
  self.assertEqual([x["item_id"] for x in requests],["0","1","2"])
  self.assertEqual(output["examined"],3)
  self.assertTrue(output["complete"])
  self.assertEqual(events[-1],(3,3,"2"))
  self.assertEqual(calls,["/internal/analysis/desktop/profile/153/scientific-items"])
 def test_one_engine_error_does_not_cancel_others(self):
  def infer(request):
   if request["item_id"]=="1":
    return {"status":"error","reason":"invalid_model_response"}
   return {"status":"completed","summary":"Avis consultatif"}
  result=examine_modules(153,lambda p:self.payload(),infer)
  self.assertEqual(result["examined"],3)
  self.assertTrue(result["complete"])
  self.assertFalse(result["inference_complete"])
  self.assertEqual(result["error_count"],1)
  self.assertEqual(result["failed_modules"],["1"])
  self.assertEqual([r["status"] for r in result["results"]],["completed","error","completed"])
  self.assertEqual(result["results"][1]["assessment"]["reason"],"invalid_model_response")

 def test_exception_is_recorded_without_losing_following_modules(self):
  def infer(request):
   if request["item_id"]=="1":
    raise ValueError("model_generated_secret_not_retained")
   return {"status":"abstain","reason":"insufficient_data"}
  result=examine_modules(153,lambda p:self.payload(),infer)
  self.assertEqual(result["error_count"],1)
  self.assertEqual(result["results"][1]["assessment"]["reason"],"module_inference_exception")
  self.assertNotIn("model_generated_secret",str(result))
  self.assertEqual(result["results"][2]["status"],"abstain")
