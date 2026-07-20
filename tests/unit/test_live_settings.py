from __future__ import annotations

import os
import pathlib
import re
import sys

import pytest

from tests.live.environment import (
    MAX_LABEL_NAME_LEN,
    LiveSettings,
    LiveSetupError,
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
    assert target.upstream_ref == "v0.3.10"
    assert target.upstream_commit == "be32e5af00c74cda60c2fe8c47d31402bc62b3a6"
    assert target.backend_digest == (
        "sha256:0370ec3dd10d988f9a48c758d326680a24f51bbf4181101d403940136af983c6"
    )
    assert target.backend_digest_linux_amd64 == (
        "sha256:29e78b94fb260daeac9cd6b64b797221a468c17208a2f9161c1d7bd36fd9b077"
    )
    assert target.cli_release_sha256_linux_amd64 == (
        "cbb8cd5dad60a209455d67f5f3c844c4e418209f818c34209f7470f6ff0ebabd"
    )


def test_rejects_latest_in_target(tmp_path: pathlib.Path) -> None:
    manifest = TARGET_FILE.read_text(encoding="utf-8").replace(
        'upstream_ref = "v0.3.10"',
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
    run = create_live_test_run(
        load_compatibility_target(TARGET_FILE),
        settings,
        run_id="abcdef0123456789abcdef0123456789",
    )
    assert run.secrets_dir == secrets_root.resolve() / "abcdef0123456789abcdef0123456789"
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
