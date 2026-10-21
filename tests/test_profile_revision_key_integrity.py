import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class RevisionKeyContract(unittest.TestCase):
    def test_revision_key_includes_module_consultations(self):
        src=(ROOT/"runtime/profile_ai_requests_worker.py").read_text(encoding="utf-8")
        self.assertIn("'sequential': sequential",src)
        self.assertIn("['module_consultations'] = sequential",src)
        ast.parse(src)
