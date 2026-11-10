"""Local Assistant FIFO contract tests, independent of network/MAIN resources."""
import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / 'runtime' / 'profile_ai_requests_worker.py'

class LocalHandoff170Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKER.read_text(encoding='utf-8')
        cls.tree = ast.parse(cls.source)

    def test_local_backend_and_no_token_in_traces(self):
        self.assertIn("'http://127.0.0.1:8701'", self.source)
        self.assertIn("'authorization': 'redacted'", self.source)
        self.assertNotIn("'headers': headers", self.source)
        self.assertNotIn('XPS only', self.source)

    def test_token_loader_reads_existing_lab_env_without_mutation(self):
        fn = next(node for node in self.tree.body if isinstance(node, ast.FunctionDef) and node.name == '_load_lab_token')
        isolated = ast.Module(body=[fn], type_ignores=[])
        namespace = {'os': os, 'Path': Path}
        exec(compile(isolated, str(WORKER), 'exec'), namespace)
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / '.env.local'
            env.write_text('EZSTUDIO_ANALYSIS_WORKER_TOKEN=test-only-secret\n', encoding='utf-8')
            with patch.dict(os.environ, {'EZSTUDIO_LAB_ROOT': tmp}, clear=True):
                self.assertEqual(namespace['_load_lab_token'](), 'test-only-secret')
            self.assertEqual(env.read_text(encoding='utf-8'), 'EZSTUDIO_ANALYSIS_WORKER_TOKEN=test-only-secret\n')

    def test_oneshot_reports_errors_and_retains_existing_review_logic(self):
        self.assertIn('if args.once:\n                return 2', self.source)
        self.assertIn("payload['status'] = 'draft'", self.source)
        self.assertIn("'review_status': 'draft'", self.source)
        self.assertIn('assert_running(rid, job_id)', self.source)
        self.assertIn("'/cancelled', {'job_id': job_id}", self.source)
        self.assertIn('raise SystemExit(main())', self.source)
        self.assertIn('revision_non_confirmee', self.source)
        self.assertIn('finish_not_confirmed', self.source)
        self.assertIn('cancellation_not_confirmed', self.source)
        self.assertIn('expertise_failed_after_finish', self.source)
        self.assertNotIn('if enabled():\n        purge()', self.source)

if __name__ == '__main__':
    unittest.main()
