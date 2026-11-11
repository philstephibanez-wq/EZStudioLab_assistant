"""Real investigator behavior: do not turn provider failures into 'no evidence'."""
from __future__ import annotations
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / 'app' / 'profile_web_investigator.py'


def investigator():
    stubs = {
        'profile_final_verifier': {'final_assertions': lambda row: []},
        'profile_public_web': {'search': lambda *a, **k: [], 'fetch_document': lambda url: {}},
        'profile_live_evidence': {'evaluate_live_documents': lambda a, ident, docs: {'verdict': 'non_trouve', 'references': []}},
        'profile_musicbrainz_structured': {'discover_recordings': lambda *a: {'status': 'unavailable', 'candidates': []}},
    }
    fake = {name: types.SimpleNamespace(**contents) for name, contents in stubs.items()}
    with patch.dict(sys.modules, fake):
        spec = importlib.util.spec_from_file_location('investigator_under_test_1710', TARGET)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


ONE = [{'key': 'tempo', 'value': '92 BPM'}]
IDENTITY = {'title': 'Test Song', 'artist': 'Test Artist'}
HIT = {'url': 'https://example.org/test-song', 'title': 'Test Song Test Artist', 'snippet': 'Test Song by Test Artist'}


class WebSearchReliability1710(unittest.TestCase):
    def test_three_search_failures_are_error_not_missing_evidence(self):
        m = investigator()
        with patch.object(m, 'search', side_effect=RuntimeError('blocked')):
            output = m.research_assertions(ONE, IDENTITY)
        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['reason'], 'web_search_failed_for_all_items')
        self.assertEqual(output['technical_errors'], 1)
        self.assertEqual(output['items'][0]['status'], 'error')
        self.assertEqual(output['items'][0]['reason'], 'web_search_unavailable')
        self.assertEqual(output['items'][0]['search_error_count'], 3)
        self.assertNotIn('blocked', str(output))
        self.assertFalse(output['automatic_verdicts'])

    def test_partial_base_failure_keeps_successful_readable_document(self):
        m = investigator()
        with patch.object(m, 'search', side_effect=[RuntimeError('credential-private'), [HIT], RuntimeError('more-broken')]), \
             patch.object(m, 'fetch_document', return_value={'status': 'read', 'url': HIT['url'], 'text': 'Test Artist Test Song tempo 92 BPM'}):
            output = m.research_assertions(ONE, IDENTITY)
        self.assertEqual(output['status'], 'partial')
        self.assertEqual(output['technical_errors'], 1)
        item = output['items'][0]
        self.assertEqual(item['status'], 'documents_read')
        self.assertEqual(item['search_error_count'], 2)
        self.assertEqual(len(item['documents']), 1)
        self.assertEqual(item['evidence_review']['verdict'], 'non_trouve')
        self.assertNotIn('credential-private', str(output))
        self.assertFalse(item['eligible_for_verdict'])

    def test_empty_successful_search_is_not_a_technical_error(self):
        m = investigator()
        with patch.object(m, 'search', return_value=[]):
            output = m.research_assertions(ONE, IDENTITY)
        self.assertEqual(output['status'], 'completed')
        self.assertEqual(output['technical_errors'], 0)
        self.assertEqual(output['items'][0]['status'], 'no_results')
        self.assertEqual(output['items'][0]['search_error_count'], 0)

    def test_readable_document_does_not_promote_candidate_to_verdict(self):
        m = investigator()
        with patch.object(m, 'search', return_value=[HIT]), \
             patch.object(m, 'fetch_document', return_value={'status': 'read', 'url': HIT['url'], 'text': 'Test Song Test Artist'}):
            result = m.research_assertions(ONE, IDENTITY)
        self.assertEqual(result['status'], 'completed')
        self.assertFalse(result['automatic_verdicts'])
        self.assertFalse(result['items'][0]['eligible_for_verdict'])

    def test_no_title_does_not_trigger_invented_web_research(self):
        m = investigator()
        with patch.object(m, 'search') as search:
            result = m.research_assertions(ONE, {'title': '', 'artist': 'Test Artist'})
        search.assert_not_called()
        self.assertEqual(result['items'][0]['status'], 'identity_unavailable')
        self.assertFalse(result['automatic_verdicts'])


if __name__ == '__main__':
    unittest.main()
