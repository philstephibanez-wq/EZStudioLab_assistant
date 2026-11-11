"""No-network contract tests for cross-repository archive verification."""
from __future__ import annotations
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from profile_archive_contract import validate_manifest


class ArchiveContract1712(unittest.TestCase):
    def setUp(self):
        self.raw = b'{"run_id":197}\n'
        self.files = {'timeline-0000.jsonl': self.raw}
        self.manifest = {
            'schema': 'ezstudio.assistant-profile-raw-archive.v1',
            'producer': 'EZStudioLab_assistant', 'run_id': 197,
            'trace_id': 'a' * 32, 'revision_id': None,
            'artifact_count': 1,
            'artifacts': [{'path': 'timeline-0000.jsonl', 'size_bytes': len(self.raw),
                           'sha256': hashlib.sha256(self.raw).hexdigest()}],
        }

    def test_valid_bytes(self):
        self.assertEqual(validate_manifest(self.manifest, self.files), 1)

    def test_mutated_byte_fails(self):
        with self.assertRaisesRegex(ValueError, 'sha256_mismatch'):
            validate_manifest(self.manifest, {'timeline-0000.jsonl': b'{"run_id":198}\n'})

    def test_missing_file_fails(self):
        with self.assertRaisesRegex(ValueError, 'inventory_mismatch'):
            validate_manifest(self.manifest, {})

    def test_duplicate_paths_fail(self):
        m = dict(self.manifest, artifact_count=2, artifacts=self.manifest['artifacts'] * 2)
        with self.assertRaisesRegex(ValueError, 'inventory_mismatch|duplicate'):
            validate_manifest(m, self.files)

    def test_traversal_fails(self):
        self.manifest['artifacts'][0]['path'] = '../VERSION'
        with self.assertRaisesRegex(ValueError, 'path_invalid'):
            validate_manifest(self.manifest, self.files)

    def test_unlisted_artifact_fails(self):
        with self.assertRaisesRegex(ValueError, 'inventory_mismatch'):
            validate_manifest(self.manifest, {**self.files, 'timeline-0001.jsonl': b'foo'})

    def test_invalid_trace_identity_fails(self):
        self.manifest['trace_id'] = 'not-a-trace'
        with self.assertRaisesRegex(ValueError, 'trace_invalid'):
            validate_manifest(self.manifest, self.files)


if __name__ == '__main__':
    unittest.main()
