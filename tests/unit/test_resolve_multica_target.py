from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from unittest.mock import patch

import pytest

from scripts.resolve_multica_target import (
    ResolvedTarget,
    build_version_report,
    read_cli_version,
    resolve_cli_executable,
    verify_cli_version,
)
from tests.live.exceptions import LiveSetupError
from tests.live.settings import load_compatibility_target

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "contracts" / "multica-live-target.toml"


def test_build_version_report_contains_expected_fields() -> None:
    target = load_compatibility_target(TARGET)
    resolved = ResolvedTarget(
        target=target,
        cli_executable=pathlib.Path(sys.executable),
        cli_version_actual=target.cli_version_expected,
    )
    report = build_version_report(resolved)
    assert report["upstream_ref"] == "v0.3.35"
    assert report["cli_version_expected"] == "0.3.35"
    assert report["cli_version_actual"] == "0.3.35"
    assert "backend_digest" in report


def test_read_cli_version_from_stub(tmp_path: pathlib.Path) -> None:
    script = tmp_path / "multica"
    script.write_text("#!/usr/bin/env true\n", encoding="utf-8")
    script.chmod(0o755)
    with patch(
        "scripts.resolve_multica_target.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=[str(script), "version", "--output", "json"],
            returncode=0,
            stdout=json.dumps({"version": "0.3.35"}),
            stderr="",
        ),
    ):
        assert read_cli_version(script) == "0.3.35"


def test_verify_cli_version_fail_closed_on_mismatch(tmp_path: pathlib.Path) -> None:
    script = tmp_path / "multica"
    script.write_text("#!/usr/bin/env true\n", encoding="utf-8")
    script.chmod(0o755)
    with (
        patch(
            "scripts.resolve_multica_target.read_cli_version",
            return_value="9.9.9",
        ),
        pytest.raises(LiveSetupError, match="version mismatch"),
    ):
        verify_cli_version(script, "0.3.35")


def test_resolve_cli_executable_uses_explicit_path() -> None:
    target = load_compatibility_target(TARGET)
    explicit = pathlib.Path(sys.executable)
    with patch(
        "scripts.resolve_multica_target.verify_cli_version", return_value="0.3.35"
    ) as verify:
        resolved = resolve_cli_executable(target, explicit)
    verify.assert_called_once()
    assert resolved == explicit.resolve()


def test_resolve_cli_executable_downloads_for_release_when_missing(
    tmp_path: pathlib.Path,
) -> None:
    target = load_compatibility_target(TARGET)
    fake_cli = tmp_path / "multica"
    fake_cli.write_text("#!/usr/bin/env true\n", encoding="utf-8")
    fake_cli.chmod(0o755)
    with (
        patch("scripts.resolve_multica_target._download_release_cli", return_value=fake_cli),
        patch("scripts.resolve_multica_target.verify_cli_version", return_value="0.3.35"),
    ):
        resolved = resolve_cli_executable(target, None, cache_dir=tmp_path / "cache")
    assert resolved == fake_cli.resolve()
