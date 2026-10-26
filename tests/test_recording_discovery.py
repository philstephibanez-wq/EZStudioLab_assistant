import io
import json
import unittest
from runtime.recording_discovery import canonical, discover


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class Tests(unittest.TestCase):
    def query(self, payload):
        def opener(request, timeout):
            self.assertEqual(request.full_url.split("/ws/")[0], "https://musicbrainz.org")
            self.assertEqual(timeout, 20)
            return Response(json.dumps(payload).encode("utf-8"))
        return discover({"title": "Été", "artist": "Artiste"}, opener=opener)

    def test_exact_title_artist_only(self):
        rows = self.query({"recordings": [
            {"id": "12345678-1234-1234-1234-123456789abc", "title": "Ete", "artist-credit": [{"name": "Artiste"}]},
            {"id": "12345678-1234-1234-1234-123456789abd", "title": "Été", "artist-credit": [{"name": "Autre"}]}]})["candidates"]
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["musical_claims_verified"])
        self.assertEqual(rows[0]["recording_identity"], "candidate_only")

    def test_no_hit_means_no_verdict(self):
        r = self.query({"recordings": []})
        self.assertEqual(r["candidates"], [])
        self.assertIsNone(r["musical_verdict"])

    def test_untrusted_id_excluded(self):
        r = self.query({"recordings": [{"id": "../../attack", "title": "Été", "artist-credit": [{"name": "Artiste"}]}]})
        self.assertEqual(r["candidates"], [])

    def test_invalid_identity_rejected(self):
        with self.assertRaises(ValueError):
            discover({"title": "", "artist": "X"}, opener=lambda *a, **k: None)

    def test_canonical_accents(self):
        self.assertEqual(canonical("Été"), canonical("Ete"))


if __name__ == "__main__":
    unittest.main()
