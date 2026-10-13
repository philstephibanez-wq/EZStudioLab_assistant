from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = (ROOT / "app" / "worker.py").read_text(encoding="utf-8")
STATUS = (ROOT / "app" / "runtime_status.py").read_text(encoding="utf-8")
WINDOW = (ROOT / "app" / "status_window.pyw").read_text(encoding="utf-8")


class V1D5ALocalStatusContract(unittest.TestCase):
    def test_atomic_status(self):
        self.assertIn("assistant.status.json", STATUS)
        self.assertIn("os.replace(tmp, path)", STATUS)
        self.assertIn("ezstudio.assistant-local-status.v1", STATUS)

    def test_watch_updates_status_without_claim(self):
        self.assertIn("from runtime_status import write_status", WORKER)
        tail = WORKER.split("def watch_distributed", 1)[1]
        self.assertIn("Recherche de job compatible", tail)
        self.assertIn("En veille — aucun job compatible", tail)
        self.assertNotIn("distributed_claim_job(", tail)

    def test_pythonw_window_has_no_worker_control(self):
        self.assertIn('APP_TITLE = "EZStudioLab Assistant"', WINDOW)
        self.assertIn('self.root.protocol("WM_DELETE_WINDOW", self.hide)', WINDOW)
        self.assertIn("self.root.withdraw()", WINDOW)
        self.assertIn("self.root.deiconify()", WINDOW)
        self.assertNotIn("subprocess", WINDOW)
        self.assertNotIn("Stop-Process", WINDOW)
        self.assertNotIn("taskkill", WINDOW.lower())

    def test_native_tray_is_dependency_free(self):
        self.assertIn("Shell_NotifyIconW", WINDOW)
        self.assertIn("NIM_ADD", WINDOW)
        self.assertIn("NIM_DELETE", WINDOW)
        self.assertIn("WM_LBUTTONDBLCLK", WINDOW)
        self.assertIn("TRAY_ADD_OK", WINDOW)
        self.assertNotIn("pystray", WINDOW)

    def test_operator_information(self):
        self.assertIn(
            'self.root.title(f"{APP_TITLE} v{self._read_version()}")',
            WINDOW,
        )
        self.assertIn(
            'text=f"{APP_TITLE} v{self._read_version()}"',
            WINDOW,
        )
        for value in (
            "Dernier contact :",
            "ARRÊTÉ",
            "EN LIGNE",
            "OCCUPÉ",
            "ERREUR",
            "PÉRIMÉ",
        ):
            self.assertIn(value, WINDOW)


if __name__ == "__main__":
    unittest.main()
