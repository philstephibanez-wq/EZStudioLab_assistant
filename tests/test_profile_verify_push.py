"""Tests du receveur XPS; sans API réelle ni réseaux."""
import unittest
from unittest.mock import patch
from runtime.profile_verify_push import ITEMS, process

class PushProtocolTests(unittest.TestCase):
    def test_authenticated_request(self):
        payload = {"_auth_token": "TEST_NON_SECRET", "expertise_type": "profile",
            "analysis_id": 142, "preset_id": None, "title": "Title", "artist": "Artist",
            "items": {key: "present" for key in ITEMS}, "diagnostics": {"token": "SECRET"}}
        with patch("runtime.profile_verify_push.research_assertions", return_value={"items": [], "status": "completed", "technical_errors": 0}):
            result = process(payload, token_reader=lambda _: "TEST_NON_SECRET")
        self.assertEqual(result["expertise_type"], "profile")
        self.assertEqual(len(result["reviews"]), 10)
        self.assertEqual({r["verdict"] for r in result["reviews"].values()}, {"non_trouve"})
        self.assertNotIn("SECRET", str(result))
    def test_rejects_wrong_token(self):
        with self.assertRaises(PermissionError):
            process({"_auth_token": "wrong"}, token_reader=lambda _: "expected")

if __name__ == "__main__":
    unittest.main()
