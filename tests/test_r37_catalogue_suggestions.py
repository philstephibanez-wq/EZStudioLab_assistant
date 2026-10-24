"""R37 advisory catalogue payload contract."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_catalogue_suggestions import build_catalogue_suggestions

class R37(unittest.TestCase):
    def test_corrob_performer(self):
        result = build_catalogue_suggestions("My Sweet Lord", "G.Harison", {
            "documentary_links": [{"url":"https://example.org/harrison",
                "artist_candidates_extracted":["George Harrison"]}]})
        self.assertEqual(result["recording"]["performers"][0]["value"], "George Harrison")
        self.assertEqual(result["recording"]["performers"][0]["status"], "corroborated")
        self.assertEqual(result["work"]["full_title"]["original"], "My Sweet Lord")
        self.assertFalse(result["lab_write_allowed"])
        self.assertFalse(result["identity_verified"])

    def test_unknown_creators_not_invented(self):
        result = build_catalogue_suggestions("Dance Me to the End of Love", None, {})
        self.assertEqual(result["work"]["lyricists"], [])
        self.assertEqual(result["work"]["composers"], [])
        self.assertEqual(result["recording"]["arrangers"], [])
        self.assertEqual(result["recording"]["performers"], [])
        self.assertEqual(result["missing"]["performers"], "not_documented")

    def test_ambiguous_performer(self):
        result = build_catalogue_suggestions("A Song", "John Smith", {
            "documentary_links":[
                {"url":"https://example.org/one","artist_candidates_extracted":["John Smith"]},
                {"url":"https://example.org/two","artist_candidates_extracted":["Smith John"]}]})
        self.assertEqual(result["recording"]["performers"], [])

    def test_no_http_evidence(self):
        result = build_catalogue_suggestions("My Sweet Lord", "G.Harison", {
            "documentary_links":[{"url":"http://example.org", "artist_candidates_extracted":["George Harrison"]}]})
        self.assertEqual(result["recording"]["performers"], [])

if __name__ == "__main__":
    unittest.main()
