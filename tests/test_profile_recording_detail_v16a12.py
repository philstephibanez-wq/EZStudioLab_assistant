import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_auto_review import _musicbrainz

MBID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
class SimulatedHttp:
    request_count=0
    class budget:
        max_requests_per_item=10
    def get_json(self, url, retries=1):
        self.request_count+=1
        if "/recording/?" in url:
            return {"recordings":[{"id":MBID, "title":"Wish You Were Here",
                    "score":100, "artist-credit":[{"name":"Pink Floyd"}]}]}
        if "/recording/" in url:
            raise ConnectionError("simulated detail outage")
        return {}

class RecordingDetailDiagnostic(unittest.TestCase):
    def test_detail_outage_is_visible_not_silent(self):
        value=_musicbrainz(SimulatedHttp(),"Wish You Were Here","Pink Floyd")
        self.assertEqual(value["recording_detail_status"],"unavailable")
        self.assertEqual(value["recording_detail_error"],"ConnectionError")
        self.assertEqual(value["recording_credits"],[])

if __name__=="__main__":
    unittest.main()
