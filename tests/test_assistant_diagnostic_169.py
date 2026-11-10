"""Read-only diagnostic contract: no worker lifecycle action added."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AssistantDiagnostic169Test(unittest.TestCase):
    def test_backoffice_panel_is_read_only(self):
        twig = (ROOT / 'templates/backoffice/main.html.twig').read_text(encoding='utf-8')
        self.assertIn('id="ezs-assistant-diagnostic"', twig)
        self.assertIn('ezstudio-assistant-diagnostic.js', twig)
        self.assertIn('app.environment', twig)

    def test_json_sources_are_existing_read_only_endpoints(self):
        js = (ROOT / 'public/js/ezstudio-assistant-diagnostic.js').read_text(encoding='utf-8')
        self.assertIn("source('assistant.api.status', '/api/status')", js)
        self.assertIn("source('assistant.api.backoffice.inference', '/api/backoffice/inference')", js)
        self.assertIn("method: 'GET'", js)
        self.assertIn("credentials: 'same-origin'", js)
        self.assertIn('sensitive.test(key)', js)
        self.assertNotIn('window.confirm(', js)
        self.assertNotIn('window.alert(', js)
        self.assertNotIn('window.prompt(', js)


if __name__ == '__main__':
    unittest.main()
