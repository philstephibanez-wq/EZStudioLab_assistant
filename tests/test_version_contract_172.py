"""Current Assistant VERSION must obey the platform's no-parenthesis rule."""
from __future__ import annotations
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r'(?:[1-9]\d*|0)\.(?:[1-9]\d*|0)(?:[a-z]+(?:0|[1-9]\d*)?)?\Z')

class VersionContract172Test(unittest.TestCase):
    def test_version_is_exact_canonical_release_counter(self):
        raw = (ROOT / 'VERSION').read_bytes()
        self.assertFalse(raw.startswith(b'\xef\xbb\xbf'))
        version = raw.decode('utf-8').strip()
        self.assertRegex(version, VERSION_PATTERN)
        self.assertEqual(version, '1.7a2')

    def test_agents_requires_counter_without_parentheses(self):
        raw = (ROOT / 'AGENTS.md').read_bytes()
        self.assertFalse(raw.startswith(b'\xef\xbb\xbf'))
        data = raw.decode('utf-8')
        start = data.index('## VERSIONING TRANSVERSAL — OBLIGATOIRE')
        end = data.index('## CONTRAT TRANSVERSAL — UTF-8', start)
        normative = data[start:end]
        self.assertIn('sans parenthèses', normative)
        self.assertIn('1.7a2', normative)
        self.assertNotRegex(normative, r'\d+[a-z]?\(\d+\)')
        self.assertIn('[v1.7a2] fix(version)', data)

if __name__ == '__main__':
    unittest.main()
