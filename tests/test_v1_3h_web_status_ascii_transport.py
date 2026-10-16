from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WEB_STATUS = (ROOT / "app" / "web_status.py").read_text(encoding="utf-8")


class AssistantWebStatusAsciiTransportV13h(unittest.TestCase):
    def test_web_status_uses_ascii_safe_json(self):
        self.assertIn(
            "print(json.dumps(payload, ensure_ascii=True))",
            WEB_STATUS,
        )
        self.assertNotIn(
            "print(json.dumps(payload, ensure_ascii=False))",
            WEB_STATUS,
        )

    def test_non_ascii_activity_is_ascii_transport_safe(self):
        payload = {"activity": "En veille — aucun job compatible"}
        encoded = json.dumps(payload, ensure_ascii=True).encode("ascii")
        decoded = json.loads(encoded.decode("ascii"))
        self.assertEqual(payload, decoded)

    def test_single_root_contract_remains(self):
        self.assertIn(
            'DEFAULT_STATUS_FILE = ROOT / "logs" / "assistant.status.json"',
            WEB_STATUS,
        )
        self.assertIn(
            'DEFAULT_TOKEN_FILE = ROOT / "runtime" / "state" / '
            '"analysis-worker-token.dpapi"',
            WEB_STATUS,
        )
        self.assertNotIn(r"C:\var\assistant", WEB_STATUS)


if __name__ == "__main__":
    unittest.main()
