import unittest
from runtime import musical_contract as m

def fixture():
    return {'recording': {'title': 'Titre', 'artist': 'Interprète', 'version': None, 'track_id': 'r12'}, 'assertions': [
        {'id': 'a', 'characteristic': 'tempo', 'value': 120},
        {'id': 'b', 'characteristic': 'instrument:1', 'value': 'piano'},
        {'id': 'c', 'characteristic': 'instrument:2', 'value': 'guitare'},
        {'id': 'd', 'characteristic': 'choeurs', 'value': 'not_scored'}]}

class VerificationContractTest(unittest.TestCase):
    def test_dynamic_items_and_no_sources_default_to_abstention(self):
        rows = m.verify(fixture(), reviewed_at='2026-10-26')['results']
        self.assertEqual([r['verdict'] for r in rows], ['non_trouve'] * 3 + ['sans_valeur_lab'])
        self.assertEqual([r['confidence_pct'] for r in rows], [None] * 4)
        self.assertEqual([r['evidence'] for r in rows], [[]] * 4)
    def test_reject_model_provenance(self):
        obj = fixture(); obj['assertions'][0]['engine'] = 'CLAP'
        with self.assertRaises(ValueError): m.normalize(obj)
    def test_reject_unverified_https_as_proof(self):
        rows = m.verify(fixture(), {'a': [{'url': 'https://example.org/song', 'claim': '140 BPM', 'same_recording': True}]})['results']
        self.assertEqual(rows[0]['verdict'], 'non_trouve')
        self.assertIsNone(rows[0]['reference_value'])
    def test_reject_unsafe_url(self):
        for url in ['http://example.org', 'https://localhost/test', 'https://user:pass@example.org/', 'file:///c:/test']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                m.verify(fixture(), {'a': [{'url': url}]})
    def test_duplicate_id_fails(self):
        obj = fixture(); obj['assertions'][1]['id'] = 'a'
        with self.assertRaises(ValueError): m.normalize(obj)
    def test_malformed_identity_rejected(self):
        obj = fixture(); obj['recording'].pop('artist')
        with self.assertRaises(ValueError): m.normalize(obj)
    def test_unknown_ambiguous_value_abstains(self):
        obj = fixture(); obj['assertions'][0]['value'] = 'indéterminé'
        self.assertEqual(m.verify(obj)['results'][0]['verdict'], 'sans_valeur_lab')

if __name__ == '__main__':
    unittest.main()
