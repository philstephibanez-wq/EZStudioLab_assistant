from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from profile_review import normalize_track_identity


class V11BIdentityNormalizationContract(unittest.TestCase):
    def check_case(self, raw_title, expected_title, expected_artist):
        value = normalize_track_identity({"title": raw_title, "artist": ""})
        self.assertEqual(value["title"], expected_title)
        self.assertEqual(value["artist"], expected_artist)
        self.assertTrue(value["requires_verification"])

    def test_catalogue_cases(self):
        cases = [
            ("Breakfast In America - Supertramp", "Breakfast In America", "Supertramp"),
            ("Dance Me to the End of Love -  Leonard Cohen - Gmin", "Dance Me to the End of Love", "Leonard Cohen"),
            ("La fille du père Noël- Jacques Dutronc", "La fille du père Noël", "Jacques Dutronc"),
            ("La maladie d’amour - Michel Sardou (C)", "La maladie d’amour", "Michel Sardou"),
            ("Les Champs-Elysées - Joe Dassin(C)", "Les Champs-Elysées", "Joe Dassin"),
            ("My Sweet Lord - G.Harison - 121bpm - G#min", "My Sweet Lord", "G.Harison"),
            ("Ring of Fire - Johny Cash - 105bpm - Gmaj", "Ring of Fire", "Johny Cash"),
            ("Sarbacane - Francis Cabrel  (1989)", "Sarbacane", "Francis Cabrel"),
        ]
        for raw, title, artist in cases:
            with self.subTest(raw=raw):
                self.check_case(raw, title, artist)

    def test_missing_artist_stays_unresolved(self):
        value = normalize_track_identity({
            "title": "Dance Me to the End of Love",
            "artist": "",
        })
        self.assertEqual(value["artist"], "")
        self.assertEqual(value["method"], "catalog_incomplete")
        self.assertTrue(value["requires_verification"])


if __name__ == "__main__":
    unittest.main()
