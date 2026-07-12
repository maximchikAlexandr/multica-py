from __future__ import annotations

import os
import pathlib

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import ProjectStatus


def test_project_list_with_fake_binary():
    fake_dir = str(pathlib.Path(__file__).parent.parent.parent / "fixtures")
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = fake_dir + os.pathsep + old_path
    try:
        config = ClientConfig(executable="fake_multica.py")
        client = MulticaClient(config)
        projects = client.projects.list()
        assert len(projects) > 0
    finally:
        os.environ["PATH"] = old_path


def test_project_set_status_with_fake_binary() -> None:
    fake_dir = str(pathlib.Path(__file__).parent.parent.parent / "fixtures")
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = fake_dir + os.pathsep + old_path
    try:
        config = ClientConfig(executable="fake_multica.py")
        client = MulticaClient(config)
        project = client.projects.set_status("pr_001", ProjectStatus.completed)
        assert project.status == ProjectStatus.completed
    finally:
        os.environ["PATH"] = old_path
