"""Targeted tests: no LAB network, no Windows services, no GPU operations."""
import ast
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / 'runtime' / 'profile_ai_requests_worker.py'
BOOT = ROOT / 'runtime' / 'profile_worker_task.py'


class ProfileWorkerAuto171(unittest.TestCase):
    def test_no_hardcoded_zero_score(self):
        text = WORKER.read_text(encoding='utf-8')
        self.assertNotIn('scored_count = 0', text)
        self.assertIn("scored_count = verdict_counts['bon'] + verdict_counts['faux']", text)
        self.assertIn("'non_trouve_count': verdict_counts['non_trouve']", text)
        self.assertIn("'assertion_count': len(verification['assertions'])", text)
        self.assertIn("'profile.verdict_counts'", text)

    def test_existing_one_shot_guard_unchanged(self):
        text = WORKER.read_text(encoding='utf-8')
        self.assertIn('one_shot_exclusive_fifo_head_required', text)
        self.assertIn("parser.error('--once requires positive --job-id and --run-id')", text)
        self.assertIn('one_shot_claim_refused', text)

    def test_task_bootstrap_delegates_existing_worker_without_new_queue(self):
        text = BOOT.read_text(encoding='utf-8')
        self.assertIn("runpy.run_path(str(WORKER), run_name='__main__')", text)
        self.assertIn("sys.argv = [str(WORKER), '--poll-seconds', '8']", text)
        self.assertNotIn('urllib', text)
        self.assertNotIn("api(PATH", text)
        ast.parse(text)

    def test_headless_bootstrap_writes_durable_log_and_does_not_emit_secret(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('profile_worker_task_171', BOOT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            module.LOG = Path(tmp) / 'var' / 'log' / 'worker.log'
            with patch.object(module.runpy, 'run_path', return_value=None) as call:
                original = list(sys.argv)
                cwd = Path.cwd()
                try:
                    self.assertEqual(module.main(), 0)
                finally:
                    sys.argv = original
                    import os
                    os.chdir(cwd)
            call.assert_called_once_with(str(module.WORKER), run_name='__main__')
            data = module.LOG.read_text(encoding='utf-8')
            self.assertIn('profile.worker.task.start', data)
            self.assertNotIn('X-EZScore-Analysis-Token', data)

    def test_failure_is_recorded_and_nonzero(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('profile_worker_task_171b', BOOT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            module.LOG = Path(tmp) / 'worker.log'
            with patch.object(module.runpy, 'run_path', side_effect=RuntimeError('synthetic_test_failure')):
                original = list(sys.argv)
                cwd = Path.cwd()
                try:
                    self.assertEqual(module.main(), 1)
                finally:
                    sys.argv = original
                    import os
                    os.chdir(cwd)
            self.assertIn('synthetic_test_failure', module.LOG.read_text(encoding='utf-8'))

if __name__ == '__main__':
    unittest.main()
