import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class MainBackofficeContracts(unittest.TestCase):
    def test_routes_and_no_direct_verdict(self):
        source = (ROOT / 'src/Controller/MainBackofficeController.php').read_text(encoding='utf-8')
        self.assertIn("'/backoffice'", source)
        self.assertIn("'/api/backoffice/inference'", source)
        self.assertIn("'/api/backoffice/recordings'", source)
        self.assertIn("'musical_verdict' => null", source)
    def test_no_client_controlled_url(self):
        source = (ROOT / 'src/Controller/MainBackofficeController.php').read_text(encoding='utf-8')
        self.assertIn('https://musicbrainz.org/ws/2/recording/', source)
        self.assertIn('http://host.docker.internal:18720/health', source)
        self.assertNotIn("$request->query->get('url'", source)
    def test_backoffice_is_explicitly_not_full_workflow(self):
        source = (ROOT / 'templates/backoffice/main.html.twig').read_text(encoding='utf-8')
        self.assertIn('non raccordés', source)
        self.assertIn('identité non confirmée', source)

if __name__ == '__main__':
    unittest.main()
