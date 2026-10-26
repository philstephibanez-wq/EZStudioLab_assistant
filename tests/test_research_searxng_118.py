import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from research_searxng import search,validate_endpoint,ResearchSearchError

class SearxSearchTests(unittest.TestCase):
 def test_loopback_only(self):
  for uri in ("https://127.0.0.1:8888","http://8.8.8.8:8888","http://localhost:8888?api_key=paid","http://user:secret@localhost:8888"):
   with self.assertRaises(ValueError):validate_endpoint(uri)
 def test_no_api_key_and_normalized_results(self):
  def mocked(url):
   self.assertIn("format=json",url)
   self.assertNotIn("key=",url)
   return json.dumps({"results":[{"url":"https://example.org/a","title":"Music","content":"review"},{"url":"https://example.org/a"},{"url":"file:///a"},{"url":"https://example.net/b"}]}).encode()
  result=search("eagles hotel california",transport=mocked)
  self.assertEqual(result["count"],2)
  self.assertEqual(result["status"],"discovery_only_no_documentary_verdict")
 def test_disabled_json_detected(self):
  with self.assertRaises(ResearchSearchError):
   search("music",transport=lambda _:b"<html>403 Forbidden</html>")
 def test_empty_query_rejected(self):
  with self.assertRaises(ValueError):search("")
 def test_malformed_result_rejected(self):
  with self.assertRaises(ResearchSearchError):
   search("music",transport=lambda _:json.dumps({"results":{}}).encode())
if __name__=="__main__":unittest.main()
