from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

_NESTED_RESOURCE_ATTRS: dict[tuple[str, str], str] = {
    ("agents", "skills"): "agent_skills",
    ("issues", "comments"): "issue_comments",
    ("issues", "labels"): "issue_labels",
    ("issues", "metadata"): "issue_metadata",
    ("issues", "subscribers"): "issue_subscribers",
    ("autopilots", "triggers"): "autopilot_triggers",
    ("projects", "resources"): "project_resources",
    ("skills", "files"): "skill_files",
}

_SPAWN_SDK_METHODS: frozenset[str] = frozenset(
    {
        "daemon.start",
        "daemon.logs",
        "maintenance.update",
        "setup.cloud",
        "setup.self_host",
    }
)


def _derive_resource(sdk_method: str) -> tuple[str, str]:
    parts = sdk_method.split(".")
    if len(parts) >= 3:
        key = (parts[0], parts[1])
        nested = _NESTED_RESOURCE_ATTRS.get(key)
        if nested is not None:
            return nested, parts[-1]
    return parts[0], parts[-1]


def _infer_transport(
    sdk_method: str,
    expected_argv: tuple[str, ...],
) -> Literal["run_bytes", "run_text", "spawn"]:
    if sdk_method in _SPAWN_SDK_METHODS:
        return "spawn"
    if len(expected_argv) >= 2 and expected_argv[-2:] == ("--output", "json"):
        return "run_bytes"
    return "run_text"


@dataclass(frozen=True)
class ArgvCase:
    resource_attr: str
    method: str
    args: tuple[object, ...]
    kwargs: Mapping[str, object]
    stdout: bytes
    expected_argv: tuple[str, ...]
    transport_method: Literal["run_bytes", "run_text", "spawn"]
    stdin: bytes | None = None
    timeout: float | None = None
    sdk_method: str = ""
    id: str = ""


def A(
    sdk_method: str,
    expected_argv: tuple[str, ...],
    *,
    stdout: bytes = b"",
    args: tuple[object, ...] = (),
    kwargs: Mapping[str, object] | None = None,
    transport: Literal["run_bytes", "run_text", "spawn"] | None = None,
    resource_attr: str | None = None,
    method: str | None = None,
    id: str = "",
    stdin: bytes | None = None,
    timeout: float | None = None,
) -> ArgvCase:
    derived_resource, derived_method = _derive_resource(sdk_method)
    return ArgvCase(
        resource_attr=resource_attr or derived_resource,
        method=method or derived_method,
        args=args,
        kwargs=kwargs or {},
        stdout=stdout,
        expected_argv=expected_argv,
        transport_method=transport or _infer_transport(sdk_method, expected_argv),
        stdin=stdin,
        timeout=timeout,
        sdk_method=sdk_method,
        id=id,
    )


@dataclass(frozen=True)
class DecodeCase:
    resource_attr: str
    method: str
    check: Callable[[object], None]
    args: tuple[object, ...] = ()
    stdout: bytes = b""
    id: str = ""


def D(
    sdk_method: str,
    stdout: bytes,
    check: Callable[[object], None],
    *,
    args: tuple[object, ...] = (),
    resource_attr: str | None = None,
    method: str | None = None,
    id: str = "",
) -> DecodeCase:
    derived_resource, derived_method = _derive_resource(sdk_method)
    return DecodeCase(
        resource_attr=resource_attr or derived_resource,
        method=method or derived_method,
        args=args,
        stdout=stdout,
        check=check,
        id=id or f"{sdk_method}.decode",
    )
