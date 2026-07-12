from __future__ import annotations

import os
import pathlib

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus


def test_issue_set_status_and_deprioritize_with_fake_binary() -> None:
    fake_dir = str(pathlib.Path(__file__).parent.parent.parent / "fixtures")
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = fake_dir + os.pathsep + old_path
    try:
        config = ClientConfig(executable="fake_multica.py")
        client = MulticaClient(config)
        issue = client.issues.set_status("iss_001", IssueStatus.done)
        assert issue.status == IssueStatus.done
        text = client.issues.deprioritize("iss_001")
        assert "deprioritized" in text
    finally:
        os.environ["PATH"] = old_path
