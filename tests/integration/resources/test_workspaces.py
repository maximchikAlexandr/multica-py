from __future__ import annotations

import os
import pathlib

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


def test_workspace_list_with_fake_binary():
    fake_dir = str(pathlib.Path(__file__).parent.parent.parent / "fixtures")
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = fake_dir + os.pathsep + old_path
    try:
        config = ClientConfig(executable="fake_multica.py")
        client = MulticaClient(config)
        workspaces = client.workspaces.list()
        assert len(workspaces) > 0
    finally:
        os.environ["PATH"] = old_path
