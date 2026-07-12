from __future__ import annotations

import os
import pathlib

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


def test_auth_status_with_fake_binary():
    fake_dir = str(pathlib.Path(__file__).parent.parent.parent / "fixtures")
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = fake_dir + os.pathsep + old_path
    try:
        config = ClientConfig(executable="fake_multica.py")
        client = MulticaClient(config)
        status = client.auth.status()
        assert status.authenticated is True
    finally:
        os.environ["PATH"] = old_path


def test_auth_login_with_token_uses_finite_typed_path():
    fake_dir = str(pathlib.Path(__file__).parent.parent.parent / "fixtures")
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = fake_dir + os.pathsep + old_path
    try:
        config = ClientConfig(executable="fake_multica.py")
        client = MulticaClient(config)
        status = client.auth.login("secret-token")
        assert status == "Login successful"
    finally:
        os.environ["PATH"] = old_path
