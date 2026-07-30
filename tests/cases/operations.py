from __future__ import annotations

import inspect
import typing
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path as _Path
from typing import cast

from multica_py.resources.agent_skills import AgentSkillResource
from multica_py.resources.agents import AgentResource
from multica_py.resources.attachments import AttachmentResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.autopilot_triggers import AutopilotTriggerResource
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.configuration import ConfigurationResource
from multica_py.resources.daemon import DaemonResource
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issue_subscribers import IssueSubscriberResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.labels import LabelResource
from multica_py.resources.maintenance import MaintenanceResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import ProjectResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.setup import SetupResource
from multica_py.resources.skill_files import SkillFileResource
from multica_py.resources.skills import SkillResource
from multica_py.resources.squad_members import SquadMemberResource
from multica_py.resources.squads import SquadResource
from multica_py.resources.users import UserResource
from multica_py.resources.workspaces import WorkspaceResource
from tools.upstream_contract.contract import validate_contract as _validate_contract


@dataclass(frozen=True)
class OperationCase:
    id: str
    sdk_method: str
    is_canonical: bool
    resource_attr: str
    method: str
    expected_argv: tuple[str, ...] = ()
    transport_method: str = "run_bytes"
    args: tuple[object, ...] = ()
    kwargs: tuple[tuple[str, object], ...] = ()
    stdout: bytes = b""
    stderr: bytes = b""
    exit_code: int = 0
    stdin: bytes | None = None
    timeout: float | None = None
    assert_result: Callable[[object], None] | None = None
    contract_operation_id: str | None = None
    source_ref: str | None = None


RESOURCE_SPECS: tuple[tuple[str, type], ...] = (
    ("agents", AgentResource),
    ("agent_skills", AgentSkillResource),
    ("attachments", AttachmentResource),
    ("auth", AuthResource),
    ("autopilot_triggers", AutopilotTriggerResource),
    ("autopilots", AutopilotResource),
    ("configuration", ConfigurationResource),
    ("daemon", DaemonResource),
    ("issue_comments", IssueCommentResource),
    ("issue_labels", IssueLabelResource),
    ("issue_metadata", IssueMetadataResource),
    ("issue_subscribers", IssueSubscriberResource),
    ("issues", IssueResource),
    ("labels", LabelResource),
    ("maintenance", MaintenanceResource),
    ("project_resources", ProjectResourceCollection),
    ("projects", ProjectResource),
    ("repositories", RepositoryResource),
    ("runtimes", RuntimeResource),
    ("setup", SetupResource),
    ("skill_files", SkillFileResource),
    ("skills", SkillResource),
    ("squads", SquadResource),
    ("squads_members", SquadMemberResource),
    ("users", UserResource),
    ("workspaces", WorkspaceResource),
)

_NESTED_RESOURCE_ATTRS: dict[tuple[str, str], str] = {
    ("agents", "skills"): "agent_skills",
    ("issues", "comments"): "issue_comments",
    ("issues", "labels"): "issue_labels",
    ("issues", "metadata"): "issue_metadata",
    ("issues", "subscribers"): "issue_subscribers",
    ("autopilots", "triggers"): "autopilot_triggers",
    ("projects", "resources"): "project_resources",
    ("skills", "files"): "skill_files",
    ("squads", "members"): "squads_members",
}

_NESTED_DOTTED_PREFIXES: dict[str, str] = {
    resource_attr: f"{parent}.{attribute}"
    for (parent, attribute), resource_attr in _NESTED_RESOURCE_ATTRS.items()
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


def _resource_attr(sdk_method: str) -> str:
    parts = sdk_method.split(".")
    if len(parts) >= 3:
        nested = _NESTED_RESOURCE_ATTRS.get((parts[0], parts[1]))
        if nested is not None:
            return nested
    return parts[0]


def discover_public_methods() -> frozenset[str]:
    methods: set[str] = set()
    for flat_key, cls in RESOURCE_SPECS:
        dotted = _NESTED_DOTTED_PREFIXES.get(flat_key, flat_key)
        for name, value in cls.__dict__.items():
            if name.startswith("_"):
                continue
            function = value.__func__ if isinstance(value, (classmethod, staticmethod)) else value
            if not inspect.isfunction(function):
                continue
            overloads = typing.get_overloads(function)
            if function in overloads:
                continue
            if function.__name__ != name:
                continue
            methods.add(f"{dotted}.{name}")
    return frozenset(methods)


def generated_operation_cases(catalog: object) -> tuple[OperationCase, ...]:
    import datetime
    from base64 import b64decode

    from multica_py.enums import (
        AutopilotExecutionMode,
        IssueSort,
        IssueStatus,
        ProjectStatus,
        SortDirection,
    )
    from multica_py.models.common import Page
    from multica_py.models.issue_activity import (
        CommentCursor,
        CommentListFlatRequest,
        CommentListRecentRequest,
        CommentListThreadRequest,
    )
    from multica_py.models.issues import (
        FileDescription,
        InlineDescription,
        IssueCreateRequest,
        StdinDescription,
    )
    from multica_py.models.project_resources import (
        ProjectResourceAddLocalDirectoryRequest,
        ProjectResourceUpdateLocalDirectoryRequest,
    )
    from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
    from multica_py.sentinels import Unset
    from tools.upstream_contract.contract import ContractCatalog, ResultAssertion

    if not isinstance(catalog, ContractCatalog):
        raise TypeError("generated_operation_cases requires a validated ContractCatalog")

    request_types = {
        "CommentListFlatRequest": CommentListFlatRequest,
        "CommentListThreadRequest": CommentListThreadRequest,
        "CommentListRecentRequest": CommentListRecentRequest,
        "IssueCreateRequest": IssueCreateRequest,
        "ProjectCreateRequest": ProjectCreateRequest,
        "ProjectUpdateRequest": ProjectUpdateRequest,
        "ProjectResourceAddLocalDirectoryRequest": ProjectResourceAddLocalDirectoryRequest,
        "ProjectResourceUpdateLocalDirectoryRequest": ProjectResourceUpdateLocalDirectoryRequest,
    }
    enum_types = {
        "IssueSort": IssueSort,
        "SortDirection": SortDirection,
        "IssueStatus": IssueStatus,
        "ProjectStatus": ProjectStatus,
        "AutopilotExecutionMode": AutopilotExecutionMode,
    }

    def materialize(tagged: dict[str, object]) -> object:
        kind = tagged["kind"]
        if kind == "enum":
            enum_type = enum_types[str(tagged["type"])]
            return enum_type[str(tagged["member"])]
        if kind == "primitive":
            return tagged["value"]
        if kind == "datetime":
            return datetime.datetime.fromisoformat(str(tagged["value"]).replace("Z", "+00:00"))
        if kind == "path":
            return str(tagged["value"])
        if kind == "unset":
            return Unset
        if kind == "inline_description":
            return InlineDescription(text=str(tagged["text"]))
        if kind == "file_description":
            return FileDescription(path=str(tagged["path"]))
        if kind == "stdin_description":
            return StdinDescription()
        if kind == "comment_cursor":
            return CommentCursor(before=str(tagged["before"]), before_id=str(tagged["before_id"]))
        if kind == "list":
            items = cast("list[dict[str, object]]", tagged["items"])
            return tuple(materialize(item) for item in items)
        if kind == "request":
            request_type = request_types[str(tagged["type"])]
            fields = {
                str(name): materialize(value)
                for name, value in cast("list[tuple[str, dict[str, object]]]", tagged["fields"])
            }
            return request_type(**fields)
        raise ValueError(f"unsupported tagged value {kind!r}")

    def assertion_for(assertion: ResultAssertion) -> Callable[[object], None] | None:
        if assertion.kind == "none":
            return _assert_none
        if assertion.kind == "decoded_type":
            expected = str(assertion.expected["value"])

            def assert_type(result: object) -> None:
                actual = f"{type(result).__module__}.{type(result).__qualname__}"
                if actual != expected:
                    raise AssertionError(f"expected {expected}, got {actual}")

            return assert_type
        expected_items = tuple(
            str(item["value"])
            for item in cast("list[dict[str, object]]", assertion.expected["items"])
        )

        def assert_page(result: object) -> None:
            if type(result) is not Page:
                raise AssertionError("expected multica_py.models.common.Page")
            if tuple(item.id for item in result.items) != expected_items:
                raise AssertionError("page item IDs differ from the approved vector")

        return assert_page

    def _assert_none(result: object) -> None:
        if result is not None:
            raise AssertionError(f"expected None, got {result!r}")

    class_by_name = {cls.__name__: (flat_key, cls) for flat_key, cls in RESOURCE_SPECS}
    generated: list[OperationCase] = []
    for vector in catalog.test_vectors:
        operation = next(
            item for item in catalog.operations if item.operation_id == vector.operation_id
        )
        entrypoint = next(
            item for item in operation.entrypoints if item.entrypoint_id == vector.entrypoint_id
        )
        class_name = entrypoint.public_symbol.rsplit(".", 2)[-2]
        flat_key, _ = class_by_name[class_name]
        dotted_prefix = _NESTED_DOTTED_PREFIXES.get(flat_key, flat_key)
        method = entrypoint.public_symbol.rsplit(".", 1)[-1]
        sdk_method = f"{dotted_prefix}.{method}"
        generated.append(
            OperationCase(
                id=vector.vector_id,
                sdk_method=sdk_method,
                is_canonical=":variant:" not in vector.vector_id,
                resource_attr=_resource_attr(sdk_method),
                method=method,
                expected_argv=vector.expected_argv,
                transport_method=vector.transport_method,
                args=tuple(materialize(value) for value in vector.args),
                kwargs=tuple((name, materialize(value)) for name, value in vector.kwargs),
                stdout=b64decode(vector.stdout_base64),
                stderr=vector.stderr.encode("utf-8"),
                exit_code=vector.exit_code,
                stdin=b64decode(vector.stdin_base64) if vector.stdin_base64 is not None else None,
                timeout=vector.timeout,
                assert_result=assertion_for(vector.assertion),
                contract_operation_id=vector.operation_id,
                source_ref=None,
            )
        )
    return tuple(generated)


LEGACY_ARGV_MIGRATION: dict[str, str] = {
    "legacy:001": "manual:agents.list:canonical",
    "legacy:002": "manual:agents.get:canonical",
    "legacy:003": "manual:agents.skills.list:canonical",
    "legacy:004": "manual:agents.create:canonical",
    "legacy:005": "manual:agents.create:variant:01",
    "legacy:006": "manual:agents.create:variant:02",
    "legacy:007": "manual:agents.create:variant:03",
    "legacy:008": "manual:agents.update:canonical",
    "legacy:009": "manual:agents.update:variant:01",
    "legacy:010": "manual:agents.archive:canonical",
    "legacy:011": "manual:agents.restore:canonical",
    "legacy:012": "manual:agents.tasks:canonical",
    "legacy:013": "manual:agents.upload_avatar:canonical",
    "legacy:014": "manual:attachments.list:canonical",
    "legacy:015": "manual:attachments.upload:canonical",
    "legacy:016": "manual:attachments.download:canonical",
    "legacy:017": "generated:autopilots.list:default:canonical",
    "legacy:018": "generated:autopilots.get:default:canonical",
    "legacy:019": "generated:autopilots.create:default:canonical",
    "legacy:020": "generated:autopilots.update:default:canonical",
    "legacy:021": "manual:autopilots.update:variant:01",
    "legacy:022": "manual:autopilots.update:variant:02",
    "legacy:023": "generated:autopilots.delete:default:canonical",
    "legacy:024": "generated:autopilots.run:default:canonical",
    "legacy:025": "generated:autopilots.history:default:canonical",
    "legacy:026": "manual:autopilots.get_run:canonical",
    "legacy:027": "manual:configuration.show:canonical",
    "legacy:028": "manual:configuration.get:canonical",
    "legacy:029": "manual:configuration.set:canonical",
    "legacy:030": "generated:issues.comments.list:direct:canonical",
    "legacy:031": "generated:issues.comments.list:flat:canonical",
    "legacy:032": "generated:issues.comments.list:thread:canonical",
    "legacy:033": "generated:issues.comments.list:thread:variant:01",
    "legacy:034": "generated:issues.comments.list:recent:canonical",
    "legacy:035": "generated:issues.comments.list:recent:variant:01",
    "legacy:036": "generated:issues.labels.add:default:canonical",
    "legacy:037": "generated:issues.labels.remove:default:canonical",
    "legacy:038": "generated:issues.labels.list:default:canonical",
    "legacy:039": "manual:issues.metadata.set:canonical",
    "legacy:040": "manual:issues.metadata.set:variant:01",
    "legacy:041": "manual:issues.metadata.list:canonical",
    "legacy:042": "manual:issues.metadata.get:canonical",
    "legacy:043": "manual:issues.metadata.delete:canonical",
    "legacy:044": "manual:issues.subscribers.list:canonical",
    "legacy:045": "manual:issues.subscribers.add:canonical",
    "legacy:046": "manual:issues.subscribers.remove:canonical",
    "legacy:047": "generated:issues.list:default:canonical",
    "legacy:048": "manual:issues.get:canonical",
    "legacy:049": "generated:issues.create:default:canonical",
    "legacy:050": "generated:issues.create:default:variant:01",
    "legacy:051": "generated:issues.create:default:variant:02",
    "legacy:052": "generated:issues.create:default:variant:03",
    "legacy:053": "generated:issues.create:default:variant:04",
    "legacy:054": "manual:projects.list:canonical",
    "legacy:055": "manual:projects.get:canonical",
    "legacy:056": "generated:projects.create:default:canonical",
    "legacy:057": "generated:projects.create:default:variant:01",
    "legacy:058": "generated:projects.update:default:canonical",
    "legacy:059": "generated:projects.update:default:variant:01",
    "legacy:060": "generated:projects.update:default:variant:02",
    "legacy:061": "generated:projects.update:default:variant:03",
    "legacy:062": "manual:projects.delete:canonical",
    "legacy:063": "generated:projects.resources.list:default:canonical",
    "legacy:064": "generated:projects.resources.add_local_directory:default:canonical",
    "legacy:065": "generated:projects.resources.add_local_directory:default:variant:01",
    "legacy:066": "generated:projects.resources.update_local_directory:default:canonical",
    "legacy:067": "generated:projects.resources.remove:default:canonical",
    "legacy:068": "manual:repositories.list:canonical",
    "legacy:069": "manual:repositories.get:canonical",
    "legacy:070": "manual:repositories.checkout:canonical",
    "legacy:071": "manual:runtimes.list:canonical",
    "legacy:072": "manual:runtimes.get:canonical",
    "legacy:073": "manual:skills.list:canonical",
    "legacy:074": "manual:skills.get:canonical",
    "legacy:075": "manual:skills.create:canonical",
    "legacy:076": "manual:skills.create:variant:01",
    "legacy:077": "manual:skills.update:canonical",
    "legacy:078": "manual:skills.update:variant:01",
    "legacy:079": "manual:skills.delete:canonical",
    "legacy:080": "manual:skills.import_from_url:canonical",
    "legacy:081": "manual:squads.list:canonical",
    "legacy:082": "manual:squads.get:canonical",
    "legacy:083": "manual:users.list:canonical",
    "legacy:084": "manual:users.get:canonical",
    "legacy:085": "manual:auth.login:canonical",
    "legacy:086": "manual:auth.status:canonical",
    "legacy:087": "manual:auth.logout:canonical",
    "legacy:088": "manual:daemon.status:canonical",
    "legacy:089": "manual:issues.deprioritize:canonical",
    "legacy:090": "generated:issues.set_status:default:canonical",
    "legacy:091": "manual:labels.list:canonical",
    "legacy:092": "manual:labels.get:canonical",
    "legacy:093": "manual:labels.create:canonical",
    "legacy:094": "manual:labels.update:canonical",
    "legacy:095": "manual:labels.delete:canonical",
    "legacy:096": "generated:projects.set_status:default:canonical",
    "legacy:097": "manual:workspaces.list:canonical",
    "legacy:098": "manual:workspaces.get:canonical",
    "legacy:099": "manual:issues.update:canonical",
    "legacy:100": "manual:issues.update:variant:01",
    "legacy:101": "manual:issues.assign:canonical",
    "legacy:102": "manual:issues.reorder:canonical",
    "legacy:103": "manual:issues.search:canonical",
    "legacy:104": "manual:issues.children:canonical",
    "legacy:105": "manual:issues.pull_requests:canonical",
    "legacy:106": "manual:issues.runs:canonical",
    "legacy:107": "manual:issues.usage:canonical",
    "legacy:108": "generated:issues.comments.add:default:canonical",
    "legacy:109": "generated:issues.comments.delete:default:canonical",
    "legacy:110": "manual:issues.comments.resolve:canonical",
    "legacy:111": "manual:issues.comments.unresolve:canonical",
    "legacy:112": "manual:workspaces.members:canonical",
    "legacy:113": "manual:autopilots.triggers.list:canonical",
    "legacy:114": "manual:autopilots.triggers.delete:canonical",
    "legacy:115": "manual:skills.files.list:canonical",
    "legacy:116": "manual:skills.files.delete:canonical",
    "legacy:117": "manual:daemon.disk_usage:canonical",
    "legacy:118": "manual:agents.skills.set:canonical",
    "legacy:119": "manual:autopilots.triggers.create:canonical",
    "legacy:120": "manual:daemon.start:canonical",
    "legacy:121": "manual:daemon.stop:canonical",
    "legacy:122": "manual:daemon.restart:canonical",
    "legacy:123": "manual:daemon.logs:canonical",
    "legacy:124": "manual:issues.cancel_task:canonical",
    "legacy:125": "manual:issues.comments.reply:canonical",
    "legacy:126": "manual:issues.rerun:canonical",
    "legacy:127": "manual:issues.run_messages:canonical",
    "legacy:128": "manual:maintenance.update:canonical",
    "legacy:129": "manual:setup.cloud:canonical",
    "legacy:130": "manual:setup.self_host:canonical",
    "legacy:131": "manual:skills.files.upsert:canonical",
    "legacy:132": "manual:workspaces.switch:canonical",
    "legacy:133": "manual:workspaces.watch:canonical",
    "legacy:134": "manual:workspaces.unwatch:canonical",
    "legacy:135": "manual:maintenance.version:canonical",
    "legacy:136": "manual:issues.create:variant:05",
    "legacy:137": "manual:issues.create:variant:06",
    "legacy:138": "manual:issues.update:variant:02",
    "legacy:139": "manual:autopilots.history:variant:01",
    "legacy:140": "manual:autopilots.history:variant:02",
    "legacy:141": "manual:autopilots.history:variant:03",
    "legacy:142": "manual:autopilots.update:variant:03",
    "legacy:143": "manual:autopilots.create:variant:01",
}


def _build_operation_cases() -> tuple[OperationCase, ...]:
    import datetime
    import pathlib

    import msgspec

    from multica_py.enums import (
        AutopilotExecutionMode,
        IssueStatus,
        MetadataValueType,
        ProjectStatus,
    )
    from multica_py.models.agents import Agent, AgentCreateRequest, AgentSkill, AgentUpdateRequest
    from multica_py.models.autopilots import (
        Autopilot,
        AutopilotListPage,
        AutopilotRun,
        AutopilotRunListPage,
        AutopilotSubscriber,
    )
    from multica_py.models.issue_activity import (
        CommentCursor,
        CommentListFlatRequest,
        CommentListRecentRequest,
        CommentListThreadRequest,
        IssueUsage,
        MetadataEntry,
        MetadataListRequest,
        MetadataPredicate,
        MetadataSetRequest,
        RunMessage,
        TaskRun,
    )
    from multica_py.models.issues import (
        FileDescription,
        InlineDescription,
        IssueAssignmentRequest,
        IssueChildStageGroup,
        IssueCreateRequest,
        IssueReorderRequest,
        IssueUpdateRequest,
        LinkedPullRequest,
        StdinDescription,
    )
    from multica_py.models.labels import Label
    from multica_py.models.project_resources import (
        ProjectResourceAddLocalDirectoryRequest,
        ProjectResourceUpdateLocalDirectoryRequest,
    )
    from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
    from multica_py.models.skills import Skill, SkillCreateRequest, SkillFile, SkillUpdateRequest
    from multica_py.models.system import (
        AttachmentResult,
        AuthenticationStatus,
        DaemonDiskUsageEntry,
        DaemonStatus,
        MaintenanceVersion,
        Repository,
        RepositoryCheckoutResult,
        RuntimeDefinition,
        Squad,
        SquadMember,
        User,
    )
    from multica_py.models.workspaces import Workspace, WorkspaceMember

    # ponytail: all 135 cases built from argv_data source data inline
    _LOCAL_DIR = pathlib.Path("/tmp/sandbox").resolve()

    # Pre-encode common payloads to match legacy ARGV_CASES
    _AG = msgspec.json.encode(Agent(id="a1", name="n"))
    _AP = msgspec.json.encode(
        Autopilot(
            id="a1",
            workspace_id="w1",
            title="AP",
            assignee_type="member",
            assignee_id="u1",
            status="active",
            execution_mode="create_issue",
            created_by_type="member",
            created_by_id="u1",
        )
    )
    _APRUN = msgspec.json.encode(
        AutopilotRun(id="r1", autopilot_id="a1", source="manual", status="running")
    )
    _AR = msgspec.json.encode(AttachmentResult(id="a1", filename="f.txt"))
    _LBL = msgspec.json.encode([Label(id="lbl_1", name="bug", color="#ff0000")])
    _REPO = msgspec.json.encode(Repository(id="r1", name="repo1"))
    _RT = msgspec.json.encode(RuntimeDefinition(id="r1", name="py3"))
    _SK = msgspec.json.encode(Skill(id="s1", name="sk"))
    _PR_RES = {
        "id": "res_001",
        "project_id": "pr_001",
        "resource_type": "local_directory",
        "resource_ref": {"local_path": "/tmp/sandbox", "daemon_id": "daemon-001", "label": "main"},
    }
    _PR_RES_BYTES = msgspec.json.encode(_PR_RES)
    _SQ = msgspec.json.encode(Squad(id="s1", name="S"))
    _SQ_MEMBERS = msgspec.json.encode(
        [SquadMember(member_id="a1", member_type="agent", role="architecture-reviewer")]
    )
    _AG_SKILLS = msgspec.json.encode([AgentSkill(id="sk_1", name="openspec-propose", enabled=True)])
    _USR = msgspec.json.encode(User(id="u1", name="Alice"))
    _WS_LIST = msgspec.json.encode([Workspace(id="ws_001", name="Main Workspace")])
    _WS = msgspec.json.encode(Workspace(id="ws_001", name="Main Workspace"))
    _WS_MEMBERS = msgspec.json.encode([WorkspaceMember(id="usr_1", name="Alice")])
    _SK_FILE = msgspec.json.encode(SkillFile(id="f_1", path="SKILL.md"))
    _PR_LINK = msgspec.json.encode([LinkedPullRequest(url="https://example.com/pr/1")])
    _TASK_RUN = msgspec.json.encode([TaskRun(id="run_1", status="done")])
    _USAGE = msgspec.json.encode(IssueUsage(total_runs=3))
    _DS_STOP = msgspec.json.encode(DaemonStatus(running=False))
    _DS = msgspec.json.encode(DaemonStatus(running=True, pid=12345, uptime=3600.0))
    _DS_RESTART = msgspec.json.encode(DaemonStatus(running=True, pid=12345))
    _AUTH_STATUS = msgspec.json.encode(
        AuthenticationStatus(authenticated=True, user_id="usr_001", token_type="bearer")
    )
    _AUTH_LOGOUT = msgspec.json.encode(
        AuthenticationStatus(authenticated=False, user_id=None, token_type=None)
    )

    _GENERATED_CANONICAL_IDS: frozenset[str] = frozenset(
        {
            "generated:issues.comments.list:direct:canonical",
            "generated:issues.comments.list:flat:canonical",
            "generated:issues.comments.list:thread:canonical",
            "generated:issues.comments.list:recent:canonical",
            "generated:issues.labels.add:default:canonical",
            "generated:issues.labels.remove:default:canonical",
            "generated:issues.labels.list:default:canonical",
            "generated:issues.list:default:canonical",
            "generated:issues.create:default:canonical",
            "generated:projects.create:default:canonical",
            "generated:projects.update:default:canonical",
            "generated:projects.resources.list:default:canonical",
            "generated:projects.resources.add_local_directory:default:canonical",
            "generated:projects.resources.update_local_directory:default:canonical",
            "generated:projects.resources.remove:default:canonical",
            "generated:issues.set_status:default:canonical",
            "generated:projects.set_status:default:canonical",
            "generated:issues.comments.add:default:canonical",
            "generated:issues.comments.delete:default:canonical",
            "generated:autopilots.list:default:canonical",
            "generated:autopilots.get:default:canonical",
            "generated:autopilots.create:default:canonical",
            "generated:autopilots.update:default:canonical",
            "generated:autopilots.delete:default:canonical",
            "generated:autopilots.run:default:canonical",
            "generated:autopilots.history:default:canonical",
        }
    )

    def _c(
        sdk_method: str,
        expected_argv: tuple[str, ...],
        *,
        method: str | None = None,
        resource_attr: str | None = None,
        args: tuple[object, ...] = (),
        kwargs: tuple[tuple[str, object], ...] = (),
        stdout: bytes = b"",
        transport: str = "",
        stdin: bytes | None = None,
        timeout: float | None = None,
        id: str = "",
        canonical: bool | None = None,
        source_ref: str | None = None,
    ) -> OperationCase:
        if not transport:
            if sdk_method in _SPAWN_SDK_METHODS:
                transport = "spawn"
            elif len(expected_argv) >= 2 and expected_argv[-2:] == ("--output", "json"):
                transport = "run_bytes"
            else:
                transport = "run_text"
        ra = resource_attr or _resource_attr(sdk_method)
        m = method or sdk_method.rsplit(".", 1)[-1]
        legacy_key = next(
            (key for key, value in LEGACY_ARGV_MIGRATION.items() if value == id), None
        )

        is_canonical = (":canonical" in id) if canonical is None else canonical
        if id.startswith("generated:") and id not in _GENERATED_CANONICAL_IDS:
            is_canonical = False

        return OperationCase(
            id=id,
            sdk_method=sdk_method,
            is_canonical=is_canonical,
            resource_attr=ra,
            method=m,
            expected_argv=expected_argv,
            transport_method=transport,
            args=args,
            kwargs=kwargs,
            stdout=stdout,
            stdin=stdin,
            timeout=timeout,
            contract_operation_id=(
                id.removeprefix("generated:").rsplit(":", 2)[0]
                if id.startswith("generated:")
                else None
            ),
            source_ref=(legacy_key or source_ref) if not id.startswith("generated:") else None,
        )

    cases: list[OperationCase] = [
        _c(
            "agents.list",
            ("agent", "list", "--output", "json"),
            stdout=b"[]",
            id="manual:agents.list:canonical",
        ),
        _c(
            "agents.get",
            ("agent", "get", "a1", "--output", "json"),
            args=("a1",),
            stdout=_AG,
            id="manual:agents.get:canonical",
        ),
        _c(
            "agents.skills.list",
            ("agent", "skill", "list", "a1", "--output", "json"),
            args=("a1",),
            stdout=_AG_SKILLS,
            id="manual:agents.skills.list:canonical",
        ),
        _c(
            "agents.create",
            ("agent", "create", "--name", "my-agent", "--output", "json"),
            args=(AgentCreateRequest(name="my-agent"),),
            stdout=_AG,
            id="manual:agents.create:canonical",
        ),
        _c(
            "agents.create",
            ("agent", "create", "--name", "my-agent", "--description", "desc", "--output", "json"),
            args=(AgentCreateRequest(name="my-agent", description="desc"),),
            stdout=_AG,
            id="manual:agents.create:variant:01",
        ),
        _c(
            "agents.create",
            ("agent", "create", "--name", "my-agent", "--runtime-id", "rt_001", "--output", "json"),
            args=(AgentCreateRequest(name="my-agent", runtime_id="rt_001"),),
            stdout=_AG,
            id="manual:agents.create:variant:02",
        ),
        _c(
            "agents.create",
            (
                "agent",
                "create",
                "--name",
                "my-agent",
                "--runtime-id",
                "rt_001",
                "--model",
                "multica-test/fake",
                "--output",
                "json",
            ),
            args=(
                AgentCreateRequest(name="my-agent", runtime_id="rt_001", model="multica-test/fake"),
            ),
            stdout=_AG,
            id="manual:agents.create:variant:03",
        ),
        _c(
            "agents.update",
            ("agent", "update", "a1", "--output", "json"),
            args=("a1", AgentUpdateRequest()),
            stdout=_AG,
            id="manual:agents.update:canonical",
        ),
        _c(
            "agents.update",
            ("agent", "update", "a1", "--name", "new", "--output", "json"),
            args=("a1", AgentUpdateRequest(name="new")),
            stdout=_AG,
            id="manual:agents.update:variant:01",
        ),
        _c(
            "agents.archive",
            ("agent", "archive", "a1"),
            args=("a1",),
            id="manual:agents.archive:canonical",
        ),
        _c(
            "agents.restore",
            ("agent", "restore", "a1"),
            args=("a1",),
            id="manual:agents.restore:canonical",
        ),
        _c(
            "agents.tasks",
            ("agent", "tasks", "a1", "--output", "json"),
            args=("a1",),
            stdout=b"[]",
            id="manual:agents.tasks:canonical",
        ),
        _c(
            "agents.upload_avatar",
            ("agent", "avatar", "upload", "a1", "--image", "/path/image.png"),
            args=("a1", "/path/image.png"),
            id="manual:agents.upload_avatar:canonical",
        ),
        _c(
            "attachments.list",
            ("attachment", "list", "i1", "--output", "json"),
            args=("i1",),
            stdout=b"[]",
            id="manual:attachments.list:canonical",
        ),
        _c(
            "attachments.upload",
            ("attachment", "upload", "i1", "--file", "/p/f.txt", "--output", "json"),
            args=("i1", "/p/f.txt"),
            stdout=_AR,
            id="manual:attachments.upload:canonical",
        ),
        _c(
            "attachments.download",
            ("attachment", "download", "a1", "--output", "/out"),
            args=("a1", "/out"),
            id="manual:attachments.download:canonical",
        ),
        _c(
            "autopilots.list",
            ("autopilot", "list", "--output", "json"),
            stdout=b'{"autopilots":[],"total":0}',
            method="list",
            id="generated:autopilots.list:default:canonical",
        ),
        _c(
            "autopilots.get",
            ("autopilot", "get", "a1", "--output", "json"),
            args=("a1",),
            stdout=_AP,
            id="generated:autopilots.get:default:canonical",
        ),
        _c(
            "autopilots.create",
            (
                "autopilot",
                "create",
                "--title",
                "my-ap",
                "--agent",
                "ag1",
                "--mode",
                "create_issue",
                "--priority",
                "none",
                "--output",
                "json",
            ),
            args=("my-ap",),
            kwargs=(("agent", "ag1"), ("execution_mode", AutopilotExecutionMode.create_issue)),
            stdout=_AP,
            method="create",
            id="generated:autopilots.create:default:canonical",
        ),
        _c(
            "autopilots.update",
            ("autopilot", "update", "a1", "--output", "json"),
            args=("a1",),
            stdout=_AP,
            method="update",
            id="generated:autopilots.update:default:canonical",
        ),
        _c(
            "autopilots.update",
            ("autopilot", "update", "a1", "--title", "new", "--output", "json"),
            args=("a1",),
            kwargs=(("title", "new"),),
            stdout=_AP,
            method="update",
            id="manual:autopilots.update:variant:01",
        ),
        _c(
            "autopilots.update",
            ("autopilot", "update", "a1", "--status", "active", "--output", "json"),
            args=("a1",),
            kwargs=(("status", "active"),),
            stdout=_AP,
            method="update",
            id="manual:autopilots.update:variant:02",
        ),
        _c(
            "autopilots.delete",
            ("autopilot", "delete", "a1"),
            args=("a1",),
            id="generated:autopilots.delete:default:canonical",
        ),
        _c(
            "autopilots.run",
            ("autopilot", "run", "a1", "--output", "json"),
            args=("a1",),
            stdout=_APRUN,
            method="run",
            id="generated:autopilots.run:default:canonical",
        ),
        _c(
            "autopilots.history",
            ("autopilot", "runs", "a1", "--output", "json"),
            args=("a1",),
            stdout=b'{"runs":[],"total":0}',
            method="history",
            id="generated:autopilots.history:default:canonical",
        ),
        _c(
            "autopilots.get_run",
            ("autopilot", "run", "get", "r1", "--output", "json"),
            args=("r1",),
            stdout=_APRUN,
            id="manual:autopilots.get_run:canonical",
        ),
        _c(
            "autopilots.history",
            ("autopilot", "runs", "a1", "--limit", "10", "--output", "json"),
            args=("a1",),
            kwargs=(("limit", 10), ("offset", None)),
            stdout=b'{"runs":[],"total":0}',
            method="history",
            id="manual:autopilots.history:variant:01",
        ),
        _c(
            "autopilots.history",
            ("autopilot", "runs", "a1", "--offset", "20", "--output", "json"),
            args=("a1",),
            kwargs=(("offset", 20), ("limit", None)),
            stdout=b'{"runs":[],"total":0}',
            method="history",
            id="manual:autopilots.history:variant:02",
        ),
        _c(
            "autopilots.history",
            ("autopilot", "runs", "a1", "--limit", "10", "--offset", "20", "--output", "json"),
            args=("a1",),
            kwargs=(("limit", 10), ("offset", 20)),
            stdout=b'{"runs":[],"total":0}',
            method="history",
            id="manual:autopilots.history:variant:03",
        ),
        _c(
            "autopilots.update",
            ("autopilot", "update", "a1", "--project", "", "--output", "json"),
            args=("a1",),
            kwargs=(("project_id", ""),),
            stdout=_AP,
            method="update",
            id="manual:autopilots.update:variant:03",
        ),
        _c(
            "autopilots.create",
            (
                "autopilot",
                "create",
                "--title",
                "my-ap",
                "--agent",
                "ag1",
                "--mode",
                "create_issue",
                "--priority",
                "none",
                "--description",
                "desc",
                "--project",
                "p1",
                "--issue-title-template",
                "{{title}}",
                "--subscriber",
                "u1",
                "--subscriber",
                "u2",
                "--output",
                "json",
            ),
            args=("my-ap",),
            kwargs=(
                ("agent", "ag1"),
                ("execution_mode", AutopilotExecutionMode.create_issue),
                ("description", "desc"),
                ("project_id", "p1"),
                ("issue_title_template", "{{title}}"),
                ("subscribers", ("u1", "u2")),
            ),
            stdout=_AP,
            method="create",
            id="manual:autopilots.create:variant:01",
        ),
        _c("configuration.show", ("config", "show"), id="manual:configuration.show:canonical"),
        _c(
            "configuration.get",
            ("config", "get", "key"),
            args=("key",),
            id="manual:configuration.get:canonical",
        ),
        _c(
            "configuration.set",
            ("config", "set", "key", "val"),
            args=("key", "val"),
            id="manual:configuration.set:canonical",
        ),
        _c(
            "issues.comments.list_flat",
            ("issue", "comment", "list", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=b"[]",
            method="list",
            id="generated:issues.comments.list:direct:canonical",
        ),
        _c(
            "issues.comments.list_thread",
            (
                "issue",
                "comment",
                "list",
                "iss_1",
                "--since",
                "2026-07-12T10:00:00+00:00",
                "--output",
                "json",
            ),
            args=(
                CommentListFlatRequest(
                    issue_id="iss_1",
                    since=datetime.datetime(2026, 7, 12, 10, 0, tzinfo=datetime.UTC),
                ),
            ),
            stdout=b'[{"id":"c1","content":"hello"}]',
            method="list_flat",
            transport="run_text",
            id="generated:issues.comments.list:flat:canonical",
        ),
        _c(
            "issues.comments.list_recent",
            (
                "issue",
                "comment",
                "list",
                "iss_1",
                "--thread",
                "th_1",
                "--tail",
                "10",
                "--output",
                "json",
            ),
            args=(CommentListThreadRequest(issue_id="iss_1", thread_id="th_1", limit=10),),
            stdout=b'[{"id":"c1","content":"reply","parent_id":"th_1"}]',
            method="list_thread",
            transport="run_text",
            id="generated:issues.comments.list:thread:canonical",
        ),
        _c(
            "issues.comments.list",
            (
                "issue",
                "comment",
                "list",
                "iss_1",
                "--thread",
                "th_1",
                "--before",
                "cur_b",
                "--before-id",
                "cur_id",
                "--tail",
                "10",
                "--output",
                "json",
            ),
            args=(
                CommentListThreadRequest(
                    issue_id="iss_1",
                    thread_id="th_1",
                    cursor=CommentCursor(before="cur_b", before_id="cur_id"),
                    limit=10,
                ),
            ),
            stdout=b'[{"id":"c1","content":"reply","parent_id":"th_1"}]',
            method="list_thread",
            transport="run_text",
            id="generated:issues.comments.list:thread:variant:01",
        ),
        _c(
            "issues.comments.list",
            ("issue", "comment", "list", "iss_1", "--recent", "5", "--output", "json"),
            args=(CommentListRecentRequest(issue_id="iss_1", limit=5),),
            stdout=b'[{"id":"th_1","comments":[{"id":"c1","content":"root comment"}],"resolved":false}]',
            method="list_recent",
            transport="run_text",
            id="generated:issues.comments.list:recent:canonical",
        ),
        _c(
            "issues.comments.list",
            ("issue", "comment", "list", "iss_1", "--recent", "10", "--output", "json"),
            args=(CommentListRecentRequest(issue_id="iss_1"),),
            stdout=b"[]",
            method="list_recent",
            transport="run_text",
            id="generated:issues.comments.list:recent:variant:01",
        ),
        _c(
            "issues.labels.add",
            ("issue", "label", "add", "iss_1", "lbl_1", "--output", "json"),
            args=("iss_1", "lbl_1"),
            stdout=_LBL,
            id="generated:issues.labels.add:default:canonical",
        ),
        _c(
            "issues.labels.remove",
            ("issue", "label", "remove", "iss_1", "lbl_1", "--output", "json"),
            args=("iss_1", "lbl_1"),
            stdout=b"[]",
            id="generated:issues.labels.remove:default:canonical",
        ),
        _c(
            "issues.labels.list",
            ("issue", "label", "list", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=_LBL,
            id="generated:issues.labels.list:default:canonical",
        ),
        _c(
            "issues.metadata.set",
            (
                "issue",
                "metadata",
                "set",
                "iss_1",
                "--key",
                "flag",
                "--value",
                "true",
                "--type",
                "boolean",
                "--output",
                "json",
            ),
            args=("iss_1", "flag", True),
            stdout=b'{"key":"flag","value":true}',
            id="manual:issues.metadata.set:canonical",
            canonical=False,
        ),
        _c(
            "issues.metadata.set_typed",
            (
                "issue",
                "metadata",
                "set",
                "iss_1",
                "--key",
                "answer",
                "--value",
                "42",
                "--type",
                "integer",
                "--output",
                "json",
            ),
            args=(
                MetadataSetRequest(
                    issue_id="iss_1", key="answer", value="42", value_type=MetadataValueType.integer
                ),
            ),
            stdout=b'{"key":"answer","value":"42"}',
            method="set_typed",
            id="manual:issues.metadata.set:variant:01",
            canonical=True,
        ),
        _c(
            "issues.metadata.query",
            (
                "issue",
                "metadata",
                "list",
                "iss_1",
                "--metadata",
                "priority=high",
                "--metadata-type",
                "string",
                "--metadata",
                "visible=true",
                "--metadata-type",
                "boolean",
                "--cursor",
                "cur_1",
                "--limit",
                "25",
                "--output",
                "json",
            ),
            args=(
                MetadataListRequest(
                    issue_id="iss_1",
                    predicates=(
                        MetadataPredicate(key="priority", value="high"),
                        MetadataPredicate(key="visible", value=True),
                    ),
                    cursor="cur_1",
                    limit=25,
                ),
            ),
            stdout=b'[{"key":"priority","value":"high"}]',
            method="query",
            transport="run_text",
            id="manual:issues.metadata.list:canonical",
        ),
        _c(
            "issues.metadata.list",
            ("issue", "metadata", "list", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=b"[]",
            id="manual:issues.metadata.list:coverage:canonical",
            source_ref="SDK-ISSUE-METADATA:list",
        ),
        _c(
            "issues.metadata.set",
            (
                "issue",
                "metadata",
                "set",
                "iss_1",
                "--key",
                "flag",
                "--value",
                "true",
                "--type",
                "boolean",
                "--output",
                "json",
            ),
            args=("iss_1", "flag", True),
            stdout=b'{"key":"flag","value":true}',
            id="manual:issues.metadata.set:coverage:canonical",
            source_ref="SDK-ISSUE-METADATA:set",
        ),
        _c(
            "issues.metadata.get",
            ("issue", "metadata", "get", "iss_1", "--key", "flag", "--output", "json"),
            args=("iss_1", "flag"),
            stdout=b'{"key":"flag","value":true}',
            id="manual:issues.metadata.get:canonical",
        ),
        _c(
            "issues.metadata.delete",
            ("issue", "metadata", "delete", "iss_1", "--key", "flag"),
            args=("iss_1", "flag"),
            id="manual:issues.metadata.delete:canonical",
        ),
        _c(
            "issues.subscribers.list",
            ("issue", "subscriber", "list", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=b"[]",
            id="manual:issues.subscribers.list:canonical",
        ),
        _c(
            "issues.subscribers.add",
            ("issue", "subscriber", "add", "iss_1", "--user-id", "usr_1"),
            args=("iss_1", "usr_1"),
            id="manual:issues.subscribers.add:canonical",
        ),
        _c(
            "issues.subscribers.remove",
            ("issue", "subscriber", "remove", "iss_1", "--user-id", "usr_1"),
            args=("iss_1", "usr_1"),
            id="manual:issues.subscribers.remove:canonical",
        ),
        _c(
            "issues.list",
            ("issue", "list", "--output", "json"),
            stdout=b'{"issues":[]}',
            id="generated:issues.list:default:canonical",
        ),
        _c(
            "issues.get",
            ("issue", "get", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="manual:issues.get:canonical",
        ),
        _c(
            "issues.create",
            ("issue", "create", "--title", "Test", "--output", "json"),
            args=(IssueCreateRequest(title="Test"),),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="generated:issues.create:default:canonical",
        ),
        _c(
            "issues.create",
            ("issue", "create", "--title", "Test", "--description", "hello", "--output", "json"),
            args=(
                IssueCreateRequest(title="Test", description_input=InlineDescription(text="hello")),
            ),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="generated:issues.create:default:variant:01",
        ),
        _c(
            "issues.create",
            (
                "issue",
                "create",
                "--title",
                "Test",
                "--description-file",
                "/nonexistent/desc.txt",
                "--output",
                "json",
            ),
            args=(
                IssueCreateRequest(
                    title="Test", description_input=FileDescription(path="/nonexistent/desc.txt")
                ),
            ),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="generated:issues.create:default:variant:02",
        ),
        _c(
            "issues.create",
            ("issue", "create", "--title", "Test", "--description-stdin", "--output", "json"),
            args=(IssueCreateRequest(title="Test", description_input=StdinDescription()),),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="generated:issues.create:default:variant:03",
        ),
        _c(
            "issues.create",
            ("issue", "create", "--title", "Test", "--project", "pr_001", "--output", "json"),
            args=(IssueCreateRequest(title="Test", project_id="pr_001"),),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="generated:issues.create:default:variant:04",
        ),
        _c(
            "issues.create",
            ("issue", "create", "--title", "Test", "--parent", "iss_parent", "--output", "json"),
            args=(IssueCreateRequest(title="Test", parent_id="iss_parent"),),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="manual:issues.create:variant:05",
        ),
        _c(
            "issues.create",
            (
                "issue",
                "create",
                "--title",
                "Test",
                "--project",
                "pr_001",
                "--parent",
                "iss_parent",
                "--output",
                "json",
            ),
            args=(IssueCreateRequest(title="Test", parent_id="iss_parent", project_id="pr_001"),),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="manual:issues.create:variant:06",
        ),
        _c(
            "projects.list",
            ("project", "list", "--output", "json"),
            stdout=b"[]",
            id="manual:projects.list:canonical",
        ),
        _c(
            "projects.get",
            ("project", "get", "pr_1", "--output", "json"),
            args=("pr_1",),
            stdout=b'{"id":"pr_1","title":"Alpha","status":"planned"}',
            id="manual:projects.get:canonical",
        ),
        _c(
            "projects.create",
            ("project", "create", "--title", "Alpha", "--output", "json"),
            args=(ProjectCreateRequest(name="Alpha"),),
            stdout=b'{"id":"pr_1","title":"Alpha","status":"planned"}',
            id="generated:projects.create:default:canonical",
        ),
        _c(
            "projects.create",
            ("project", "create", "--title", "Alpha", "--description", "desc", "--output", "json"),
            args=(ProjectCreateRequest(name="Alpha", description="desc"),),
            stdout=b'{"id":"pr_1","title":"Alpha","status":"planned"}',
            id="generated:projects.create:default:variant:01",
        ),
        _c(
            "projects.update",
            ("project", "update", "pr_1", "--output", "json"),
            args=("pr_1", ProjectUpdateRequest()),
            stdout=b'{"id":"pr_1","title":"Alpha","status":"planned"}',
            id="generated:projects.update:default:canonical",
        ),
        _c(
            "projects.update",
            ("project", "update", "pr_1", "--title", "only-title", "--output", "json"),
            args=("pr_1", ProjectUpdateRequest(name="only-title")),
            stdout=b'{"id":"pr_1","title":"New","status":"planned"}',
            id="generated:projects.update:default:variant:01",
        ),
        _c(
            "projects.update",
            ("project", "update", "pr_1", "--description", "", "--output", "json"),
            args=("pr_1", ProjectUpdateRequest(description="")),
            stdout=b'{"id":"pr_1","title":"Alpha","status":"planned"}',
            id="generated:projects.update:default:variant:02",
        ),
        _c(
            "projects.update",
            ("project", "update", "pr_1", "--description", "new", "--output", "json"),
            args=("pr_1", ProjectUpdateRequest(description="new")),
            stdout=b'{"id":"pr_1","title":"Alpha","status":"planned"}',
            id="generated:projects.update:default:variant:03",
        ),
        _c(
            "projects.delete",
            ("project", "delete", "pr_1"),
            args=("pr_1",),
            id="manual:projects.delete:canonical",
        ),
        _c(
            "projects.resources.list",
            ("project", "resource", "list", "pr_001", "--output", "json"),
            args=("pr_001",),
            stdout=msgspec.json.encode([_PR_RES]),
            id="generated:projects.resources.list:default:canonical",
        ),
        _c(
            "projects.resources.add_local_directory",
            (
                "project",
                "resource",
                "add",
                "pr_001",
                "--type",
                "local_directory",
                "--local-path",
                str(_LOCAL_DIR),
                "--daemon-id",
                "daemon-001",
                "--output",
                "json",
            ),
            args=(
                "pr_001",
                ProjectResourceAddLocalDirectoryRequest(
                    local_path="/tmp/sandbox", daemon_id="daemon-001"
                ),
            ),
            stdout=_PR_RES_BYTES,
            id="generated:projects.resources.add_local_directory:default:canonical",
        ),
        _c(
            "projects.resources.add_local_directory",
            (
                "project",
                "resource",
                "add",
                "pr_001",
                "--type",
                "local_directory",
                "--local-path",
                str(_LOCAL_DIR),
                "--daemon-id",
                "daemon-001",
                "--ref-label",
                "main",
                "--output",
                "json",
            ),
            args=(
                "pr_001",
                ProjectResourceAddLocalDirectoryRequest(
                    local_path="/tmp/sandbox", daemon_id="daemon-001", label="main"
                ),
            ),
            stdout=_PR_RES_BYTES,
            id="generated:projects.resources.add_local_directory:default:variant:01",
        ),
        _c(
            "projects.resources.update_local_directory",
            (
                "project",
                "resource",
                "update",
                "pr_001",
                "res_001",
                "--local-path",
                str(_LOCAL_DIR),
                "--output",
                "json",
            ),
            args=(
                "pr_001",
                "res_001",
                ProjectResourceUpdateLocalDirectoryRequest(local_path="/tmp/sandbox"),
            ),
            stdout=_PR_RES_BYTES,
            id="generated:projects.resources.update_local_directory:default:canonical",
        ),
        _c(
            "projects.resources.remove",
            ("project", "resource", "remove", "pr_001", "res_001"),
            args=("pr_001", "res_001"),
            id="generated:projects.resources.remove:default:canonical",
        ),
        _c(
            "repositories.list",
            ("repo", "list", "--output", "json"),
            stdout=b"[]",
            id="manual:repositories.list:canonical",
        ),
        _c(
            "repositories.get",
            ("repo", "get", "r1", "--output", "json"),
            args=("r1",),
            stdout=_REPO,
            id="manual:repositories.get:canonical",
        ),
        _c(
            "repositories.checkout",
            ("repo", "checkout", "r1", "--branch", "main", "--output", "json"),
            args=("r1", "main"),
            stdout=b'{"path":"/p","branch":"main","success":true}',
            id="manual:repositories.checkout:canonical",
        ),
        _c(
            "runtimes.list",
            ("runtime", "list", "--output", "json"),
            stdout=b"[]",
            id="manual:runtimes.list:canonical",
        ),
        _c(
            "runtimes.get",
            ("runtime", "get", "r1", "--output", "json"),
            args=("r1",),
            stdout=_RT,
            id="manual:runtimes.get:canonical",
        ),
        _c(
            "skills.list",
            ("skill", "list", "--output", "json"),
            stdout=b"[]",
            id="manual:skills.list:canonical",
        ),
        _c(
            "skills.get",
            ("skill", "get", "s1", "--output", "json"),
            args=("s1",),
            stdout=_SK,
            id="manual:skills.get:canonical",
        ),
        _c(
            "skills.create",
            ("skill", "create", "--name", "my-sk", "--output", "json"),
            args=(SkillCreateRequest(name="my-sk"),),
            stdout=_SK,
            id="manual:skills.create:canonical",
        ),
        _c(
            "skills.create",
            ("skill", "create", "--name", "my-sk", "--description", "desc", "--output", "json"),
            args=(SkillCreateRequest(name="my-sk", description="desc"),),
            stdout=_SK,
            id="manual:skills.create:variant:01",
        ),
        _c(
            "skills.update",
            ("skill", "update", "s1", "--output", "json"),
            args=("s1", SkillUpdateRequest()),
            stdout=_SK,
            id="manual:skills.update:canonical",
        ),
        _c(
            "skills.update",
            ("skill", "update", "s1", "--name", "new", "--output", "json"),
            args=("s1", SkillUpdateRequest(name="new")),
            stdout=_SK,
            id="manual:skills.update:variant:01",
        ),
        _c(
            "skills.delete",
            ("skill", "delete", "s1"),
            args=("s1",),
            id="manual:skills.delete:canonical",
        ),
        _c(
            "skills.import_from_url",
            ("skill", "import", "--url", "https://x.com", "--output", "json"),
            args=("https://x.com",),
            stdout=_SK,
            id="manual:skills.import_from_url:canonical",
        ),
        _c(
            "squads.list",
            ("squad", "list", "--output", "json"),
            stdout=b"[]",
            id="manual:squads.list:canonical",
        ),
        _c(
            "squads.get",
            ("squad", "get", "s1", "--output", "json"),
            args=("s1",),
            stdout=_SQ,
            id="manual:squads.get:canonical",
        ),
        _c(
            "squads.members.list",
            ("squad", "member", "list", "s1", "--output", "json"),
            args=("s1",),
            stdout=_SQ_MEMBERS,
            id="manual:squads.members.list:canonical",
            source_ref="manual:squads.members.list:canonical",
        ),
        _c(
            "users.list",
            ("user", "list", "--output", "json"),
            stdout=b"[]",
            id="manual:users.list:canonical",
        ),
        _c(
            "users.get",
            ("user", "get", "u1", "--output", "json"),
            args=("u1",),
            stdout=_USR,
            id="manual:users.get:canonical",
        ),
        _c(
            "auth.login",
            ("auth", "login", "--token", "secret-token"),
            args=("secret-token",),
            stdout=b"Login successful",
            id="manual:auth.login:canonical",
        ),
        _c(
            "auth.status",
            ("auth", "status", "--output", "json"),
            stdout=_AUTH_STATUS,
            id="manual:auth.status:canonical",
        ),
        _c(
            "auth.logout",
            ("auth", "logout", "--output", "json"),
            stdout=_AUTH_LOGOUT,
            id="manual:auth.logout:canonical",
        ),
        _c(
            "daemon.status",
            ("daemon", "status", "--output", "json"),
            stdout=_DS,
            id="manual:daemon.status:canonical",
        ),
        _c(
            "issues.deprioritize",
            ("issue", "deprioritize", "iss_001"),
            args=("iss_001",),
            stdout=b"Issue iss_001 deprioritized\n",
            id="manual:issues.deprioritize:canonical",
        ),
        _c(
            "issues.set_status",
            ("issue", "status", "iss_001", "done", "--output", "json"),
            args=("iss_001", IssueStatus.done),
            stdout=b'{"id":"iss_001","title":"Test issue","status":"done"}',
            id="generated:issues.set_status:default:canonical",
        ),
        _c(
            "labels.list",
            ("label", "list", "--output", "json"),
            stdout=b'[{"id":"lbl_001","name":"bug","color":"red"}]',
            id="manual:labels.list:canonical",
        ),
        _c(
            "labels.get",
            ("label", "get", "lbl_001", "--output", "json"),
            args=("lbl_001",),
            stdout=b'{"id":"lbl_001","name":"bug","color":"red"}',
            id="manual:labels.get:canonical",
        ),
        _c(
            "labels.create",
            ("label", "create", "--name", "bug", "--output", "json"),
            args=("bug",),
            stdout=b'{"id":"lbl_001","name":"bug","color":"red"}',
            id="manual:labels.create:canonical",
        ),
        _c(
            "labels.update",
            ("label", "update", "lbl_001", "--name", "feature", "--output", "json"),
            args=("lbl_001",),
            kwargs=(("name", "feature"),),
            stdout=b'{"id":"lbl_001","name":"feature","color":"red"}',
            id="manual:labels.update:canonical",
        ),
        _c(
            "labels.delete",
            ("label", "delete", "lbl_001"),
            args=("lbl_001",),
            id="manual:labels.delete:canonical",
        ),
        _c(
            "projects.set_status",
            ("project", "status", "pr_001", "completed", "--output", "json"),
            args=("pr_001", ProjectStatus.completed),
            stdout=b'{"id":"pr_001","title":"Project Alpha","status":"completed"}',
            id="generated:projects.set_status:default:canonical",
        ),
        _c(
            "workspaces.list",
            ("workspace", "list", "--output", "json"),
            stdout=_WS_LIST,
            id="manual:workspaces.list:canonical",
        ),
        _c(
            "workspaces.get",
            ("workspace", "get", "ws_001", "--output", "json"),
            args=("ws_001",),
            stdout=_WS,
            id="manual:workspaces.get:canonical",
        ),
        _c(
            "issues.update",
            ("issue", "update", "iss_1", "--title", "Updated", "--output", "json"),
            args=("iss_1", IssueUpdateRequest(title="Updated")),
            stdout=b'{"id":"iss_1","title":"Updated","status":"todo"}',
            id="manual:issues.update:canonical",
        ),
        _c(
            "issues.update",
            ("issue", "update", "iss_1", "--project", "pr_001", "--output", "json"),
            args=("iss_1", IssueUpdateRequest(project_id="pr_001")),
            stdout=b'{"id":"iss_1","title":"Updated","status":"todo"}',
            id="manual:issues.update:variant:01",
        ),
        _c(
            "issues.update",
            ("issue", "update", "iss_1", "--parent", "iss_parent", "--output", "json"),
            args=("iss_1", IssueUpdateRequest(parent_id="iss_parent")),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="manual:issues.update:variant:02",
        ),
        _c(
            "issues.assign",
            ("issue", "assign", "iss_1", "--to-id", "usr_1", "--output", "json"),
            args=(IssueAssignmentRequest(issue_id="iss_1", member_id="usr_1"),),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="manual:issues.assign:canonical",
        ),
        _c(
            "issues.reorder",
            ("issue", "reorder", "iss_1", "--top", "--output", "json"),
            args=(IssueReorderRequest(issue_id="iss_1", top=True),),
            stdout=b'{"id":"iss_1","title":"Test","status":"todo"}',
            id="manual:issues.reorder:canonical",
        ),
        _c(
            "issues.search",
            ("issue", "search", "bug", "--output", "json"),
            args=("bug",),
            stdout=b"[]",
            id="manual:issues.search:canonical",
        ),
        _c(
            "issues.children",
            ("issue", "children", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=b'[{"name":"todo","count":1}]',
            id="manual:issues.children:canonical",
        ),
        _c(
            "issues.pull_requests",
            ("issue", "pull-requests", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=_PR_LINK,
            id="manual:issues.pull_requests:canonical",
        ),
        _c(
            "issues.runs",
            ("issue", "runs", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=_TASK_RUN,
            id="manual:issues.runs:canonical",
        ),
        _c(
            "issues.usage",
            ("issue", "usage", "iss_1", "--output", "json"),
            args=("iss_1",),
            stdout=_USAGE,
            id="manual:issues.usage:canonical",
        ),
        _c(
            "issues.comments.add",
            ("issue", "comment", "add", "iss_1", "--content", "hello", "--output", "json"),
            args=("iss_1", "hello"),
            stdout=b'{"id":"cmt_1","content":"hello"}',
            id="generated:issues.comments.add:default:canonical",
        ),
        _c(
            "issues.comments.delete",
            ("issue", "comment", "delete", "cmt_1"),
            args=("cmt_1",),
            id="generated:issues.comments.delete:default:canonical",
        ),
        _c(
            "issues.comments.resolve",
            ("issue", "comment", "resolve", "thr_1"),
            args=("thr_1",),
            id="manual:issues.comments.resolve:canonical",
        ),
        _c(
            "issues.comments.unresolve",
            ("issue", "comment", "unresolve", "thr_1"),
            args=("thr_1",),
            id="manual:issues.comments.unresolve:canonical",
        ),
        _c(
            "workspaces.members",
            ("workspace", "member", "list", "ws_001", "--output", "json"),
            args=("ws_001",),
            stdout=_WS_MEMBERS,
            id="manual:workspaces.members:canonical",
        ),
        _c(
            "autopilots.triggers.list",
            ("autopilot", "trigger", "list", "ap_1", "--output", "json"),
            args=("ap_1",),
            stdout=b'[{"id":"tr_1","type":"webhook","config":{}}]',
            id="manual:autopilots.triggers.list:canonical",
        ),
        _c(
            "autopilots.triggers.delete",
            ("autopilot", "trigger", "delete", "ap_1", "--trigger-id", "tr_1"),
            args=("ap_1", "tr_1"),
            id="manual:autopilots.triggers.delete:canonical",
        ),
        _c(
            "skills.files.list",
            ("skill", "file", "list", "sk_1", "--output", "json"),
            args=("sk_1",),
            stdout=msgspec.json.encode([SkillFile(id="f_1", path="SKILL.md")]),
            id="manual:skills.files.list:canonical",
        ),
        _c(
            "skills.files.delete",
            ("skill", "file", "delete", "sk_1", "--file-id", "f_1"),
            args=("sk_1", "f_1"),
            id="manual:skills.files.delete:canonical",
        ),
        _c(
            "daemon.disk_usage",
            ("daemon", "disk-usage", "--output", "json"),
            stdout=b'[{"path":"/tmp","size_bytes":1024}]',
            id="manual:daemon.disk_usage:canonical",
        ),
        _c(
            "agents.skills.set",
            ("agent", "skill", "set", "ag_001", "--skill-id", "sk_001"),
            args=("ag_001", ("sk_001",)),
            id="manual:agents.skills.set:canonical",
        ),
        _c(
            "autopilots.triggers.create",
            (
                "autopilot",
                "trigger",
                "create",
                "ap_001",
                "--type",
                "webhook",
                "--config",
                "url=https://example.com",
                "--output",
                "json",
            ),
            args=("ap_001", "webhook"),
            kwargs=(("config", {"url": "https://example.com"}),),
            stdout=b'{"id":"tr_001","type":"webhook","config":{"url":"https://example.com"}}',
            id="manual:autopilots.triggers.create:canonical",
        ),
        _c("daemon.start", ("daemon", "start"), id="manual:daemon.start:canonical"),
        _c(
            "daemon.stop",
            ("daemon", "stop", "--output", "json"),
            stdout=_DS_STOP,
            id="manual:daemon.stop:canonical",
        ),
        _c(
            "daemon.restart",
            ("daemon", "restart", "--output", "json"),
            stdout=_DS_RESTART,
            id="manual:daemon.restart:canonical",
        ),
        _c("daemon.logs", ("daemon", "logs"), id="manual:daemon.logs:canonical"),
        _c(
            "issues.cancel_task",
            ("issue", "cancel-task", "iss_001", "--run-id", "run_001"),
            args=("iss_001", "run_001"),
            id="manual:issues.cancel_task:canonical",
        ),
        _c(
            "issues.comments.reply",
            (
                "issue",
                "comment",
                "add",
                "iss_001",
                "--content",
                "reply text",
                "--parent",
                "th_001",
                "--output",
                "json",
            ),
            args=("iss_001", "th_001", "reply text"),
            stdout=b'{"id":"cmt_002","content":"reply text","parent_id":"th_001"}',
            id="manual:issues.comments.reply:canonical",
        ),
        _c(
            "issues.rerun",
            ("issue", "rerun", "iss_001", "--run-id", "run_001"),
            args=("iss_001", "run_001"),
            id="manual:issues.rerun:canonical",
        ),
        _c(
            "issues.run_messages",
            ("issue", "run-messages", "iss_001", "--run-id", "run_001", "--output", "json"),
            args=("iss_001", "run_001"),
            stdout=msgspec.json.encode(
                [RunMessage(id="msg_001", run_id="run_001", role="assistant", content="hello")]
            ),
            id="manual:issues.run_messages:canonical",
        ),
        _c("maintenance.update", ("update",), id="manual:maintenance.update:canonical"),
        _c("setup.cloud", ("setup", "cloud"), id="manual:setup.cloud:canonical"),
        _c(
            "setup.self_host",
            ("setup", "self-host", "--url", "https://example.com"),
            args=("https://example.com",),
            id="manual:setup.self_host:canonical",
        ),
        _c(
            "skills.files.upsert",
            (
                "skill",
                "file",
                "upsert",
                "sk_001",
                "--path",
                "SKILL.md",
                "--content",
                "# content",
                "--output",
                "json",
            ),
            args=("sk_001", "SKILL.md", "# content"),
            stdout=b'{"id":"f_001","path":"SKILL.md","content":"# content"}',
            id="manual:skills.files.upsert:canonical",
        ),
        _c(
            "workspaces.switch",
            ("workspace", "switch", "ws_001"),
            args=("ws_001",),
            id="manual:workspaces.switch:canonical",
        ),
        _c(
            "workspaces.watch",
            ("workspace", "watch", "ws_001"),
            args=("ws_001",),
            id="manual:workspaces.watch:canonical",
        ),
        _c(
            "workspaces.unwatch",
            ("workspace", "unwatch", "ws_001"),
            args=("ws_001",),
            id="manual:workspaces.unwatch:canonical",
        ),
        _c(
            "maintenance.version",
            ("version", "--output", "json"),
            stdout=b'{"version":"1.0.0","commit":"abc","build_date":"2026-01-01"}',
            id="manual:maintenance.version:canonical",
        ),
    ]
    return tuple(cases)


_ALL_CASES = _build_operation_cases()

MANUAL_OPERATION_CASES: tuple[OperationCase, ...] = tuple(
    c for c in _ALL_CASES if not c.id.startswith("generated:")
)
_LEGACY_GENERATED_CASES: tuple[OperationCase, ...] = tuple(
    c for c in _ALL_CASES if c.id.startswith("generated:")
)

_APPROVED_CATALOG = _validate_contract(_Path("contracts/sdk-contract.json"))

OPERATION_CASES: tuple[OperationCase, ...] = tuple(
    sorted(
        (*MANUAL_OPERATION_CASES, *generated_operation_cases(_APPROVED_CATALOG)),
        key=lambda c: c.id,
    )
)
