from __future__ import annotations

import importlib.util
import pathlib


def test_drift_script_reads_checked_in_manifest_shape() -> None:
    script_path = pathlib.Path("scripts/check_upstream_drift.py")
    spec = importlib.util.spec_from_file_location("check_upstream_drift", script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    commands = module._load_manifest_commands(module.MANIFEST_PATH)
    assert len(commands) >= 100
    assert "issue set-status" in commands
    assert "project set-status" in commands
