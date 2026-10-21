import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_scientific_items import fetch_items, describe_items

class ScientificItemsClientContract(unittest.TestCase):
 def payload(self):
  return {"schema":"ezstudio.profile-scientific-items.r1","run_id":153,"item_total":2,
          "coverage":{"registry_total":2,"returned":2,"complete_for_registry":True},
          "items":[{"index":i+1,"item_id":name,"source_pointer":"/diagnostics/module_registry/modules/"+str(i),"module":{"id":name,"scores":[1,2,3]},"status":"ok"}
                   for i,name in enumerate(["rhythm.librosa-beat","semantic.clap-open-vocabulary"])]}
 def test_authenticated_api_path_and_full_module(self):
  seen=[]
  payload=fetch_items(153,lambda path:seen.append(path) or self.payload())
  self.assertEqual(seen,["/internal/analysis/desktop/profile/153/scientific-items"])
  self.assertEqual(payload["items"][1]["module"]["scores"],[1,2,3])
  self.assertEqual(describe_items(payload)["item_total"],2)
 def test_missing_items_rejected(self):
  x=self.payload();x["items"].pop()
  with self.assertRaisesRegex(ValueError,"coverage_mismatch"):
   fetch_items(153,lambda path:x)
 def test_duplicate_rejected(self):
  x=self.payload();x["items"][1]["item_id"]=x["items"][0]["item_id"]
  with self.assertRaisesRegex(ValueError,"duplicate"):
   fetch_items(153,lambda path:x)
 def test_module_identity_rejected(self):
  x=self.payload();x["items"][0]["module"]["id"]="other"
  with self.assertRaisesRegex(ValueError,"module_mismatch"):
   fetch_items(153,lambda path:x)
