from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

from multica_py._internal.upstream_contract.collectors import security

if TYPE_CHECKING:
    import pytest


def test_sanitized_environment_drops_non_allowlisted_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "MULTICA_AUTH_TOKEN",
        "GCP_API_KEY",
        "LD_PRELOAD",
        "DYLD_INSERT_LIBRARIES",
        "KUBECONFIG",
        "PATH",
        "HOME",
    ):
        monkeypatch.setenv(key, "value")

    env = security.sanitized_environment()
    assert "PATH" in env
    assert "HOME" in env
    assert "LANG" in env and env["LANG"] == "C"
    assert "NO_COLOR" in env and env["NO_COLOR"] == "1"
    for forbidden in (
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "MULTICA_AUTH_TOKEN",
        "GCP_API_KEY",
        "LD_PRELOAD",
        "DYLD_INSERT_LIBRARIES",
        "KUBECONFIG",
    ):
        assert forbidden not in env


def test_sanitized_environment_keeps_safe_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("PATH", "LANG", "LC_ALL", "TERM", "NO_COLOR", "TZ"):
        monkeypatch.setenv(key, "x")
    env = security.sanitized_environment()
    for key in ("PATH", "LANG", "NO_COLOR"):
        assert key in env


def test_verify_checksum_accepts_match(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "blob.bin"
    file_path.write_bytes(b"hello world")
    digest = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert security.verify_checksum(file_path, digest) is True


def test_verify_checksum_rejects_mismatch(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "blob.bin"
    file_path.write_bytes(b"hello world")
    assert security.verify_checksum(file_path, "0" * 64) is False


def test_verify_checksum_rejects_empty_expected() -> None:
    assert security.verify_checksum(pathlib.Path(__file__), "") is False


def test_is_safe_output_size() -> None:
    from multica_py._internal.upstream_contract.collectors import security

    limit = security.DEFAULT_OUTPUT_LIMIT
    assert security.is_safe_output_size(limit) is True
    assert security.is_safe_output_size(limit + 1) is False
