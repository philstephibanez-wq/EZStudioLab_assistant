import copy
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"app"))
from profile_scientific_crosscheck import crosscheck,digest

def fixture():
    modules=[]
    reviews=[]
    traces=[]
    for i,name in enumerate(["tonal.ks","tonal.cnn"],1):
        m={"id":name,"status":"ok","normalized":{"label":"C major"},"calibrated":{"confidence":0.2*i,"method":("heuristic" if i==1 else "softmax"),"status":"heuristic"}}
        modules.append(m)
        h=digest(m)
        reviews.append({"item_id":name,"index":i,"status":"completed","source_sha256":h,"assessment":{"status":"completed","supporting_evidence":[],"conflicting_evidence":[],"uncertainty":"uncertain"}})
        traces.append({"item_id":name,"index":i,"status":"completed","source_sha256":h,"qwen_request_sha256":"a"*64,"qwen_response_sha256":"b"*64})
    lab={"schema":"ezstudio.diagnostics.main.v1","producer":"lab","phase":"profile","run_id":153,"fields":{"id":153,"item":"profile","diagnostics_json":{"module_registry":{"modules":modules}}}}
    rev={"schema":"ezstudio.diagnostics.main.v1","producer":"assistant","run_id":153,"revision_id":52,"fields":{"run_id":153,"id":52,"comparison_json":{"module_consultations":{"complete":True,"item_total":2,"examined":2,"results":reviews},"assistant_ai":{"coverage":{"scored_count":0,"total_count":5}}}}}
    xps={"schema":"ezstudio.profile-execution-report.v1","run_id":153,"revision_id":52,"module_audit":{"records":traces}}
    return lab,rev,xps

class CrosscheckTest(unittest.TestCase):
    def test_verified_consensus_does_not_mean_ground_truth(self):
        result=crosscheck(*fixture())
        self.assertTrue(result["scientific_crosscheck_performed"])
        self.assertEqual(result["crosschecked_module_total"],2)
        self.assertEqual({x["code"] for x in result["scientific_findings"]},{"TONAL_LABEL_AGREEMENT","TONAL_CONFIDENCE_HETEROGENEOUS"})
        self.assertFalse(result["scientific_findings"][0]["ground_truth_validated"])
        self.assertEqual(result,crosscheck(*fixture()))
    def test_tampered_module_rejected(self):
        lab,rev,xps=fixture()
        lab["fields"]["diagnostics_json"]["module_registry"]["modules"][0]["normalized"]["label"]="D major"
        with self.assertRaisesRegex(ValueError,"provenance_mismatch"):crosscheck(lab,rev,xps)
    def test_trace_mismatch_rejected(self):
        lab,rev,xps=fixture()
        xps["module_audit"]["records"][1]["source_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"provenance_mismatch"):crosscheck(lab,rev,xps)
    def test_run_mismatch_rejected(self):
        lab,rev,xps=fixture()
        xps["run_id"]=154
        with self.assertRaisesRegex(ValueError,"identity_invalid"):crosscheck(lab,rev,xps)

if __name__=="__main__":unittest.main()
