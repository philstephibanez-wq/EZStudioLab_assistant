"""Regression: provisional documentary tempos cannot contradict half/double time."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from profile_final_verifier import _compare_documentary, attach_documentary_findings


class DocumentaryTempo1711(unittest.TestCase):
    def test_half_time_not_a_false_mismatch(self):
        self.assertEqual(_compare_documentary('tempo', '120 BPM', '60 BPM'), 'indeterminate')

    def test_double_time_not_a_false_mismatch(self):
        self.assertEqual(_compare_documentary('tempo', '60 BPM', '120 BPM'), 'indeterminate')

    def test_tolerance_matches_official_evaluator(self):
        self.assertEqual(_compare_documentary('tempo', '120 BPM', '122 BPM'), 'concordant')
        self.assertEqual(_compare_documentary('tempo', '160 BPM', '165 BPM'), 'discordant')

    def test_genuine_non_ratio_disagreement(self):
        self.assertEqual(_compare_documentary('tempo', '120 BPM', '110 BPM'), 'discordant')

    def test_unreadable_tempo_is_indeterminate(self):
        self.assertEqual(_compare_documentary('tempo', '120 BPM', 'not available'), 'indeterminate')

    def test_ambiguous_candidate_never_promotes_official_verdict(self):
        original = {'assertions': [{'key': 'tempo', 'value': '120 BPM', 'verdict': 'non_trouve'}]}
        investigation = {'items': [{
            'key': 'tempo', 'evidence_review': {
                'reference_value': '60 BPM', 'proposed_verdict': 'faux',
                'references': [{'url': 'https://example.org/recording'}],
            },
        }]}
        merged = attach_documentary_findings(original, investigation, {'items': []})
        item = merged['assertions'][0]
        self.assertEqual(item['verdict'], 'non_trouve')
        self.assertEqual(item['documentary_observation']['comparison'], 'indeterminate')
        self.assertEqual(item['documentary_observation']['status'], 'provisional')
        self.assertFalse(item['documentary_observation']['recording_identity_confirmed'])
        self.assertFalse(item['documentary_observation']['scientific_validation'])
        self.assertEqual(original['assertions'][0]['verdict'], 'non_trouve')


if __name__ == '__main__':
    unittest.main()
