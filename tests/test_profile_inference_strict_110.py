import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_inference_strict_benchmark import strict_validate,SCHEMA
class StrictTest(unittest.TestCase):
 def setUp(self):self.docs=[{"url":"https://test.example","text":"Piano. Tempo : 90 BPM."}]
 def test_valid(self):
  f={"facts":[{"item":"instrument.piano","value":"present","source_url":"https://test.example","quote":"Piano"}]}
  self.assertEqual(len(strict_validate(f,self.docs)["accepted"]),1)
 def test_wrong_field(self):
  f={"facts":[{"item":"canonical id","value":"instrument.piano","source_url":"https://test.example","quote":"Piano"}]}
  self.assertEqual(len(strict_validate(f,self.docs)["rejected"]),1)
 def test_wrong_measurement_quote(self):
  f={"facts":[{"item":"tempo","value":"92 BPM","source_url":"https://test.example","quote":"90 BPM"}]}
  self.assertEqual(len(strict_validate(f,self.docs)["rejected"]),1)
 def test_schema_ids(self):
  self.assertIn("instrument.piano",SCHEMA["properties"]["facts"]["items"]["properties"]["item"]["enum"])
if __name__=="__main__":unittest.main()
