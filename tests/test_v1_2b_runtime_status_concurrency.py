from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from app import runtime_status


class V12bRuntimeStatusConcurrencyContract(unittest.TestCase):
    def test_unique_temp_files_and_atomic_replace_under_concurrent_writers(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "assistant.status.json"
            errors: list[BaseException] = []

            def writer(index: int) -> None:
                try:
                    for iteration in range(40):
                        runtime_status.write_status(
                            "ONLINE",
                            f"writer-{index}",
                            extra={"iteration": iteration},
                        )
                except BaseException as exc:
                    errors.append(exc)

            with mock.patch.object(
                runtime_status,
                "status_path",
                return_value=target,
            ):
                threads = [
                    threading.Thread(target=writer, args=(index,))
                    for index in range(4)
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()

            self.assertEqual(errors, [])
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "ezstudio.assistant-local-status.v1")
            self.assertFalse(list(Path(tmp_dir).glob("assistant.status.json.*.tmp")))

    def test_permission_error_is_retried(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "assistant.status.json"
            real_replace = os.replace
            calls = {"count": 0}

            def flaky_replace(src, dst):
                calls["count"] += 1
                if calls["count"] < 3:
                    raise PermissionError(5, "simulated Windows destination lock")
                return real_replace(src, dst)

            with mock.patch.object(
                runtime_status,
                "status_path",
                return_value=target,
            ):
                with mock.patch.object(runtime_status.os, "replace", flaky_replace):
                    runtime_status.write_status("ONLINE", "retry-contract")

            self.assertEqual(calls["count"], 3)
            self.assertTrue(target.is_file())
            self.assertFalse(list(Path(tmp_dir).glob("assistant.status.json.*.tmp")))


if __name__ == "__main__":
    unittest.main()
