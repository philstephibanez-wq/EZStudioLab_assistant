import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class VisualizationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'templates/backoffice/main.html.twig').read_text(encoding='utf-8')
    def test_all_eight_stages(self):
        for word in ['Réception LAB','Découverte Web','Ensembles','Identité','Extraction','Recoupement','Verdicts','Retour LAB']:
            self.assertIn(word, self.source)
    def test_set_intersections_and_dynamic_rows(self):
        for needle in ['id="sets"', 'id="intersections"', 'id="assertions"', 'id="journal"']:
            self.assertIn(needle, self.source)
    def test_no_fake_success(self):
        self.assertIn('Aucune assertion finale reçue', self.source)
        self.assertIn('non calculables sans documents analysés', self.source)
        self.assertIn('aucune vérifiée', self.source)
    def test_sources_not_conflated_with_musicbrainz(self):
        self.assertIn('ne sont ni des sources musicales qualifiées', self.source)
        self.assertIn('id="recording-results"', self.source)
if __name__=='__main__':
    unittest.main()
