"""End-to-end synthetic contract for sanitized PROFILE trace backfill."""
import json
import pathlib
import sys
import tempfile
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"app"))
from backfill_profile_trace_report import select_trace
from profile_report import make_report

class BackfillReportTest(unittest.TestCase):
    def test_existing_twelve_modules_are_exported_without_raw_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            folder=root/"run-153-123456789abc"
            folder.mkdir()
            events=[{"event":"lab.submit.response","data":{"ok":True,"revision":{"id":52}}}]
            for i in range(12):
                events.append({"event":"module.review.completed","data":{
                    "item_id":f"module-{i}","index":i+1,"status":"completed",
                    "source_sha256":"a"*64,"duration_ms":123,
                    "assessment":{"status":"completed","summary":"Musical hypothesis","uncertainty":"Uncalibrated",
                                  "supporting_evidence":[{"score":.2}],"conflicting_evidence":[]}}})
            events.append({"event":"qwen.module.request","data":{"raw":"PRIVATE_PROMPT_NOT_FOR_ARCHIVE"}})
            (folder/"timeline.jsonl").write_text("\n".join(json.dumps(x) for x in events)+"\n",encoding="utf-8")
            found,timeline=select_trace(root,153,52)
            self.assertEqual(found,folder)
            trace=type("Mock",(),{"file":timeline,"run_id":153,"trace_id":"123456789abc"})()
            report=make_report(trace,{"revision":52})
            self.assertEqual(report["module_audit"]["count"],12)
            self.assertEqual(report["module_audit"]["records"][0]["assessment"]["summary"],"Musical hypothesis")
            self.assertNotIn("PRIVATE_PROMPT_NOT_FOR_ARCHIVE",json.dumps(report))
    def test_incomplete_run_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            folder=root/"run-153-123456789abc"
            folder.mkdir()
            (folder/"timeline.jsonl").write_text(json.dumps({"event":"lab.submit.response","data":{"ok":True,"revision":{"id":52}}})+"\n")
            with self.assertRaises(RuntimeError):
                select_trace(root,153,52)

if __name__=="__main__":
    unittest.main()
