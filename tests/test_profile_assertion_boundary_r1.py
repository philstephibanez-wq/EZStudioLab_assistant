"""P0: frontière LAB->Assistant, fail-closed sur les items sans valeur.

Tests déterministes ; aucune requête réseau, aucune inférence musicale.
"""
import unittest
from unittest.mock import patch
from app.profile_assertions_contract import ITEMS, build_assertions
from runtime.profile_verify_push import verify


def request():
    return {"expertise_type": "profile", "analysis_id": 197, "preset_id": None,
            "title": "Morceau", "artist": "Interprète",
            "items": {key: None for key in ITEMS}}


class BoundaryR1(unittest.TestCase):
    def test_nested_module_object_rejected(self):
        data = request()
        data["items"]["genre"] = {"engine": "CLAP", "scores": [0.9]}
        with self.assertRaisesRegex(ValueError, "profile_item_value_invalid"):
            build_assertions(data)

    def test_instrument_nested_object_rejected(self):
        data = request()
        data["items"]["instruments"] = ["guitare", {"engine": "model"}]
        with self.assertRaisesRegex(ValueError, "profile_item_value_invalid"):
            build_assertions(data)

    def test_non_instrument_list_rejected(self):
        data = request()
        data["items"]["tempo"] = [120, 240]
        with self.assertRaisesRegex(ValueError, "profile_item_value_invalid"):
            build_assertions(data)

    def test_nonfinite_value_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=repr(value)):
                data = request()
                data["items"]["tempo"] = value
                with self.assertRaisesRegex(ValueError, "profile_item_value_invalid"):
                    build_assertions(data)

    def test_instruments_list_preserved_without_diagnostics(self):
        data = request()
        data["items"]["instruments"] = ["guitare", "piano", "possible"]
        data["diagnostics"] = {"module": "CLAP", "token": "PRIVATE"}
        projected = build_assertions(data)
        self.assertEqual(projected["items"]["instruments"], ["guitare", "piano"])
        self.assertNotIn("PRIVATE", repr(projected))
        self.assertNotIn("CLAP", repr(projected))

    def test_all_absent_never_calls_documentary_search(self):
        with patch("runtime.profile_verify_push.research_assertions") as search, \
             patch("runtime.profile_verify_push.consult", return_value={"status": "completed"}), \
             patch("runtime.profile_verify_push.booklet_ocr_enabled", return_value=False):
            result = verify(request())
        search.assert_not_called()
        self.assertEqual(result["technical_status"], "no_assertions")
        self.assertTrue(all(row["verdict"] == "sans_valeur_lab"
                            for row in result["reviews"].values()))

    def test_only_final_items_are_researched(self):
        data = request()
        data["items"]["tempo"] = 120.0
        data["items"]["mesure"] = "4/4"
        def fake_research(rows, identity):
            self.assertEqual({x["label"] for x in rows}, {"tempo", "mesure"})
            self.assertEqual(identity, {"title": "Morceau", "artist": "Interprète"})
            return {"items": [], "status": "completed", "technical_errors": 0}
        with patch("runtime.profile_verify_push.research_assertions", side_effect=fake_research), \
             patch("runtime.profile_verify_push.consult", return_value={"status": "completed"}), \
             patch("runtime.profile_verify_push.booklet_ocr_enabled", return_value=False):
            result = verify(data)
        self.assertEqual(result["reviews"]["tempo"]["verdict"], "non_trouve")
        self.assertEqual(result["reviews"]["choeurs"]["verdict"], "sans_valeur_lab")


if __name__ == "__main__":
    unittest.main()
