from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WEB_STATUS_PATH = ROOT / "app" / "web_status.py"
WEB_STATUS = WEB_STATUS_PATH.read_text(encoding="utf-8")


class AssistantWebStatusSingleRootV13g(unittest.TestCase):
    def test_python_syntax(self):
        ast.parse(WEB_STATUS, filename=str(WEB_STATUS_PATH))

    def test_status_default_is_inside_single_root(self):
        self.assertIn(
            'DEFAULT_STATUS_FILE = ROOT / "logs" / "assistant.status.json"',
            WEB_STATUS,
        )
        self.assertIn('"EZSTUDIOLAB_ASSISTANT_STATUS_FILE"', WEB_STATUS)

    def test_dpapi_token_default_is_inside_single_root(self):
        self.assertIn(
            'DEFAULT_TOKEN_FILE = ROOT / "runtime" / "state" / '
            '"analysis-worker-token.dpapi"',
            WEB_STATUS,
        )
        self.assertIn("def _read_dpapi_token(path: Path) -> str:", WEB_STATUS)
        self.assertIn("ConvertTo-SecureString $cipher", WEB_STATUS)
        self.assertIn(
            "token = _read_dpapi_token(DEFAULT_TOKEN_FILE)",
            WEB_STATUS,
        )

    def test_token_precedence_preserves_environment_contract(self):
        env_read = 'os.getenv("EZSTUDIOLAB_ASSISTANT_TOKEN", "").strip()'
        fallback = "token = _read_dpapi_token(DEFAULT_TOKEN_FILE)"
        self.assertIn(env_read, WEB_STATUS)
        self.assertIn(fallback, WEB_STATUS)
        self.assertLess(WEB_STATUS.index(env_read), WEB_STATUS.index(fallback))

    def test_token_is_not_embedded_in_powershell_command_line(self):
        self.assertIn(
            'env["EZSTUDIOLAB_ASSISTANT_TOKEN_FILE"] = str(path)',
            WEB_STATUS,
        )
        self.assertIn(
            "$p=$env:EZSTUDIOLAB_ASSISTANT_TOKEN_FILE;",
            WEB_STATUS,
        )
        self.assertNotIn("$env:EZSTUDIOLAB_ASSISTANT_TOKEN=", WEB_STATUS)

    def test_legacy_external_runtime_fallback_removed(self):
        self.assertNotIn("INSTALL_ROOT = ROOT.parent", WEB_STATUS)
        self.assertNotIn(
            'RUNTIME_ROOT = INSTALL_ROOT / "var" / "assistant"',
            WEB_STATUS,
        )
        self.assertNotIn(r"C:\var\assistant", WEB_STATUS)

    def test_network_contracts_unchanged(self):
        self.assertIn(r"\\EZSTUDIO-MAIN\EZModels", WEB_STATUS)
        self.assertIn('"http://EZSTUDIO-MAIN:8702"', WEB_STATUS)
        self.assertIn('"/internal/analysis/desktop/hello"', WEB_STATUS)


if __name__ == "__main__":
    unittest.main()
