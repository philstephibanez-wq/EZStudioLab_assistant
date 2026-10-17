from __future__ import annotations
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from declarative_review import DEFAULT_PATH, load_review_preset, PHASES


class DeclarativeContract(unittest.TestCase):
    def test_common_phase_registry(self):
        self.assertEqual(PHASES, ('profile', 'stems', 'chords_n', 'lyrics'))

    def test_baseline(self):
        preset, digest = load_review_preset()
        self.assertEqual(preset['temperature'], 0.1)
        self.assertEqual(preset['max_tokens'], 1200)
        self.assertEqual(len(digest), 64)

    def test_hot_reload_without_import_reload(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'preset.json'
            data = json.loads(DEFAULT_PATH.read_text(encoding='utf-8'))
            p.write_text(json.dumps(data), encoding='utf-8')
            with patch.dict(os.environ, {'EZSTUDIOLAB_REVIEW_PRESET_PATH': str(p)}):
                first, a = load_review_preset()
                data['temperature'] = 0.35
                p.write_text(json.dumps(data), encoding='utf-8')
                second, b = load_review_preset()
            self.assertEqual(first['temperature'], 0.1)
            self.assertEqual(second['temperature'], 0.35)
            self.assertNotEqual(a, b)

    def test_no_arbitrary_code_or_bad_phase(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'preset.json'
            data = json.loads(DEFAULT_PATH.read_text(encoding='utf-8'))
            data['python_module'] = 'os.system'
            p.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'invalid_keys'):
                load_review_preset(path=p)
            with self.assertRaisesRegex(ValueError, 'phase_unknown'):
                load_review_preset(phase='untrusted', path=p)

    def test_bom_and_invalid_do_not_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'preset.json'
            p.write_bytes(b'\xef\xbb\xbf' + DEFAULT_PATH.read_bytes())
            with self.assertRaisesRegex(ValueError, 'bom_forbidden'):
                load_review_preset(path=p)
            p.write_text('{broken', encoding='utf-8')
            with self.assertRaises(json.JSONDecodeError):
                load_review_preset(path=p)

if __name__ == '__main__':
    unittest.main()
