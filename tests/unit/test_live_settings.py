from __future__ import annotations

import os
import pathlib
import re
import sys

import pytest

from tests.live.exceptions import LiveSetupError
from tests.live.settings import (
    MAX_LABEL_NAME_LEN,
    LiveSettings,
    create_live_test_run,
    label_name,
    load_compatibility_target,
    load_live_settings,
    resolve_secrets_base_dir,
    resource_prefix,
    workspace_slug,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TARGET_FILE = REPO_ROOT / "contracts" / "multica-live-target.toml"


def test_committed_target_matches_pin() -> None:
    target = load_compatibility_target(TARGET_FILE)
    assert target.upstream_ref == "v0.3.35"
    assert target.upstream_commit == "4416313f8f7f801df8b7f5072087da8a6502a89c"
    assert target.backend_digest == (
        "sha256:656dd76e866f636863a6fc034f04165227e35f427e526914ea2c9848f8f55e30"
    )
    assert target.backend_digest_linux_amd64 == (
        "sha256:d8a50acac1eb674093b0e9de4afc656328ac6b37fc641f1fb4b256547f1ffe3b"
    )
    assert target.cli_release_sha256_linux_amd64 == (
        "5bb3472eab5be4cb17a8459d7b2b1ca9bda325432f7f23966d1e81164e9e6167"
    )


def test_rejects_latest_in_target(tmp_path: pathlib.Path) -> None:
    manifest = TARGET_FILE.read_text(encoding="utf-8").replace(
        'upstream_ref = "v0.3.35"',
        'upstream_ref = "latest"',
        1,
    )
    path = tmp_path / "target.toml"
    path.write_text(manifest, encoding="utf-8")
    with pytest.raises(LiveSetupError, match="forbidden placeholder"):
        load_compatibility_target(path)


def test_rejects_missing_cli_without_resolver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MULTICA_LIVE_CLI", raising=False)
    monkeypatch.delenv("MULTICA_LIVE_RESOLVE_CLI", raising=False)
    monkeypatch.setenv("MULTICA_LIVE_UPSTREAM_DIR", "/tmp/multica")
    with pytest.raises(LiveSetupError, match="MULTICA_LIVE_CLI is required"):
        load_live_settings(repo_root=REPO_ROOT)


def test_rejects_non_loopback_existing_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MULTICA_LIVE_CLI", "/tmp/multica")
    monkeypatch.setenv("MULTICA_LIVE_EXISTING_URL", "http://example.com:8080")
    with pytest.raises(LiveSetupError, match="loopback-only"):
        load_live_settings(repo_root=REPO_ROOT)


def test_accepts_loopback_existing_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MULTICA_LIVE_CLI", sys.executable)
    monkeypatch.setenv("MULTICA_LIVE_EXISTING_URL", "http://127.0.0.1:8080")
    settings = load_live_settings(repo_root=REPO_ROOT)
    assert settings.existing_url == "http://127.0.0.1:8080"


def test_ready_timeout_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MULTICA_LIVE_CLI", sys.executable)
    monkeypatch.setenv("MULTICA_LIVE_UPSTREAM_DIR", "/tmp/multica")
    monkeypatch.setenv("MULTICA_LIVE_READY_TIMEOUT", "9")
    with pytest.raises(LiveSetupError, match="between 10 and 600"):
        load_live_settings(repo_root=REPO_ROOT)


def test_ci_forbids_keep_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("MULTICA_LIVE_CLI", sys.executable)
    monkeypatch.setenv("MULTICA_LIVE_UPSTREAM_DIR", "/tmp/multica")
    monkeypatch.setenv("MULTICA_LIVE_KEEP_ENV", "1")
    with pytest.raises(LiveSetupError, match="forbidden in CI"):
        load_live_settings(repo_root=REPO_ROOT)


def test_workspace_slug_truncates_with_hash_suffix() -> None:
    slug = workspace_slug("x" * 80, "a")
    assert len(slug) <= 48
    assert re.search(r"-[0-9a-f]{8}$", slug)


def test_resource_prefix_truncates_with_hash_suffix() -> None:
    prefix = resource_prefix("y" * 80, "test-name")
    assert len(prefix) <= 64
    assert prefix.startswith("mpy-live-")
    assert re.search(r"-[0-9a-f]{8}$", prefix)


def test_label_name_respects_upstream_max_length() -> None:
    name = label_name("mpy-live-" + ("z" * 80), "crud")
    assert len(name) <= MAX_LABEL_NAME_LEN
    assert name.endswith("-crud")


def test_secrets_dir_is_outside_artifact_root(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    secrets_root = tmp_path / "secrets"
    monkeypatch.setenv("MULTICA_LIVE_SECRETS_DIR", str(secrets_root))
    secrets_base = resolve_secrets_base_dir(artifact_root)
    assert secrets_base == secrets_root.resolve()
    assert not secrets_base.is_relative_to(artifact_root.resolve())
    settings = LiveSettings(
        target_file=TARGET_FILE,
        cli_executable=pathlib.Path(sys.executable),
        resolve_cli=False,
        upstream_dir=tmp_path / "upstream",
        artifact_dir=artifact_root,
        suite_profile="smoke",
        existing_url=None,
        keep_env=False,
        ready_timeout_seconds=120.0,
    )
    run = create_live_test_run(load_compatibility_target(TARGET_FILE), settings, run_id="abc123")
    assert run.secrets_dir == secrets_root.resolve() / "abc123"
    assert not run.secrets_dir.is_relative_to(artifact_root.resolve())


def test_rejects_secrets_dir_under_artifact_root(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    monkeypatch.setenv("MULTICA_LIVE_SECRETS_DIR", str(artifact_root / ".live-secrets"))
    with pytest.raises(LiveSetupError, match="outside MULTICA_LIVE_ARTIFACT_DIR"):
        resolve_secrets_base_dir(artifact_root)
