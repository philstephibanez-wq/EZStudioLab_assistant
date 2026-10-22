import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_auto_review import _musicbrainz

class Http:
    request_count=0
    class budget:
        max_requests_per_item=10
    def get_json(self,url,retries=1):
        self.request_count+=1
        return {"recordings":[
            {"id":"7378974f-bcba-4132-b06f-ef466133eee7","title":"Wish You Were Here","score":100,"artist-credit":[{"name":"Pink Floyd"}]},
            {"id":"1aa9b751-90e9-4e9a-8703-490f8add0d4f","title":"Wish You Were Here","score":100,"artist-credit":[{"name":"Pink Floyd"}]}]}

class StableIdentity(unittest.TestCase):
    def test_multiple_exact_recordings_abstain_not_pick_random(self):
        result=_musicbrainz(Http(),"Wish You Were Here","Pink Floyd")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"],"ambiguous_recording_identity")
        self.assertEqual(result["candidate_count"],2)

if __name__=="__main__":
    unittest.main()
