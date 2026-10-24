"""Exercise the actual LAB-triggered process() without HTTP, GPU, or LAB mutation."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
script=ROOT/"runtime"/"profile_ai_requests_worker.py"
spec=importlib.util.spec_from_file_location("r39_live_worker",script)
worker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

class FakeClient:
    def __init__(self):
        self.sent=[]
    def submit_profile_review(self,payload):
        self.sent.append(payload)
        return {"ok":True,"revision":{"id":9001}}

class ActualWorkerIntegration(unittest.TestCase):
    def test_lab_to_worker_to_persisted_payload(self):
        url="https://musicbrainz.org/recording/12345678-1234-1234-1234-123456789abc"
        row={"run_id":113,"title":"Aline - Christophe",
             "normalized_identity":{"title":"Aline","artist":"Christophe"}}
        research={"sources":[{"source":"MusicBrainz","available":True,"score":99,
            "url":url,"canonical_title":"Aline","canonical_artist":"Christophe",
            "recording_credits":[]}],"warnings":[],"request_count":1}
        verification={"assertions":[{"key":"genre","verdict":"non_trouve"}]}
        client=FakeClient()
        with patch.object(worker,"api",return_value={"item":row}), \
             patch.object(worker,"research_public_sources",return_value=research), \
             patch.object(worker,"build_review_payload",return_value={
                 "run_id":113,"status":"draft","comparison":{"legacy":"intact"},
                 "consensus":{},"revision_key":"profile-113-old"}), \
             patch.object(worker,"verify_final_values",return_value=verification), \
             patch.object(worker,"research_each_assertion",return_value={"status":"unavailable","items":[]}), \
             patch.object(worker,"review_web_items",return_value={"status":"unavailable","items":[]}):
            result=worker.process(113,client)
        self.assertEqual(result["revision"],9001)
        self.assertEqual(len(client.sent),1)
        sent=client.sent[0]
        self.assertEqual(sent["status"],"draft")
        self.assertEqual(sent["comparison"]["legacy"],"intact")
        doc=sent["comparison"]["documentary_catalogue_suggestions"]
        self.assertEqual(doc["workflow"],"profile_auto_review")
        self.assertEqual(doc["work"]["full_title"]["value"],"Aline")
        self.assertEqual(doc["recording"]["performers"][0]["value"],"Christophe")
        self.assertEqual(doc["work"]["composers"],[])
        self.assertEqual(doc["work"]["lyricists"],[])
        self.assertEqual(doc["recording"]["arrangers"],[])
        self.assertFalse(doc["lab_write_allowed"])
        self.assertFalse(doc["identity_verified"])
        self.assertIn("final_verification",sent["comparison"])
        self.assertTrue(sent["revision_key"].startswith("profile-ui-qwen-113-"))

if __name__=="__main__":
    unittest.main()
