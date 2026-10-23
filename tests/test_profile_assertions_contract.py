"""Tests durables du contrat minimal PROFILE. Sans requête réseau."""
import unittest
from app.profile_assertions_contract import ITEMS, build_assertions, validate_verdicts


class ProfileAssertionsContractTest(unittest.TestCase):
    def setUp(self):
        self.source = {
            "analysis_id": 153, "preset_id": 12, "title": "Titre",
            "artist": "Interprète", "engine": "CLAP",
            "config": {"token": "SECRET"}, "metrics": {"score": .9},
            "items": {item: "valeur" for item in ITEMS},
        }

    def review(self, request):
        return {
            "analysis_id": request["analysis_id"],
            "preset_id": request["preset_id"],
            "reviews": {item: {"verdict": "non_trouve", "evidence": [],
                               "confidence_pct": None} for item in ITEMS},
        }

    def test_strict_allowlist(self):
        request = build_assertions(self.source)
        self.assertEqual(len(request["items"]), 10)
        for forbidden in ("CLAP", "SECRET", "engine", "config", "metrics"):
            self.assertNotIn(forbidden, repr(request))

    def test_missing_value(self):
        self.source["items"]["choeurs"] = "inconclusive"
        request = build_assertions(self.source)
        self.assertIsNone(request["items"]["choeurs"])
        result = self.review(request)
        result["reviews"]["choeurs"]["verdict"] = "sans_valeur_lab"
        self.assertTrue(validate_verdicts(request, result))

    def test_abstention(self):
        request = build_assertions(self.source)
        self.assertTrue(validate_verdicts(request, self.review(request)))

    def test_wrong_analysis(self):
        request = build_assertions(self.source)
        result = self.review(request)
        result["analysis_id"] = 12
        with self.assertRaises(ValueError):
            validate_verdicts(request, result)

    def test_unproven_bon(self):
        request = build_assertions(self.source)
        result = self.review(request)
        result["reviews"]["tempo"]["verdict"] = "bon"
        with self.assertRaises(ValueError):
            validate_verdicts(request, result)

    def test_uncalibrated_confidence(self):
        request = build_assertions(self.source)
        result = self.review(request)
        result["reviews"]["tempo"]["confidence_pct"] = 87
        with self.assertRaises(ValueError):
            validate_verdicts(request, result)

    def test_preset_absent_is_explicit(self):
        self.source["preset_id"] = None
        request = build_assertions(self.source)
        self.assertIsNone(request["preset_id"])
        self.assertTrue(validate_verdicts(request, self.review(request)))

    def test_mismatched_preset(self):
        request = build_assertions(self.source)
        result = self.review(request)
        result["preset_id"] += 1
        with self.assertRaises(ValueError):
            validate_verdicts(request, result)


if __name__ == "__main__":
    unittest.main()
