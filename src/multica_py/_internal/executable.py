from __future__ import annotations

import pathlib
import shutil
import warnings

from multica_py.exceptions import ExecutableNotFoundError


def find_executable(name: str = "multica") -> pathlib.Path:
    resolved = shutil.which(name)
    if resolved is None:
        raise ExecutableNotFoundError(f"Executable not found on PATH: {name}")
    path = pathlib.Path(resolved)
    _warn_if_insecure_dir(path.parent)
    return path


def _warn_if_insecure_dir(directory: pathlib.Path) -> None:
    # ponytail: warn-only; refusing would block legitimate installs in writable dirs
    try:
        mode = directory.stat().st_mode
    except OSError:
        return
    if mode & 0o002:
        warnings.warn(
            f"Executable directory {directory} is world-writable; PATH may be tampered with",
            stacklevel=2,
        )
