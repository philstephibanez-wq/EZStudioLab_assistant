"""Advisory musical judgement must survive independent proof abstention."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from ai_provider import LocalAIProvider

class MusicalAdvisoryContract(unittest.TestCase):
    def test_advisory_survives_no_external_evidence(self):
        raw = {"summary":"Avis consultatif", "dimensions":{
            "genre":{"decision":"not_scored","confidence":None,"evidence":[],
                     "advisory":"Le genre folk est plausible selon les propositions LAB.",
                     "certainty":"moyenne","recommendation":"Comparer avec folk-rock."}
        }}
        result=LocalAIProvider._validate_local_result(raw,model="test",sent_evidence={})
        genre=result["dimensions"]["genre"]
        self.assertEqual(genre["decision"],"not_scored")
        self.assertIsNone(genre["confidence"])
        self.assertEqual(genre["certainty"],"moyenne")
        self.assertIn("folk", genre["advisory"])
        self.assertIn("folk-rock",genre["recommendation"])
    def test_invalid_certainty_cannot_be_fabricated(self):
        raw={"dimensions":{"choir":{"decision":"not_scored","certainty":"99%","advisory":"Peut être présent."}}}
        result=LocalAIProvider._validate_local_result(raw,model="test",sent_evidence={})
        self.assertEqual(result["dimensions"]["choir"]["certainty"],"indéterminée")
