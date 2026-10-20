"""Vérifier la limite de génération du preset déclaratif Assistant."""
import ast
import json
import os
from types import SimpleNamespace
import tempfile
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / 'app' / 'declarative_review.py'
tree = ast.parse(P.read_text(encoding='utf-8'))
ns = {'__name__': 'declarative_review_contract'}
exec(compile(tree, str(P), 'exec'), ns)
# Cette suite isole le contrat de valeur ; la règle UNC Windows a ses propres tests.
ns['os'] = SimpleNamespace(name='posix', getenv=os.getenv)

class ReviewPreset16KContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / 'assistant-profile.json'
        self.preset = {
            'schema':'ezs.assistant.review-preset.v1',
            'id':'profile-qwen-baseline-1',
            'phase':'profile',
            'provider':'local',
            'prompt':'Contrôle de provenance PROFILE. ' * 6,
            'temperature':0.1,
            'max_tokens':16384,
            'context_max_chars':6500,
        }

    def load(self, value):
        self.preset['max_tokens'] = value
        self.path.write_text(json.dumps(self.preset, ensure_ascii=False), encoding='utf-8')
        return ns['load_review_preset']('profile', path=str(self.path))

    def test_accept_16384(self):
        p, _ = self.load(16384)
        self.assertEqual(p['max_tokens'], 16384)

    def test_accept_previous_4096(self):
        p, _ = self.load(4096)
        self.assertEqual(p['max_tokens'], 4096)

    def test_reject_16385(self):
        with self.assertRaisesRegex(ValueError, 'review_preset_invalid_max_tokens'):
            self.load(16385)

    def test_reject_boolean(self):
        with self.assertRaisesRegex(ValueError, 'review_preset_invalid_max_tokens'):
            self.load(True)

    def test_reject_string(self):
        with self.assertRaisesRegex(ValueError, 'review_preset_invalid_max_tokens'):
            self.load('16384')

if __name__ == '__main__':
    unittest.main()
