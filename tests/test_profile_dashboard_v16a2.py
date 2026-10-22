"""Dashboard PROFILE progression is independent of obsolete Qwen module events."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from web_status import _profile_consultation_status

class IndependentDashboardV16a2(unittest.TestCase):
    def test_real_stages_and_evidence_count(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/"run-128-abcdef123456"
            folder.mkdir()
            entries=[
                {"event":"trace.begin","data":{}},
                {"event":"research.begin","data":{"identity":{"title":"Test"}}},
                {"event":"profile.final_verification","data":{"assertions":[
                    {"key":"tempo","verdict":"non_trouve","sources":[]},
                    {"key":"instrument:0","verdict":"bon",
                     "sources":[{"url":"https://musicbrainz.org/recording/test"}]}]}},
                {"event":"lab.submit.response","data":{"ok":True,"revision":{"id":62}}},
                {"event":"trace.finish","data":{"status":"completed"}},
            ]
            (folder/"timeline.jsonl").write_text(
                "".join(json.dumps(e)+"\n" for e in entries),encoding="utf-8")
            with patch.dict(os.environ,{"EZS_PROFILE_TRACE_ROOT":temp}):
                state=_profile_consultation_status()
            self.assertEqual(state["state"],"completed")
            self.assertEqual(state["completed"],4)
            self.assertEqual(state["verified_count"],2)
            self.assertEqual(state["evidence_count"],1)
            self.assertEqual(state["revision"],62)
    def test_legacy_module_progress_does_not_claim_new_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/"run-120-abcdef123456"
            folder.mkdir()
            (folder/"timeline.jsonl").write_text(
                json.dumps({"event":"module.progress","data":{"item_index":12,"item_total":12}})+"\n",
                encoding="utf-8")
            with patch.dict(os.environ,{"EZS_PROFILE_TRACE_ROOT":temp}):
                state=_profile_consultation_status()
            self.assertEqual(state["state"],"not_started")

if __name__=="__main__":
    unittest.main()
