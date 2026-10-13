from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from profile_auto_review import NetworkBudget, build_review_payload


class ProfileAutoReviewContract(unittest.TestCase):
    def _row(self):
        return {
            "run_id": 111,
            "title": "Breakfast In America - Supertramp",
            "artist": "",
            "diagnostics": {
                "profile_view": {
                    "genre_hierarchy": {
                        "primary": {"genre": "singer-songwriter"}
                    },
                    "vocal_profile": {
                        "dimensions": {
                            "lead_vocal": {"decision": "present"},
                            "backing_vocals": {"decision": "possible"},
                            "choir": {"decision": "inconclusive"},
                        }
                    },
                    "instrumentation": {
                        "candidates": [{"label": "guitar"}]
                    },
                }
            },
        }

    def test_completed_when_two_sources_and_confidence(self):
        research = {
            "status": "ok",
            "request_count": 4,
            "warnings": [],
            "sources": [
                {
                    "source": "MusicBrainz",
                    "available": True,
                    "url": "https://musicbrainz.org/recording/x",
                    "score": 100,
                    "canonical_title": "Breakfast In America",
                    "canonical_artist": "Supertramp",
                    "genres": ["progressive rock", "pop rock"],
                    "instruments": ["guitar", "bass guitar", "drums"],
                    "lead_vocals": True,
                    "backing_vocals": True,
                    "performers": [],
                },
                {
                    "source": "Wikidata",
                    "available": True,
                    "url": "https://www.wikidata.org/wiki/Q1",
                    "label": "Breakfast In America",
                    "genres": ["rock"],
                    "performers": ["Supertramp"],
                    "description": "song by Supertramp",
                },
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "completed")
        self.assertTrue(payload["identity"]["external_identity_verified"])
        self.assertEqual(payload["identity"]["external_identity_source"], "MusicBrainz")
        self.assertGreaterEqual(payload["confidence"], 0.75)
        self.assertEqual(payload["comparison"]["genre"]["decision"], "mismatch")
        self.assertEqual(payload["comparison"]["lead_vocal"]["decision"], "match")
        self.assertEqual(payload["comparison"]["backing_vocals"]["decision"], "underconfident_match")
        self.assertEqual(payload["comparison"]["choir"]["decision"], "not_inferred_from_backing_vocals")

    def test_draft_when_identity_is_not_externally_verified(self):
        research = {
            "status": "ok",
            "request_count": 4,
            "warnings": [],
            "sources": [
                {
                    "source": "MusicBrainz",
                    "available": True,
                    "url": "https://musicbrainz.org/recording/x",
                    "score": 100,
                    "canonical_title": "Different Song",
                    "canonical_artist": "Different Artist",
                    "genres": ["rock"],
                },
                {
                    "source": "Wikidata",
                    "available": True,
                    "url": "https://www.wikidata.org/wiki/Q1",
                    "genres": ["rock"],
                    "performers": ["Supertramp"],
                },
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "draft")
        self.assertFalse(payload["identity"]["external_identity_verified"])

    def test_irrelevant_wikipedia_does_not_make_review_completed(self):
        research = {
            "status": "ok",
            "request_count": 4,
            "warnings": [],
            "sources": [
                {
                    "source": "MusicBrainz",
                    "available": True,
                    "url": "https://musicbrainz.org/recording/x",
                    "score": 100,
                    "canonical_title": "Breakfast In America",
                    "canonical_artist": "Supertramp",
                    "genres": ["progressive rock", "pop rock"],
                    "instruments": [],
                    "performers": [],
                },
                {
                    "source": "Wikipedia",
                    "available": True,
                    "url": "https://en.wikipedia.org/wiki/The_Best_of_Leonard_Cohen",
                    "title": "The Best of Leonard Cohen",
                    "extract": "A greatest hits album by Leonard Cohen released in 1975.",
                    "genres": [],
                    "performers": [],
                },
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(len(payload["sources"]), 1)
        self.assertLess(payload["confidence"], 0.75)
        self.assertEqual(payload["external_validation"]["confidence_band"], "moderate")
        self.assertEqual(payload["external_validation"]["scored_dimensions"], ["genre"])



    def test_identity_only_sources_do_not_complete_profile_review(self):
        research = {
            "status": "ok",
            "request_count": 4,
            "warnings": [],
            "sources": [
                {
                    "source": "MusicBrainz",
                    "available": True,
                    "url": "https://musicbrainz.org/recording/x",
                    "score": 100,
                    "canonical_title": "Breakfast In America",
                    "canonical_artist": "Supertramp",
                    "genres": [],
                    "instruments": ["live"],
                    "lead_vocals": False,
                    "backing_vocals": False,
                    "performers": [],
                },
                {
                    "source": "Wikipedia",
                    "available": True,
                    "url": "https://en.wikipedia.org/wiki/Supertramp",
                    "title": "Supertramp",
                    "extract": "Supertramp is an English band whose songs include Breakfast in America.",
                    "genres": [],
                    "instruments": [],
                    "performers": [],
                },
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(payload["consensus"]["external_identity_source_count"], 2)
        self.assertEqual(payload["consensus"]["external_profile_evidence_source_count"], 0)
        self.assertEqual(payload["consensus"]["instruments_credited_or_related"], [])



    def test_artist_wikipedia_page_never_counts_as_profile_evidence(self):
        research = {
            "status": "ok",
            "request_count": 4,
            "warnings": [],
            "sources": [
                {
                    "source": "MusicBrainz",
                    "available": True,
                    "url": "https://musicbrainz.org/recording/x",
                    "score": 100,
                    "canonical_title": "Breakfast In America",
                    "canonical_artist": "Supertramp",
                    "genres": [],
                    "instruments": ["live"],
                    "lead_vocals": False,
                    "backing_vocals": False,
                    "performers": [],
                },
                {
                    "source": "Wikipedia",
                    "available": True,
                    "url": "https://en.wikipedia.org/wiki/Supertramp",
                    "title": "Supertramp",
                    "extract": "Supertramp is a rock band. Breakfast in America is one of its songs.",
                    "genres": [],
                    "instruments": [],
                    "performers": [],
                },
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(payload["consensus"]["external_profile_evidence_source_count"], 0)

    def test_wikipedia_song_page_can_contribute_profile_evidence(self):
        research = {
            "status": "ok",
            "request_count": 4,
            "warnings": [],
            "sources": [
                {
                    "source": "MusicBrainz",
                    "available": True,
                    "url": "https://musicbrainz.org/recording/x",
                    "score": 100,
                    "canonical_title": "Breakfast In America",
                    "canonical_artist": "Supertramp",
                    "genres": ["rock"],
                    "instruments": [],
                    "lead_vocals": False,
                    "backing_vocals": False,
                    "performers": [],
                },
                {
                    "source": "Wikipedia",
                    "available": True,
                    "url": "https://en.wikipedia.org/wiki/Breakfast_in_America_(song)",
                    "title": "Breakfast In America",
                    "extract": "Breakfast in America is a rock song by Supertramp with guitar and keyboard.",
                    "genres": [],
                    "instruments": [],
                    "performers": [],
                },
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["consensus"]["external_profile_evidence_source_count"], 2)




    def test_musicbrainz_tags_are_profile_genre_evidence(self):
        research = {
            "status": "available",
            "request_count": 3,
            "warnings": [],
            "sources": [
                {
                    "source": "MusicBrainz",
                    "available": True,
                    "url": "https://musicbrainz.org/recording/x",
                    "score": 100,
                    "canonical_title": "Breakfast In America",
                    "canonical_artist": "Supertramp",
                    "genres": [],
                    "tags": ["progressive rock", "pop rock"],
                    "instruments": [],
                    "lead_vocals": False,
                    "backing_vocals": False,
                    "performers": [],
                }
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["external_validation"]["scored_dimensions"], ["genre"])
        self.assertEqual(payload["comparison"]["genre"]["decision"], "mismatch")
        self.assertIn("progressive rock", payload["consensus"]["genre_labels"])


    def test_single_reliable_reference_can_complete_only_the_scored_dimension(self):
        research = {
            "status": "available",
            "request_count": 2,
            "warnings": [],
            "sources": [
                {
                    "source": "MusicBrainz",
                    "available": True,
                    "url": "https://musicbrainz.org/recording/x",
                    "score": 100,
                    "canonical_title": "Breakfast In America",
                    "canonical_artist": "Supertramp",
                    "genres": ["pop rock"],
                    "instruments": [],
                    "lead_vocals": False,
                    "backing_vocals": False,
                    "performers": [],
                }
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "completed")
        self.assertTrue(payload["external_validation"]["available"])
        self.assertFalse(payload["external_validation"]["analysis_dependency"])
        self.assertTrue(payload["external_validation"]["unscored_dimensions_unchanged"])
        self.assertEqual(payload["external_validation"]["scored_dimensions"], ["genre"])
        self.assertEqual(payload["comparison"]["genre"]["decision"], "mismatch")
        self.assertEqual(payload["comparison"]["lead_vocal"]["decision"], "not_scored")
        self.assertEqual(payload["comparison"]["instrumentation"]["decision"], "not_scored")

    def test_no_reliable_profile_reference_has_no_effect_on_other_dimensions(self):
        research = {
            "status": "unavailable",
            "request_count": 1,
            "warnings": ["no reference"],
            "sources": [],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "draft")
        self.assertFalse(payload["external_validation"]["available"])
        self.assertFalse(payload["external_validation"]["analysis_dependency"])
        self.assertTrue(payload["external_validation"]["unscored_dimensions_unchanged"])
        self.assertEqual(payload["external_validation"]["scored_dimensions"], [])
        self.assertEqual(payload["comparison"]["genre"]["decision"], "not_scored")
        self.assertEqual(payload["comparison"]["lead_vocal"]["decision"], "not_scored")
        self.assertEqual(payload["comparison"]["backing_vocals"]["decision"], "not_scored")
        self.assertEqual(payload["comparison"]["instrumentation"]["decision"], "not_scored")



    def test_watch_persists_completed_and_cools_down_draft(self):
        import tempfile
        import profile_auto_review as par

        rows = [
            {"run_id": 301, "title": "Song A - Artist A", "artist": "", "diagnostics": {"profile_view": {}}},
            {"run_id": 302, "title": "Song B - Artist B", "artist": "", "diagnostics": {"profile_view": {}}},
        ]

        class FakeClient:
            def __init__(self):
                self.submitted = []
            def submit_profile_review(self, payload):
                self.submitted.append(payload["run_id"])
                return {"ok": True, "revision": {"run_id": payload["run_id"], "status": "completed"}}

        original_snapshot = par.profile_review_queue_snapshot
        original_research = par.research_public_sources
        original_build = par.build_review_payload
        try:
            par.profile_review_queue_snapshot = lambda client, limit=100: {"reviews": rows}
            par.research_public_sources = lambda identity, budget: {
                "status": "available",
                "request_count": 1,
                "reason": None,
                "warnings": [],
                "sources": [],
            }
            def fake_build(row, research, min_confidence=0.75):
                if row["run_id"] == 301:
                    return {"run_id": 301, "status": "draft", "confidence": 0.40}
                return {"run_id": 302, "status": "completed", "confidence": 0.91}
            par.build_review_payload = fake_build

            client = FakeClient()
            with tempfile.TemporaryDirectory() as td:
                state = Path(td) / "watch.json"
                events = []
                result = par.auto_review_watch(
                    client,
                    state_file=state,
                    iterations=1,
                    poll_seconds=60,
                    draft_cooldown_seconds=3600,
                    abstain_cooldown_seconds=7200,
                    max_items=5,
                    now_fn=lambda: 1000.0,
                    sleep_fn=lambda _: None,
                    emit_fn=events.append,
                )
                saved = json.loads(state.read_text(encoding="utf-8"))
        finally:
            par.profile_review_queue_snapshot = original_snapshot
            par.research_public_sources = original_research
            par.build_review_payload = original_build

        self.assertEqual(client.submitted, [302])
        self.assertEqual(result["totals"]["submitted"], 1)
        self.assertIn("301", saved["runs"])
        self.assertNotIn("302", saved["runs"])
        self.assertEqual(saved["runs"]["301"]["next_retry_epoch"], 4600.0)
        self.assertEqual(events[0]["sweep"]["draft"], 1)
        self.assertEqual(events[0]["sweep"]["submitted"], 1)

    def test_sweep_skips_ids_in_cooldown(self):
        import profile_auto_review as par

        rows = [
            {"run_id": 401, "title": "Song A - Artist A", "artist": "", "diagnostics": {"profile_view": {}}},
            {"run_id": 402, "title": "Song B - Artist B", "artist": "", "diagnostics": {"profile_view": {}}},
        ]

        original_snapshot = par.profile_review_queue_snapshot
        original_research = par.research_public_sources
        original_build = par.build_review_payload
        seen = []
        try:
            par.profile_review_queue_snapshot = lambda client, limit=100: {"reviews": rows}
            par.research_public_sources = lambda identity, budget: {"status":"unavailable","request_count":0,"reason":"none","warnings":[],"sources":[]}
            def fake_build(row, research, min_confidence=0.75):
                seen.append(row["run_id"])
                return {"run_id": row["run_id"], "status": "draft", "confidence": 0.0}
            par.build_review_payload = fake_build
            result = par.auto_review_sweep(object(), max_items=5, dry_run=True, skip_run_ids={401})
        finally:
            par.profile_review_queue_snapshot = original_snapshot
            par.research_public_sources = original_research
            par.build_review_payload = original_build

        self.assertEqual(seen, [402])
        self.assertEqual(result["skipped_cooldown"], 1)


    def test_sweep_skips_draft_and_submits_only_completed(self):
        import profile_auto_review as par

        rows = [
            {"run_id": 201, "title": "Song A - Artist A", "artist": "", "diagnostics": {"profile_view": {}}},
            {"run_id": 202, "title": "Song B - Artist B", "artist": "", "diagnostics": {"profile_view": {}}},
        ]

        class FakeClient:
            def __init__(self):
                self.submitted = []
            def submit_profile_review(self, payload):
                self.submitted.append(payload["run_id"])
                return {"ok": True, "revision": {"run_id": payload["run_id"], "status": "completed"}}

        original_snapshot = par.profile_review_queue_snapshot
        original_research = par.research_public_sources
        original_build = par.build_review_payload
        try:
            par.profile_review_queue_snapshot = lambda client, limit=100: {"reviews": rows}
            par.research_public_sources = lambda identity, budget: {
                "status": "ok",
                "request_count": 2,
                "reason": None,
                "warnings": [],
                "sources": [],
            }
            def fake_build(row, research, min_confidence=0.75):
                if row["run_id"] == 201:
                    return {"run_id": 201, "status": "draft", "confidence": 0.60}
                return {"run_id": 202, "status": "completed", "confidence": 0.91}
            par.build_review_payload = fake_build

            client = FakeClient()
            result = par.auto_review_sweep(
                client,
                max_items=2,
                dry_run=False,
                budget_factory=lambda: par.NetworkBudget(max_requests_per_item=2),
            )
        finally:
            par.profile_review_queue_snapshot = original_snapshot
            par.research_public_sources = original_research
            par.build_review_payload = original_build

        self.assertEqual(result["examined"], 2)
        self.assertEqual(result["draft"], 1)
        self.assertEqual(result["completed"], 1)
        self.assertEqual(result["submitted"], 1)
        self.assertEqual(client.submitted, [202])


    def test_draft_when_external_sources_insufficient(self):
        research = {
            "status": "abstain",
            "request_count": 1,
            "warnings": [],
            "sources": [
                {"source": "MusicBrainz", "available": True, "genres": ["rock"]}
            ],
        }
        payload = build_review_payload(self._row(), research, min_confidence=0.75)
        self.assertEqual(payload["status"], "draft")


if __name__ == "__main__":
    unittest.main()
