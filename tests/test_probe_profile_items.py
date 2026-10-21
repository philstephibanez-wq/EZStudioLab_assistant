import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from probe_profile_items import probe
class ProbeProfileItemsContract(unittest.TestCase):
 def test_no_mutation_and_complete_modules(self):
  class Client:
   def __init__(self):self.calls=[]
   def request(self,method,path,**kw):
    self.calls.append((method,path))
    return {"schema":"ezstudio.profile-scientific-items.r1","run_id":153,"item_total":2,
      "coverage":{"registry_total":2,"returned":2,"complete_for_registry":True},
      "items":[{"index":i+1,"item_id":key,"module":{"id":key,"data":[1,2]},"source_pointer":"/diagnostics/module_registry/modules/"+str(i),"status":"ok"}
      for i,key in enumerate(("clap","passt"))]}
  c=Client()
  result=probe(153,c)
  self.assertEqual(result["item_total"],2)
  self.assertEqual([x["item_id"] for x in result["items"]],["clap","passt"])
  self.assertEqual(c.calls,[("GET","/internal/analysis/desktop/profile/153/scientific-items")])
