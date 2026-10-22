"""Regression: recording-scoped artist credits must be explicitly requested."""
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_auto_review import _musicbrainz

class FakeHttp:
    def __init__(self):
        self.urls=[]
        self.request_count=0
        self.budget=type("Budget", (), {"max_requests_per_item": 2})()
    def get_json(self,url, **kwargs):
        self.urls.append(url)
        self.request_count+=1
        if "query=" in url:
            return {"recordings":[{"id":"12345678-1234-1234-1234-123456789abc",
                "title":"Example Track","score":100,
                "artist-credit":[{"name":"Example Artist"}]}]}
        return {"title":"Example Track","artist-credit":[{"name":"Example Artist"}],
            "relations":[{"target-type":"artist","type":"instrument",
                "artist":{"name":"A Musician"},
                "instrument":{"name":"guitar"},
                "attributes":[]}]}

class MusicBrainzV16a1(unittest.TestCase):
    def test_recording_requests_artist_relations_for_performer_credits(self):
        http=FakeHttp()
        result=_musicbrainz(http,"Example Track","Example Artist")
        self.assertEqual(len(http.urls),2)
        includes=parse_qs(urlparse(http.urls[1]).query)["inc"][0].split("+")
        self.assertIn("artist-rels",includes)
        self.assertEqual(result["recording_credits"][0]["instruments"],["guitar"])
        self.assertEqual(result["recording_credits"][0]["scope"],"recording")

class RecordingIdentityV16a4(unittest.TestCase):
    def test_year_suffix_is_not_a_song_title(self):
        http=FakeHttp()
        _musicbrainz(http,"Example Track (1964)","Example Artist")
        query=parse_qs(urlparse(http.urls[0]).query)["query"][0]
        self.assertIn('recording:"Example Track"',query)
        self.assertNotIn("1964",query)

    def test_unrelated_candidate_is_rejected_without_fetching_details(self):
        class WrongHttp(FakeHttp):
            def get_json(self,url,**kwargs):
                self.urls.append(url)
                self.request_count+=1
                return {"recordings":[{"id":"12345678-1234-1234-1234-123456789abc",
                    "title":"Unrelated Track","score":98,
                    "artist-credit":[{"name":"Example Artist"}]}]}
        http=WrongHttp()
        result=_musicbrainz(http,"Example Track","Example Artist")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"],"no_matching_recording")
        self.assertEqual(len(http.urls),1)

if __name__=="__main__":
    unittest.main()
