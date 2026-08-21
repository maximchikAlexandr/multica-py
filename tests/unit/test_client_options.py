from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from multica_py import ClientConfig, MulticaClient, OperationOptions
from multica_py.config import _apply_operation_options
from multica_py.sentinels import Unset


@dataclass(frozen=True)
class OperationOptionOverlayCase:
    case_id: str
    field_name: str
    options: OperationOptions
    expected: object


@dataclass(frozen=True)
class InvalidOptionCase:
    case_id: str
    factory: Callable[[], OperationOptions]
    error: type[Exception]
    message: str


_OPTION_OVERLAY_CASES = (
    OperationOptionOverlayCase("profile", "profile", OperationOptions(profile="scoped"), "scoped"),
    OperationOptionOverlayCase(
        "workspace_id", "workspace_id", OperationOptions(workspace_id="scoped-ws"), "scoped-ws"
    ),
    OperationOptionOverlayCase(
        "timeout", "timeout", OperationOptions(timeout=2), datetime.timedelta(seconds=2)
    ),
    OperationOptionOverlayCase("cwd", "cwd", OperationOptions(cwd=Path("scoped")), "scoped"),
    OperationOptionOverlayCase(
        "environment",
        "environment",
        OperationOptions(environment={"SCOPED": "1"}),
        (("SCOPED", "1"),),
    ),
)

_INVALID_OPTION_CASES = (
    InvalidOptionCase(
        "blank_profile", lambda: OperationOptions(profile=" "), ValueError, "profile"
    ),
    InvalidOptionCase(
        "blank_workspace_id", lambda: OperationOptions(workspace_id=" "), ValueError, "workspace_id"
    ),
    InvalidOptionCase(
        "negative_timeout", lambda: OperationOptions(timeout=-1), ValueError, "timeout"
    ),
    InvalidOptionCase(
        "invalid_cwd",
        lambda: OperationOptions(cwd=1),  # type: ignore[arg-type]
        TypeError,
        "cwd",
    ),
    InvalidOptionCase(
        "invalid_environment",
        lambda: OperationOptions(environment=(("A", 1),)),  # type: ignore[arg-type]
        TypeError,
        "environment",
    ),
)


def _base_option_config() -> ClientConfig:
    return ClientConfig(
        executable="custom-multica",
        server_url="https://api.example.test",
        profile="base",
        workspace_id="base-ws",
        cwd=Path("base"),
        environment=(("BASE", "1"),),
        timeout=datetime.timedelta(seconds=10),
        debug=True,
    )


@pytest.mark.parametrize("case", _OPTION_OVERLAY_CASES, ids=lambda case: case.case_id)
def test_operation_options_overlay_covers_metadata_fields(
    case: OperationOptionOverlayCase,
) -> None:
    base = _base_option_config()
    snapshot = _apply_operation_options(base, case.options)

    assert snapshot is not base
    assert getattr(snapshot, case.field_name) == case.expected
    for other_case in _OPTION_OVERLAY_CASES:
        if other_case.field_name != case.field_name:
            assert getattr(snapshot, other_case.field_name) == getattr(base, other_case.field_name)


def test_operation_options_unset_is_inheritance_and_always_snapshots() -> None:
    base = _base_option_config()

    snapshot = _apply_operation_options(base, OperationOptions())

    assert snapshot == base
    assert snapshot is not base


def test_operation_options_none_and_empty_environment_clear_values() -> None:
    base = _base_option_config()

    snapshot = _apply_operation_options(
        base,
        OperationOptions(
            profile=None,
            workspace_id=None,
            timeout=None,
            cwd=None,
            environment=(),
        ),
    )

    assert snapshot.profile is None
    assert snapshot.workspace_id is None
    assert snapshot.timeout is None
    assert snapshot.cwd is None
    assert snapshot.environment == ()
    assert snapshot.executable == base.executable
    assert snapshot.debug is base.debug


@pytest.mark.parametrize("case", _INVALID_OPTION_CASES, ids=lambda case: case.case_id)
def test_operation_options_reject_invalid_values(case: InvalidOptionCase) -> None:
    with pytest.raises(case.error, match=case.message):
        case.factory()


def test_operation_options_are_frozen_and_normalize_values() -> None:
    options = OperationOptions(
        profile="automation",
        workspace_id="ws_1",
        timeout=30,
        cwd="./repo",
        environment={"B": "2", "A": "1"},
    )

    assert options.profile == "automation"
    assert options.workspace_id == "ws_1"
    assert options.timeout == datetime.timedelta(seconds=30)
    assert options.cwd == "./repo"
    assert options.environment == (("B", "2"), ("A", "1"))
    assert OperationOptions().profile is Unset
    with pytest.raises(AttributeError):
        options.profile = "other"  # type: ignore[misc]


@pytest.mark.parametrize("timeout", [-1, float("nan"), float("inf")])
def test_operation_options_reject_invalid_timeouts(timeout: float) -> None:
    with pytest.raises(ValueError, match="finite and nonnegative"):
        OperationOptions(timeout=timeout)


def test_operation_options_reject_blank_identifiers() -> None:
    with pytest.raises(ValueError, match="nonblank"):
        OperationOptions(profile="   ")
    with pytest.raises(ValueError, match="nonblank"):
        OperationOptions(workspace_id="   ")


def test_client_config_keeps_app_settings_independent_from_api_settings() -> None:
    config = ClientConfig(
        server_url="https://api.example.test/",
        app_url="https://multica.ai/",
        workspace_slug="team",
    )

    assert config.server_url == "https://api.example.test/"
    assert config.app_url == "https://multica.ai"
    assert config.workspace_slug == "team"

    with pytest.raises(ValueError, match="app_url must not contain query"):
        ClientConfig(app_url="https://multica.ai/?token=secret")
    with pytest.raises(ValueError, match="workspace_slug"):
        ClientConfig(workspace_slug="team/child")


def test_client_default_matches_explicit_default_and_preserves_explicit_config() -> None:
    explicit = ClientConfig()
    with MulticaClient() as default_client, MulticaClient(explicit) as explicit_client:
        assert default_client.config == explicit
        assert explicit_client.config is explicit


def test_with_options_is_isolated_and_shares_only_semaphore() -> None:
    base = MulticaClient(
        ClientConfig(
            profile="base",
            workspace_id="base-ws",
            timeout=datetime.timedelta(seconds=5),
            cwd=Path("base"),
            environment=(("BASE", "1"),),
        )
    )
    try:
        scoped = base.with_options(
            profile="automation",
            workspace_id="ws_1",
            timeout=30,
            cwd="./repo",
            environment={"A": "1"},
        )
        try:
            assert base.config == ClientConfig(
                profile="base",
                workspace_id="base-ws",
                timeout=datetime.timedelta(seconds=5),
                cwd=Path("base"),
                environment=(("BASE", "1"),),
            )
            assert scoped.config == ClientConfig(
                profile="automation",
                workspace_id="ws_1",
                timeout=datetime.timedelta(seconds=30),
                cwd="./repo",
                environment=(("A", "1"),),
            )
            assert scoped._semaphore is base._semaphore
            assert scoped._transport is not base._transport
            assert scoped.issues is not base.issues
        finally:
            scoped._transport.close()
    finally:
        base._transport.close()


def test_with_environment_replaces_and_can_clear_environment() -> None:
    base = MulticaClient(ClientConfig(environment=(("BASE", "1"),)))
    try:
        replacement = base.with_environment({"A": "1"})
        cleared = base.with_environment(())
        try:
            assert replacement.config.environment == (("A", "1"),)
            assert cleared.config.environment == ()
        finally:
            replacement._transport.close()
            cleared._transport.close()
    finally:
        base._transport.close()


@pytest.mark.parametrize(
    ("helper", "argument", "expected"),
    [
        ("with_profile", "automation", {"profile": "automation"}),
        ("with_workspace", "ws_1", {"workspace_id": "ws_1"}),
        ("with_timeout", 30, {"timeout": 30}),
        ("with_cwd", "repo", {"cwd": "repo"}),
        ("with_environment", {"A": "1"}, {"environment": {"A": "1"}}),
    ],
)
def test_single_option_helpers_delegate_to_with_options(
    helper: str,
    argument: object,
    expected: dict[str, object],
) -> None:
    client = MulticaClient()
    try:
        with patch.object(client, "with_options", return_value="view") as with_options:
            assert getattr(client, helper)(argument) == "view"
        with_options.assert_called_once_with(**expected)
    finally:
        client._transport.close()
