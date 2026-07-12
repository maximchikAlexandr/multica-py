from __future__ import annotations

import importlib.metadata

from multica_py._internal.executable import find_executable
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


def show_version() -> int:
    try:
        pkg_ver = importlib.metadata.version("multica-py")
        print(f"multica-py {pkg_ver}")
    except importlib.metadata.PackageNotFoundError:
        print("multica-py (development)")

    try:
        exe = find_executable()
        config = ClientConfig(executable=str(exe))
        client = MulticaClient(config)
        ver = client.maintenance.version()
        print(f"Upstream multica: {ver.version} (commit {ver.commit})")
    except Exception as e:
        print(f"Could not detect upstream CLI version: {e}")

    return 0
