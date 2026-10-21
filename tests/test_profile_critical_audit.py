import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"app"))
from profile_critical_audit import audit

def sample():
    results=[]
    for i,name in enumerate(("tonal.first","tonal.second"),1):
        results.append({"item_id":name,"index":i,"status":"completed","source_sha256":"a"*64,"assessment":{"status":"completed","supporting_evidence":[],"conflicting_evidence":[],"uncertainty":"uncalibrated"}})
    return {"schema":"ezstudio.diagnostics.main.v1","producer":"assistant","run_id":153,"revision_id":52,"fields":{"run_id":153,"id":52,"comparison_json":{"module_consultations":{"complete":True,"item_total":2,"examined":2,"results":results},"assistant_ai":{"coverage":{"scored_count":0,"total_count":5}}}}}
class AuditTest(unittest.TestCase):
    def test_findings_and_immutable_output(self):
        source=sample()
        result=audit(source)
        self.assertEqual(result["module_total"],2)
        self.assertEqual({f["code"] for f in result["findings"]},{"NO_CONTRADICTIONS_REPORTED","TONAL_CALIBRATION_UNVERIFIED","ZERO_VALIDATED_DIMENSIONS"})
        self.assertTrue(result["no_preset_mutation"])
        self.assertEqual(result,audit(source))
    def test_reject_incomplete(self):
        source=sample()
        source["fields"]["comparison_json"]["module_consultations"]["examined"]=1
        with self.assertRaises(ValueError):audit(source)
    def test_reject_duplicate(self):
        source=sample()
        source["fields"]["comparison_json"]["module_consultations"]["results"][1]["item_id"]="tonal.first"
        with self.assertRaises(ValueError):audit(source)

if __name__=="__main__":unittest.main()
