import ast
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from profile_sequential_review import examine_modules
class R15AContract(unittest.TestCase):
 def test_worker_wires_one_sequential_loop_before_persistence(self):
  tree=ast.parse((ROOT/"runtime/profile_ai_requests_worker.py").read_text(encoding="utf-8"))
  process=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="process")
  names=[n.func.id for n in ast.walk(process) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
  self.assertEqual(names.count("examine_modules"),1)
  self.assertIn("submit_profile_review",ast.unparse(process))
 def test_twelve_full_modules_all_examined_once(self):
  names=[f"module-{i}" for i in range(12)]
  payload={"schema":"ezstudio.profile-scientific-items.r1","run_id":153,"item_total":12,
           "coverage":{"registry_total":12,"returned":12,"complete_for_registry":True},
           "items":[{"item_id":name,"index":i+1,"source_pointer":"/diagnostics/module_registry/modules/"+str(i),
                     "module":{"id":name,"scores":[i,1,2,3]}} for i,name in enumerate(names)]}
  seen=[]
  result=examine_modules(153,lambda path:payload,lambda request:seen.append(request["item_id"]) or {"status":"abstain","summary":"unknown"})
  self.assertEqual(seen,names)
  self.assertEqual(result["examined"],12)
  self.assertTrue(result["complete"])
