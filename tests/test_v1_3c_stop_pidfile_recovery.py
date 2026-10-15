from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
STOP = (ROOT / "scripts" / "stop.ps1").read_text(encoding="utf-8-sig")


class AssistantStopPidFileRecovery13C(unittest.TestCase):
    def test_version_stays_13c(self):
        self.assertEqual(
            "1.3e",
            (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip(),
        )

    def test_strict_commandline_ownership_remains(self):
        self.assertIn("Test-AssistantProcess", STOP)
        self.assertIn("CommandLine", STOP)
        self.assertIn("IndexOf($root", STOP)

    def test_pidfile_fallback_is_bounded(self):
        self.assertIn("function Add-PidFilePortCandidate", STOP)
        self.assertIn("[string]$processInfo.Name -ne $ExpectedName", STOP)
        self.assertIn("Get-PortOwner $ExpectedPort", STOP)
        self.assertIn("[int]$owner -ne $pidValue", STOP)

    def test_exact_ports_are_bound_to_exact_process_types(self):
        self.assertIn(
            "Add-PidFilePortCandidate $candidates $caddyPidPath 'caddy.exe' 8712",
            STOP,
        )
        self.assertIn(
            "Add-PidFilePortCandidate $candidates $phpPidPath 'php.exe' 8713",
            STOP,
        )

    def test_final_port_check_remains(self):
        self.assertIn("assistant_web_stop_incomplete", STOP)
        self.assertIn("ASSISTANT_WEB_STOP_OK", STOP)


if __name__ == "__main__":
    unittest.main()


