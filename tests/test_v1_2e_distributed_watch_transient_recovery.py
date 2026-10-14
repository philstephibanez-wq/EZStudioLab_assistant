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
            "worker_v12e_transient_recovery",
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


class TransientStartupClient:
    def __init__(self, api_error):
        self.api_error = api_error
        self.start_attempts = 0
        self.events = []

    def distributed_worker_heartbeat(self, worker_id, cap, *, state):
        self.events.append(("heartbeat", state))
        if state == "starting":
            self.start_attempts += 1
            if self.start_attempts == 1:
                raise self.api_error(
                    "/internal/analysis/desktop/distributed/workers/heartbeat: "
                    "URLError:<urlopen error timed out>"
                )
        return {"state": state}

    def distributed_eligible_jobs(self, worker_id, *, limit):
        self.events.append(("eligible", limit))
        return []


class FatalClient:
    def distributed_worker_heartbeat(self, worker_id, cap, *, state):
        return {"state": state}

    def distributed_eligible_jobs(self, worker_id, *, limit):
        raise RuntimeError("programming_contract_failure")


class DistributedTransientRecoveryContract(unittest.TestCase):
    def test_transient_analysis_api_error_retries_and_recovers(self):
        worker = load_worker()
        client = TransientStartupClient(worker.AnalysisApiError)
        statuses = []
        sleeps = []

        original_status = worker.write_status
        original_sleep = worker.time.sleep
        worker.write_status = lambda *a, **k: statuses.append((a, k))
        worker.time.sleep = lambda seconds: sleeps.append(seconds)
        try:
            rc = worker.watch_distributed(
                client,
                Caps(),
                poll_seconds=5,
                iterations=1,
                limit=100,
            )
        finally:
            worker.write_status = original_status
            worker.time.sleep = original_sleep

        self.assertEqual(rc, 0)
        self.assertEqual(client.start_attempts, 2)
        self.assertIn(5.0, sleeps)
        self.assertTrue(
            any(
                args[:2] == (
                    "ERROR",
                    "Connexion LAB temporairement indisponible — nouvelle tentative",
                )
                and kwargs.get("extra", {}).get("worker_continues") is True
                for args, kwargs in statuses
            )
        )
        self.assertTrue(
            any(
                args[:2] == ("ONLINE", "En veille — aucun job compatible")
                for args, _kwargs in statuses
            )
        )

    def test_non_transport_failure_remains_fatal(self):
        worker = load_worker()
        statuses = []

        original_status = worker.write_status
        worker.write_status = lambda *a, **k: statuses.append((a, k))
        try:
            with self.assertRaisesRegex(
                RuntimeError,
                "programming_contract_failure",
            ):
                worker.watch_distributed(
                    FatalClient(),
                    Caps(),
                    poll_seconds=1,
                    iterations=1,
                    limit=100,
                )
        finally:
            worker.write_status = original_status

        self.assertTrue(
            any(
                kwargs.get("extra", {}).get("worker_continues") is False
                for _args, kwargs in statuses
            )
        )

    def test_retry_delay_is_bounded(self):
        worker = load_worker()
        self.assertEqual(worker._distributed_retry_delay(5, 1), 5.0)
        self.assertEqual(worker._distributed_retry_delay(5, 2), 10.0)
        self.assertEqual(worker._distributed_retry_delay(5, 3), 20.0)
        self.assertEqual(worker._distributed_retry_delay(5, 4), 30.0)
        self.assertEqual(worker._distributed_retry_delay(5, 99), 30.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
