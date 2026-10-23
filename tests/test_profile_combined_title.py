"""Contract tests for provisional identity hints and source provenance."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import profile_web_investigator as investigator


class CombinedTitleTests(unittest.TestCase):
    def test_combined_title_passed_to_search_and_evidence(self):
        seen_queries = []
        seen_identities = []

        def fake_search(query, max_results=10):
            seen_queries.append(query)
            return [{
                "title": "La fille du père Noël Jacques Dutronc",
                "snippet": "123 BPM", "url": "https://music.example.org/song",
            }]

        def fake_evaluate(assertion, identity, documents):
            seen_identities.append(identity)
            self.assertEqual(
                documents[0]["text"],
                "This is the actual downloaded document.",
            )
            self.assertNotIn("123 BPM", documents[0]["text"])
            return {"verdict": "non_trouve", "references": []}

        with patch.object(investigator, "search", side_effect=fake_search), \
             patch.object(investigator, "fetch_document", return_value={
                 "status": "read",
                 "url": "https://music.example.org/song",
                 "text": "This is the actual downloaded document.",
             }), \
             patch.object(investigator, "evaluate_live_documents", side_effect=fake_evaluate):
            result = investigator.research_assertions(
                [{"key": "tempo", "value": 123}],
                {"title": "La fille du père Noël- Jacques Dutronc", "artist": ""},
            )

        self.assertEqual(result["searched"], 1)
        self.assertTrue(seen_queries)
        self.assertTrue(all("Jacques Dutronc" in q for q in seen_queries))
        self.assertEqual(
            seen_identities,
            [{"title": "La fille du père Noël", "artist": "Jacques Dutronc"}],
        )

    def test_no_separator_does_not_invent_artist(self):
        with patch.object(investigator, "search", return_value=[]) as search:
            investigator.research_assertions(
                [{"key": "tempo", "value": 123}],
                {"title": "Music-Box", "artist": ""},
            )
        self.assertTrue(search.called)
        self.assertNotIn("Jacques Dutronc", search.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
