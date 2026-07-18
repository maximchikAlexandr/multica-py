from __future__ import annotations

import pathlib
from unittest.mock import patch

import pytest

from tests.live.compose import (
    ComposeLifecycle,
    ReadinessResult,
    compose_down_argv,
    compose_up_argv,
    is_ready,
    probe_readiness,
)
from tests.live.diagnostics import DiagnosticCollector
from tests.live.exceptions import LiveSetupError
from tests.live.settings import CompatibilityTarget, LiveSettings, LiveTestRun, create_live_test_run


def _target() -> CompatibilityTarget:
    return CompatibilityTarget(
        name="supported-v0.3.35",
        upstream_ref="v0.3.35",
        upstream_commit="4416313f8f7f801df8b7f5072087da8a6502a89c",
        compose_file="docker-compose.selfhost.yml",
        backend_image="ghcr.io/multica-ai/multica-backend",
        backend_tag="v0.3.35",
        backend_digest="sha256:656dd76e866f636863a6fc034f04165227e35f427e526914ea2c9848f8f55e30",
        backend_digest_linux_amd64="sha256:d8a50acac1eb674093b0e9de4afc656328ac6b37fc641f1fb4b256547f1ffe3b",
        cli_source="release",
        cli_version_expected="0.3.35",
        cli_release_sha256_linux_amd64="5bb3472eab5be4cb17a8459d7b2b1ca9bda325432f7f23966d1e81164e9e6167",
        cli_release_sha256_darwin_arm64="4ffdb1f5d9cb3f27b5ba4979ef2de6b98caaf9e7f7d7fa02113e225f2a974b23",
        cli_release_sha256_darwin_amd64="6c81ae111bbcdfd4c10227c6954bfdba87f0177c8149906c8484e4a31aa3fcba",
        verified_at="2026-07-18",
    )


def _settings(tmp_path: pathlib.Path) -> LiveSettings:
    return LiveSettings(
        target_file=tmp_path / "target.toml",
        cli_executable=pathlib.Path("/bin/true"),
        resolve_cli=False,
        upstream_dir=tmp_path / "upstream",
        artifact_dir=tmp_path / "artifacts",
        suite_profile="smoke",
        existing_url=None,
        keep_env=False,
        ready_timeout_seconds=120.0,
    )


def test_compose_up_argv_uses_list_form_without_shell(tmp_path: pathlib.Path) -> None:
    settings = _settings(tmp_path)
    run = create_live_test_run(_target(), settings, run_id="abc")
    lifecycle = ComposeLifecycle(settings, _target(), run, DiagnosticCollector(run.artifact_dir, run.run_id))
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    compose_file = upstream / "docker-compose.selfhost.yml"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    lifecycle._compose_file = compose_file
    secrets = lifecycle.generate_compose_secrets()
    env_file = lifecycle.write_env_file(secrets)
    argv = compose_up_argv((compose_file,), run.compose_project, env_file)
    assert argv[0:2] == ["docker", "compose"]
    assert "--env-file" in argv
    env_index = argv.index("--env-file") + 1
    env_path = pathlib.Path(argv[env_index])
    assert env_path == run.secrets_dir / "compose.env"
    assert not env_path.is_relative_to(settings.artifact_dir)
    host_port = lifecycle.server_url.rsplit(":", 1)[-1]
    assert secrets["BACKEND_PORT"] == host_port
    assert secrets["APP_URL"] == f"http://127.0.0.1:{host_port}"
    assert f"BACKEND_PORT={host_port}" in env_path.read_text(encoding="utf-8")
    assert argv[-2:] == ["postgres", "backend"]
    assert ";" not in " ".join(argv)
    assert "|" not in " ".join(argv)


def test_compose_down_argv_includes_volume_removal(tmp_path: pathlib.Path) -> None:
    settings = _settings(tmp_path)
    run = create_live_test_run(_target(), settings, run_id="abc")
    compose_file = tmp_path / "docker-compose.selfhost.yml"
    argv = compose_down_argv((compose_file,), run.compose_project)
    assert argv[-3:] == ["down", "-v", "--remove-orphans"]


def test_is_ready_requires_exact_json_checks() -> None:
    assert is_ready(
        ReadinessResult(
            status_code=200,
            json_body={"status": "ok", "checks": {"db": "ok", "migrations": "ok"}},
            body_excerpt="",
        )
    )
    assert not is_ready(
        ReadinessResult(
            status_code=200,
            json_body={"status": "ok", "checks": {"db": "ok", "migrations": "pending"}},
            body_excerpt="",
        )
    )


def test_wait_ready_respects_timeout(tmp_path: pathlib.Path) -> None:
    settings = _settings(tmp_path)
    settings = LiveSettings(
        target_file=settings.target_file,
        cli_executable=settings.cli_executable,
        resolve_cli=settings.resolve_cli,
        upstream_dir=settings.upstream_dir,
        artifact_dir=settings.artifact_dir,
        suite_profile=settings.suite_profile,
        existing_url="http://127.0.0.1:8080",
        keep_env=settings.keep_env,
        ready_timeout_seconds=10.0,
    )
    run = create_live_test_run(_target(), settings, run_id="abc")
    lifecycle = ComposeLifecycle(settings, _target(), run, DiagnosticCollector(run.artifact_dir, run.run_id))
    with (
        patch("tests.live.compose.probe_readiness", return_value=ReadinessResult(503, None, "not ready")),
        patch("tests.live.compose.time.sleep", return_value=None),
        pytest.raises(LiveSetupError, match="backend not ready"),
    ):
        lifecycle.wait_ready()


def test_teardown_skips_when_not_started(tmp_path: pathlib.Path) -> None:
    settings = _settings(tmp_path)
    run = create_live_test_run(_target(), settings, run_id="abc")
    lifecycle = ComposeLifecycle(settings, _target(), run, DiagnosticCollector(run.artifact_dir, run.run_id))
    with patch("tests.live.compose.subprocess.run") as run_mock:
        lifecycle.teardown()
        run_mock.assert_not_called()
