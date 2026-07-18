from __future__ import annotations

import json
import pathlib
import subprocess
import time

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import (
    AuthenticationError,
    CommandExecutionError,
    NetworkError,
    NotFoundError,
    ValidationError,
)
from multica_py.models.labels import Label
from tests.live.bootstrap import TestIdentity
from tests.live.compose import (
    capture_compose_diagnostics_from_environment,
    compose_argv,
    is_ready,
    probe_readiness,
)
from tests.live.diagnostics import (
    VERIFICATION_CODE,
    DiagnosticCollector,
    assert_text_excludes_secrets,
)
from tests.live.settings import LiveTestEnvironment, label_name

pytestmark = [pytest.mark.live, pytest.mark.live_smoke]

CANONICAL_ARTIFACTS = (
    "target.json",
    "run.json",
    "failure.json",
    "cleanup.json",
    "compose-ps.txt",
    "backend.log",
    "postgres.log",
)


def _assert_safe_message(exc: BaseException, test_identity: TestIdentity) -> None:
    text = f"{exc!r}{exc}"
    assert_text_excludes_secrets(text, test_identity.pat.reveal())


def _assert_canonical_artifacts_exclude_secrets(collector: DiagnosticCollector) -> None:
    for filename in CANONICAL_ARTIFACTS:
        path = collector.artifact_dir / filename
        if not path.is_file():
            continue
        collector.assert_no_secret_leak(path.read_text(encoding="utf-8", errors="replace"))


def _capture_compose_logs(
    live_environment: LiveTestEnvironment,
    diagnostic_collector: DiagnosticCollector,
) -> None:
    capture_compose_diagnostics_from_environment(live_environment, diagnostic_collector)


def _stop_compose_service(
    live_environment: LiveTestEnvironment,
    service: str,
) -> None:
    if not live_environment.compose_files:
        msg = "compose files are unavailable for destructive backend stop"
        raise RuntimeError(msg)
    completed = subprocess.run(
        compose_argv(live_environment.compose_files, live_environment.compose_project, "stop", service),
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"docker compose stop failed: {detail}")


def _start_compose_service(
    live_environment: LiveTestEnvironment,
    service: str,
) -> None:
    if not live_environment.compose_files:
        msg = "compose files are unavailable for backend restart"
        raise RuntimeError(msg)
    completed = subprocess.run(
        compose_argv(live_environment.compose_files, live_environment.compose_project, "start", service),
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"docker compose start failed: {detail}")


def _wait_for_backend(live_environment: LiveTestEnvironment) -> None:
    deadline = time.monotonic() + live_environment.readiness_timeout_seconds
    while time.monotonic() < deadline:
        result = probe_readiness(live_environment.readiness_endpoint)
        if is_ready(result):
            return
        time.sleep(1.0)
    raise RuntimeError("backend did not become ready after restart")


def _count_cli_processes(cli_executable: pathlib.Path) -> int:
    completed = subprocess.run(
        ["pgrep", "-f", str(cli_executable)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode == 1:
        return 0
    if completed.returncode != 0:
        return 0
    return len([line for line in completed.stdout.splitlines() if line.strip()])


def _write_exit_wrapper(tmp_path: pathlib.Path, exit_code: int) -> pathlib.Path:
    script = tmp_path / f"exit-{exit_code}.sh"
    script.write_text(f"#!/bin/sh\nexit {exit_code}\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | 0o111)
    return script


def test_invalid_pat_raises_authentication_error_with_safe_message(
    invalid_pat_client: MulticaClient,
    test_identity: TestIdentity,
) -> None:
    """Invalid PAT must map to AuthenticationError without leaking credentials."""
    with pytest.raises(AuthenticationError) as exc_info:
        invalid_pat_client.workspaces.list()
    _assert_safe_message(exc_info.value, test_identity)


def test_missing_resource_raises_not_found_error(
    live_client: MulticaClient,
    missing_resource_id: str,
    test_identity: TestIdentity,
) -> None:
    """Missing resource identifiers must map to NotFoundError."""
    with pytest.raises(NotFoundError) as exc_info:
        live_client.labels.get(missing_resource_id)
    _assert_safe_message(exc_info.value, test_identity)


def test_invalid_label_color_raises_validation_error(
    live_client: MulticaClient,
    resource_name: str,
    test_identity: TestIdentity,
    register_resource,
) -> None:
    """Invalid field values must map to ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        live_client.labels.create(label_name(resource_name, "bad"), color="not-a-color")
    _assert_safe_message(exc_info.value, test_identity)


def test_primary_label_via_secondary_client_raises_not_found_error(
    secondary_live_client: MulticaClient,
    primary_workspace_label: Label,
    test_identity: TestIdentity,
) -> None:
    """Cross-workspace access collapse must map to NotFoundError."""
    with pytest.raises(NotFoundError) as exc_info:
        secondary_live_client.labels.get(primary_workspace_label.id)
    _assert_safe_message(exc_info.value, test_identity)


def test_closed_port_raises_network_error(
    closed_port_client: MulticaClient,
    test_identity: TestIdentity,
) -> None:
    """Closed backend ports must map to NetworkError."""
    with pytest.raises(NetworkError) as exc_info:
        closed_port_client.workspaces.list()
    _assert_safe_message(exc_info.value, test_identity)


@pytest.mark.serial
@pytest.mark.destructive
def test_backend_stop_mid_operation_raises_network_error_without_orphan_cli(
    live_client: MulticaClient,
    live_environment: LiveTestEnvironment,
    test_identity: TestIdentity,
) -> None:
    """Stopped backend must raise NetworkError on SDK calls and leave no orphan CLI process."""
    before = _count_cli_processes(live_environment.cli_executable)
    try:
        _stop_compose_service(live_environment, "backend")
        with pytest.raises(NetworkError) as exc_info:
            live_client.labels.list()
        _assert_safe_message(exc_info.value, test_identity)
    finally:
        _start_compose_service(live_environment, "backend")
        _wait_for_backend(live_environment)
    after = _count_cli_processes(live_environment.cli_executable)
    assert after <= before


@pytest.mark.parametrize(
    ("exit_code", "expected_type"),
    [
        (2, NetworkError),
        (99, CommandExecutionError),
    ],
)
def test_synthetic_wrapper_exit_code_mapping(
    live_environment: LiveTestEnvironment,
    primary_workspace,
    tmp_path: pathlib.Path,
    exit_code: int,
    expected_type: type[Exception],
    test_identity: TestIdentity,
) -> None:
    """Synthetic wrapper executables must map exit codes to public exceptions."""
    wrapper = _write_exit_wrapper(tmp_path, exit_code)
    config = ClientConfig(
        executable=str(wrapper),
        server_url=live_environment.server_url,
        workspace_id=primary_workspace.id,
        profile=primary_workspace.profile_name,
        environment={"HOME": str(live_environment.home_dir)},
        compatibility=CompatibilityPolicy.ignore,
    )
    client = MulticaClient(config)
    with pytest.raises(expected_type) as exc_info:
        client.workspaces.list()
    assert exc_info.type is expected_type
    _assert_safe_message(exc_info.value, test_identity)


def test_diagnostic_bundle_has_no_registered_secret_leaks(
    invalid_pat_client: MulticaClient,
    diagnostic_collector: DiagnosticCollector,
    test_identity: TestIdentity,
    live_environment: LiveTestEnvironment,
    assert_no_secret_leak,
) -> None:
    """Generated diagnostic artifacts must not contain registered secret values."""
    diagnostic_collector.register_secret(VERIFICATION_CODE)
    try:
        invalid_pat_client.workspaces.list()
    except AuthenticationError as exc:
        diagnostic_collector.record_failure(
            stage="test",
            exc_type=exc.__class__.__name__,
            message=str(exc),
            operation="workspaces list",
            exit_code=exc.exit_code,
            resource="workspaces",
        )
    else:
        pytest.fail("expected AuthenticationError for invalid PAT")
    _capture_compose_logs(live_environment, diagnostic_collector)
    _assert_canonical_artifacts_exclude_secrets(diagnostic_collector)
    assert_no_secret_leak()
    assert_text_excludes_secrets(
        (diagnostic_collector.artifact_dir / "failure.json").read_text(encoding="utf-8"),
        test_identity.pat.reveal(),
    )


def test_diagnostic_bundle_contains_required_metadata(
    live_client: MulticaClient,
    missing_resource_id: str,
    diagnostic_collector: DiagnosticCollector,
    live_environment: LiveTestEnvironment,
) -> None:
    """Diagnostic bundle must include target, stage, resource, operation, exit code, and logs."""
    try:
        live_client.labels.get(missing_resource_id)
    except NotFoundError as exc:
        diagnostic_collector.record_failure(
            stage="test",
            exc_type=exc.__class__.__name__,
            message=str(exc),
            operation=" ".join(exc.argv),
            exit_code=exc.exit_code,
            resource="label",
        )
    else:
        pytest.fail("expected NotFoundError for missing label")
    _capture_compose_logs(live_environment, diagnostic_collector)
    target = json.loads(
        (diagnostic_collector.artifact_dir / "target.json").read_text(encoding="utf-8")
    )
    failure = json.loads(
        (diagnostic_collector.artifact_dir / "failure.json").read_text(encoding="utf-8")
    )
    assert target["upstream_ref"]
    assert failure["stage"] == "test"
    assert failure["resource"] == "label"
    assert failure["operation"]
    assert failure["exit_code"] == 4
    backend_log = (diagnostic_collector.artifact_dir / "backend.log").read_text(encoding="utf-8")
    postgres_log = (diagnostic_collector.artifact_dir / "postgres.log").read_text(encoding="utf-8")
    diagnostic_collector.assert_no_secret_leak(backend_log)
    diagnostic_collector.assert_no_secret_leak(postgres_log)
