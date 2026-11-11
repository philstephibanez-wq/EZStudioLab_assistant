"""PROFILE report receipt: existing publishing semantics, local proof, no network."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from profile_publication_receipt import publish_with_receipt


class PublicationReceipt1716(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.trace = SimpleNamespace(run_id=196, trace_id='a' * 32)
        self.outcome = {'revision': 83, 'token': 'PRIVATE_SHOULD_NOT_LEAK', 'diagnostic': 'SECRET'}

    def receipt(self):
        return json.loads((self.root / 'profile/run-000196/trace-aaaaaaaaaaaa.json').read_text(encoding='utf-8'))

    def test_success_publishes_exactly_once_and_records_receipt(self):
        publisher = Mock(return_value='published')
        self.assertEqual(publish_with_receipt(self.trace, self.outcome, publisher, job_id=225, receipt_root=self.root), 'published')
        publisher.assert_called_once_with(self.trace, self.outcome)
        result = self.receipt()
        self.assertEqual((result['status'], result['run_id'], result['revision_id']), ('published', 196, 83))
        self.assertEqual(result['job_id'], 225)
        self.assertNotIn('PRIVATE_SHOULD_NOT_LEAK', json.dumps(result))
        self.assertNotIn('SECRET', json.dumps(result))

    def test_failure_is_visible_but_re_raised(self):
        def fail(*args):
            raise PermissionError('PRIVATE_SHOULD_NOT_LEAK')
        with self.assertRaises(PermissionError):
            publish_with_receipt(self.trace, self.outcome, fail, receipt_root=self.root)
        result = self.receipt()
        self.assertEqual((result['status'], result['error_type']), ('failed', 'PermissionError'))
        self.assertNotIn('PRIVATE_SHOULD_NOT_LEAK', json.dumps(result))

    def test_partial_and_disabled_statuses_are_not_marked_published(self):
        for result, expected in [('raw_published:disabled', 'disabled'), ('raw_failed:published', 'partial')]:
            publish_with_receipt(self.trace, self.outcome, Mock(return_value=result), receipt_root=self.root)
            self.assertEqual(self.receipt()['status'], expected)

    def test_invalid_identity_refused_before_publisher(self):
        publisher = Mock()
        for trace in [SimpleNamespace(run_id=-1, trace_id='a' * 32),
                      SimpleNamespace(run_id=196, trace_id='../foo'),
                      SimpleNamespace(run_id=True, trace_id='a' * 32)]:
            with self.assertRaises(ValueError):
                publish_with_receipt(trace, self.outcome, publisher, receipt_root=self.root)
        publisher.assert_not_called()

    def test_previous_receipt_is_replaced_atomically(self):
        publish_with_receipt(self.trace, self.outcome, Mock(return_value='published'), receipt_root=self.root)
        publish_with_receipt(self.trace, self.outcome, Mock(return_value='raw_partial:published'), receipt_root=self.root)
        self.assertEqual(self.receipt()['status'], 'partial')
        self.assertFalse(list(self.root.rglob('*.tmp')))

    def test_atomic_temp_file_is_on_receipt_volume(self):
        from profile_publication_receipt import _atomic_json
        import profile_publication_receipt as module
        destination = self.root / 'profile' / 'run-000196' / 'receipt.json'
        original = module.tempfile.mkstemp
        created = []
        def checked(*args, **kwargs):
            created.append(Path(kwargs['dir']))
            return original(*args, **kwargs)
        with patch.object(module.tempfile, 'mkstemp', side_effect=checked):
            _atomic_json(destination, {'status': 'published'})
        self.assertEqual(created, [destination.parent])
        self.assertEqual(json.loads(destination.read_text(encoding='utf-8')), {'status': 'published'})
        self.assertFalse(list(destination.parent.glob('*.tmp')))

    def test_write_failure_is_not_silently_ignored(self):
        with patch('profile_publication_receipt._atomic_json', side_effect=OSError('blocked')):
            with self.assertRaises(OSError):
                publish_with_receipt(self.trace, self.outcome, Mock(return_value='published'), receipt_root=self.root)


if __name__ == '__main__':
    unittest.main()
