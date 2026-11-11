"""Contrats durables R2 : inventaire dynamique, instruments, sécurité, abstention."""
import unittest
from unittest.mock import patch
from app.profile_assertions_contract import ITEMS
from app.profile_dynamic_contract_r2 import project_final_assertions, build_final_reviews, validate_final_reviews
from runtime.profile_verify_push import verify


def sample():
    raw = [
        {'id': 'tempo', 'dimension': 'tempo', 'value': 120},
        {'id': 'instruments:0', 'dimension': 'instruments', 'value': 'guitare'},
        {'id': 'instruments:1', 'dimension': 'instruments', 'value': 'piano'},
        {'id': 'choeurs', 'dimension': 'choeurs', 'value': 'présents'},
    ]
    return {'expertise_type': 'profile', 'analysis_id': 197, 'preset_id': None,
            'title': 'Morceau', 'artist': 'Interprète',
            'items': {k: None for k in ITEMS},
            'final_assertions_schema': 'ezstudio.profile-final-assertions.v1',
            'final_assertions': raw, 'final_assertions_count': len(raw),
            'diagnostics': {'engine': 'CLAP', 'token': 'PRIVATE'}}


class DynamicBoundaryR2(unittest.TestCase):
    def test_arbitrary_instrument_cardinality_and_no_internal_data(self):
        payload = sample()
        for i in range(2, 21):
            payload['final_assertions'].append({'id': f'instruments:{i}', 'dimension': 'instruments', 'value': f'instrument {i}'})
        payload['final_assertions_count'] = len(payload['final_assertions'])
        projected = project_final_assertions(payload)
        self.assertEqual(len(projected), 23)
        self.assertEqual(len({i['search_key'] for i in projected}), 23)
        self.assertNotIn('CLAP', repr(projected))
        self.assertNotIn('PRIVATE', repr(projected))

    def test_partial_dynamic_envelope_is_never_silently_legacy(self):
        payload = sample()
        del payload['final_assertions_count']
        with self.assertRaisesRegex(ValueError, 'r2_final_assertions_incomplete_envelope'):
            project_final_assertions(payload)

    def test_duplicate_id_fails_closed(self):
        payload = sample()
        payload['final_assertions'][1]['id'] = 'tempo'
        with self.assertRaises(ValueError): project_final_assertions(payload)

    def test_cardinality_mismatch_fails_closed(self):
        payload = sample()
        payload['final_assertions_count'] += 1
        with self.assertRaises(ValueError): project_final_assertions(payload)

    def test_bad_schema_or_shape_fails_closed(self):
        payload = sample()
        payload['final_assertions_schema'] = 'unknown'
        with self.assertRaises(ValueError): project_final_assertions(payload)
        payload = sample()
        payload['final_assertions'][0]['engine'] = 'CLAP'
        with self.assertRaises(ValueError): project_final_assertions(payload)

    def test_scientific_dimension_and_nested_values_rejected(self):
        payload = sample()
        payload['final_assertions'][0] = {'id': 'module:0', 'dimension': 'tempo', 'value': 120}
        with self.assertRaises(ValueError): project_final_assertions(payload)
        payload = sample()
        payload['final_assertions'][0]['value'] = {'score': 0.98}
        with self.assertRaises(ValueError): project_final_assertions(payload)

    def test_legacy_without_inventory_remains_supported(self):
        payload = sample()
        del payload['final_assertions'], payload['final_assertions_schema'], payload['final_assertions_count']
        self.assertIsNone(project_final_assertions(payload))

    def test_every_dynamic_item_researched_separately_with_abstention(self):
        payload = sample()
        def fake_research(rows, identity):
            self.assertEqual([x['key'] for x in rows], ['tempo','instrument:0','instrument:1','choir'])
            self.assertEqual(rows[0]['value'], '120 BPM')
            self.assertEqual(identity, {'title': 'Morceau', 'artist': 'Interprète'})
            return {'status': 'completed', 'items': [], 'technical_errors': 0}
        with patch('runtime.profile_verify_push.research_assertions', side_effect=fake_research), \
             patch('runtime.profile_verify_push.consult') as ai, \
             patch('runtime.profile_verify_push.booklet_ocr_enabled', return_value=False):
            result = verify(payload)
        ai.assert_not_called()
        self.assertEqual([x['id'] for x in result['final_reviews']], [x['id'] for x in payload['final_assertions']])
        self.assertTrue(all(x['verdict']=='non_trouve' for x in result['final_reviews']))
        self.assertEqual(result['final_assertions_count'], 4)
        self.assertNotIn('CLAP', repr(result))
        self.assertNotIn('PRIVATE', repr(result))
        self.assertEqual(len(result['reviews']), 10)

    def test_empty_inventory_never_calls_search(self):
        payload = sample()
        payload['final_assertions'], payload['final_assertions_count'] = [], 0
        with patch('runtime.profile_verify_push.research_assertions') as search, \
             patch('runtime.profile_verify_push.consult') as ai, \
             patch('runtime.profile_verify_push.booklet_ocr_enabled', return_value=False):
            result = verify(payload)
        search.assert_not_called()
        ai.assert_not_called()
        self.assertEqual(result['final_reviews'], [])

    def test_validator_rejects_fabricated_verdict(self):
        projected = project_final_assertions(sample())
        result = {'final_reviews': build_final_reviews(projected, {'items': []})}
        self.assertTrue(validate_final_reviews(projected, result))
        result['final_reviews'][0]['verdict'] = 'bon'
        with self.assertRaises(ValueError): validate_final_reviews(projected, result)


if __name__ == '__main__':
    unittest.main()
