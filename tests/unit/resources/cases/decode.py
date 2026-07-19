from __future__ import annotations

import msgspec

from multica_py.models.agents import Agent, AgentTask
from multica_py.models.autopilots import Autopilot, AutopilotRun
from multica_py.models.skills import Skill
from multica_py.models.system import (
    AttachmentResult,
    MaintenanceVersion,
    Repository,
    RepositoryCheckoutResult,
    RuntimeDefinition,
    Squad,
    User,
)

from ._payloads import APRUN, AR
from ._types import D, DecodeCase


def _check_agents_list(result: object) -> None:
    assert len(result) == 2  # type: ignore[arg-type]
    assert result[0].id == "a1"  # type: ignore[index]
    assert result[1].name == "Bob"  # type: ignore[index]


def _check_agents_get(result: object) -> None:
    assert result.id == "a1"  # type: ignore[attr-defined]
    assert result.description == "desc"  # type: ignore[attr-defined]


def _check_agents_tasks(result: object) -> None:
    assert len(result) == 1  # type: ignore[arg-type]
    assert result[0].id == "t1"  # type: ignore[index]


def _check_attachments_list(result: object) -> None:
    assert len(result) == 1  # type: ignore[arg-type]
    assert result[0].filename == "x"  # type: ignore[index]


def _check_attachments_upload(result: object) -> None:
    assert result.id == "a1"  # type: ignore[attr-defined]


def _check_autopilots_list(result: object) -> None:
    assert len(result) == 2  # type: ignore[arg-type]
    assert result[0].name == "X"  # type: ignore[index]


def _check_autopilots_get_run(result: object) -> None:
    assert result.id == "r1"  # type: ignore[attr-defined]
    assert result.status == "running"  # type: ignore[attr-defined]


def _check_maintenance_version(result: object) -> None:
    assert result.version == "1.0.0"  # type: ignore[attr-defined]
    assert result.commit == "abc"  # type: ignore[attr-defined]


def _check_repositories_list(result: object) -> None:
    assert len(result) == 2  # type: ignore[arg-type]


def _check_repositories_checkout(result: object) -> None:
    assert result.success is True  # type: ignore[attr-defined]


def _check_runtimes_list(result: object) -> None:
    assert result[0].name == "py3"  # type: ignore[index]


def _check_skills_list(result: object) -> None:
    assert len(result) == 2  # type: ignore[arg-type]
    assert result[0].name == "S1"  # type: ignore[index]


def _check_squads_list(result: object) -> None:
    assert result[0].member_count == 3  # type: ignore[index]


def _check_users_list(result: object) -> None:
    assert len(result) == 2  # type: ignore[arg-type]


DECODE_CASES: tuple[DecodeCase, ...] = (
    D(
        "agents.list",
        msgspec.json.encode([Agent(id="a1", name="Alice"), Agent(id="a2", name="Bob")]),
        _check_agents_list,
    ),
    D(
        "agents.get",
        msgspec.json.encode(Agent(id="a1", name="Alice", description="desc")),
        _check_agents_get,
        args=("a1",),
    ),
    D(
        "agents.tasks",
        msgspec.json.encode([AgentTask(id="t1", status="running", issue_id="i1")]),
        _check_agents_tasks,
        args=("a1",),
    ),
    D(
        "attachments.list",
        msgspec.json.encode([AttachmentResult(id="a1", filename="x")]),
        _check_attachments_list,
        args=("i1",),
    ),
    D("attachments.upload", AR, _check_attachments_upload, args=("i1", "/f")),
    D(
        "autopilots.list",
        msgspec.json.encode([Autopilot(id="a1", name="X"), Autopilot(id="a2", name="Y")]),
        _check_autopilots_list,
    ),
    D("autopilots.get_run", APRUN, _check_autopilots_get_run, args=("r1",)),
    D(
        "maintenance.version",
        msgspec.json.encode(
            MaintenanceVersion(version="1.0.0", commit="abc", build_date="2026-01-01")
        ),
        _check_maintenance_version,
    ),
    D(
        "repositories.list",
        msgspec.json.encode([Repository(id="r1", name="R1"), Repository(id="r2", name="R2")]),
        _check_repositories_list,
    ),
    D(
        "repositories.checkout",
        msgspec.json.encode(RepositoryCheckoutResult(path="/p", branch="main", success=True)),
        _check_repositories_checkout,
        args=("r1", "main"),
    ),
    D(
        "runtimes.list",
        msgspec.json.encode([RuntimeDefinition(id="r1", name="py3")]),
        _check_runtimes_list,
    ),
    D(
        "skills.list",
        msgspec.json.encode([Skill(id="s1", name="S1"), Skill(id="s2", name="S2")]),
        _check_skills_list,
    ),
    D(
        "squads.list",
        msgspec.json.encode([Squad(id="s1", name="S1", member_count=3)]),
        _check_squads_list,
    ),
    D(
        "users.list",
        msgspec.json.encode([User(id="u1", name="Alice"), User(id="u2", name="Bob")]),
        _check_users_list,
    ),
)
