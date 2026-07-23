from __future__ import annotations

import json
import pathlib
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass

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
from tests.live._live_helpers import WorkspaceContext, label_name
from tests.live.backend import (
    capture_compose_diagnostics,
    compose_argv,
    is_ready,
    probe_readiness,
)
from tests.live.diagnostics import (
    VERIFICATION_CODE,
    assert_text_excludes_secrets,
)
from tests.live.session import LiveCase, LiveEnvironment, LiveSession

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]

CANONICAL_ARTIFACTS = (
    "target.json",
    "run.json",
    "failure.json",
    "cleanup.json",
    "compose-ps.txt",
    "backend.log",
    "postgres.log",
)

INVALID_PAT_TOKEN = "mpy-live-invalid-pat-token"
MISSING_RESOURCE_ID = "00000000-0000-0000-0000-000000000000"


@dataclass(frozen=True)
class ErrorMappingCase:
    """One client operation to expected exception mapping.

    Attributes:
        client: The MulticaClient to run the failing operation against.
        operation: The failing SDK call.
        expected_exc: Expected public exception type.
        id: pytest.param id.
    """

    client: MulticaClient
    operation: Callable[[MulticaClient], object]
    expected_exc: type[Exception]
    id: str


def _build_invalid_pat_client(
    live_environment: LiveEnvironment,
    primary_workspace: WorkspaceContext,
) -> MulticaClient:
    from tests.live._live_helpers import write_cli_profile

    invalid_profile = f"invalid-{live_environment.run_id}"
    write_cli_profile(
        live_environment.home_dir,
        invalid_profile,
        server_url=live_environment.server_url,
        app_url=live_environment.server_url,
        workspace_id=primary_workspace.id,
        token=INVALID_PAT_TOKEN,
    )
    return MulticaClient(
        ClientConfig(
            executable=str(live_environment.cli_executable),
            server_url=live_environment.server_url,
            workspace_id=primary_workspace.id,
            profile=invalid_profile,
            environment=(("HOME", str(live_environment.home_dir)),),
            compatibility=CompatibilityPolicy.ignore,
        )
    )


def _build_closed_port_client(
    live_environment: LiveEnvironment,
    primary_workspace: WorkspaceContext,
) -> MulticaClient:
    from tests.live.backend import allocate_loopback_port

    closed_port_server_url = f"http://127.0.0.1:{allocate_loopback_port()}"
    return MulticaClient(
        ClientConfig(
            executable=str(live_environment.cli_executable),
            server_url=closed_port_server_url,
            workspace_id=primary_workspace.id,
            profile=primary_workspace.profile_name,
            environment=(("HOME", str(live_environment.home_dir)),),
            compatibility=CompatibilityPolicy.ignore,
        )
    )


def _assert_safe_message(exc: BaseException, live_session: LiveSession) -> None:
    text = f"{exc!r}{exc}"
    assert_text_excludes_secrets(text, live_session.identity.pat.reveal())


def _assert_canonical_artifacts_exclude_secrets(live_environment: LiveEnvironment) -> None:
    collector = live_environment.diagnostics
    for filename in CANONICAL_ARTIFACTS:
        path = collector.artifact_dir / filename
        if not path.is_file():
            continue
        collector.assert_no_secret_leak(path.read_text(encoding="utf-8", errors="replace"))


def _capture_compose_logs(live_environment: LiveEnvironment) -> None:
    if not live_environment.managed_compose or not live_environment.compose_files:
        return
    capture_compose_diagnostics(
        compose_files=live_environment.compose_files,
        compose_project=live_environment.compose_project,
        diagnostics=live_environment.diagnostics,
    )


def _stop_compose_service(
    live_environment: LiveEnvironment,
    service: str,
) -> None:
    if not live_environment.compose_files:
        msg = "compose files are unavailable for destructive backend stop"
        raise RuntimeError(msg)
    completed = subprocess.run(
        compose_argv(
            live_environment.compose_files, live_environment.compose_project, "stop", service
        ),
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"docker compose stop failed: {detail}")


def _start_compose_service(
    live_environment: LiveEnvironment,
    service: str,
) -> None:
    if not live_environment.compose_files:
        msg = "compose files are unavailable for backend restart"
        raise RuntimeError(msg)
    completed = subprocess.run(
        compose_argv(
            live_environment.compose_files, live_environment.compose_project, "start", service
        ),
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"docker compose start failed: {detail}")


def _wait_for_backend(live_environment: LiveEnvironment) -> None:
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


def _make_error_cases(
    live_session: LiveSession,
    live_environment: LiveEnvironment,
) -> list[ErrorMappingCase]:
    primary_workspace = live_environment.primary_workspace
    invalid_pat_client = _build_invalid_pat_client(live_environment, primary_workspace)
    closed_port_client = _build_closed_port_client(live_environment, primary_workspace)
    return [
        ErrorMappingCase(
            client=invalid_pat_client,
            operation=lambda c: c.workspaces.list(),
            expected_exc=AuthenticationError,
            id="invalid-pat",
        ),
        ErrorMappingCase(
            client=live_session.client,
            operation=lambda c: c.labels.get("00000000-0000-0000-0000-000000000000"),
            expected_exc=NotFoundError,
            id="missing-resource",
        ),
        ErrorMappingCase(
            client=closed_port_client,
            operation=lambda c: c.workspaces.list(),
            expected_exc=NetworkError,
            id="closed-port",
        ),
    ]


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(case_id, id=case_id)
        for case_id in ("invalid-pat", "missing-resource", "closed-port")
    ],
)
def test_error_mapping(
    case: str,
    live_session: LiveSession,
    live_environment: LiveEnvironment,
) -> None:
    """Parametrized error mapping: each client operation produces the expected exception with safe message."""
    cases_by_id = {c.id: c for c in _make_error_cases(live_session, live_environment)}
    error_case = cases_by_id[case]
    with pytest.raises(error_case.expected_exc) as exc_info:
        error_case.operation(error_case.client)
    _assert_safe_message(exc_info.value, live_session)


def test_invalid_label_color_raises_validation_error(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Invalid field values must map to ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        live_session.client.labels.create(
            label_name(live_case.unique_name, "bad"), color="not-a-color"
        )
    _assert_safe_message(exc_info.value, live_session)


def test_primary_label_via_secondary_client_raises_not_found_error(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Cross-workspace access collapse must map to NotFoundError."""
    label = live_session.client.labels.create(
        label_name(live_case.unique_name, "pri"), color="#336699"
    )
    live_case.defer_cleanup(lambda: live_session.client.labels.delete(label.id))
    with pytest.raises(NotFoundError) as exc_info:
        live_session.client_secondary.labels.get(label.id)
    _assert_safe_message(exc_info.value, live_session)


@pytest.mark.destructive
def test_backend_stop_mid_operation_raises_network_error_without_orphan_cli(
    live_session: LiveSession,
    live_environment: LiveEnvironment,
) -> None:
    """Stopped backend must raise NetworkError on SDK calls and leave no orphan CLI process."""
    before = _count_cli_processes(live_environment.cli_executable)
    try:
        _stop_compose_service(live_environment, "backend")
        with pytest.raises(NetworkError) as exc_info:
            live_session.client.labels.list()
        _assert_safe_message(exc_info.value, live_session)
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
    live_environment: LiveEnvironment,
    tmp_path: pathlib.Path,
    exit_code: int,
    expected_type: type[Exception],
    live_session: LiveSession,
) -> None:
    """Synthetic wrapper executables must map exit codes to public exceptions."""
    primary_workspace = live_environment.primary_workspace
    wrapper = _write_exit_wrapper(tmp_path, exit_code)
    config = ClientConfig(
        executable=str(wrapper),
        server_url=live_environment.server_url,
        workspace_id=primary_workspace.id,
        profile=primary_workspace.profile_name,
        environment=(("HOME", str(live_environment.home_dir)),),
        compatibility=CompatibilityPolicy.ignore,
    )
    client = MulticaClient(config)
    with pytest.raises(expected_type) as exc_info:
        client.workspaces.list()
    assert exc_info.type is expected_type
    _assert_safe_message(exc_info.value, live_session)


def test_diagnostic_bundle_has_no_registered_secret_leaks(
    live_session: LiveSession,
    live_environment: LiveEnvironment,
) -> None:
    """Generated diagnostic artifacts must not contain registered secret values."""
    invalid_pat_client = _build_invalid_pat_client(
        live_environment, live_environment.primary_workspace
    )
    collector = live_environment.diagnostics
    collector.register_secret(VERIFICATION_CODE)
    try:
        invalid_pat_client.workspaces.list()
    except AuthenticationError as exc:
        collector.record_failure(
            stage="test",
            exc_type=exc.__class__.__name__,
            message=str(exc),
            operation="workspaces list",
            exit_code=exc.exit_code,
            resource="workspaces",
        )
    else:
        pytest.fail("expected AuthenticationError for invalid PAT")
    _capture_compose_logs(live_environment)
    _assert_canonical_artifacts_exclude_secrets(live_environment)
    collector.assert_no_secret_leak()
    assert_text_excludes_secrets(
        (collector.artifact_dir / "failure.json").read_text(encoding="utf-8"),
        live_session.identity.pat.reveal(),
    )


def test_diagnostic_bundle_contains_required_metadata(
    live_session: LiveSession,
    live_environment: LiveEnvironment,
) -> None:
    """Diagnostic bundle must include target, stage, resource, operation, exit code, and logs."""
    try:
        live_session.client.labels.get(MISSING_RESOURCE_ID)
    except NotFoundError as exc:
        live_environment.diagnostics.record_failure(
            stage="test",
            exc_type=exc.__class__.__name__,
            message=str(exc),
            operation=" ".join(exc.argv),
            exit_code=exc.exit_code,
            resource="label",
        )
    else:
        pytest.fail("expected NotFoundError for missing label")
    _capture_compose_logs(live_environment)
    target = json.loads(
        (live_environment.diagnostics.artifact_dir / "target.json").read_text(encoding="utf-8")
    )
    failure = json.loads(
        (live_environment.diagnostics.artifact_dir / "failure.json").read_text(encoding="utf-8")
    )
    assert target["upstream_ref"]
    assert failure["stage"] == "test"
    assert failure["resource"] == "label"
    assert failure["operation"]
    assert failure["exit_code"] == 4
    backend_log = (live_environment.diagnostics.artifact_dir / "backend.log").read_text(
        encoding="utf-8"
    )
    postgres_log = (live_environment.diagnostics.artifact_dir / "postgres.log").read_text(
        encoding="utf-8"
    )
    live_environment.diagnostics.assert_no_secret_leak(backend_log)
    live_environment.diagnostics.assert_no_secret_leak(postgres_log)
