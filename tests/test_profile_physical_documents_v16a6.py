import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_physical_documents import discover_release_documents


ID = "12345678-1234-1234-1234-123456789abc"


class Http:
    request_count = 0
    budget = type("Budget", (), {"max_requests_per_item": 10})()
    def get_json(self, url, **kwargs):
        self.request_count += 1
        return {"images": [
            {"approved": True, "types": ["Front"], "image": "https://coverartarchive.org/front.jpg"},
            {"approved": True, "types": ["Booklet"], "image": "https://coverartarchive.org/booklet.jpg"},
            {"approved": True, "types": ["Back"], "image": "https://coverartarchive.org/back.jpg"},
            {"approved": False, "types": ["Booklet"], "image": "https://coverartarchive.org/rejected.jpg"},
            {"approved": True, "types": ["Booklet"], "image": "https://example.com/invalid.jpg"},
        ]}


class PhysicalDocuments(unittest.TestCase):
    def test_documents_are_discovered_but_never_proof(self):
        http = Http()
        rows = discover_release_documents(http, [ID])
        self.assertEqual(len(rows), 2)
        self.assertEqual(http.request_count, 1)
        self.assertEqual({tuple(x["types"]) for x in rows}, {("booklet",), ("back",)})
        self.assertTrue(all(x["evidence_eligible"] is False for x in rows))
        self.assertTrue(all(x["credit_text"] is None and x["track_attribution"] is None for x in rows))

    def test_invalid_release_and_budget_do_not_request_images(self):
        http = Http()
        self.assertEqual(discover_release_documents(http, ["not-a-uuid"]), [])
        self.assertEqual(http.request_count, 0)
        http.budget = type("Budget", (), {"max_requests_per_item": 0})()
        self.assertEqual(discover_release_documents(http, [ID]), [])
        self.assertEqual(http.request_count, 0)


if __name__ == "__main__":
    unittest.main()
