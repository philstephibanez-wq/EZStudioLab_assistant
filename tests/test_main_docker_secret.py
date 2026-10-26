"""Portable deterministic contract tests; no Docker/LAB/network required."""
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.profile_secret_reader import read_profile_token
from runtime.profile_verify_push import process

ENV = "EZSTUDIOLAB_ASSISTANT_TOKEN_FILE"


class DockerSecretTests(unittest.TestCase):
    def test_missing_secret_is_denied(self):
        with patch.dict(os.environ, {ENV: ""}):
            self.assertEqual(read_profile_token(platform="posix"), "")

    def test_relative_path_denied(self):
        with patch.dict(os.environ, {ENV: "relative/token"}):
            self.assertEqual(read_profile_token(platform="posix"), "")

    def test_readonly_regular_file(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "token"
            path.write_text("unit-test-token\n", encoding="utf-8")
            info = path.lstat()
            mode = (info.st_mode & ~0o777) | 0o400
            with patch.dict(os.environ, {ENV: str(path)}), patch.object(
                Path, "lstat", return_value=SimpleNamespace(st_mode=mode, st_size=info.st_size)
            ):
                self.assertEqual(read_profile_token(platform="posix"), "unit-test-token")

    def test_group_writable_secret_denied(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "token"
            path.write_text("unit-test-token", encoding="utf-8")
            info = path.lstat()
            mode = (info.st_mode & ~0o777) | 0o660
            with patch.dict(os.environ, {ENV: str(path)}), patch.object(
                Path, "lstat", return_value=SimpleNamespace(st_mode=mode, st_size=info.st_size)
            ):
                self.assertEqual(read_profile_token(platform="posix"), "")

    def test_rejects_embedded_control_characters(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "token"
            for payload in ("abc\x00def", "abc\ndef"):
                path.write_text(payload, encoding="utf-8")
                info = path.lstat()
                mode = (info.st_mode & ~0o777) | 0o400
                with patch.dict(os.environ, {ENV: str(path)}), patch.object(
                    Path, "lstat", return_value=SimpleNamespace(st_mode=mode, st_size=info.st_size)
                ):
                    self.assertEqual(read_profile_token(platform="posix"), "")

    def test_wrong_token_rejected(self):
        with self.assertRaises(PermissionError):
            process({"_auth_token": "wrong"}, token_reader=lambda: "correct")


if __name__ == "__main__":
    unittest.main()
