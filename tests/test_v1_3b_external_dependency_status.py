from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import importlib.util
import json
import subprocess
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_web_status():
    path = ROOT / "app" / "web_status.py"
    spec = importlib.util.spec_from_file_location("web_status_v13b", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AssistantExternalDependencyStatusV13B(TestCase):
    def test_lab_uses_canonical_hello(self):
        source = (ROOT / "app" / "web_status.py").read_text(encoding="utf-8")
        self.assertIn("/internal/analysis/desktop/hello", source)
        self.assertNotIn("/api/status", source)

    def test_smb_probe_is_bounded(self):
        source = (ROOT / "app" / "web_status.py").read_text(encoding="utf-8")
        self.assertIn("SMB_TIMEOUT_SECONDS", source)
        self.assertIn("subprocess.run(", source)
        self.assertIn("TimeoutExpired", source)

    def test_lab_failure_is_degraded_not_process_failure(self):
        module = load_web_status()
        with patch.object(
            module.AnalysisApiClient,
            "request",
            side_effect=module.AnalysisApiError("boom"),
        ):
            result = module._probe_lab("http://lab.invalid", "token")
        self.assertFalse(result["reachable"])
        self.assertFalse(result["authorized"])
        self.assertIn("boom", result["error"])

    def test_smb_timeout_returns_status(self):
        module = load_web_status()
        with patch.object(
            module.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["python"], 1.5),
        ):
            result = module._probe_model_root(Path(r"\\host\share"))
        self.assertFalse(result["accessible"])
        self.assertEqual("model_root_timeout", result["error"])

    def test_symfony_string_dependency_is_explicit(self):
        require = json.loads(
            (ROOT / "composer.json").read_text(encoding="utf-8")
        )["require"]
        self.assertEqual("7.4.*", require.get("symfony/string"))


if __name__ == "__main__":
    import unittest
    unittest.main()
