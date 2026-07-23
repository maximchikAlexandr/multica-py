from __future__ import annotations

import datetime
import pathlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal, cast

import msgspec

from multica_py.enums import IssueStatus, MetadataValueType, ProjectStatus
from multica_py.models.agents import Agent, AgentCreateRequest, AgentUpdateRequest
from multica_py.models.autopilots import Autopilot, AutopilotRun
from multica_py.models.issue_activity import (
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
    User,
)
from multica_py.models.workspaces import Workspace, WorkspaceMember

_NESTED_RESOURCE_ATTRS = {
    ("agents", "skills"): "agent_skills",
    ("issues", "comments"): "issue_comments",
    ("issues", "labels"): "issue_labels",
    ("issues", "metadata"): "issue_metadata",
    ("issues", "subscribers"): "issue_subscribers",
    ("autopilots", "triggers"): "autopilot_triggers",
    ("projects", "resources"): "project_resources",
    ("skills", "files"): "skill_files",
}

_SPAWN_SDK_METHODS = frozenset(
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
    sdk_method: str, expected_argv: tuple[str, ...]
) -> Literal["run_bytes", "run_text", "spawn"]:
    if sdk_method in _SPAWN_SDK_METHODS:
        return "spawn"
    if len(expected_argv) >= 2 and expected_argv[-2:] == ("--output", "json"):
        return "run_bytes"
    return "run_text"


@dataclass(frozen=True)
class ArgvSpec:
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
) -> ArgvSpec:
    derived_resource, derived_method = _derive_resource(sdk_method)
    return ArgvSpec(
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
class DecodeSpec:
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
) -> DecodeSpec:
    derived_resource, derived_method = _derive_resource(sdk_method)
    return DecodeSpec(
        resource_attr=resource_attr or derived_resource,
        method=method or derived_method,
        args=args,
        stdout=stdout,
        check=check,
        id=id or f"{sdk_method}.decode",
    )


AG = msgspec.json.encode(Agent(id="a1", name="n"))
AP = msgspec.json.encode(Autopilot(id="a1", name="AP"))
APRUN = msgspec.json.encode(AutopilotRun(id="r1", status="running"))
AR = msgspec.json.encode(AttachmentResult(id="a1", filename="f.txt"))
CMT_FLAT = msgspec.json.encode([{"id": "c1", "content": "hello"}])
CMT_THREAD = msgspec.json.encode([{"id": "c1", "content": "reply", "parent_id": "th_1"}])
CMT_RECENT = msgspec.json.encode(
    [{"id": "th_1", "comments": [{"id": "c1", "content": "root comment"}], "resolved": False}]
)
LBL = msgspec.json.encode([{"id": "lbl_1", "name": "bug", "color": "#ff0000"}])
META = msgspec.json.encode([MetadataEntry(key="priority", value="high")])
REPO = msgspec.json.encode(Repository(id="r1", name="repo1"))
RT = msgspec.json.encode(RuntimeDefinition(id="r1", name="py3"))
SK = msgspec.json.encode(Skill(id="s1", name="sk"))


_PROJECT_RESOURCE_RECORD = {
    "id": "res_001",
    "project_id": "pr_001",
    "resource_type": "local_directory",
    "resource_ref": {
        "local_path": "/tmp/sandbox",
        "daemon_id": "daemon-001",
        "label": "main",
    },
}
_LOCAL_DIR = pathlib.Path("/tmp/sandbox").resolve()

# fmt: off
ARGV_CASES: tuple[ArgvSpec, ...] = (
    A("agents.list", ("agent", "list", "--output", "json"), stdout=b"[]"),
    A("agents.get", ("agent", "get", "a1", "--output", "json"),
        stdout=AG, args=("a1",),
    ),
    A("agents.skills.list", ("agent", "skill", "list", "a1", "--output", "json"),
        stdout=b"[]", args=("a1",),
    ),
    A("agents.create", ("agent", "create", "--name", "my-agent", "--output", "json"),
        stdout=AG, args=(AgentCreateRequest(name="my-agent"),),
    ),
    A("agents.create", ("agent", "create", "--name", "my-agent", "--description", "desc", "--output", "json"),
        stdout=AG, args=(AgentCreateRequest(name="my-agent", description="desc"),),
    ),
    A("agents.create", ("agent", "create", "--name", "my-agent", "--runtime-id", "rt_001", "--output", "json"),
        stdout=AG, args=(AgentCreateRequest(name="my-agent", runtime_id="rt_001"),),
    ),
    A("agents.create", ("agent", "create", "--name", "my-agent", "--runtime-id", "rt_001", "--model", "multica-test/fake", "--output", "json"),
        stdout=AG, args=(AgentCreateRequest(name="my-agent", runtime_id="rt_001", model="multica-test/fake"),),
    ),
    A("agents.update", ("agent", "update", "a1", "--output", "json"),
        stdout=AG, args=("a1", AgentUpdateRequest()),
    ),
    A("agents.update", ("agent", "update", "a1", "--name", "new", "--output", "json"),
        stdout=AG, args=("a1", AgentUpdateRequest(name="new")),
    ),
    A("agents.archive", ("agent", "archive", "a1"), args=("a1",)),
    A("agents.restore", ("agent", "restore", "a1"), args=("a1",)),
    A("agents.tasks", ("agent", "tasks", "a1", "--output", "json"), stdout=b"[]", args=("a1",)),
    A("agents.upload_avatar", ("agent", "avatar", "upload", "a1", "--image", "/path/image.png"),
        args=("a1", "/path/image.png"),
    ),
    A("attachments.list", ("attachment", "list", "i1", "--output", "json"),
        stdout=b"[]", args=("i1",),
    ),
    A("attachments.upload", ("attachment", "upload", "i1", "--file", "/p/f.txt", "--output", "json"),
        stdout=AR, args=("i1", "/p/f.txt"),
    ),
    A("attachments.download", ("attachment", "download", "a1", "--output", "/out"),
        args=("a1", "/out"),
    ),
    A("autopilots.list", ("autopilot", "list", "--output", "json"), stdout=b"[]"),
    A("autopilots.get", ("autopilot", "get", "a1", "--output", "json"), stdout=AP, args=("a1",)),
    A("autopilots.create", ("autopilot", "create", "--name", "my-ap", "--output", "json"),
        stdout=AP, args=("my-ap",),
    ),
    A("autopilots.update", ("autopilot", "update", "a1", "--name", "new", "--output", "json"),
        stdout=AP, args=("a1",), kwargs={"name": "new"},
    ),
    A("autopilots.update", ("autopilot", "update", "a1", "--enabled", "true", "--output", "json"),
        stdout=AP, args=("a1",), kwargs={"enabled": True},
    ),
    A("autopilots.update", ("autopilot", "update", "a1", "--name", "n", "--enabled", "false", "--output", "json"),
        stdout=AP, args=("a1",), kwargs={"name": "n", "enabled": False},
    ),
    A("autopilots.delete", ("autopilot", "delete", "a1"), args=("a1",)),
    A("autopilots.run", ("autopilot", "run", "a1", "--output", "json"), stdout=APRUN, args=("a1",)),
    A("autopilots.history", ("autopilot", "history", "a1", "--output", "json"),
        stdout=b"[]", args=("a1",),
    ),
    A("autopilots.get_run", ("autopilot", "run", "get", "r1", "--output", "json"),
        stdout=APRUN, args=("r1",),
    ),
    A("configuration.show", ("config", "show")),
    A("configuration.get", ("config", "get", "key"), args=("key",)),
    A("configuration.set", ("config", "set", "key", "val"), args=("key", "val")),
    A("issues.comments.list", ("issue", "comment", "list", "iss_1", "--before", "cur_1", "--limit", "50", "--since", "2026-07-12T10:00:00+00:00", "--output", "json"),
        stdout=CMT_FLAT,
        args=(
            CommentListFlatRequest(
                issue_id="iss_1",
                cursor="cur_1",
                limit=50,
                since=datetime.datetime(2026, 7, 12, 10, 0, tzinfo=datetime.UTC),
            ),
        ),
        method="list_flat",
        transport="run_text",
        id="issues.comments.list.flat",
    ),
    A("issues.comments.list", ("issue", "comment", "list", "iss_1", "--thread", "th_1", "--tail", "10", "--output", "json"),
        stdout=CMT_THREAD, args=(CommentListThreadRequest(issue_id="iss_1", thread_id="th_1", limit=10),),
        method="list_thread", transport="run_text", id="issues.comments.list.thread",
    ),
    A("issues.comments.list", ("issue", "comment", "list", "iss_1", "--recent", "5", "--output", "json"),
        stdout=CMT_RECENT, args=(CommentListRecentRequest(issue_id="iss_1", limit=5),), method="list_recent",
        transport="run_text", id="issues.comments.list.recent-limit",
    ),
    A("issues.comments.list", ("issue", "comment", "list", "iss_1", "--recent", "10", "--output", "json"),
        stdout=b"[]", args=(CommentListRecentRequest(issue_id="iss_1"),), method="list_recent",
        transport="run_text", id="issues.comments.list.recent-default",
    ),
    A("issues.labels.add", ("issue", "label", "add", "iss_1", "lbl_1", "--output", "json"),
        stdout=LBL, args=("iss_1", "lbl_1"),
    ),
    A("issues.labels.remove", ("issue", "label", "remove", "iss_1", "lbl_1", "--output", "json"),
        stdout=b"[]", args=("iss_1", "lbl_1"),
    ),
    A("issues.labels.list", ("issue", "label", "list", "iss_1", "--output", "json"),
        stdout=msgspec.json.encode([Label(id="lbl_1", name="bug", color="#ff0000")]), args=("iss_1",),
    ),
    A("issues.metadata.set", ("issue", "metadata", "set", "iss_1", "--key", "flag", "--value", "true", "--type", "boolean", "--output", "json"),
        stdout=msgspec.json.encode(MetadataEntry(key="flag", value=True)), args=("iss_1", "flag", True),
    ),
    A("issues.metadata.set", ("issue", "metadata", "set", "iss_1", "--key", "answer", "--value", "42", "--type", "integer", "--output", "json"),
        stdout=msgspec.json.encode(MetadataEntry(key="answer", value="42")),
        args=(
            MetadataSetRequest(
                issue_id="iss_1",
                key="answer",
                value="42",
                value_type=MetadataValueType.integer,
            ),
        ),
        method="set_typed",
        id="issues.metadata.set.typed",
    ),
    A("issues.metadata.list", ("issue", "metadata", "list", "iss_1", "--metadata", "priority=high", "--metadata-type", "string", "--metadata", "visible=true", "--metadata-type", "boolean", "--cursor", "cur_1", "--limit", "25", "--output", "json"),
        stdout=META,
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
        method="query",
        transport="run_text",
    ),
    A("issues.metadata.get", ("issue", "metadata", "get", "iss_1", "--key", "flag", "--output", "json"),
        stdout=msgspec.json.encode(MetadataEntry(key="flag", value=True)), args=("iss_1", "flag"),
    ),
    A("issues.metadata.delete", ("issue", "metadata", "delete", "iss_1", "--key", "flag"),
        args=("iss_1", "flag"),
    ),
    A("issues.subscribers.list", ("issue", "subscriber", "list", "iss_1", "--output", "json"),
        stdout=b"[]", args=("iss_1",),
    ),
    A("issues.subscribers.add", ("issue", "subscriber", "add", "iss_1", "--user-id", "usr_1"), stdout=b"",
        args=("iss_1", "usr_1"),
    ),
    A("issues.subscribers.remove", ("issue", "subscriber", "remove", "iss_1", "--user-id", "usr_1"),
        args=("iss_1", "usr_1"),
    ),
    A("issues.list", ("issue", "list", "--output", "json"),
        stdout=msgspec.json.encode({"issues": []}),
    ),
    A("issues.get", ("issue", "get", "iss_1", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Test", "status": "todo"}), args=("iss_1",),
    ),
    A("issues.create", ("issue", "create", "--title", "Test", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Test", "status": "todo"}), args=(IssueCreateRequest(title="Test"),),
    ),
    A("issues.create", ("issue", "create", "--title", "Test", "--description", "hello", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Test", "status": "todo"}), args=(IssueCreateRequest(title="Test", description_input=InlineDescription(text="hello")),),
    ),
    A("issues.create", ("issue", "create", "--title", "Test", "--description-file", "/nonexistent/desc.txt", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Test", "status": "todo"}),
        args=(
            IssueCreateRequest(
                title="Test", description_input=FileDescription(path="/nonexistent/desc.txt")
            ),
        ),
    ),
    A("issues.create", ("issue", "create", "--title", "Test", "--description-stdin", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Test", "status": "todo"}), args=(IssueCreateRequest(title="Test", description_input=StdinDescription()),),
    ),
    A("issues.create", ("issue", "create", "--title", "Test", "--project", "pr_001", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Test", "status": "todo"}), args=(IssueCreateRequest(title="Test", project_id="pr_001"),),
    ),
    A("projects.list", ("project", "list", "--output", "json"), stdout=b"[]"),
    A("projects.get", ("project", "get", "pr_1", "--output", "json"),
        stdout=msgspec.json.encode({"id": "pr_1", "title": "Alpha", "status": "planned"}), args=("pr_1",),
    ),
    A("projects.create", ("project", "create", "--title", "Alpha", "--output", "json"),
        stdout=msgspec.json.encode({"id": "pr_1", "title": "Alpha", "status": "planned"}), args=(ProjectCreateRequest(name="Alpha"),),
    ),
    A("projects.create", ("project", "create", "--title", "Alpha", "--description", "desc", "--output", "json"),
        stdout=msgspec.json.encode({"id": "pr_1", "title": "Alpha", "status": "planned"}), args=(ProjectCreateRequest(name="Alpha", description="desc"),),
    ),
    A("projects.update", ("project", "update", "pr_1", "--output", "json"),
        stdout=msgspec.json.encode({"id": "pr_1", "title": "Alpha", "status": "planned"}), args=("pr_1", ProjectUpdateRequest()),
    ),
    A("projects.update", ("project", "update", "pr_1", "--title", "only-title", "--output", "json"),
        stdout=msgspec.json.encode({"id": "pr_1", "title": "New", "status": "planned"}), args=("pr_1", ProjectUpdateRequest(name="only-title")),
    ),
    A("projects.update", ("project", "update", "pr_1", "--description", "", "--output", "json"),
        stdout=msgspec.json.encode({"id": "pr_1", "title": "Alpha", "status": "planned"}), args=("pr_1", ProjectUpdateRequest(description="")),
    ),
    A("projects.update", ("project", "update", "pr_1", "--description", "new", "--output", "json"),
        stdout=msgspec.json.encode({"id": "pr_1", "title": "Alpha", "status": "planned"}), args=("pr_1", ProjectUpdateRequest(description="new")),
    ),
    A("projects.delete", ("project", "delete", "pr_1"), args=("pr_1",)),
    A("projects.resources.list", ("project", "resource", "list", "pr_001", "--output", "json"),
        stdout=msgspec.json.encode([_PROJECT_RESOURCE_RECORD]), args=("pr_001",),
    ),
    A("projects.resources.add_local_directory",
        ("project", "resource", "add", "pr_001", "--type", "local_directory", "--local-path", str(_LOCAL_DIR), "--daemon-id", "daemon-001", "--output", "json"),
        stdout=msgspec.json.encode(_PROJECT_RESOURCE_RECORD), args=("pr_001", ProjectResourceAddLocalDirectoryRequest(local_path="/tmp/sandbox", daemon_id="daemon-001")),
    ),
    A("projects.resources.add_local_directory",
        ("project", "resource", "add", "pr_001", "--type", "local_directory", "--local-path", str(_LOCAL_DIR), "--daemon-id", "daemon-001", "--ref-label", "main", "--output", "json"),
        stdout=msgspec.json.encode(_PROJECT_RESOURCE_RECORD), args=("pr_001", ProjectResourceAddLocalDirectoryRequest(local_path="/tmp/sandbox", daemon_id="daemon-001", label="main")),
        id="projects.resources.add_local_directory.label",
    ),
    A("projects.resources.update_local_directory",
        ("project", "resource", "update", "pr_001", "res_001", "--local-path", str(_LOCAL_DIR), "--output", "json"),
        stdout=msgspec.json.encode(_PROJECT_RESOURCE_RECORD), args=("pr_001", "res_001", ProjectResourceUpdateLocalDirectoryRequest(local_path="/tmp/sandbox")),
    ),
    A("projects.resources.remove", ("project", "resource", "remove", "pr_001", "res_001"), args=("pr_001", "res_001")),
    A("repositories.list", ("repo", "list", "--output", "json"), stdout=b"[]"),
    A("repositories.get", ("repo", "get", "r1", "--output", "json"), stdout=REPO, args=("r1",)),
    A("repositories.checkout", ("repo", "checkout", "r1", "--branch", "main", "--output", "json"),
        stdout=msgspec.json.encode(RepositoryCheckoutResult(path="/p", branch="main", success=True)),
        args=("r1", "main"),
    ),
    A("runtimes.list", ("runtime", "list", "--output", "json"), stdout=b"[]"),
    A("runtimes.get", ("runtime", "get", "r1", "--output", "json"), stdout=RT, args=("r1",)),
    A("skills.list", ("skill", "list", "--output", "json"), stdout=b"[]"),
    A("skills.get", ("skill", "get", "s1", "--output", "json"), stdout=SK, args=("s1",)),
    A("skills.create", ("skill", "create", "--name", "my-sk", "--output", "json"),
        stdout=SK, args=(SkillCreateRequest(name="my-sk"),),
    ),
    A("skills.create", ("skill", "create", "--name", "my-sk", "--description", "desc", "--output", "json"),
        stdout=SK, args=(SkillCreateRequest(name="my-sk", description="desc"),),
    ),
    A("skills.update", ("skill", "update", "s1", "--output", "json"),
        stdout=SK, args=("s1", SkillUpdateRequest()),
    ),
    A("skills.update", ("skill", "update", "s1", "--name", "new", "--output", "json"),
        stdout=SK, args=("s1", SkillUpdateRequest(name="new")),
    ),
    A("skills.delete", ("skill", "delete", "s1"), args=("s1",)),
    A("skills.import_from_url", ("skill", "import", "--url", "https://x.com", "--output", "json"),
        stdout=SK, args=("https://x.com",),
    ),
    A("squads.list", ("squad", "list", "--output", "json"), stdout=b"[]"),
    A("squads.get", ("squad", "get", "s1", "--output", "json"),
        stdout=msgspec.json.encode(Squad(id="s1", name="S")), args=("s1",),
    ),
    A("users.list", ("user", "list", "--output", "json"), stdout=b"[]"),
    A("users.get", ("user", "get", "u1", "--output", "json"),
        stdout=msgspec.json.encode(User(id="u1", name="Alice")), args=("u1",),
    ),
    A("auth.login", ("auth", "login", "--token", "secret-token"),
        stdout=b"Login successful", args=("secret-token",),
    ),
    A("auth.status", ("auth", "status", "--output", "json"),
        stdout=msgspec.json.encode(AuthenticationStatus(authenticated=True, user_id="usr_001", token_type="bearer")),
    ),
    A("auth.logout", ("auth", "logout", "--output", "json"),
        stdout=msgspec.json.encode(AuthenticationStatus(authenticated=False, user_id=None, token_type=None)),
    ),
    A("daemon.status", ("daemon", "status", "--output", "json"),
        stdout=msgspec.json.encode(DaemonStatus(running=True, pid=12345, uptime=3600.0)),
    ),
    A("issues.deprioritize", ("issue", "deprioritize", "iss_001"),
        stdout=b"Issue iss_001 deprioritized\n", args=("iss_001",),
    ),
    A("issues.set_status", ("issue", "status", "iss_001", "done", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_001", "title": "Test issue", "status": "done"}), args=("iss_001", IssueStatus.done),
    ),
    A("labels.list", ("label", "list", "--output", "json"),
        stdout=msgspec.json.encode([Label(id="lbl_001", name="bug", color="red")]),
    ),
    A("labels.get", ("label", "get", "lbl_001", "--output", "json"),
        stdout=msgspec.json.encode(Label(id="lbl_001", name="bug", color="red")), args=("lbl_001",),
    ),
    A("labels.create", ("label", "create", "--name", "bug", "--output", "json"),
        stdout=msgspec.json.encode(Label(id="lbl_001", name="bug", color="red")), args=("bug",),
    ),
    A("labels.update", ("label", "update", "lbl_001", "--name", "feature", "--output", "json"),
        stdout=msgspec.json.encode(Label(id="lbl_001", name="feature", color="red")), args=("lbl_001",), kwargs={"name": "feature"},
    ),
    A("labels.delete", ("label", "delete", "lbl_001"), args=("lbl_001",)),
    A("projects.set_status", ("project", "status", "pr_001", "completed", "--output", "json"),
        stdout=msgspec.json.encode({"id": "pr_001", "title": "Project Alpha", "status": "completed"}),
        args=("pr_001", ProjectStatus.completed),
    ),
    A("workspaces.list", ("workspace", "list", "--output", "json"),
        stdout=msgspec.json.encode([Workspace(id="ws_001", name="Main Workspace")]),
    ),
    A("workspaces.get", ("workspace", "get", "ws_001", "--output", "json"),
        stdout=msgspec.json.encode(Workspace(id="ws_001", name="Main Workspace")), args=("ws_001",),
    ),
    A("issues.update", ("issue", "update", "iss_1", "--title", "Updated", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Updated", "status": "todo"}), args=("iss_1", IssueUpdateRequest(title="Updated")),
    ),
    A("issues.update", ("issue", "update", "iss_1", "--project", "pr_001", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Updated", "status": "todo"}), args=("iss_1", IssueUpdateRequest(project_id="pr_001")),
        id="issues.update.project",
    ),
    A("issues.assign", ("issue", "assign", "iss_1", "--to-id", "usr_1", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Test", "status": "todo"}), args=(IssueAssignmentRequest(issue_id="iss_1", member_id="usr_1"),),
    ),
    A("issues.reorder", ("issue", "reorder", "iss_1", "--top", "--output", "json"),
        stdout=msgspec.json.encode({"id": "iss_1", "title": "Test", "status": "todo"}), args=(IssueReorderRequest(issue_id="iss_1", top=True),),
    ),
    A("issues.search", ("issue", "search", "bug", "--output", "json"), stdout=b"[]", args=("bug",)),
    A("issues.children", ("issue", "children", "iss_1", "--output", "json"),
        stdout=msgspec.json.encode([IssueChildStageGroup(name="todo", count=1)]), args=("iss_1",),
    ),
    A("issues.pull_requests", ("issue", "pull-requests", "iss_1", "--output", "json"),
        stdout=msgspec.json.encode([LinkedPullRequest(url="https://example.com/pr/1")]), args=("iss_1",),
    ),
    A("issues.runs", ("issue", "runs", "iss_1", "--output", "json"),
        stdout=msgspec.json.encode([TaskRun(id="run_1", status="done")]), args=("iss_1",),
    ),
    A("issues.usage", ("issue", "usage", "iss_1", "--output", "json"),
        stdout=msgspec.json.encode(IssueUsage(total_runs=3)), args=("iss_1",),
    ),
    A("issues.comments.add", ("issue", "comment", "add", "iss_1", "--content", "hello", "--output", "json"),
        stdout=msgspec.json.encode({"id": "cmt_1", "content": "hello"}), args=("iss_1", "hello"),
    ),
    A("issues.comments.delete", ("issue", "comment", "delete", "cmt_1"), args=("cmt_1",)),
    A("issues.comments.resolve", ("issue", "comment", "resolve", "thr_1"), args=("thr_1",)),
    A("issues.comments.unresolve", ("issue", "comment", "unresolve", "thr_1"), args=("thr_1",)),
    A("workspaces.members", ("workspace", "member", "list", "ws_001", "--output", "json"),
        stdout=msgspec.json.encode([WorkspaceMember(id="usr_1", name="Alice")]), args=("ws_001",),
    ),
    A("autopilots.triggers.list", ("autopilot", "trigger", "list", "ap_1", "--output", "json"),
        stdout=msgspec.json.encode([{"id": "tr_1", "type": "webhook", "config": {}}]), args=("ap_1",),
    ),
    A("autopilots.triggers.delete", ("autopilot", "trigger", "delete", "ap_1", "--trigger-id", "tr_1"),
        args=("ap_1", "tr_1"),
    ),
    A("skills.files.list", ("skill", "file", "list", "sk_1", "--output", "json"),
        stdout=msgspec.json.encode([SkillFile(id="f_1", path="SKILL.md")]), args=("sk_1",),
    ),
    A("skills.files.delete", ("skill", "file", "delete", "sk_1", "--file-id", "f_1"),
        args=("sk_1", "f_1"),
    ),
    A("daemon.disk_usage", ("daemon", "disk-usage", "--output", "json"),
        stdout=msgspec.json.encode([DaemonDiskUsageEntry(path="/tmp", size_bytes=1024)]),
    ),
    A("agents.skills.set", ("agent", "skill", "set", "ag_001", "--skill-id", "sk_001"),
        args=("ag_001", ("sk_001",)),
    ),
    A("autopilots.triggers.create", ("autopilot", "trigger", "create", "ap_001", "--type", "webhook", "--config", "url=https://example.com", "--output", "json"),
        stdout=msgspec.json.encode({"id": "tr_001", "type": "webhook", "config": {"url": "https://example.com"}}),
        args=("ap_001", "webhook"), kwargs={"config": {"url": "https://example.com"}},
    ),
    A("daemon.start", ("daemon", "start")),
    A("daemon.stop", ("daemon", "stop", "--output", "json"),
        stdout=msgspec.json.encode(DaemonStatus(running=False)),
    ),
    A("daemon.restart", ("daemon", "restart", "--output", "json"),
        stdout=msgspec.json.encode(DaemonStatus(running=True, pid=12345)),
    ),
    A("daemon.logs", ("daemon", "logs")),
    A("issues.cancel_task", ("issue", "cancel-task", "iss_001", "--run-id", "run_001"),
        args=("iss_001", "run_001"),
    ),
    A("issues.comments.reply", ("issue", "comment", "add", "iss_001", "--content", "reply text", "--parent", "th_001", "--output", "json"),
        stdout=msgspec.json.encode({"id": "cmt_002", "content": "reply text", "parent_id": "th_001"}),
        args=("iss_001", "th_001", "reply text"),
    ),
    A("issues.rerun", ("issue", "rerun", "iss_001", "--run-id", "run_001"),
        args=("iss_001", "run_001"),
    ),
    A("issues.run_messages", ("issue", "run-messages", "iss_001", "--run-id", "run_001", "--output", "json"),
        stdout=msgspec.json.encode([RunMessage(id="msg_001", run_id="run_001", role="assistant", content="hello")]),
        args=("iss_001", "run_001"),
    ),
    A("maintenance.update", ("update",)),
    A("setup.cloud", ("setup", "cloud")),
    A("setup.self_host", ("setup", "self-host", "--url", "https://example.com"),
        args=("https://example.com",),
    ),
    A("skills.files.upsert", ("skill", "file", "upsert", "sk_001", "--path", "SKILL.md", "--content", "# content", "--output", "json"),
        stdout=msgspec.json.encode(SkillFile(id="f_001", path="SKILL.md", content="# content")),
        args=("sk_001", "SKILL.md", "# content"),
    ),
    A("workspaces.switch", ("workspace", "switch", "ws_001"), args=("ws_001",)),
    A("workspaces.watch", ("workspace", "watch", "ws_001"), args=("ws_001",)),
    A("workspaces.unwatch", ("workspace", "unwatch", "ws_001"), args=("ws_001",)),
    A("maintenance.version", ("version", "--output", "json"),
        stdout=msgspec.json.encode(MaintenanceVersion(version="1.0.0", commit="abc", build_date="2026-01-01")),
    ),
)
# fmt: on


# fmt: off
_CHECKS: dict[str, Callable[[object], None]] = {
    "agents.list": cast("Callable[[object], None]", lambda r: len(r) == 2 and r[0].id == "a1" and r[1].name == "Bob"),
    "agents.get": cast("Callable[[object], None]", lambda r: r.id == "a1" and r.description == "desc"),
    "agents.tasks": cast("Callable[[object], None]", lambda r: len(r) == 1 and r[0].id == "t1"),
    "attachments.list": cast("Callable[[object], None]", lambda r: len(r) == 1 and r[0].filename == "x"),
    "attachments.upload": cast("Callable[[object], None]", lambda r: r.id == "a1"),
    "autopilots.list": cast("Callable[[object], None]", lambda r: len(r) == 2 and r[0].name == "X"),
    "autopilots.get_run": cast("Callable[[object], None]", lambda r: r.id == "r1" and r.status == "running"),
    "maintenance.version": cast("Callable[[object], None]", lambda r: r.version == "1.0.0" and r.commit == "abc"),
    "repositories.list": cast("Callable[[object], None]", lambda r: len(r) == 2),
    "repositories.checkout": cast("Callable[[object], None]", lambda r: r.success is True),
    "runtimes.list": cast("Callable[[object], None]", lambda r: r[0].name == "py3"),
    "skills.list": cast("Callable[[object], None]", lambda r: len(r) == 2 and r[0].name == "S1"),
    "squads.list": cast("Callable[[object], None]", lambda r: r[0].member_count == 3),
    "users.list": cast("Callable[[object], None]", lambda r: len(r) == 2),
    "projects.resources.list": cast("Callable[[object], None]", lambda r: len(r) == 1 and r[0].resource_type == "local_directory" and r[0].resource_ref.daemon_id == "daemon-001"),
    "projects.resources.add_local_directory": cast("Callable[[object], None]", lambda r: r.id == "res_001" and r.resource_ref.local_path.endswith("sandbox")),
}
# fmt: on


# fmt: off
DECODE_CASES: tuple[DecodeSpec, ...] = (
    D("agents.list", msgspec.json.encode([Agent(id="a1", name="Alice"), Agent(id="a2", name="Bob")]), _CHECKS["agents.list"]),
    D("agents.get", msgspec.json.encode(Agent(id="a1", name="Alice", description="desc")), _CHECKS["agents.get"], args=("a1",)),
    D("agents.tasks", msgspec.json.encode([{"id": "t1", "status": "running", "issue_id": "i1"}]), _CHECKS["agents.tasks"], args=("a1",)),
    D("attachments.list", msgspec.json.encode([AttachmentResult(id="a1", filename="x")]), _CHECKS["attachments.list"], args=("i1",)),
    D("attachments.upload", AR, _CHECKS["attachments.upload"], args=("i1", "/f")),
    D("autopilots.list", msgspec.json.encode([Autopilot(id="a1", name="X"), Autopilot(id="a2", name="Y")]), _CHECKS["autopilots.list"]),
    D("autopilots.get_run", APRUN, _CHECKS["autopilots.get_run"], args=("r1",)),
    D("maintenance.version", msgspec.json.encode(MaintenanceVersion(version="1.0.0", commit="abc", build_date="2026-01-01")), _CHECKS["maintenance.version"]),
    D("repositories.list", msgspec.json.encode([Repository(id="r1", name="R1"), Repository(id="r2", name="R2")]), _CHECKS["repositories.list"]),
    D("repositories.checkout", msgspec.json.encode(RepositoryCheckoutResult(path="/p", branch="main", success=True)), _CHECKS["repositories.checkout"], args=("r1", "main")),
    D("runtimes.list", msgspec.json.encode([{"id": "r1", "name": "py3"}]), _CHECKS["runtimes.list"]),
    D("skills.list", msgspec.json.encode([Skill(id="s1", name="S1"), Skill(id="s2", name="S2")]), _CHECKS["skills.list"]),
    D("squads.list", msgspec.json.encode([Squad(id="s1", name="S1", member_count=3)]), _CHECKS["squads.list"]),
    D("users.list", msgspec.json.encode([User(id="u1", name="Alice"), User(id="u2", name="Bob")]), _CHECKS["users.list"]),
    D("projects.resources.list", msgspec.json.encode([{
            "id": "res_001", "project_id": "pr_001", "resource_type": "local_directory",
            "resource_ref": {"local_path": "/tmp/sandbox", "daemon_id": "daemon-001"},
        }]),
        _CHECKS["projects.resources.list"], args=("pr_001",),
    ),
    D("projects.resources.add_local_directory", msgspec.json.encode({
            "id": "res_001", "project_id": "pr_001", "resource_type": "local_directory",
            "resource_ref": {"local_path": "/tmp/sandbox", "daemon_id": "daemon-001"},
        }),
        _CHECKS["projects.resources.add_local_directory"],
        args=("pr_001", ProjectResourceAddLocalDirectoryRequest(local_path="/tmp/sandbox", daemon_id="daemon-001")),
    ),
)
# fmt: on
