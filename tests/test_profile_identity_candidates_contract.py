from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from profile_identity import confirm_candidates

def rec(title, artist, score=100):
    return {'title': title, 'score': score, 'artist-credit': [{'name': artist}]}

class IdentityCandidatesContract(unittest.TestCase):
    def test_unique_verified_artist(self):
        data = {'recordings': [rec('Dance Me to the End of Love', 'Leonard Cohen')]}
        self.assertEqual(confirm_candidates('Dance Me to the End of Love', ['Leonard Cohen'], data, 90), 'Leonard Cohen')

    def test_multiple_performers_require_confirmation(self):
        data = {'recordings': [rec('Song', 'Artist A'), rec('Song', 'Artist B')]}
        self.assertIsNone(confirm_candidates('Song', ['Artist A', 'Artist B'], data, 90))

    def test_other_title_never_used(self):
        self.assertIsNone(confirm_candidates('Song', ['Artist A'], {'recordings': [rec('Other Song', 'Artist A')]}, 90))

    def test_low_score_never_used(self):
        self.assertIsNone(confirm_candidates('Song', ['Artist A'], {'recordings': [rec('Song', 'Artist A', 70)]}, 90))
