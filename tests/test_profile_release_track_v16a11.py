import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_release_track_credits import track_credits_on_release

RELEASE="12345678-1234-1234-1234-123456789abc"
RECORD="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OTHER="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

class FakeHttp:
    request_count=0
    class budget:
        max_requests_per_item=10
    def get_json(self,url,retries=0):
        self.request_count+=1
        return {"media":[{"tracks":[
            {"recording":{"id":OTHER,"relations":[{"target-type":"artist","type":"instrument",
              "artist":{"name":"Wrong Song"},"attributes":["acoustic guitar"]}]}},
            {"recording":{"id":RECORD,"relations":[{"target-type":"artist","type":"instrument",
              "artist":{"name":"Correct Song"},"attributes":["acoustic guitar"]}]}}
        ]}]}

class EditionCreditsTests(unittest.TestCase):
    def test_exact_recording_only(self):
        got=track_credits_on_release(FakeHttp(),[RELEASE],RECORD)
        self.assertEqual(len(got),1)
        self.assertEqual(got[0]["musician"],"Correct Song")
        self.assertEqual(got[0]["scope"],"recording")
    def test_invalid_id_no_request(self):
        http=FakeHttp()
        self.assertEqual(track_credits_on_release(http,[RELEASE],"invalid"),[])
        self.assertEqual(http.request_count,0)
    def test_release_wide_credit_is_not_inherited(self):
        class AlbumHttp(FakeHttp):
            def get_json(self,url,retries=0):
                self.request_count+=1
                return {"relations":[{"target-type":"artist","type":"instrument",
                          "artist":{"name":"Album musician"},"attributes":["electric guitar"]}],
                        "media":[{"tracks":[{"recording":{"id":RECORD,"relations":[]}}]}]}
        self.assertEqual(track_credits_on_release(AlbumHttp(),[RELEASE],RECORD),[])

if __name__=="__main__":
    unittest.main()
