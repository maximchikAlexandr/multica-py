"""Phase 3 tests: agent/skill/squad/member graph (tasks 4.1-4.6).

Covers 7 relations (R11-R17):
- R11 Agent.skills (unpaged, seed-migration, set invalidation)
- R12 Agent.tasks (unpaged)
- R13 Agent.issues (offset-paged via --assignee-id)
- R14 Skill.files (unpaged, file mutation invalidation)
- R15 Squad.members (unpaged)
- R16 Squad.issues (offset-paged via --assignee-id)
- R17 WorkspaceMember.issues (offset-paged via --assignee-id)

Plus: reject legacy singular agent-skill/skill-file argv (D08, D09).
"""

from __future__ import annotations

import datetime
import inspect
import pathlib
import shlex
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.commands import Command, _Step
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models.agents import AgentSkill, AgentTask
from multica_py.models.issues import IssueListFilter, IssueListPage, IssueSummary
from multica_py.models.relations import LazyCollection, OffsetLazyCollection
from multica_py.models.skills import SkillFile
from multica_py.models.system import SquadMember
from multica_py.resources._base import BaseResource
from multica_py.resources.agent_skills import AgentSkillResource
from multica_py.resources.agents import Agent, AgentResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.skill_files import SkillFileResource
from multica_py.resources.skills import Skill, SkillResource
from multica_py.resources.squad_members import SquadMemberResource
from multica_py.resources.squads import Squad, SquadResource
from multica_py.resources.workspaces import WorkspaceMember

_TODO = IssueStatus("todo")


@dataclass(frozen=True)
class AvatarValidationCase:
    agent_id: str
    path_kind: str


AVATAR_VALIDATION_CASES = (
    AvatarValidationCase("", "file"),
    AvatarValidationCase("ag_1", "missing"),
    AvatarValidationCase("ag_1", "directory"),
)


@dataclass(frozen=True)
class AvatarArgvCase:
    agent_id: str
    filename: str


AVATAR_ARGV_CASES = (AvatarArgvCase("ag_1", "avatar.png"),)


def _make_client(
    skills: tuple[AgentSkill, ...] = (),
    tasks: tuple[AgentTask, ...] = (),
    issues: list[IssueListPage] | None = None,
    files: tuple[SkillFile, ...] = (),
    members: tuple[SquadMember, ...] = (),
) -> MagicMock:
    client = MagicMock()
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = RawCommandResult(
        argv=("skill", "files", "upsert", "sk_1"),
        exit_code=0,
        stdout=b'{"id":"f1","path":"X.md","content":"new"}',
        stderr=b"",
        duration=datetime.timedelta(),
    )
    command_resource = BaseResource(transport, ClientConfig())

    def empty_command(loader: Callable[[], object]) -> Command[object]:
        return command_resource._plan(steps=(), finalize=lambda _results: loader())

    def effect_command(loader: Callable[[], object]) -> Command[object]:
        transport = MagicMock(spec=CliTransport)
        transport.run_text.side_effect = lambda _argv: (
            loader(),
            TextResult("", "", 0),
        )[1]
        resource = BaseResource(transport, ClientConfig())
        return resource._plan(
            steps=(_Step(("squad", "member", "mutation"), "run_text"),),
            finalize=lambda _results: None,
        )

    client.agents.skills.list.return_value = skills
    client.agents.skills.set.return_value = None
    client.agents.tasks.return_value = tasks
    if issues is not None:
        client.issues.list.side_effect = issues
    else:
        client.issues.list.return_value = IssueListPage(
            issues=(), has_more=False, limit=50, offset=0, total=0
        )
    client.skills.files.list.return_value = files
    client.skills.files.upsert.return_value = None
    client.skills.files.delete.return_value = None
    client.squads.members.list.return_value = members
    client.agents.skills.list_command = lambda agent_id: empty_command(
        lambda: client.agents.skills.list(agent_id)
    )
    client.agents.skills.set_command = lambda agent_id, skill_ids: empty_command(
        lambda: client.agents.skills.set(agent_id, skill_ids)
    )
    client.agents.tasks_command = lambda agent_id: empty_command(
        lambda: client.agents.tasks(agent_id)
    )

    def issues_command(issue_filter: IssueListFilter) -> Command[object]:
        def decode(_stdout: bytes, command_text: str) -> object:
            words = shlex.split(command_text)
            offset = int(words[words.index("--offset") + 1])
            limit = int(words[words.index("--limit") + 1])
            request = IssueListFilter(
                assignee_id=issue_filter.assignee_id,
                limit=limit,
                offset=offset,
            )
            return client.issues.list(request)

        def run_bytes(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
            return RawCommandResult(
                argv=argv,
                exit_code=0,
                stdout=b"",
                stderr=b"",
                duration=datetime.timedelta(),
            )

        transport = command_resource._transport
        cast("MagicMock", transport.run_bytes).side_effect = run_bytes
        args = (
            "issue",
            "list",
            "--assignee-id",
            issue_filter.assignee_id or "",
            "--limit",
            str(issue_filter.limit),
            "--offset",
            str(issue_filter.offset),
        )
        return command_resource._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: results[0],
        )

    client.issues.list_command = issues_command
    client.skills.files.list_command = lambda skill_id: empty_command(
        lambda: client.skills.files.list(skill_id)
    )
    client.skills.files.upsert_command = lambda skill_id, path, content: empty_command(
        lambda: SkillFile(id="f1", path=path, content=content)
    )
    client.skills.files.delete_command = lambda skill_id, file_id: empty_command(
        lambda: client.skills.files.delete(skill_id, file_id)
    )
    client.squads.members.add_command = lambda squad_id, member_id: effect_command(
        lambda: client.squads.members.add(squad_id, member_id)
    )
    client.squads.members.remove_command = lambda squad_id, member_id: effect_command(
        lambda: client.squads.members.remove(squad_id, member_id)
    )
    client.squads.members.list_command = lambda squad_id: empty_command(
        lambda: client.squads.members.list(squad_id)
    )
    return client


def _agent(client: MulticaClient | None = None) -> Agent:
    return Agent(
        id="ag_1",
        name="Agent",
        description="d",
        skill_refs=(),
        archived_at=None,
        _client=client,
    )


def _skill(client: MulticaClient | None = None) -> Skill:
    return Skill(
        id="sk_1",
        name="Skill",
        description="d",
        file_count=0,
        _client=client,
    )


def _squad(client: MulticaClient | None = None) -> Squad:
    return Squad(
        id="sq_1",
        name="Squad",
        member_count=0,
        leader_id=None,
        archived_at=None,
        _client=client,
    )


def _workspace_member(
    client: MulticaClient | None = None,
) -> WorkspaceMember:
    return WorkspaceMember(
        id="wm_1",
        name="Alice",
        role="admin",
        _client=client,
    )


@dataclass(frozen=True)
class AssigneeIssueRelationCase:
    name: str
    entity_factory: Callable[[MagicMock], Agent | Squad | WorkspaceMember]
    assignee_id: str


ASSIGNEE_ISSUE_RELATION_CASES = (
    AssigneeIssueRelationCase("agent", _agent, "ag_1"),
    AssigneeIssueRelationCase("squad", _squad, "sq_1"),
    AssigneeIssueRelationCase("workspace member", _workspace_member, "wm_1"),
)


# ============================================================================
# R11 - Agent.skills
# ============================================================================


def test_agent_skills_loads_once() -> None:
    skills = (AgentSkill(id="s1", name="S1", enabled=True),)
    client = _make_client(skills=skills)
    entity = _agent(client=client)
    items = entity.skills.all()
    assert len(items) == 1
    client.agents.skills.list.assert_called_once_with("ag_1")


def test_agent_skills_is_lazy_collection() -> None:
    entity = _agent(client=_make_client())
    assert isinstance(entity.skills, LazyCollection)


def test_agent_skills_set_invalidates_cache() -> None:
    state = {"calls": 0}

    def loader() -> tuple[AgentSkill, ...]:
        state["calls"] += 1
        return (AgentSkill(id=f"sk{state['calls']}", name="S", enabled=True),)

    entity = _agent(client=_make_client())
    entity._set_runtime("_skills", cast("LazyCollection[AgentSkill]", LazyCollection(loader)))
    entity.skills.all()
    assert state["calls"] == 1
    entity.set_skills(("new_skill",))
    entity.skills.all()
    assert state["calls"] == 2


def test_agent_skills_detached_raises() -> None:
    entity = _agent(client=None)
    with pytest.raises(DetachedEntityError):
        entity.skills.all()


# ============================================================================
# R12 - Agent.tasks
# ============================================================================


def test_agent_tasks_loads_once() -> None:
    tasks = (AgentTask(id="t1", status="todo", issue_id="i1", started_at=None, completed_at=None),)
    client = _make_client(tasks=tasks)
    entity = _agent(client=client)
    items = entity.tasks.all()
    assert len(items) == 1
    client.agents.tasks.assert_called_once_with("ag_1")


def test_agent_tasks_cached_after_all() -> None:
    client = _make_client()
    entity = _agent(client=client)
    entity.tasks.all()
    entity.tasks.all()
    assert client.agents.tasks.call_count == 1


# ============================================================================
# R13 - Agent.issues
# ============================================================================


@pytest.mark.parametrize("case", ASSIGNEE_ISSUE_RELATION_CASES, ids=lambda case: case.name)
def test_assignee_issue_relations_paginate_offset(case: AssigneeIssueRelationCase) -> None:
    p1 = IssueListPage(
        issues=(IssueSummary(id="i1", title="t1", status=_TODO),),
        has_more=True,
        limit=1,
        offset=0,
        total=2,
    )
    p2 = IssueListPage(
        issues=(IssueSummary(id="i2", title="t2", status=_TODO),),
        has_more=False,
        limit=1,
        offset=1,
        total=2,
    )
    client = _make_client(issues=[p1, p2])
    entity = case.entity_factory(client)
    items = entity.issues.all()
    assert len(items) == 2
    assert client.issues.list.call_count == 2
    assert all(isinstance(item, IssueSummary) for item in items)
    flt = client.issues.list.call_args_list[0][0][0]
    assert flt.assignee_id == case.assignee_id
    assert flt.limit == 50
    assert flt.offset == 0
    second_filter = client.issues.list.call_args_list[1][0][0]
    assert second_filter.assignee_id == case.assignee_id
    assert second_filter.limit == 50
    assert second_filter.offset == 1
    client.issues.get.assert_not_called()


def test_agent_issues_single_page() -> None:
    p = IssueListPage(
        issues=(IssueSummary(id="i1", title="t1", status=_TODO),),
        has_more=False,
        limit=50,
        offset=0,
        total=1,
    )
    client = _make_client(issues=[p, p])
    entity = _agent(client=client)
    items = entity.issues.all()
    assert len(items) == 1
    assert isinstance(items[0], IssueSummary)
    client.issues.get.assert_not_called()
    entity.issues.refresh()
    assert client.issues.list.call_count == 2
    client.issues.get.assert_not_called()


def test_agent_issues_is_offset_lazy() -> None:
    entity = _agent(client=_make_client())
    assert isinstance(entity.issues, OffsetLazyCollection)


def test_agent_relation_commands_use_public_resource_plans(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    agents = AgentResource(mock_transport, ClientConfig())
    issues = IssueResource(mock_transport, ClientConfig())
    agents._set_client(client)
    issues._set_client(client)
    client.agents = agents
    client.issues = issues
    entity = _agent(client=client)

    commands = (
        entity.skills.all_command(),
        entity.tasks.all_command(),
        entity.issues.page_command(limit=50, offset=0),
    )
    all_issues = entity.issues.all_command()

    assert tuple(command.commands[0] for command in commands) == (
        "multica agent skills list ag_1 --output json",
        "multica agent tasks ag_1 --output json",
        "multica issue list --assignee-id ag_1 --limit 50 --offset 0 --output json",
    )
    assert all_issues.commands == (
        "multica issue list --assignee-id ag_1 --limit 50 --offset 0 --output json",
        "multica issue list --assignee-id ag_1 --limit 50 --offset '${page.next_offset}' --output json",
    )
    mock_transport.run_bytes.assert_not_called()


# ============================================================================
# R14 - Skill.files
# ============================================================================


def test_skill_files_loads_once() -> None:
    files = (SkillFile(id="f1", path="SKILL.md", content=None),)
    client = _make_client(files=files)
    entity = _skill(client=client)
    items = entity.files.all()
    assert len(items) == 1
    client.skills.files.list.assert_called_once_with("sk_1")


def test_skill_files_relation_command_delegates_to_skill_file_resource() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    client.skills.files = SkillFileResource(transport, ClientConfig())
    entity = _skill(client=client)

    command = entity.files.all_command()

    assert command.commands == ("multica skill files list sk_1 --output json",)


def test_skill_files_upsert_invalidates_cache() -> None:
    state = {"calls": 0}

    def loader() -> tuple[SkillFile, ...]:
        state["calls"] += 1
        return (SkillFile(id=f"f{state['calls']}", path="X.md", content=None),)

    entity = _skill(client=_make_client())
    entity._set_runtime("_files", cast("LazyCollection[SkillFile]", LazyCollection(loader)))
    entity.files.all()
    assert state["calls"] == 1
    entity.upsert_file("X.md", "new")
    entity.files.all()
    assert state["calls"] == 2


def test_skill_files_delete_invalidates_cache() -> None:
    state = {"calls": 0}

    def loader() -> tuple[SkillFile, ...]:
        state["calls"] += 1
        return ()

    entity = _skill(client=_make_client())
    entity._set_runtime("_files", cast("LazyCollection[SkillFile]", LazyCollection(loader)))
    entity.files.all()
    entity.delete_file("f1")
    entity.files.all()
    assert state["calls"] == 2


def test_skill_file_commands_invalidate_only_after_success() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = RawCommandResult(
        (
            "skill",
            "files",
            "upsert",
            "sk_1",
            "--path",
            "X.md",
            "--content",
            "new",
            "--output",
            "json",
        ),
        0,
        b'{"id":"f_1","path":"X.md","content":"new"}',
        b"",
        datetime.timedelta(),
    )
    transport.run_text.return_value = TextResult("", "", 0)
    client.skills.files._transport = transport
    entity = _skill(client=client)
    entity._set_runtime(
        "_files", LazyCollection(lambda: (SkillFile(id="f_0", path="X.md", content="old"),))
    )
    assert entity.files.all()[0].id == "f_0"

    upsert = entity.upsert_file_command("X.md", "new")
    assert upsert.commands == (
        "multica skill files upsert sk_1 --path X.md --content new --output json",
    )
    assert transport.run_bytes.call_count == 0
    assert entity.files.loaded
    assert upsert.run().id == "f_1"

    entity.files.all()
    transport.run_text.side_effect = RuntimeError("transport failure")
    delete = entity.delete_file_command("f_1")
    assert delete.commands == ("multica skill files delete sk_1 f_1",)
    with pytest.raises(RuntimeError, match="transport failure"):
        delete.run()
    assert entity.files.loaded

    transport.run_text.side_effect = None
    delete.run()
    assert not entity.files.loaded


# ============================================================================
# R15 - Squad.members
# ============================================================================


def test_squad_command_forms_and_relation_previews_preserve_argv() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.side_effect = (
        RawCommandResult(
            stdout=b'[{"id":"sq_1","name":"Squad"}]',
            stderr=b"",
            exit_code=0,
            argv=("squad", "list", "--output", "json"),
            duration=datetime.timedelta(),
        ),
        RawCommandResult(
            stdout=b'{"id":"sq_1","name":"Squad"}',
            stderr=b"",
            exit_code=0,
            argv=("squad", "get", "sq_1", "--output", "json"),
            duration=datetime.timedelta(),
        ),
        RawCommandResult(
            stdout=b'[{"member_id":"m1","member_type":"agent","role":"dev"}]',
            stderr=b"",
            exit_code=0,
            argv=("squad", "member", "list", "sq_1", "--output", "json"),
            duration=datetime.timedelta(),
        ),
        RawCommandResult(
            stdout=b'{"issues":[{"id":"i1","title":"Issue","status":"todo"}],"total":1}',
            stderr=b"",
            exit_code=0,
            argv=(
                "issue",
                "list",
                "--assignee-id",
                "sq_1",
                "--limit",
                "10",
                "--offset",
                "20",
                "--output",
                "json",
            ),
            duration=datetime.timedelta(),
        ),
    )
    client.squads._transport = transport
    client.squads.members._transport = transport
    client.issues._transport = transport

    list_command = client.squads.list_command()
    get_command = client.squads.get_command("sq_1")
    entity = _squad(client=client)
    members_command = entity.members.all_command()
    issues_page_command = entity.issues.page_command(limit=10, offset=20)

    assert transport.run_bytes.call_count == 0
    assert list_command.commands == ("multica squad list --output json",)
    assert get_command.commands == ("multica squad get sq_1 --output json",)
    assert members_command.commands == ("multica squad member list sq_1 --output json",)
    assert issues_page_command.commands == (
        "multica issue list --assignee-id sq_1 --limit 10 --offset 20 --output json",
    )
    assert len(list_command.run()) == 1
    assert get_command.run().id == "sq_1"
    assert members_command.run()[0].member_id == "m1"
    assert issues_page_command.run().items[0].id == "i1"


def test_squad_issue_all_command_previews_next_page_and_runs_exact_offset() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.side_effect = (
        RawCommandResult(
            stdout=b'{"issues":[{"id":"i1","title":"One","status":"todo"}],"has_more":true,"limit":50,"offset":0,"total":2}',
            stderr=b"",
            exit_code=0,
            argv=(),
            duration=datetime.timedelta(),
        ),
        RawCommandResult(
            stdout=b'{"issues":[{"id":"i2","title":"Two","status":"todo"}],"has_more":false,"limit":50,"offset":1,"total":2}',
            stderr=b"",
            exit_code=0,
            argv=(),
            duration=datetime.timedelta(),
        ),
    )
    client.squads._transport = transport
    client.squads.members._transport = transport
    client.issues._transport = transport
    command = _squad(client=client).issues.all_command()

    assert command.commands == (
        "multica issue list --assignee-id sq_1 --limit 50 --offset 0 --output json",
        "multica issue list --assignee-id sq_1 --limit 50 --offset '${page.next_offset}' --output json",
    )
    assert transport.run_bytes.call_count == 0
    assert [issue.id for issue in command.run()] == ["i1", "i2"]
    assert transport.run_bytes.call_args_list[1].args[0] == (
        "issue",
        "list",
        "--assignee-id",
        "sq_1",
        "--limit",
        "50",
        "--offset",
        "1",
        "--output",
        "json",
    )


def test_squad_member_commands_invalidate_only_after_success() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = RawCommandResult(
        stdout=b'[{"member_id":"m1","member_type":"agent","role":"dev"}]',
        stderr=b"",
        exit_code=0,
        argv=("squad", "member", "list", "sq_1", "--output", "json"),
        duration=datetime.timedelta(),
    )
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_text.return_value = TextResult("", "", 0)
    client.squads._transport = transport
    client.squads.members._transport = transport
    entity = _squad(client=client)
    relation = entity.members
    entity.members.all()

    add = entity.add_member_command("m2")
    assert add.commands == ("multica squad member add sq_1 m2",)
    assert relation.loaded
    add.run()
    if relation.loaded:
        pytest.fail("members relation stayed loaded after successful mutation")


def test_squad_remove_command_failure_keeps_members_cache() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = RawCommandResult(
        stdout=b'[{"member_id":"m1","member_type":"agent","role":"dev"}]',
        stderr=b"",
        exit_code=0,
        argv=("squad", "member", "list", "sq_1", "--output", "json"),
        duration=datetime.timedelta(),
    )
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_text.side_effect = RuntimeError("transport failed")
    client.squads._transport = transport
    client.squads.members._transport = transport
    entity = _squad(client=client)
    relation = entity.members
    relation.all()

    failed = entity.remove_member_command("m1")
    with pytest.raises(RuntimeError, match="transport failed"):
        failed.run()
    assert relation.loaded


def test_squad_members_loads_once() -> None:
    members = (SquadMember(member_id="m1", member_type="agent", role="dev"),)
    client = _make_client(members=members)
    entity = _squad(client=client)
    items = entity.members.all()
    assert len(items) == 1
    client.squads.members.list.assert_called_once_with("sq_1")


def test_squad_members_cached_after_all() -> None:
    client = _make_client()
    entity = _squad(client=client)
    entity.members.all()
    entity.members.all()
    assert client.squads.members.list.call_count == 1


@dataclass(frozen=True)
class SquadParentMutationCase:
    name: str
    method: str
    member_id: str
    succeeds: bool


SQUAD_PARENT_MUTATION_CASES = (
    SquadParentMutationCase("add succeeds", "add_member", "m1", True),
    SquadParentMutationCase("remove succeeds", "remove_member", "m1", True),
    SquadParentMutationCase("add transport failure", "add_member", "m1", False),
    SquadParentMutationCase("remove transport failure", "remove_member", "m1", False),
)


@dataclass(frozen=True)
class SquadParentValidationCase:
    method: str


SQUAD_PARENT_VALIDATION_CASES = (
    SquadParentValidationCase("add_member"),
    SquadParentValidationCase("remove_member"),
)


@pytest.mark.parametrize("case", SQUAD_PARENT_MUTATION_CASES, ids=lambda case: case.name)
def test_squad_parent_mutations_invalidate_only_members(case: SquadParentMutationCase) -> None:
    page = IssueListPage(issues=(), has_more=False, limit=50, offset=0, total=0)
    client = _make_client(
        members=(SquadMember(member_id="m1", member_type="agent", role="dev"),), issues=[page]
    )
    child = getattr(client.squads.members, case.method.removesuffix("_member"))
    if not case.succeeds:
        child.side_effect = RuntimeError("transport failed")
    entity = _squad(client=client)

    cached_members = entity.members.all()
    entity.issues.all()
    if case.succeeds:
        assert getattr(entity, case.method)(case.member_id) is None
        assert entity.members.all() == cached_members
        assert client.squads.members.list.call_count == 2
    else:
        with pytest.raises(RuntimeError, match="transport failed"):
            getattr(entity, case.method)(case.member_id)
        assert entity.members.all() == cached_members
        assert client.squads.members.list.call_count == 1
    assert child.call_args.args == ("sq_1", case.member_id)
    assert client.issues.list.call_count == 1


def test_squad_parent_mutation_does_not_invalidate_another_wrapper() -> None:
    client = _make_client(members=(SquadMember(member_id="m1", member_type="agent", role="dev"),))
    first = _squad(client=client)
    second = _squad(client=client)

    first.members.all()
    second.members.all()
    first.add_member("m1")
    first.members.all()
    second.members.all()

    assert client.squads.members.list.call_count == 3


@pytest.mark.parametrize("case", SQUAD_PARENT_VALIDATION_CASES, ids=lambda case: case.method)
def test_squad_parent_validation_preserves_loaded_members(case: SquadParentValidationCase) -> None:
    client = _make_client(members=(SquadMember(member_id="m1", member_type="agent", role="dev"),))
    entity = _squad(client=client)
    cached_members = entity.members.all()

    with pytest.raises(ValueError):
        getattr(entity, case.method)("")

    assert entity.members.all() == cached_members
    assert client.squads.members.list.call_count == 1
    getattr(client.squads.members, case.method.removesuffix("_member")).assert_not_called()


# ============================================================================
# R16 - Squad.issues
# ============================================================================


def test_squad_issues_uses_assignee_id() -> None:
    p = IssueListPage(
        issues=(IssueSummary(id="i1", title="t1", status=_TODO),),
        has_more=False,
        limit=50,
        offset=0,
        total=1,
    )
    client = _make_client(issues=[p])
    entity = _squad(client=client)
    items = entity.issues.all()
    assert len(items) == 1
    assert isinstance(items[0], IssueSummary)
    flt = client.issues.list.call_args_list[0][0][0]
    assert flt.assignee_id == "sq_1"
    client.issues.get.assert_not_called()


def test_squad_issues_two_pages() -> None:
    p1 = IssueListPage(
        issues=(IssueSummary(id="i1", title="t1", status=_TODO),),
        has_more=True,
        limit=1,
        offset=0,
        total=2,
    )
    p2 = IssueListPage(
        issues=(IssueSummary(id="i2", title="t2", status=_TODO),),
        has_more=False,
        limit=1,
        offset=1,
        total=2,
    )
    client = _make_client(issues=[p1, p2, p1, p2])
    entity = _squad(client=client)
    items = entity.issues.all()
    assert len(items) == 2
    assert client.issues.list.call_count == 2
    assert all(isinstance(item, IssueSummary) for item in items)
    first_filter = client.issues.list.call_args_list[0][0][0]
    second_filter = client.issues.list.call_args_list[1][0][0]
    assert first_filter.assignee_id == "sq_1"
    assert first_filter.limit == 50
    assert first_filter.offset == 0
    assert second_filter.assignee_id == "sq_1"
    assert second_filter.limit == 50
    assert second_filter.offset == 1
    client.issues.get.assert_not_called()
    entity.issues.refresh()
    assert client.issues.list.call_count == 4
    assert client.issues.list.call_args_list[2][0][0].offset == 0
    assert client.issues.list.call_args_list[3][0][0].offset == 1
    client.issues.get.assert_not_called()


# ============================================================================
# R17 - WorkspaceMember.issues
# ============================================================================


def test_workspace_member_issues_uses_assignee_id() -> None:
    p = IssueListPage(
        issues=(IssueSummary(id="i1", title="t1", status=_TODO),),
        has_more=False,
        limit=50,
        offset=0,
        total=1,
    )
    client = _make_client(issues=[p])
    entity = _workspace_member(client=client)
    items = entity.issues.all()
    assert len(items) == 1
    assert isinstance(items[0], IssueSummary)
    flt = client.issues.list.call_args_list[0][0][0]
    assert flt.assignee_id == "wm_1"
    client.issues.get.assert_not_called()


def test_workspace_member_issues_two_pages() -> None:
    p1 = IssueListPage(
        issues=(IssueSummary(id="i1", title="t1", status=_TODO),),
        has_more=True,
        limit=1,
        offset=0,
        total=2,
    )
    p2 = IssueListPage(
        issues=(IssueSummary(id="i2", title="t2", status=_TODO),),
        has_more=False,
        limit=1,
        offset=1,
        total=2,
    )
    client = _make_client(issues=[p1, p2, p1, p2])
    entity = _workspace_member(client=client)
    items = entity.issues.all()
    assert len(items) == 2
    assert client.issues.list.call_count == 2
    assert all(isinstance(item, IssueSummary) for item in items)
    first_filter = client.issues.list.call_args_list[0][0][0]
    second_filter = client.issues.list.call_args_list[1][0][0]
    assert first_filter.assignee_id == "wm_1"
    assert first_filter.limit == 50
    assert first_filter.offset == 0
    assert second_filter.assignee_id == "wm_1"
    assert second_filter.limit == 50
    assert second_filter.offset == 1
    client.issues.get.assert_not_called()
    entity.issues.refresh()
    assert client.issues.list.call_count == 4
    assert client.issues.list.call_args_list[2][0][0].offset == 0
    assert client.issues.list.call_args_list[3][0][0].offset == 1
    client.issues.get.assert_not_called()


def test_workspace_member_detached_raises() -> None:
    entity = _workspace_member(client=None)
    with pytest.raises(DetachedEntityError):
        entity.issues.all()


def test_workspace_member_zero_io_property_access() -> None:
    client = _make_client()
    entity = _workspace_member(client=client)
    _ = entity.issues
    assert client.issues.list.call_count == 0
    client.issues.get.assert_not_called()


# ============================================================================
# Reject legacy singular agent-skill/skill-file argv (D08, D09)
# ============================================================================


@dataclass(frozen=True)
class SkillFileArgvCase:
    method: str
    args: tuple[str, ...]
    expected_argv: tuple[str, ...]
    stdout: bytes | None


SKILL_FILE_ARGV_CASES = (
    SkillFileArgvCase(
        "list",
        ("sk_1",),
        ("skill", "files", "list", "sk_1", "--output", "json"),
        b"[]",
    ),
    SkillFileArgvCase(
        "upsert",
        ("sk_1", "X.md", "content"),
        (
            "skill",
            "files",
            "upsert",
            "sk_1",
            "--path",
            "X.md",
            "--content",
            "content",
            "--output",
            "json",
        ),
        b'{"id":"f_1","path":"X.md","content":"content"}',
    ),
    SkillFileArgvCase(
        "upsert",
        ("sk_1", "EMPTY.md", ""),
        (
            "skill",
            "files",
            "upsert",
            "sk_1",
            "--path",
            "EMPTY.md",
            "--content",
            "",
            "--output",
            "json",
        ),
        b'{"id":"f_2","path":"EMPTY.md","content":""}',
    ),
    SkillFileArgvCase("delete", ("sk_1", "f_1"), ("skill", "files", "delete", "sk_1", "f_1"), None),
)


@dataclass(frozen=True)
class SkillFileValidationCase:
    method: str
    args: tuple[str, ...]


SKILL_FILE_VALIDATION_CASES = (
    SkillFileValidationCase("list", ("",)),
    SkillFileValidationCase("upsert", ("", "X.md", "content")),
    SkillFileValidationCase("upsert", ("sk_1", "", "content")),
    SkillFileValidationCase("delete", ("", "f_1")),
    SkillFileValidationCase("delete", ("sk_1", "")),
)


@pytest.mark.parametrize("case", SKILL_FILE_ARGV_CASES)
def test_skill_files_use_authoritative_argv(case: SkillFileArgvCase) -> None:
    import datetime

    from multica_py._internal.specs import RawCommandResult

    transport = MagicMock()
    if case.stdout is not None:
        transport.run_bytes.return_value = RawCommandResult(
            argv=case.expected_argv,
            exit_code=0,
            stdout=case.stdout,
            stderr=b"",
            duration=datetime.timedelta(),
        )
    resource = SkillFileResource(transport, ClientConfig())

    result = getattr(resource, f"{case.method}_command")(*case.args).run()

    if case.stdout is None:
        assert result is None
        transport.run_text.assert_called_once_with(case.expected_argv)
        transport.run_bytes.assert_not_called()
    else:
        assert transport.run_bytes.call_args.args == (case.expected_argv,)
        assert transport.run_bytes.call_args.kwargs == {"stdin": None, "timeout": None}
        transport.run_text.assert_not_called()


@pytest.mark.parametrize("case", SKILL_FILE_VALIDATION_CASES)
def test_skill_files_reject_blank_identifiers_before_transport(
    case: SkillFileValidationCase,
) -> None:
    transport = MagicMock()
    resource = SkillFileResource(transport, ClientConfig())

    with pytest.raises(ValueError):
        getattr(resource, f"{case.method}_command")(*case.args)

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def test_agent_skills_set_full_argv_uses_plural() -> None:
    transport = MagicMock()
    resource = AgentSkillResource(transport, ClientConfig())
    resource.set_command("ag_1", ("sk_001", "sk_002")).run()
    transport.run_text.assert_called_once_with(
        (
            "agent",
            "skills",
            "set",
            "ag_1",
            "--skill-id",
            "sk_001",
            "--skill-id",
            "sk_002",
        )
    )
    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    "relation_name",
    ["skills", "tasks"],
)
def test_agent_unpaged_relations_lazy_state(relation_name: str) -> None:
    entity = _agent(client=_make_client())
    r1 = getattr(entity, relation_name)
    r2 = getattr(entity, relation_name)
    assert r1 is r2


def test_empty_results_return_empty_tuple() -> None:
    client = _make_client()
    entity = _agent(client=client)
    assert entity.skills.all() == ()
    assert entity.tasks.all() == ()


def test_agent_set_skills_command_invalidates_only_after_success() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_text.return_value = TextResult("", "", 0)
    client.agents.skills._transport = transport
    entity = _agent(client=client)
    entity._set_runtime(
        "_skills", LazyCollection(lambda: (AgentSkill(id="sk_1", name="Skill", enabled=True),))
    )
    assert entity.skills.all()[0].id == "sk_1"

    command = entity.set_skills_command(("sk_2", "sk_3"))
    assert command.commands == ("multica agent skills set ag_1 --skill-id sk_2 --skill-id sk_3",)
    assert transport.run_text.call_count == 0
    assert entity.skills.loaded

    command.run()

    assert transport.run_text.call_count == 1
    assert not entity.skills.loaded


@pytest.mark.parametrize("case", AVATAR_VALIDATION_CASES)
def test_avatar_rejects_invalid_context_before_transport(
    case: AvatarValidationCase, tmp_path: pathlib.Path
) -> None:
    path = tmp_path / "missing.png" if case.path_kind == "missing" else tmp_path / "avatar.png"
    if case.path_kind == "directory":
        path.mkdir()
    elif case.path_kind == "file":
        path.write_bytes(b"image")
    transport = MagicMock(spec=CliTransport)
    resource = AgentResource(transport, ClientConfig())

    with pytest.raises(ValueError):
        resource.avatar_command(case.agent_id, path)

    transport.run_text.assert_not_called()
    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize("case", AVATAR_ARGV_CASES)
def test_avatar_uses_exact_transport(case: AvatarArgvCase, tmp_path: pathlib.Path) -> None:
    file = tmp_path / case.filename
    file.write_bytes(b"image")
    transport = MagicMock(spec=CliTransport)
    resource = AgentResource(transport, ClientConfig())

    resource.avatar_command(case.agent_id, file).run()

    transport.run_text.assert_called_once_with(
        ("agent", "avatar", case.agent_id, "--file", str(file.resolve()))
    )
    transport.run_bytes.assert_not_called()


def test_avatar_public_signature_and_legacy_absence() -> None:
    signature = inspect.signature(AgentResource.avatar, eval_str=True)
    parameters = tuple(signature.parameters.values())[1:]

    assert tuple((item.name, item.kind, item.annotation) for item in parameters) == (
        ("agent_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
        ("file", inspect.Parameter.POSITIONAL_OR_KEYWORD, pathlib.Path),
    )
    assert signature.return_annotation is None
    assert not hasattr(AgentResource, "upload_avatar")
