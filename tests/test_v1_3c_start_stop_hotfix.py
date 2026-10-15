from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AssistantStartStopHotfix13C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.start = (ROOT / "scripts" / "start.ps1").read_text(encoding="utf-8-sig")
        cls.stop = (ROOT / "scripts" / "stop.ps1").read_text(encoding="utf-8-sig")

    def test_version_stays_13c(self):
        self.assertEqual("1.3f", (ROOT / "VERSION").read_text(encoding="utf-8").strip())

    def test_start_is_singleton_and_can_recover_running_instance(self):
        self.assertIn("instance.lock", self.start)
        self.assertIn("ASSISTANT_WEB_ALREADY_RUNNING", self.start)
        self.assertIn("ASSISTANT_WEB_START_IN_PROGRESS_OR_RUNNING", self.start)
        self.assertIn("recovered_at=", self.start)

    def test_start_validates_real_listeners(self):
        self.assertIn("Get-NetTCPConnection", self.start)
        self.assertIn("assistant_web_foreign_port_owner", self.start)
        self.assertIn("assistant_web_listener_validation_failed", self.start)

    def test_stop_does_not_trust_pid_files_blindly(self):
        self.assertIn("Test-AssistantProcess", self.stop)
        self.assertIn("CommandLine", self.stop)
        self.assertIn("IndexOf($root", self.stop)

    def test_stop_recovers_orphaned_processes(self):
        self.assertIn("Get-PortOwner $port", self.stop)
        self.assertIn("Get-CimInstance Win32_Process", self.stop)

    def test_stop_verifies_ports_are_free(self):
        self.assertIn("assistant_web_stop_incomplete", self.stop)
        self.assertIn("ASSISTANT_WEB_STOP_OK", self.stop)


if __name__ == "__main__":
    unittest.main()


