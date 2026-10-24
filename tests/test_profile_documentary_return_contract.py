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

if __name__=="__main__":
    unittest.main()
