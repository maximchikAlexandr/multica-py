#!/usr/bin/env python3
"""Compatibility wrapper for the old drift check command.

Delegates to the unified `scripts/upstream_contract.py check` command.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE / "upstream_contract.py"


def main() -> int:
    argv = ["check", "--format", "human", "--repo-root", str(HERE.parent)]
    result = subprocess.run([sys.executable, str(TARGET), *argv], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
