from __future__ import annotations

import contextlib
import os
import pathlib
import tempfile

from .renderer import GeneratedOutput


def write_outputs(outputs: tuple[GeneratedOutput, ...], repo_root: pathlib.Path) -> None:
    for out in outputs:
        dest = repo_root / out.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix=f".tmp.{dest.name}.",
            dir=str(dest.parent),
            delete=False,
        ) as tmp:
            try:
                tmp.write(out.content)
                tmp.flush()
                os.fsync(tmp.fileno())
            except BaseException:
                with contextlib.suppress(OSError):
                    os.unlink(tmp.name)
                raise
        os.replace(tmp.name, str(dest))


def check_outputs(outputs: tuple[GeneratedOutput, ...], repo_root: pathlib.Path) -> int:
    exit_code = 0
    for out in outputs:
        dest = repo_root / out.path
        if not dest.is_file():
            print(f"MISSING: {out.path}")
            exit_code = 1
            continue
        existing = dest.read_bytes()
        if existing != out.content:
            diff_lines = _diff_info(out.path, len(existing), len(out.content))
            for line in diff_lines:
                print(line)
            exit_code = 1
    return exit_code


def _diff_info(path: pathlib.PurePath, existing_len: int, expected_len: int) -> list[str]:
    lines = [f"MISMATCH: {path}"]
    if existing_len != expected_len:
        lines.append(f"  size: existing={existing_len} expected={expected_len}")
    return lines
