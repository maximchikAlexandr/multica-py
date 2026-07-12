from __future__ import annotations

import platform
import sys

from multica_py._internal.executable import find_executable
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


def doctor() -> int:
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.system()} {platform.machine()}")

    try:
        exe = find_executable()
        print(f"Multica executable: {exe}")
    except Exception as e:
        print(f"Multica executable: NOT FOUND ({e})")
        return 1

    try:
        config = ClientConfig(executable=str(exe))
        client = MulticaClient(config)
        ver = client.maintenance.version()
        print(f"CLI version: {ver.version}")
        auth_status = client.auth.status()
        if auth_status.authenticated:
            print(f"Auth: authenticated (user {auth_status.user_id})")
        else:
            print("Auth: not authenticated")
    except Exception as e:
        print(f"CLI check failed: {e}")
        return 1

    return 0
