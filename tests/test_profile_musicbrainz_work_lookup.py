"""MusicBrainz work credits: documentary even when recording identity is ambiguous."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from profile_auto_review import _musicbrainz_work, enrich_review_payload_with_documentary

WORK_ID="b3b3b3b3-1111-2222-3333-444444444444"

class FakeHttp:
    request_count=0
    class Budget:
        max_requests_per_item=10
    budget=Budget()
    def get_json(self,url,**kwargs):
        self.request_count+=1
        if "/work/?" in url:
            return {"works":[{"id":WORK_ID,"title":"Dance Me to the End of Love"}]}
        return {"title":"Dance Me to the End of Love","relations":[
            {"target-type":"artist","type":"composer","artist":{"name":"Leonard Cohen"}},
            {"target-type":"artist","type":"lyricist","artist":{"name":"Leonard Cohen"}}]}

class WorkLookup(unittest.TestCase):
    def test_work_credit_without_recording(self):
        source=_musicbrainz_work(FakeHttp(),"Dance Me to the End of Love","Leonard Cohen")
        self.assertTrue(source["available"])
        row={"normalized_identity":{"title":"Dance Me to the End of Love","artist":"Leonard Cohen"}}
        research={"sources":[{"source":"MusicBrainz","available":False,
                              "reason":"ambiguous_recording_identity"},source]}
        suggestions=enrich_review_payload_with_documentary(
            {"comparison":{}},row,research)["comparison"]["documentary_catalogue_suggestions"]
        self.assertEqual(suggestions["work"]["composers"][0]["value"],"Leonard Cohen")
        self.assertEqual(suggestions["work"]["lyricists"][0]["value"],"Leonard Cohen")
        self.assertFalse(suggestions["recording_identity_verified"])
        self.assertFalse(suggestions["identity_verified"])

    def test_unrelated_artist_is_not_credited(self):
        source=_musicbrainz_work(FakeHttp(),"Dance Me to the End of Love","Unrelated Artist")
        self.assertFalse(source["available"])

if __name__=="__main__":
    unittest.main()
