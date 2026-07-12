from __future__ import annotations

import pathlib
import shutil

from multica_py.exceptions import ExecutableNotFoundError


def find_executable(name: str = "multica") -> pathlib.Path:
    resolved = shutil.which(name)
    if resolved is None:
        raise ExecutableNotFoundError(f"Executable not found on PATH: {name}")
    return pathlib.Path(resolved)
