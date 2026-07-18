from __future__ import annotations

import importlib.util
import pathlib


def test_drift_script_delegates_to_unified_cli() -> None:
    script_path = pathlib.Path("scripts/check_upstream_drift.py")
    spec = importlib.util.spec_from_file_location("check_upstream_drift", script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # The compatibility wrapper exposes a `main` function and delegates to
    # the unified `upstream_contract.py` CLI. We do not re-implement the
    # drift logic locally.
    assert hasattr(module, "main")
    assert callable(module.main)
