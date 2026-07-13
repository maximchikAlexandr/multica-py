from __future__ import annotations

import datetime
import sys
from typing import BinaryIO, cast

from multica_py._internal.decoders import decode_text
from multica_py._internal.executable import find_executable
from multica_py._internal.processes import run_with_timeout
from multica_py._internal.redaction import collect_secret_values, redact_text
from multica_py.exceptions import CommandTimeoutError, ExecutableNotFoundError

_DEFAULT_EXEC_TIMEOUT = datetime.timedelta(minutes=10)


def exec_command(args: list[str], timeout: datetime.timedelta | None = None) -> int:
    if not args:
        print("Usage: multica-py exec -- <multica arguments>", file=sys.stderr)
        return 1

    try:
        exe = find_executable()
    except (FileNotFoundError, ExecutableNotFoundError) as e:
        print(f"multica not found: {e}", file=sys.stderr)
        return 1

    effective_timeout = timeout if timeout is not None else _DEFAULT_EXEC_TIMEOUT
    multica_args = (str(exe), *args)
    try:
        result = run_with_timeout(multica_args, timeout=effective_timeout)
    except CommandTimeoutError:
        print(f"multica-py exec timed out after {effective_timeout}", file=sys.stderr)
        return 124
    # ponytail: stdout left raw to preserve binary passthrough (e.g. downloads); only stderr (text) is redacted.
    cast("BinaryIO", sys.stdout.buffer).write(result.stdout)
    secrets = collect_secret_values(tuple(args))
    # ponytail: decode defensively so non-UTF-8 stderr is still redacted, never leaks as a traceback.
    try:
        err_text = decode_text(result.stderr)
    except Exception:
        err_text = result.stderr.decode("utf-8", errors="replace")
    redacted_err = redact_text(err_text, secret_values=secrets)
    cast("BinaryIO", sys.stderr.buffer).write(redacted_err.encode("utf-8"))
    return result.returncode
