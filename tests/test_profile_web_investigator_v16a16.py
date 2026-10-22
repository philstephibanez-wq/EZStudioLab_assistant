import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_web_investigator import research_each_assertion

ROW={"metrics":{"tempo":{"bpm":123.0},"time_signature":{"label":"4/4"}},
 "diagnostics":{"profile_view":{"tonal":{"label":"G major"},"genre_hierarchy":{"primary":{"genre":"rock"}},"instrumentation":{"candidates":[{"label":"guitar"}]},"vocal_profile":{"dimensions":{"lead_vocal":{"decision":"present"}}}}}}
ID={"title":"An unpublished original","artist":"Unknown personal artist"}
class FakeResponse:
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def read(self,n):return json.dumps({"output":[{"type":"web_search_call","status":"completed"},{"type":"message","content":[{"type":"output_text","text":"possible reference - NOT validation","annotations":[{"type":"url_citation","url":"https://example.org/music"}]}]}]}).encode()
class Investigator(unittest.TestCase):
 def test_one_real_web_tool_invocation_per_assertion(self):
  calls=[]
  def opener(req,timeout):
   data=json.loads(req.data.decode());calls.append(data)
   self.assertEqual(data["tools"],[{"type":"web_search"}])
   return FakeResponse()
  result=research_each_assertion(ROW,ID,opener=opener,api_key="fake",model="test")
  self.assertEqual(len(calls),len(result["items"]))
  self.assertEqual(result["searched"],6)
  self.assertTrue(all(x["status"]=="discovered" for x in result["items"]))
  self.assertTrue(all(x["eligible_for_verdict"] is False for x in result["items"]))
  self.assertFalse(result["automatic_verdicts"])
 def test_missing_credentials_no_requests_or_fake_verdict(self):
  result=research_each_assertion(ROW,ID,api_key="")
  self.assertEqual(result["status"],"unavailable")
  self.assertEqual(result["searched"],0)
 def test_no_model_citations_no_eligible_proof(self):
  class NoCite:
   def __enter__(self):return self
   def __exit__(self,*a):return False
   def read(self,n):return json.dumps({"output":[{"type":"message","content":[{"type":"output_text","text":"guitar"}]}]}).encode()
  result=research_each_assertion(ROW,ID,opener=lambda req,timeout:NoCite(),api_key="fake")
  self.assertTrue(all(x["status"]=="unverified" for x in result["items"]))
if __name__=="__main__":unittest.main()
