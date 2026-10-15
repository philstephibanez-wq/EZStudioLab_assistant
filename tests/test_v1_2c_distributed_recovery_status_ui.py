from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
WORKER = APP / "worker.py"


def load_worker():
    sys.path.insert(0, str(APP))
    try:
        spec = importlib.util.spec_from_file_location(
            "worker_v12c_contract",
            WORKER,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(APP))


class Caps:
    node_id = "worker-test"

    def to_dict(self):
        return {"protocol": "ezstudio.distributed.v1"}


class Client:
    def __init__(self):
        self.events = []

    def distributed_worker_heartbeat(self, worker_id, cap, *, state):
        self.events.append(("heartbeat", state))
        return {"state": state}

    def distributed_eligible_jobs(self, worker_id, *, limit):
        self.events.append(("eligible", limit))
        return []


class DistributedRecoveryContract(unittest.TestCase):
    def test_watch_heartbeats_before_eligible(self):
        worker = load_worker()
        client = Client()
        original = worker.write_status
        worker.write_status = lambda *a, **k: None
        try:
            rc = worker.watch_distributed(
                client,
                Caps(),
                poll_seconds=1,
                iterations=1,
                limit=100,
            )
        finally:
            worker.write_status = original

        self.assertEqual(rc, 0)
        self.assertEqual(
            client.events[:4],
            [
                ("heartbeat", "starting"),
                ("heartbeat", "polling"),
                ("eligible", 100),
                ("heartbeat", "idle"),
            ],
        )

    def test_error_summary_for_stale_worker(self):
        worker = load_worker()
        exc = RuntimeError(
            'HTTP 409 /eligible: {"error":"worker_heartbeat_stale"}'
        )
        self.assertEqual(
            worker._distributed_error_summary(exc),
            "Worker distribué expiré côté LAB",
        )




if __name__ == "__main__":
    unittest.main(verbosity=2)
