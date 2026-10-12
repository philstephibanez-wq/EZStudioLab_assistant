from __future__ import annotations
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = (ROOT / "app" / "worker.py").read_text(encoding="utf-8")
STATUS = (ROOT / "app" / "runtime_status.py").read_text(encoding="utf-8")
WINDOW = (ROOT / "app" / "status_window.ps1").read_text(encoding="utf-8-sig")

class V1DLocalWindowContract(unittest.TestCase):
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

    def test_window_reads_status_as_utf8(self):
        self.assertIn(
            "Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8",
            WINDOW,
        )
        self.assertIn(
            "Get-Content -LiteralPath $commitPath -Raw -Encoding UTF8",
            WINDOW,
        )

    def test_close_hides_to_tray_without_stopping_worker(self):
        self.assertIn("System.Windows.Forms.NotifyIcon", WINDOW)
        self.assertIn("UserClosing", WINDOW)
        self.assertIn("$e.Cancel = $true", WINDOW)
        self.assertIn("$form.Hide()", WINDOW)
        self.assertIn("Afficher EZStudioLab Assistant", WINDOW)
        self.assertNotIn("Stop-Process", WINDOW)
        self.assertNotIn("taskkill", WINDOW.lower())

    def test_operator_information(self):
        for value in ("Version :", "Dernier contact :", "ARRÊTÉ", "EN LIGNE", "OCCUPÉ", "ERREUR"):
            self.assertIn(value, WINDOW)

if __name__ == "__main__":
    unittest.main()
