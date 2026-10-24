"""R36: noisy/concatenated search result headings stay advisory and clean."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_documentary_reconcile import _artist_from_hit, reconcile

class R36(unittest.TestCase):
    def test_concatenated_youtube(self):
        title = "Les Champs-Elysees"
        headline = "Joe Dassin - Les Champs-Elysees (Audio) - YouTubeJoe Dassin - Les Champs-Elysees (Official) - YouTube"
        self.assertEqual(_artist_from_hit(title, headline), ["Joe Dassin"])

    def test_lyrics_platform(self):
        self.assertEqual(_artist_from_hit("My Sweet Lord", "George Harrison - My Sweet Lord Lyrics | Genius Lyrics"), ["George Harrison"])

    def test_wrong_extraction(self):
        self.assertEqual(_artist_from_hit("Je laime à mourir", "Paroles Je l'aime à mourir par Francis Cabrel - Paroles.net ..."), [])

    def test_animals(self):
        self.assertEqual(_artist_from_hit("The House of the Rising Sun", "The Animals - House Of The Rising Sun (Official Music Video)"), ["The Animals"])

    def test_no_artists_from_title_only(self):
        self.assertEqual(_artist_from_hit("Dance Me to the End of Love", "Dance Me to the End of Love - Wikipedia"), [])

    def test_no_false_confirmation(self):
        result = reconcile("My Sweet Lord", "G.Harison", {"candidates": [
            {"url": "https://example.org", "title": "George Harrison - My Sweet Lord - YouTubeGenius Lyrics"}]}, [])
        self.assertTrue(result["documentary_links"][0]["artist_hint_supported"])
        self.assertFalse(result["work_identity_verified"])
        self.assertFalse(result["performer_identity_verified"])
        self.assertFalse(result["recording_identity_verified"])

if __name__ == "__main__":
    unittest.main()
