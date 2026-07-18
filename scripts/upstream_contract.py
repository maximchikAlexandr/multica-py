#!/usr/bin/env python3
"""Thin adapter for the upstream-contract CLI.

The actual implementation lives in
``multica_py._internal.upstream_contract.cli``. This script exists so
existing invocations like ``python scripts/upstream_contract.py ...``
continue to work.
"""

from __future__ import annotations

import sys

from multica_py._internal.upstream_contract.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
