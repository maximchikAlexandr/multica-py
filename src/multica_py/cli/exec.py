from __future__ import annotations

import sys
from typing import BinaryIO, cast

from multica_py._internal.executable import find_executable
from multica_py._internal.processes import run_with_timeout
from multica_py.exceptions import ExecutableNotFoundError


def exec_command(args: list[str]) -> int:
    if not args:
        print("Usage: multica-py exec -- <multica arguments>", file=sys.stderr)
        return 1

    try:
        exe = find_executable()
    except (FileNotFoundError, ExecutableNotFoundError) as e:
        print(f"multica not found: {e}", file=sys.stderr)
        return 1

    multica_args = (str(exe), *args)
    result = run_with_timeout(multica_args)
    cast("BinaryIO", sys.stdout.buffer).write(result.stdout)
    cast("BinaryIO", sys.stderr.buffer).write(result.stderr)
    return result.returncode
