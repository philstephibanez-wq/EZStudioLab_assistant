"""Linux secret is fail closed; no network, no Docker or LAB calls."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.profile_secret_reader import read_profile_token
from runtime.profile_verify_push import process


class DockerSecretTests(unittest.TestCase):
    def _linux(self, p):
        with patch("app.profile_secret_reader.os.name", "posix"):
            return read_profile_token()

    def test_missing_explicit_secret_refuses(self):
        with patch.dict(os.environ, {"EZSTUDIOLAB_ASSISTANT_TOKEN_FILE": ""}):
            self.assertEqual(self._linux(None), "")

    def test_explicit_read_only_regular_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("unit-test-token\\n", encoding="utf-8")
            path.chmod(0o400)
            with patch.dict(os.environ, {"EZSTUDIOLAB_ASSISTANT_TOKEN_FILE": str(path)}):
                self.assertEqual(self._linux(path), "unit-test-token")

    def test_rejects_writable_and_directory_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("unsafe-token", encoding="utf-8")
            path.chmod(0o666)
            with patch.dict(os.environ, {"EZSTUDIOLAB_ASSISTANT_TOKEN_FILE": str(path)}):
                self.assertEqual(self._linux(path), "")
            with patch.dict(os.environ, {"EZSTUDIOLAB_ASSISTANT_TOKEN_FILE": directory}):
                self.assertEqual(self._linux(None), "")

    def test_wrong_token_rejected_before_research(self):
        with self.assertRaises(PermissionError):
            process({"_auth_token": "wrong"}, token_reader=lambda: "correct")


if __name__ == "__main__":
    unittest.main()
