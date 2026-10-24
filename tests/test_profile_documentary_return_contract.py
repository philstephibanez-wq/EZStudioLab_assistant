"""Contract: documentary metadata is advisory, inside existing comparison."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_auto_review import enrich_review_payload_with_documentary

class DocumentaryReturnContract(unittest.TestCase):
    def test_payload_shape_unchanged(self):
        payload={"run_id":123,"status":"draft","comparison":{"legacy":"kept"},"consensus":{"keep":True}}
        row={"title":"Aline - Christophe","artist":"","normalized_identity":{"title":"Aline","artist":"Christophe"}}
        research={"sources":[{"source":"MusicBrainz","available":True,"url":"https://musicbrainz.org/recording/valid",
                   "canonical_artist":"Christophe","canonical_title":"Aline"}]}
        result=enrich_review_payload_with_documentary(payload,row,research)
        self.assertEqual(result["comparison"]["legacy"],"kept")
        self.assertEqual(result["consensus"],payload["consensus"])
        self.assertEqual(result["status"],"draft")
        doc=result["comparison"]["documentary_catalogue_suggestions"]
        self.assertTrue(doc["advisory_only"])
        self.assertFalse(doc["lab_write_allowed"])
        self.assertFalse(doc["identity_verified"])
        self.assertEqual(doc["work"]["lyricists"],[])
        self.assertEqual(doc["work"]["composers"],[])
        self.assertEqual(doc["recording"]["arrangers"],[])

    def test_missing_documentation_does_not_claim_credits(self):
        payload={"comparison":{}}
        row={"normalized_identity":{"title":"Folsom Prison Blues","artist":"Johnny Cash"}}
        result=enrich_review_payload_with_documentary(payload,row,{"sources":[]})
        doc=result["comparison"]["documentary_catalogue_suggestions"]
        self.assertEqual(doc["recording"]["performers"],[])
        self.assertFalse(doc["recording_identity_verified"])


    def test_realistic_musicbrainz_evidence(self):
        row={"normalized_identity":{"title":"Aline","artist":"Christophe"}}
        reference="https://musicbrainz.org/recording/12345678-1234-1234-1234-123456789abc"
        research={"sources":[{"source":"MusicBrainz","available":True,"score":98,
            "url":reference,"canonical_title":"Aline","canonical_artist":"Christophe",
            "recording_credits":[{"musician":"Musicien crédité","role":"instrument",
                                  "scope":"recording","source_url":reference}]}]}
        result=enrich_review_payload_with_documentary({"status":"draft","comparison":{}},row,research)
        doc=result["comparison"]["documentary_catalogue_suggestions"]
        self.assertEqual(doc["work"]["full_title"]["value"],"Aline")
        self.assertEqual(doc["recording"]["performers"][0]["value"],"Christophe")
        self.assertEqual(doc["recording"]["musician_credits"][0]["name"],"Musicien crédité")
        self.assertEqual(doc["work"]["lyricists"],[])
        self.assertEqual(doc["work"]["composers"],[])
        self.assertEqual(doc["recording"]["arrangers"],[])
        self.assertFalse(doc["recording_identity_verified"])

    def test_mismatched_recording_not_adopted(self):
        row={"normalized_identity":{"title":"Aline","artist":"Christophe"}}
        research={"sources":[{"source":"MusicBrainz","available":True,"score":99,
            "url":"https://musicbrainz.org/recording/1234",
            "canonical_title":"Aline","canonical_artist":"Other Artist"}]}
        doc=enrich_review_payload_with_documentary({"comparison":{}},row,research)["comparison"]["documentary_catalogue_suggestions"]
        self.assertEqual(doc["recording"]["performers"],[])
        self.assertFalse(doc["identity_verified"])

    def test_live_worker_process_wires_documentary_before_persistence(self):
        import ast
        worker=Path(__file__).resolve().parents[1]/"runtime"/"profile_ai_requests_worker.py"
        tree=ast.parse(worker.read_text(encoding="utf-8"))
        process=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="process")
        calls=[n.func.id for n in ast.walk(process)
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertIn("enrich_review_payload_with_documentary",calls)
        line_doc=next(n.lineno for n in ast.walk(process) if isinstance(n,ast.Call)
                      and isinstance(n.func,ast.Name) and n.func.id=="enrich_review_payload_with_documentary")
        line_submit=next(n.lineno for n in ast.walk(process) if isinstance(n,ast.Call)
                         and isinstance(n.func,ast.Attribute) and n.func.attr=="submit_profile_review")
        self.assertLess(line_doc,line_submit)

if __name__=="__main__":
    unittest.main()
