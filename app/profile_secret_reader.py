"""Fail-closed PROFILE authentication on Windows/XPS and Linux/MAIN.

Linux accepts only an explicitly configured read-only secret file.
No token is taken from environment values or committed resources.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

from web_status import DEFAULT_TOKEN_FILE, _read_dpapi_token

SECRET_PATH_ENV = "EZSTUDIOLAB_ASSISTANT_TOKEN_FILE"


def read_profile_token() -> str:
    if os.name == "nt":
        return _read_dpapi_token(DEFAULT_TOKEN_FILE)
    secret_name = os.environ.get(SECRET_PATH_ENV, "")
    if not secret_name or not Path(secret_name).is_absolute():
        return ""
    secret_path = Path(secret_name)
    try:
        info = secret_path.lstat()
        if not stat.S_ISREG(info.st_mode):
            return ""
        if info.st_mode & 0o022:
            return ""
        if info.st_size < 1 or info.st_size > 4096:
            return ""
        value = secret_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError, ValueError):
        return ""
    if not value or len(value) > 2048 or "\\x00" in value or "\\n" in value or "\\r" in value:
        return ""
    return value
