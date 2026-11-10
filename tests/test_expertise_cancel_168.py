"""Pure cancellation tests: no LAB, network, model or GPU required."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def selected_function(path, function_name, extra=None):
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function_name)
    code = compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec')
    namespace = dict(extra or {})
    exec(code, namespace)
    return namespace[function_name]


class FakeClient:
    def __init__(self, state):
        self.state = state
        self.calls = []

    def request(self, path, data=None):
        self.calls.append((path, data))
        if path.endswith('/state?job_id=17'):
            return {'request': {'job_id': 17, 'run_id': 11, 'status': self.state}}
        if path.endswith('/cancelled'):
            self.state = 'cancelled'
            return {'ok': True, 'request': {'status': 'cancelled'}}
        if path.endswith('/finish'):
            return {'ok': True, 'request': {'status': data['status']}}
        raise AssertionError(path)


class ExpertiseCancelTest(unittest.TestCase):
    def terminal(self):
        return selected_function('runtime/canonical_job_worker.py', 'finish_or_ack_cancel',
                                 {'PATH': '/internal/analysis/desktop/profile/ai-requests',
                                  'RuntimeError': RuntimeError})

    def test_running_to_cancelled_does_not_finish(self):
        client = FakeClient('cancelling')
        status, _ = self.terminal()(client,17,11,'error','failed')
        self.assertEqual('cancelled',status)
        self.assertEqual(1,len([path for path,_ in client.calls if path.endswith('/cancelled')]))
        self.assertFalse(any(path.endswith('/finish') for path,_ in client.calls))

    def test_running_to_failed_uses_exact_id(self):
        client = FakeClient('running')
        status, _ = self.terminal()(client,17,11,'error','failed')
        self.assertEqual('error',status)
        requests = [data for path,data in client.calls if path.endswith('/finish')]
        self.assertEqual([{'job_id':17,'status':'error','message':'failed'}],requests)

    def test_non_running_cannot_finish(self):
        client = FakeClient('completed')
        with self.assertRaises(RuntimeError):
            self.terminal()(client,17,11,'error','failed')
        self.assertFalse(any(path.endswith('/finish') for path,_ in client.calls))

    def test_main_worker_probes_running_and_acks_cancel(self):
        source=(ROOT/'runtime/profile_ai_requests_worker.py').read_text(encoding='utf-8')
        self.assertIn('assert_running(rid, job_id)',source)
        self.assertIn("'/cancelled', {'job_id': job_id}",source)
        self.assertIn('if trace:\n',source)
        self.assertNotIn('window.confirm(',source)


if __name__ == '__main__':
    unittest.main()
