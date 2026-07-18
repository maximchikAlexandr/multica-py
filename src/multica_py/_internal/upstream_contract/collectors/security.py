from __future__ import annotations

import hashlib
import hmac
import os
import pathlib

SAFE_ENV_KEYS: frozenset[str] = frozenset(
    {
        "PATH",
        "HOME",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TERM",
        "NO_COLOR",
        "TZ",
    }
)

DEFAULT_OUTPUT_LIMIT = 16 * 1024 * 1024


def sanitized_environment() -> dict[str, str]:
    """Return an allowlist-only environment for collector subprocesses."""
    env: dict[str, str] = {}
    for key in SAFE_ENV_KEYS:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value
    env["LANG"] = "C"
    env["NO_COLOR"] = "1"
    return env


def is_safe_output_size(size: int, *, limit: int = DEFAULT_OUTPUT_LIMIT) -> bool:
    """Return whether ``size`` is within the collector stdout/stderr cap."""
    return 0 <= size <= limit


def verify_checksum(
    path: pathlib.Path,
    expected_sha256: str,
    *,
    block_size: int = 65536,
) -> bool:
    if not expected_sha256:
        return False
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError:
        return False
    digest = hashlib.sha256()
    try:
        with os.fdopen(fd, "rb") as fh:
            while True:
                chunk = fh.read(block_size)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError:
        return False
    return hmac.compare_digest(digest.hexdigest(), expected_sha256)
