"""Small, offline non-regression tests for the native service/REST FIFO attachment."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / 'runtime' / 'profile_ai_requests_worker.py'
HOST = ROOT / 'src' / 'Service' / 'AssistantPlatformHost.php'
LIFECYCLE = ROOT / 'src' / 'Service' / 'AssistantProfileWorkerProcess.php'


def isolated_main(root, worker_once):
    parsed = ast.parse(WORKER.read_text(encoding='utf-8'))
    f = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    module = types.ModuleType('isolated_profile_service_main')
    module.__dict__.update({
        'argparse': argparse, 'Path': Path, 'os': __import__('os'),
        'ROOT': root, 'TOKEN': 'dummy', '_load_lab_token': lambda: 'dummy',
        'assistant_main': types.SimpleNamespace(_client_from_args=lambda _: object()),
        'BASE': 'http://127.0.0.1:8701', 'once': worker_once,
        'time': types.SimpleNamespace(sleep=lambda n: None),
    })
    exec(compile(ast.Module(body=[f], type_ignores=[]), str(WORKER), 'exec'), module.__dict__)
    return module.main


class ProfileServiceHost172(unittest.TestCase):
    def test_stop_signal_consumed_after_claimed_job_not_before_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'runtime' / 'state'
            state.mkdir(parents=True)
            stop = state / 'profile-service-stop-test.signal'
            calls = []
            def once(_):
                calls.append('job_finished')
                stop.write_text('stop', encoding='utf-8')
            main = isolated_main(root, once)
            original = sys.argv
            try:
                sys.argv = ['worker', '--service-stop-file', str(stop)]
                self.assertEqual(main(), 0)
            finally:
                sys.argv = original
            self.assertEqual(calls, ['job_finished'])

    def test_existing_stop_signal_prevents_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'runtime' / 'state'
            state.mkdir(parents=True)
            stop = state / 'profile-service-stop-test.signal'
            stop.write_text('stop', encoding='utf-8')
            once = Mock()
            main = isolated_main(root, once)
            original = sys.argv
            try:
                sys.argv = ['worker', '--service-stop-file', str(stop)]
                self.assertEqual(main(), 0)
            finally:
                sys.argv = original
            once.assert_not_called()

    def test_stop_file_cannot_target_unrelated_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'runtime' / 'state').mkdir(parents=True)
            main = isolated_main(root, Mock())
            original = sys.argv
            try:
                sys.argv = ['worker', '--service-stop-file', str(root / 'VERSION')]
                with self.assertRaises(SystemExit) as error:
                    main()
                self.assertEqual(error.exception.code, 2)
            finally:
                sys.argv = original

    def test_native_host_no_parallel_task_or_shell(self):
        code = LIFECYCLE.read_text(encoding='utf-8')
        self.assertIn("'bypass_shell' => true", code)
        self.assertIn('proc_open($cmd', code)
        self.assertIn('START_REFUSED_EXISTING_PROFILE_WORKER', code)
        self.assertIn('STOP_PENDING_ACTIVE_WORKER_NO_FORCE_KILL', code)
        for forbidden in ('powershell.exe', 'cmd.exe', 'schtasks', 'proc_terminate(', 'Stop-Process'):
            self.assertNotIn(forbidden, code)
        host = HOST.read_text(encoding='utf-8')
        self.assertIn('new AssistantProfileWorkerProcess()', host)
        self.assertIn('$this->profileWorker?->requestStop()', host)
        self.assertIn('$this->profileWorker?->drain()', host)
        self.assertIn('LLAMA_STOP_DEFERRED_ACTIVE_PROFILE', host)

    def test_worker_remains_rest_client_and_exact_one_shot(self):
        code = WORKER.read_text(encoding='utf-8')
        self.assertIn("parser.error('--once requires positive --job-id and --run-id')", code)
        self.assertIn('one_shot_exclusive_fifo_head_required', code)
        self.assertIn('LAB_PROFILE_IA_PENDING=', code)
        self.assertIn("parser.error('--service-stop-file incompatible with --once')", code)
        self.assertNotIn('scored_count = 0', code)

if __name__ == '__main__':
    unittest.main()
