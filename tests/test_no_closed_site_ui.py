import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NoClosedSiteUI(unittest.TestCase):
    def test_no_catalogue_as_search(self):
        ui=(ROOT/'templates/backoffice/main.html.twig').read_text(encoding='utf-8')
        self.assertIn('Recherche Web documentaire autonome',ui)
        self.assertIn('Moteur non raccordé',ui)
        self.assertNotIn('recording-search',ui)
        self.assertNotIn('Consulter les identités candidates',ui)
        self.assertNotIn('Rechercher MusicBrainz',ui)
if __name__=='__main__':unittest.main()
