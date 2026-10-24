"""R35 documentary reconciliation regression tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from profile_documentary_reconcile import reconcile, _similar

class R35(unittest.TestCase):
    def check(self, title, hint, headline, expected):
        result = reconcile(title, hint, {'candidates': [{'title': headline, 'url': 'https://example.org'}]}, [])
        self.assertEqual(result['documentary_links'][0]['artist_hint_supported'], expected)
        self.assertFalse(result['recording_identity_verified'])
        self.assertFalse(result['performer_identity_verified'])

    def test_joe(self):
        self.check('Les Champs-Elysees', 'Joe Dassin', 'Joe Dassin - Les Champs-Élysées (Audio) - YouTube', True)

    def test_cabrel(self):
        self.check('Je laime à mourir', 'Cabrel Francis', 'Francis Cabrel - Je l’aime à mourir - YouTube', True)

    def test_animals(self):
        self.check('The House of the Rising Sun', 'The Animals', 'The Animals - House Of The Rising Sun (Official Music Video)', True)

    def test_wrong_artist(self):
        self.check('My Sweet Lord', 'George Harrison', 'Megadeth - My Sweet Lord', False)

    def test_initial(self):
        self.assertTrue(_similar('G.Harison', 'George Harrison'))

    def test_spelling(self):
        self.assertTrue(_similar('Harison', 'Harrison'))

    def test_mb_overlap(self):
        r = reconcile('My Sweet Lord', None, {'candidates': [{'url': 'https://example.org', 'title': 'George Harrison - My Sweet Lord'}]}, [{'artist_candidates': ['George Harrison']}])
        self.assertEqual(r['documentary_links'][0]['musicbrainz_web_artist_overlap'], ['George Harrison'])
        self.assertFalse(r['recording_identity_verified'])

if __name__ == '__main__':
    unittest.main()
