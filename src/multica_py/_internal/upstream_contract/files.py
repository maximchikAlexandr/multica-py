from __future__ import annotations

import os
import pathlib
import shutil
import tempfile


def atomic_write_bytes(
    path: pathlib.Path,
    data: bytes,
    *,
    write: bool = True,
) -> pathlib.Path | None:
    if not write:
        return None
    atomic_write_files({path: data})
    return path


def atomic_write_files(files_map: dict[pathlib.Path, bytes]) -> None:
    if not files_map:
        return
    paths = tuple(files_map.keys())
    parent = paths[0].parent
    for path in paths[1:]:
        if path.parent != parent:
            raise ValueError("atomic_write_files requires paths in the same directory")
    parent.mkdir(parents=True, exist_ok=True)
    staging = pathlib.Path(tempfile.mkdtemp(prefix="atomic.", dir=str(parent)))
    try:
        for path, data in files_map.items():
            (staging / path.name).write_bytes(data)
        for path in paths:
            os.replace(staging / path.name, path)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def writing_ok(*, check: bool, dry_run: bool, output: str | None = None) -> bool:
    if dry_run:
        return False
    if check:
        return output is not None
    return True
