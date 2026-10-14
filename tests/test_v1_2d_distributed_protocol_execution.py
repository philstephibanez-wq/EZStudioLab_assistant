from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1] / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import worker


class Caps:
    node_id = "worker-test"

    def to_dict(self):
        return {"protocol": "ezstudio.distributed.v1"}


class FakeClient:
    def __init__(self, source: Path, *, kind="distributed_test", flag=True):
        self.source = source
        self.kind = kind
        self.flag = flag
        self.calls = []

    def distributed_worker_heartbeat(self, worker_id, cap, *, state="idle"):
        self.calls.append(("worker_heartbeat", state))
        return {"state": state}

    def distributed_eligible_jobs(self, worker_id, *, limit=100):
        self.calls.append(("eligible", limit))
        return [{"job_id": 154, "kind": self.kind}]

    def distributed_claim_job(self, job_id, worker_id, *, lease_seconds=60):
        self.calls.append(("claim", job_id, lease_seconds))
        return {
            "lease": {
                "worker_id": worker_id,
                "lease_token": "secret",
                "lease_seconds": lease_seconds,
                "expires_at_epoch": 9999999999,
            }
        }

    def distributed_context(self, job_id, worker_id, lease_token):
        self.calls.append(("context", job_id))
        return {
            "request": {"protocol_test_only": self.flag},
            "paths": {"shared_source": str(self.source)},
        }

    def distributed_progress(
        self, job_id, worker_id, lease_token, progress
    ):
        self.calls.append(("progress", progress))
        return {"progress": progress}

    def distributed_lease_heartbeat(
        self, job_id, worker_id, lease_token, *, lease_seconds=60
    ):
        self.calls.append(("lease_heartbeat", lease_seconds))
        return {"status": "lease_renewed"}

    def distributed_complete(self, job_id, worker_id, lease_token):
        self.calls.append(("complete", job_id))
        return {"status": "completed"}

    def distributed_fail(
        self, job_id, worker_id, lease_token, error
    ):
        self.calls.append(("fail", error))
        return {"status": "failed"}


class ProtocolExecutionContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.source = Path(self.tmp.name) / "source.bin"
        self.source.write_bytes(b"ezstudio-protocol-test")

    def tearDown(self):
        self.tmp.cleanup()

    def test_success_is_bounded_and_has_lease_progress_complete(self):
        client = FakeClient(self.source)
        client.source = Path(
            r"\\\\EZSTUDIO-MAIN\\EZStudioLab-Imports\\fixture.bin"
        )

        with patch.object(
            worker,
            "_shared_source_metadata",
            return_value=(22, "A" * 64),
        ):
            result = worker.distributed_execute_protocol_once(
                client,
                Caps(),
                job_id=154,
                lease_seconds=60,
            )

        self.assertFalse(result["scientific_execution_enabled"])
        self.assertTrue(result["protocol_test_only"])

        names = [c[0] for c in client.calls]
        self.assertLess(names.index("eligible"), names.index("claim"))
        self.assertIn(("progress", 5), client.calls)
        self.assertIn(("progress", 50), client.calls)
        self.assertIn(("progress", 95), client.calls)
        self.assertGreaterEqual(names.count("lease_heartbeat"), 2)
        self.assertEqual(names.count("complete"), 1)
        self.assertEqual(names.count("fail"), 0)

    def test_shared_source_helper_rejects_non_unc(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "shared_source_not_unc",
        ):
            worker._shared_source_metadata(str(self.source))

    def test_rejects_non_protocol_kind_before_claim(self):
        client = FakeClient(self.source, kind="profile")

        with self.assertRaisesRegex(RuntimeError, "kind_not_allowed"):
            worker.distributed_execute_protocol_once(
                client,
                Caps(),
                job_id=154,
            )

        self.assertFalse(any(c[0] == "claim" for c in client.calls))

    def test_requires_protocol_test_flag_and_fails_claimed_job(self):
        client = FakeClient(self.source, flag=False)

        with self.assertRaisesRegex(
            RuntimeError,
            "protocol_test_flag_required",
        ):
            worker.distributed_execute_protocol_once(
                client,
                Caps(),
                job_id=154,
            )

        self.assertTrue(any(c[0] == "claim" for c in client.calls))
        self.assertTrue(any(c[0] == "fail" for c in client.calls))
        self.assertFalse(any(c[0] == "complete" for c in client.calls))


if __name__ == "__main__":
    unittest.main()
