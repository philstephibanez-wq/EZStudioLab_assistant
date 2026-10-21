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
 def test_fail_closed_without_marking_completion(self):
  with self.assertRaisesRegex(RuntimeError,"module_inference_failed"):
   examine_modules(153,lambda p:self.payload(),lambda x:{"status":"error"})
