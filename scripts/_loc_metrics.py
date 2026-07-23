"""Shared logical-line counting helpers for test quality gates."""

from __future__ import annotations

import pathlib


def logical_lines(path: pathlib.Path) -> int:
    count = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        count += 1
    return count


def glob_logical_lines(root: pathlib.Path, pattern: str) -> int:
    total = 0
    for path in sorted(root.glob(pattern)):
        if path.is_file():
            total += logical_lines(path)
    return total


def live_support_loc(repo_root: pathlib.Path) -> int:
    total = 0
    for p in sorted((repo_root / "tests" / "live").rglob("*.py")):
        if p.is_file() and not p.name.startswith("test_"):
            total += logical_lines(p)
    total += glob_logical_lines(repo_root / "tools" / "live_support", "**/*.py")
    return total


def max_test_support_file(repo_root: pathlib.Path) -> int:
    max_lines = 0
    for p in sorted((repo_root / "tests").rglob("*.py")):
        if p.is_file():
            max_lines = max(max_lines, logical_lines(p))
    for p in sorted((repo_root / "tools" / "live_support").rglob("*.py")):
        if p.is_file():
            max_lines = max(max_lines, logical_lines(p))
    return max_lines
