"""Closed v3 approved-contract loader and semantic validator.

The loader deliberately uses only the approved JSON document.  Evidence and
transient projections are not accepted as inputs to this module.
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import keyword
import pathlib
import re
from dataclasses import dataclass
from typing import cast


class ContractError(ValueError):
    """Raised when an approved contract is not a closed valid v3 document."""


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
_PYTHON_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$", re.ASCII)
_VECTOR_ID = re.compile(
    r"^generated:(?P<operation>[a-z0-9_.]+):(?P<entrypoint>[a-z][a-z0-9_]*):"
    r"(?P<kind>canonical|variant:(?P<ordinal>[0-9]{2}))$"
)
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_TAG_KINDS = frozenset(
    {
        "primitive",
        "datetime",
        "enum",
        "path",
        "unset",
        "inline_description",
        "file_description",
        "stdin_description",
        "comment_cursor",
        "list",
        "request",
    }
)
_ENUM_TYPES = frozenset(
    {"IssueStatus", "ProjectStatus", "IssueSort", "SortDirection", "AutopilotExecutionMode"}
)
_REQUEST_TYPES = frozenset(
    {
        "CommentListFlatRequest",
        "CommentListThreadRequest",
        "CommentListRecentRequest",
        "IssueCreateRequest",
        "IssueListFilter",
        "ProjectCreateRequest",
        "ProjectUpdateRequest",
        "ProjectResourceAddLocalDirectoryRequest",
        "ProjectResourceUpdateLocalDirectoryRequest",
    }
)
_DECODED_TYPES = frozenset(
    {
        "builtins.tuple",
        "multica_py.models.issue_activity.Comment",
        "multica_py.models.issues.Issue",
        "multica_py.models.projects.Project",
        "multica_py.models.project_resources.ProjectResourceRecord",
        "multica_py.models.autopilots.Autopilot",
        "multica_py.models.autopilots.AutopilotListPage",
        "multica_py.models.autopilots.AutopilotRun",
        "multica_py.models.autopilots.AutopilotRunListPage",
        "multica_py.models.issues.IssueListPage",
        "multica_py.models.agents.Agent",
        "multica_py.models.agents.AgentSkill",
        "multica_py.models.agents.AgentTask",
        "multica_py.models.attachments.AttachmentResult",
        "multica_py.models.autopilots.AutopilotTrigger",
        "multica_py.models.issue_activity.CommentThread",
        "multica_py.models.issue_activity.LinkedPullRequest",
        "multica_py.models.issue_activity.MetadataEntry",
        "multica_py.models.issue_activity.RunMessage",
        "multica_py.models.issue_activity.Subscriber",
        "multica_py.models.issue_activity.TaskRun",
        "multica_py.models.issues.IssueChildStageGroup",
        "multica_py.models.skills.Skill",
        "multica_py.models.skills.SkillFile",
        "multica_py.models.squads.Squad",
        "multica_py.models.squads.SquadMember",
        "multica_py.models.repositories.RepositoryCheckoutResult",
        "multica_py.models.repositories.RepositoryRecord",
        "multica_py.models.runtimes.RuntimeActivity",
        "multica_py.models.runtimes.RuntimeDefinition",
        "multica_py.models.runtimes.RuntimeUsage",
        "multica_py.models.users.UserProfile",
        "multica_py.models.workspaces.Workspace",
        "multica_py.models.workspaces.WorkspaceMember",
    }
)
_BODY_KINDS = frozenset(
    {"nonblank", "nonnegative_int", "positive_int", "project_update", "resource_update"}
)
_VALIDATOR_ENUM_IDS = frozenset({"IssueStatus", "ProjectStatus", "AutopilotExecutionMode"})
_REQUEST_FIELD_ORDER = {
    "CommentListFlatRequest": ("issue_id", "since"),
    "CommentListThreadRequest": ("issue_id", "thread_id", "cursor", "limit"),
    "CommentListRecentRequest": ("issue_id", "limit"),
    "IssueCreateRequest": ("title", "description_input", "project_id", "label_ids"),
    "IssueListFilter": (),
    "ProjectCreateRequest": ("name", "description"),
    "ProjectUpdateRequest": ("name", "description"),
    "ProjectResourceAddLocalDirectoryRequest": ("local_path", "daemon_id", "label"),
    "ProjectResourceUpdateLocalDirectoryRequest": ("local_path",),
}
_AUXILIARY_CATALOG_KEYS = {
    "types": frozenset(
        {
            "agent",
            "agent_skills",
            "agent_tasks",
            "agent_wire",
            "attachment_result",
            "attachment_result_wire",
            "autopilot",
            "autopilot_list_page",
            "autopilot_list_page_wire",
            "autopilot_run",
            "autopilot_run_list_page",
            "autopilot_run_list_page_wire",
            "autopilot_run_wire",
            "autopilot_subscriber",
            "autopilot_subscriber_wire",
            "autopilot_trigger",
            "autopilot_trigger_create",
            "autopilot_trigger_update",
            "autopilot_trigger_wire",
            "autopilot_triggers",
            "autopilot_triggers_wire",
            "autopilot_wire",
            "comment",
            "comment_page",
            "comment_thread_page",
            "comment_threads_wire",
            "comment_wire",
            "comments",
            "comments_wire",
            "issue",
            "issue_children_result_wire",
            "issue_list_page",
            "issue_list_page_wire",
            "issue_pull_requests_result_wire",
            "issue_summaries",
            "issue_wire",
            "labels",
            "labels_wire",
            "linked_pull_request",
            "linked_pull_requests",
            "metadata_entries",
            "metadata_entries_wire",
            "none",
            "path",
            "project",
            "project_resource",
            "project_resource_wire",
            "project_resources",
            "project_resources_wire",
            "project_wire",
            "repository_mutation_result",
            "repository_mutation_result_wire",
            "repository_record",
            "repository_record_wire",
            "repository_records",
            "repository_records_wire",
            "run_message",
            "run_messages",
            "run_messages_wire",
            "runtime_activity",
            "runtime_activity_wire",
            "runtime_definition",
            "runtime_definition_wire",
            "runtime_definitions",
            "runtime_definitions_wire",
            "runtime_usage",
            "runtime_usage_wire",
            "runtime_update_result",
            "runtime_update_result_wire",
            "skill",
            "skill_file",
            "skill_files",
            "skill_files_wire",
            "skill_wire",
            "squad",
            "squad_member",
            "squad_members",
            "squad_members_wire",
            "squad_wire",
            "subscriber",
            "subscribers",
            "subscribers_wire",
            "task_run",
            "task_runs",
            "task_runs_wire",
            "user_profile",
            "user_profile_wire",
            "workspace",
            "workspace_member",
            "workspace_members",
            "workspace_members_wire",
            "workspace_wire",
        }
    ),
    "signatures": frozenset(
        {
            "agent_avatar",
            "agent_get",
            "agent_list",
            "agent_skills_list",
            "agent_skills_set",
            "agent_tasks",
            "attachment_download",
            "attachment_upload",
            "autopilot_create",
            "autopilot_delete",
            "autopilot_get",
            "autopilot_history",
            "autopilot_list",
            "autopilot_run",
            "autopilot_trigger",
            "autopilot_trigger_add",
            "autopilot_trigger_delete",
            "autopilot_trigger_update",
            "autopilot_update",
            "comment_add",
            "comment_delete",
            "comment_list",
            "comment_list_flat",
            "comment_list_recent",
            "comment_list_thread",
            "issue_cancel_task",
            "issue_children",
            "issue_create",
            "issue_get",
            "issue_labels_add",
            "issue_labels_list",
            "issue_labels_remove",
            "issue_list",
            "issue_metadata_delete",
            "issue_metadata_get",
            "issue_metadata_list",
            "issue_metadata_set",
            "issue_pull_requests",
            "issue_rerun",
            "issue_run_messages",
            "issue_runs",
            "issue_status",
            "issue_subscribers_add",
            "issue_subscribers_list",
            "issue_subscribers_remove",
            "label_get",
            "label_list",
            "project_create",
            "project_get",
            "project_list",
            "project_resource_add",
            "project_resource_list",
            "project_resource_remove",
            "project_resource_update",
            "project_status",
            "project_update",
            "repositories_add",
            "repositories_list",
            "repositories_remove",
            "runtime_activity",
            "runtime_delete",
            "runtime_list",
            "runtime_rename",
            "runtime_update",
            "runtime_usage",
            "skill_files_delete",
            "skill_files_list",
            "skill_files_upsert",
            "skill_get",
            "skill_list",
            "squad_get",
            "squad_list",
            "squad_members_add",
            "squad_members_list",
            "squad_members_remove",
            "user_profile_get",
            "user_profile_update",
            "workspace_get",
            "workspace_list",
            "workspace_members_list",
        }
    ),
    "decoders": frozenset(
        {
            "decode_agent",
            "decode_agent_skills",
            "decode_agent_tasks",
            "decode_attachment_result",
            "decode_autopilot",
            "decode_autopilot_list_page",
            "decode_autopilot_run",
            "decode_autopilot_run_list_page",
            "decode_autopilot_trigger",
            "decode_autopilot_triggers",
            "decode_comment",
            "decode_comment_page",
            "decode_comment_thread_page",
            "decode_comments",
            "decode_issue",
            "decode_issue_children",
            "decode_issue_list_page",
            "decode_issue_summaries",
            "decode_labels",
            "decode_linked_pull_requests",
            "decode_metadata_entries",
            "decode_none",
            "decode_path",
            "decode_project",
            "decode_project_resource",
            "decode_project_resources",
            "decode_repository_mutation_result",
            "decode_repository_records",
            "decode_run_messages",
            "decode_runtime_activity",
            "decode_runtime_definition",
            "decode_runtime_definitions",
            "decode_runtime_usage",
            "decode_runtime_update_result",
            "decode_skill",
            "decode_skill_file",
            "decode_skill_files",
            "decode_squad",
            "decode_squad_members",
            "decode_subscribers",
            "decode_task_runs",
            "decode_user_profile",
            "decode_workspace",
            "decode_workspace_members",
        }
    ),
    "validators": frozenset(
        {
            "at_least_one:name_description",
            "blank_label_omitted",
            "cursor_pair",
            "cursor_requires_limit",
            "description_exactly_one",
            "description_none_rejected",
            "direction_requires_sort",
            "empty_emits",
            "limit_nonnegative",
            "limit_positive",
            "nonblank:agent",
            "nonblank:agent_id",
            "nonblank:attachment_id",
            "nonblank:autopilot_id",
            "nonblank:body",
            "nonblank:comment_id",
            "nonblank:file_id",
            "nonblank:issue_id",
            "nonblank:key",
            "nonblank:label_id",
            "nonblank:member_id",
            "nonblank:name",
            "nonblank:path",
            "nonblank:project_id",
            "nonblank:request.daemon_id",
            "nonblank:request.local_path",
            "nonblank:request.name",
            "nonblank:request.title",
            "nonblank:resource_id",
            "nonblank:runtime",
            "nonblank:skill_id",
            "nonblank:squad_id",
            "nonblank:subscriber",
            "nonblank:task_id",
            "nonblank:task_run_id",
            "nonblank:title",
            "nonblank:trigger_id",
            "nonblank:url",
            "nonblank:user_id",
            "nonblank:workspace_id",
            "offset_nonnegative",
            "position_forbids_direction",
            "preserve_daemon_and_label",
            "strict:IssueStatus",
            "strict:ProjectStatus",
            "unset_omits",
        }
    ),
}
_VECTOR_KEYS = frozenset(
    {
        "vector_id",
        "operation_id",
        "entrypoint_id",
        "is_canonical",
        "args",
        "kwargs",
        "stdout_base64",
        "stderr",
        "exit_code",
        "transport_method",
        "expected_argv",
        "stdin_base64",
        "timeout",
        "assertion",
    }
)
_ASSERTION_KEYS = frozenset({"id", "kind", "expected"})
_GENERATED_NAMESPACE_RESERVED = frozenset(
    {
        "dataclass",
        "StrEnum",
        "TARGET_VERSION",
        "MIN_CLI_VERSION",
        "MAX_CLI_VERSION",
        "GeneratedMapping",
        "GeneratedBinding",
        "OPERATION_BINDINGS",
        "__all__",
        "annotations",
        "object",
        "str",
        "int",
        "bool",
        "isinstance",
        "ValueError",
    }
)


def _dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return cast("dict[str, object]", value)


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    return value


def _str(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{label} must be a string")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be a boolean")
    return value


def _int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{label} must be an integer")
    return value


def _exact_keys(value: dict[str, object], expected: frozenset[str], label: str) -> None:
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise ContractError(f"{label} has unknown fields: {', '.join(unknown)}")
    if missing:
        raise ContractError(f"{label} is missing fields: {', '.join(missing)}")


@dataclass(frozen=True)
class Target:
    version: str
    tag: str
    commit: str
    release_id: str
    release_provenance_ref: str


@dataclass(frozen=True)
class SourceRef:
    source_ref_id: str
    repository: str
    commit: str
    path: str
    symbol: str
    line_start: int
    line_end: int


@dataclass(frozen=True)
class TestRef:
    test_ref_id: str
    path: str
    node_id: str


@dataclass(frozen=True)
class EnumMember:
    name: str
    value: str


@dataclass(frozen=True)
class EnumDefinition:
    enum_id: str
    public_name: str
    members: tuple[EnumMember, ...]


@dataclass(frozen=True)
class ValidatorDefinition:
    validator_id: str
    name: str
    parameter_name: str
    body_kind: str


@dataclass(frozen=True)
class BindingDescriptor:
    descriptor_id: str
    operation_id: str
    entrypoint_id: str
    command: tuple[str, ...]
    mappings: tuple[tuple[str, str, str], ...]
    validator_ids: tuple[str, ...]


@dataclass(frozen=True)
class Entrypoint:
    entrypoint_id: str
    public_symbol: str
    signature_id: str
    binding_id: str
    response_id: str
    errors: str


@dataclass(frozen=True)
class Operation:
    operation_id: str
    compatibility: str
    rationale: str
    source_ref_ids: tuple[str, ...]
    test_ref_ids: tuple[str, ...]
    entrypoints: tuple[Entrypoint, ...]


@dataclass(frozen=True)
class ResultAssertion:
    assertion_id: str
    kind: str
    expected: dict[str, object]


@dataclass(frozen=True)
class TestVector:
    vector_id: str
    operation_id: str
    entrypoint_id: str
    is_canonical: bool
    args: tuple[dict[str, object], ...]
    kwargs: tuple[tuple[str, dict[str, object]], ...]
    stdout_base64: str
    stderr: str
    exit_code: int
    transport_method: str
    expected_argv: tuple[str, ...]
    stdin_base64: str | None
    timeout: float | None
    assertion: ResultAssertion


@dataclass(frozen=True)
class ContractCatalog:
    target: Target
    operations: tuple[Operation, ...]
    source_refs: tuple[SourceRef, ...]
    test_refs: tuple[TestRef, ...]
    enum_definitions: tuple[EnumDefinition, ...]
    validator_definitions: tuple[ValidatorDefinition, ...]
    binding_descriptors: tuple[BindingDescriptor, ...]
    test_vectors: tuple[TestVector, ...]
    legacy_argv_migration: dict[str, str]
    raw: dict[str, object]

    @property
    def operation_ids(self) -> frozenset[str]:
        return frozenset(item.operation_id for item in self.operations)

    @property
    def vector_by_id(self) -> dict[str, TestVector]:
        return {item.vector_id: item for item in self.test_vectors}


def _python_identifier(value: object, label: str) -> str:
    name = _str(value, label)
    if not _PYTHON_IDENTIFIER.fullmatch(name) or keyword.iskeyword(name):
        raise ContractError(f"{label} must be an ASCII non-keyword Python identifier")
    if name.startswith("__") and name.endswith("__"):
        raise ContractError(f"{label} must not be a Python magic name")
    return name


def _contract_identifier(value: object, label: str) -> str:
    name = _str(value, label)
    if not _IDENTIFIER.fullmatch(name) or keyword.iskeyword(name):
        raise ContractError(f"{label} must be a lowercase ASCII non-keyword identifier")
    return name


def _tag(value: object, label: str) -> dict[str, object]:
    item = _dict(value, label)
    kind = _str(item.get("kind"), f"{label}.kind")
    if kind not in _TAG_KINDS:
        raise ContractError(f"{label}.kind has unsupported value {kind!r}")
    if kind == "primitive":
        _exact_keys(item, frozenset({"kind", "value"}), label)
        primitive = item["value"]
        if not (primitive is None or isinstance(primitive, (bool, int, float, str))):
            raise ContractError(f"{label}.value is not a primitive")
    elif kind == "datetime":
        _exact_keys(item, frozenset({"kind", "value"}), label)
        raw = _str(item["value"], f"{label}.value")
        try:
            parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractError(f"{label}.value is not ISO-8601") from exc
        if parsed.tzinfo is None:
            raise ContractError(f"{label}.value must include a UTC offset")
    elif kind == "enum":
        _exact_keys(item, frozenset({"kind", "type", "member"}), label)
        if _str(item["type"], f"{label}.type") not in _ENUM_TYPES:
            raise ContractError(f"{label}.type is not a closed enum")
        _str(item["member"], f"{label}.member")
    elif kind == "path":
        _exact_keys(item, frozenset({"kind", "value"}), label)
        _str(item["value"], f"{label}.value")
    elif kind == "unset" or kind == "stdin_description":
        _exact_keys(item, frozenset({"kind"}), label)
    elif kind == "inline_description" or kind == "file_description":
        key = "text" if kind == "inline_description" else "path"
        _exact_keys(item, frozenset({"kind", key}), label)
        _str(item[key], f"{label}.{key}")
    elif kind == "comment_cursor":
        _exact_keys(item, frozenset({"kind", "before", "before_id"}), label)
        _str(item["before"], f"{label}.before")
        _str(item["before_id"], f"{label}.before_id")
    elif kind == "list":
        _exact_keys(item, frozenset({"kind", "items"}), label)
        for index, child in enumerate(_list(item["items"], f"{label}.items")):
            _tag(child, f"{label}.items[{index}]")
    else:
        _exact_keys(item, frozenset({"kind", "type", "fields"}), label)
        request_type = _str(item["type"], f"{label}.type")
        if request_type not in _REQUEST_TYPES:
            raise ContractError(f"{label}.type is not a closed request")
        fields = _list(item["fields"], f"{label}.fields")
        seen: set[str] = set()
        for index, pair in enumerate(fields):
            pair_values = _list(pair, f"{label}.fields[{index}]")
            if len(pair_values) != 2:
                raise ContractError(f"{label}.fields[{index}] must have two values")
            field_name = _str(pair_values[0], f"{label}.fields[{index}][0]")
            if field_name in seen:
                raise ContractError(f"{label} repeats field {field_name!r}")
            seen.add(field_name)
            _tag(pair_values[1], f"{label}.fields[{index}][1]")
        expected_order = _REQUEST_FIELD_ORDER[request_type]
        actual_order = tuple(
            _str(_list(pair, f"{label}.fields[{index}]")[0], f"{label}.fields[{index}][0]")
            for index, pair in enumerate(fields)
        )
        if any(name not in expected_order for name in actual_order) or actual_order != tuple(
            name for name in expected_order if name in seen
        ):
            raise ContractError(f"{label}.fields must use the approved field set and order")
    return item


def _assertion(value: object, vector_id: str) -> ResultAssertion:
    item = _dict(value, f"{vector_id}.assertion")
    _exact_keys(item, _ASSERTION_KEYS, f"{vector_id}.assertion")
    assertion_id = _str(item["id"], f"{vector_id}.assertion.id")
    if assertion_id != f"assert:{vector_id}":
        raise ContractError(f"{vector_id}.assertion.id does not match vector_id")
    kind = _str(item["kind"], f"{vector_id}.assertion.kind")
    if kind not in {"none", "decoded_type", "page_items"}:
        raise ContractError(f"{vector_id}.assertion.kind is unsupported")
    expected = _tag(item["expected"], f"{vector_id}.assertion.expected")
    if kind == "none" and not (expected["kind"] == "primitive" and expected["value"] is None):
        raise ContractError(f"{vector_id}.none assertion must expect primitive null")
    if kind == "page_items":
        if expected.get("kind") != "list":
            raise ContractError(f"{vector_id}.page_items assertion must expect a list")
        for child in cast("list[object]", expected["items"]):
            child_item = _dict(child, f"{vector_id}.assertion.expected.items")
            if child_item.get("kind") != "primitive" or not isinstance(
                child_item.get("value"), str
            ):
                raise ContractError(f"{vector_id}.page_items IDs must be primitive strings")
    if kind == "decoded_type" and expected.get("kind") != "primitive":
        raise ContractError(f"{vector_id}.decoded_type assertion must expect a primitive name")
    if kind == "decoded_type" and expected.get("value") not in _DECODED_TYPES:
        raise ContractError(f"{vector_id}.decoded_type expected type is not approved")
    return ResultAssertion(assertion_id, kind, expected)


def _parse_vector(value: object, key: str) -> TestVector:
    item = _dict(value, f"test_vectors[{key}]")
    _exact_keys(item, _VECTOR_KEYS, f"test_vectors[{key}]")
    vector_id = _str(item["vector_id"], f"test_vectors[{key}].vector_id")
    if vector_id != key:
        raise ContractError(f"test_vectors key {key!r} does not match vector_id")
    match = _VECTOR_ID.fullmatch(vector_id)
    if match is None:
        raise ContractError(f"invalid generated vector ID: {vector_id}")
    operation_id = _str(item["operation_id"], f"{vector_id}.operation_id")
    if operation_id != match.group("operation"):
        raise ContractError(f"{vector_id}.operation_id does not match vector ID")
    entrypoint_id = _str(item["entrypoint_id"], f"{vector_id}.entrypoint_id")
    if not _IDENTIFIER.fullmatch(entrypoint_id) or entrypoint_id != match.group("entrypoint"):
        raise ContractError(f"{vector_id}.entrypoint_id is invalid")
    is_canonical = _bool(item["is_canonical"], f"{vector_id}.is_canonical")
    args = tuple(
        _tag(child, f"{vector_id}.args[{index}]")
        for index, child in enumerate(_list(item["args"], f"{vector_id}.args"))
    )
    kwargs_items: list[tuple[str, dict[str, object]]] = []
    for index, pair in enumerate(_list(item["kwargs"], f"{vector_id}.kwargs")):
        pair_values = _list(pair, f"{vector_id}.kwargs[{index}]")
        if len(pair_values) != 2:
            raise ContractError(f"{vector_id}.kwargs[{index}] must have two values")
        kwargs_items.append(
            (
                _str(pair_values[0], f"{vector_id}.kwargs[{index}][0]"),
                _tag(pair_values[1], f"{vector_id}.kwargs[{index}][1]"),
            )
        )
    stdout_base64 = _str(item["stdout_base64"], f"{vector_id}.stdout_base64")
    stderr = _str(item["stderr"], f"{vector_id}.stderr")
    try:
        base64.b64decode(stdout_base64, validate=True)
    except ValueError as exc:
        raise ContractError(f"{vector_id}.stdout_base64 is invalid") from exc
    exit_code = _int(item["exit_code"], f"{vector_id}.exit_code")
    transport_method = _str(item["transport_method"], f"{vector_id}.transport_method")
    if transport_method not in {"run_bytes", "run_text", "spawn"}:
        raise ContractError(f"{vector_id}.transport_method is invalid")
    expected_argv = tuple(
        _str(value, f"{vector_id}.expected_argv[{index}]")
        for index, value in enumerate(_list(item["expected_argv"], f"{vector_id}.expected_argv"))
    )
    stdin_base64_value = item["stdin_base64"]
    if stdin_base64_value is not None:
        stdin_base64 = _str(stdin_base64_value, f"{vector_id}.stdin_base64")
        try:
            base64.b64decode(stdin_base64, validate=True)
        except ValueError as exc:
            raise ContractError(f"{vector_id}.stdin_base64 is invalid") from exc
    else:
        stdin_base64 = None
    timeout_value = item["timeout"]
    if timeout_value is not None and (
        isinstance(timeout_value, bool) or not isinstance(timeout_value, (int, float))
    ):
        raise ContractError(f"{vector_id}.timeout must be a number or null")
    return TestVector(
        vector_id,
        operation_id,
        entrypoint_id,
        is_canonical,
        args,
        tuple(kwargs_items),
        stdout_base64,
        stderr,
        exit_code,
        transport_method,
        expected_argv,
        stdin_base64,
        float(timeout_value) if timeout_value is not None else None,
        _assertion(item["assertion"], vector_id),
    )


def _enum_definitions(value: object) -> tuple[EnumDefinition, ...]:
    definitions: list[EnumDefinition] = []
    for index, raw in enumerate(_list(value, "catalogs.enum_definitions")):
        item = _dict(raw, f"catalogs.enum_definitions[{index}]")
        _exact_keys(
            item, frozenset({"enum_id", "public_name", "members"}), f"enum_definitions[{index}]"
        )
        enum_id = _contract_identifier(item["enum_id"], f"enum_definitions[{index}].enum_id")
        public_name = _python_identifier(
            item["public_name"], f"enum_definitions[{index}].public_name"
        )
        members: list[EnumMember] = []
        for member_index, raw_member in enumerate(_list(item["members"], f"{enum_id}.members")):
            member = _dict(raw_member, f"{enum_id}.members[{member_index}]")
            _exact_keys(member, frozenset({"name", "value"}), f"{enum_id}.members[{member_index}]")
            member_name = _python_identifier(member["name"], "member.name")
            if member_name.startswith("_") and member_name.endswith("_"):
                raise ContractError("generated enum member names must not be sunder names")
            members.append(EnumMember(member_name, _str(member["value"], "member.value")))
        if not members:
            raise ContractError(f"{enum_id} has no members")
        definitions.append(EnumDefinition(enum_id, public_name, tuple(members)))
    return tuple(definitions)


def _validator_definitions(value: object) -> tuple[ValidatorDefinition, ...]:
    definitions: list[ValidatorDefinition] = []
    for index, raw in enumerate(_list(value, "catalogs.validator_definitions")):
        item = _dict(raw, f"catalogs.validator_definitions[{index}]")
        _exact_keys(
            item,
            frozenset({"validator_id", "name", "parameter_name", "body_kind"}),
            f"validator_definitions[{index}]",
        )
        validator_id = _str(item["validator_id"], f"validator_definitions[{index}].validator_id")
        name = _python_identifier(item["name"], f"{validator_id}.name")
        parameter_name = _python_identifier(
            item["parameter_name"], f"{validator_id}.parameter_name"
        )
        if parameter_name in _GENERATED_NAMESPACE_RESERVED:
            raise ContractError(f"{validator_id}.parameter_name shadows a generated runtime name")
        body_kind = _str(item["body_kind"], f"{validator_id}.body_kind")
        if body_kind.startswith("one_of:"):
            if body_kind.removeprefix("one_of:") not in _VALIDATOR_ENUM_IDS:
                raise ContractError(f"{validator_id}.body_kind has an unapproved enum ID")
        elif body_kind not in _BODY_KINDS:
            raise ContractError(f"{validator_id}.body_kind is not closed")
        definitions.append(ValidatorDefinition(validator_id, name, parameter_name, body_kind))
    return tuple(definitions)


def _binding_descriptors(value: object) -> tuple[BindingDescriptor, ...]:
    descriptors: list[BindingDescriptor] = []
    for index, raw in enumerate(_list(value, "catalogs.binding_descriptors")):
        item = _dict(raw, f"catalogs.binding_descriptors[{index}]")
        _exact_keys(
            item,
            frozenset(
                {
                    "descriptor_id",
                    "operation_id",
                    "entrypoint_id",
                    "command",
                    "mappings",
                    "validator_ids",
                }
            ),
            f"binding_descriptors[{index}]",
        )
        mappings: list[tuple[str, str, str]] = []
        for mapping_index, raw_mapping in enumerate(_list(item["mappings"], "binding.mappings")):
            mapping = _dict(raw_mapping, f"binding.mappings[{mapping_index}]")
            _exact_keys(
                mapping,
                frozenset({"source", "binding", "destination"}),
                f"binding.mappings[{mapping_index}]",
            )
            mappings.append(
                (
                    _str(mapping["source"], "mapping.source"),
                    _str(mapping["binding"], "mapping.binding"),
                    _str(mapping["destination"], "mapping.destination"),
                )
            )
        descriptors.append(
            BindingDescriptor(
                _contract_identifier(item["descriptor_id"], "descriptor_id"),
                _str(item["operation_id"], "binding.operation_id"),
                _str(item["entrypoint_id"], "binding.entrypoint_id"),
                tuple(
                    _str(value, "binding.command")
                    for value in _list(item["command"], "binding.command")
                ),
                tuple(mappings),
                tuple(
                    _str(value, "binding.validator_ids")
                    for value in _list(item["validator_ids"], "binding.validator_ids")
                ),
            )
        )
    return tuple(descriptors)


def _operations(value: object) -> tuple[Operation, ...]:
    operations: list[Operation] = []
    for index, raw in enumerate(_list(value, "operations")):
        item = _dict(raw, f"operations[{index}]")
        required = frozenset(
            {
                "operation_id",
                "compatibility",
                "rationale",
                "source_ref_ids",
                "test_ref_ids",
                "entrypoints",
            }
        )
        _exact_keys(item, required, f"operations[{index}]")
        entrypoints: list[Entrypoint] = []
        for ep_index, raw_ep in enumerate(
            _list(item["entrypoints"], f"operations[{index}].entrypoints")
        ):
            ep = _dict(raw_ep, f"operations[{index}].entrypoints[{ep_index}]")
            _exact_keys(
                ep,
                frozenset(
                    {
                        "entrypoint_id",
                        "public_symbol",
                        "signature_id",
                        "binding_id",
                        "response_id",
                        "errors",
                    }
                ),
                "entrypoint",
            )
            entrypoints.append(
                Entrypoint(
                    *(
                        _str(ep[key], f"entrypoint.{key}")
                        for key in (
                            "entrypoint_id",
                            "public_symbol",
                            "signature_id",
                            "binding_id",
                            "response_id",
                            "errors",
                        )
                    )
                )
            )
        operations.append(
            Operation(
                _str(item["operation_id"], "operation_id"),
                _str(item["compatibility"], "compatibility"),
                _str(item["rationale"], "rationale"),
                tuple(
                    _str(value, "source_ref_id")
                    for value in _list(item["source_ref_ids"], "source_ref_ids")
                ),
                tuple(
                    _str(value, "test_ref_id")
                    for value in _list(item["test_ref_ids"], "test_ref_ids")
                ),
                tuple(entrypoints),
            )
        )
    return tuple(operations)


def _relative_posix_path(value: object, label: str) -> str:
    path = _str(value, label)
    pure = pathlib.PurePosixPath(path)
    if not path or pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ContractError(f"{label} must be a normalized relative POSIX path")
    if "\\" in path:
        raise ContractError(f"{label} must use POSIX separators")
    return path


def _source_refs(value: object) -> tuple[SourceRef, ...]:
    refs: list[SourceRef] = []
    for index, raw in enumerate(_list(value, "source_refs")):
        item = _dict(raw, f"source_refs[{index}]")
        _exact_keys(
            item,
            frozenset(
                {
                    "source_ref_id",
                    "repository",
                    "commit",
                    "path",
                    "symbol",
                    "line_start",
                    "line_end",
                }
            ),
            f"source_refs[{index}]",
        )
        commit = _str(item["commit"], f"source_refs[{index}].commit")
        if not _COMMIT.fullmatch(commit):
            raise ContractError(
                f"source_refs[{index}].commit must be a full lowercase hexadecimal commit"
            )
        start = _int(item["line_start"], f"source_refs[{index}].line_start")
        end = _int(item["line_end"], f"source_refs[{index}].line_end")
        if start < 1 or end < start:
            raise ContractError(f"source_refs[{index}] has an invalid line range")
        refs.append(
            SourceRef(
                _str(item["source_ref_id"], f"source_refs[{index}].source_ref_id"),
                _str(item["repository"], f"source_refs[{index}].repository"),
                commit,
                _relative_posix_path(item["path"], f"source_refs[{index}].path"),
                _str(item["symbol"], f"source_refs[{index}].symbol"),
                start,
                end,
            )
        )
    if len({item.source_ref_id for item in refs}) != len(refs):
        raise ContractError("source_refs IDs must be unique")
    return tuple(refs)


def _test_refs(value: object) -> tuple[TestRef, ...]:
    refs: list[TestRef] = []
    for index, raw in enumerate(_list(value, "test_refs")):
        item = _dict(raw, f"test_refs[{index}]")
        _exact_keys(item, frozenset({"test_ref_id", "path", "node_id"}), f"test_refs[{index}]")
        refs.append(
            TestRef(
                _str(item["test_ref_id"], f"test_refs[{index}].test_ref_id"),
                _relative_posix_path(item["path"], f"test_refs[{index}].path"),
                _str(item["node_id"], f"test_refs[{index}].node_id"),
            )
        )
    if len({item.test_ref_id for item in refs}) != len(refs):
        raise ContractError("test_refs IDs must be unique")
    return tuple(refs)


def _closed_auxiliary_catalogs(catalogs: dict[str, object]) -> None:
    """Validate retained contract metadata before any generator can observe it."""

    for name in ("types", "signatures", "decoders", "validators"):
        values = _dict(catalogs[name], f"catalogs.{name}")
        if set(values) != _AUXILIARY_CATALOG_KEYS[name]:
            raise ContractError(f"catalogs.{name} must contain exactly the approved keys")
        for key, value in values.items():
            _str(key, f"catalogs.{name} key")
            _str(value, f"catalogs.{name}[{key!r}]")
    for name in ("binding_source_refs", "mapping_presence"):
        values = _dict(catalogs[name], f"catalogs.{name}")
        if set(values) != _AUXILIARY_CATALOG_KEYS["signatures"]:
            raise ContractError(f"catalogs.{name} must contain exactly the binding keys")
        for key, value in values.items():
            _str(key, f"catalogs.{name} key")
            for index, item in enumerate(_list(value, f"catalogs.{name}[{key!r}]")):
                _str(item, f"catalogs.{name}[{key!r}][{index}]")
    for name in ("presence", "validator_evidence"):
        values = _dict(catalogs[name], f"catalogs.{name}")
        for key, value in values.items():
            _str(key, f"catalogs.{name} key")
            item = _dict(value, f"catalogs.{name}[{key!r}]")
            expected = (
                frozenset({"omitted", "null", "empty", "zero", "false"})
                if name == "presence"
                else frozenset({"positive_case_id", "negative_case_id"})
            )
            _exact_keys(item, expected, f"catalogs.{name}[{key!r}]")
            for field, field_value in item.items():
                _str(field_value, f"catalogs.{name}[{key!r}].{field}")
    if (
        set(_dict(catalogs["validator_evidence"], "catalogs.validator_evidence"))
        != _AUXILIARY_CATALOG_KEYS["validators"]
    ):
        raise ContractError("catalogs.validator_evidence must contain exactly the validator keys")
    bindings = _dict(catalogs["bindings"], "catalogs.bindings")
    if set(bindings) != _AUXILIARY_CATALOG_KEYS["signatures"]:
        raise ContractError("catalogs.bindings must contain exactly the binding keys")
    for key, value in bindings.items():
        item = _dict(value, f"catalogs.bindings[{key!r}]")
        _exact_keys(item, frozenset({"command", "output", "mappings", "constraints"}), "binding")
        for index, command in enumerate(_list(item["command"], "binding.command")):
            _str(command, f"binding.command[{index}]")
        _str(item["output"], "binding.output")
        for index, mapping in enumerate(_list(item["mappings"], "binding.mappings")):
            pair = _list(mapping, f"binding.mappings[{index}]")
            if len(pair) != 3:
                raise ContractError(f"binding.mappings[{index}] must have three values")
            for part_index, part in enumerate(pair):
                _str(part, f"binding.mappings[{index}][{part_index}]")
        for index, constraint in enumerate(_list(item["constraints"], "binding.constraints")):
            _str(constraint, f"binding.constraints[{index}]")
    responses = _dict(catalogs["responses"], "catalogs.responses")
    for key, value in responses.items():
        item = _dict(value, f"catalogs.responses[{key!r}]")
        _exact_keys(
            item,
            frozenset(
                {
                    "public_type_id",
                    "wire_type_id",
                    "decoder_id",
                    "success_exit_codes",
                    "malformed_output",
                }
            ),
            f"catalogs.responses[{key!r}]",
        )
        for field in ("public_type_id", "decoder_id", "malformed_output"):
            _str(item[field], f"catalogs.responses[{key!r}].{field}")
        if item["wire_type_id"] is not None:
            _str(item["wire_type_id"], f"catalogs.responses[{key!r}].wire_type_id")
        for index, code in enumerate(
            _list(item["success_exit_codes"], "response.success_exit_codes")
        ):
            _int(code, f"response.success_exit_codes[{index}]")


def load_contract(path: pathlib.Path) -> ContractCatalog:
    try:
        raw_value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read approved contract {path}: {exc}") from exc
    raw = _dict(raw_value, "contract")
    required = frozenset(
        {
            "schema_version",
            "target",
            "catalogs",
            "source_refs",
            "test_refs",
            "scope",
            "operations",
            "traceability",
            "legacy_argv_migration",
        }
    )
    _exact_keys(raw, required, "contract")
    if _int(raw["schema_version"], "schema_version") != 3:
        raise ContractError("approved contract schema_version must be 3")
    target_raw = _dict(raw["target"], "target")
    _exact_keys(
        target_raw,
        frozenset({"version", "tag", "commit", "release_id", "release_provenance_ref"}),
        "target",
    )
    target = Target(
        *(
            _str(target_raw[key], f"target.{key}")
            for key in ("version", "tag", "commit", "release_id", "release_provenance_ref")
        )
    )
    if not _COMMIT.fullmatch(target.commit):
        raise ContractError("target.commit must be a full lowercase hexadecimal commit")
    catalogs = _dict(raw["catalogs"], "catalogs")
    catalog_required = frozenset(
        {
            "types",
            "signatures",
            "bindings",
            "binding_source_refs",
            "presence",
            "mapping_presence",
            "responses",
            "decoders",
            "validators",
            "validator_evidence",
            "enum_definitions",
            "validator_definitions",
            "binding_descriptors",
            "test_vectors",
        }
    )
    _exact_keys(catalogs, catalog_required, "catalogs")
    _closed_auxiliary_catalogs(catalogs)
    enum_definitions = _enum_definitions(catalogs["enum_definitions"])
    validator_definitions = _validator_definitions(catalogs["validator_definitions"])
    binding_descriptors = _binding_descriptors(catalogs["binding_descriptors"])
    vectors_raw = _dict(catalogs["test_vectors"], "catalogs.test_vectors")
    vectors = tuple(_parse_vector(value, key) for key, value in vectors_raw.items())
    if len(vectors) != 55:
        raise ContractError(f"expected 37 test vectors, got {len(vectors)}")
    if len({vector.assertion.assertion_id for vector in vectors}) != len(vectors):
        raise ContractError("test vector assertion IDs must be unique")
    scope = _dict(raw["scope"], "scope")
    _exact_keys(
        scope,
        frozenset(
            {
                "operation_ids",
                "ungoverned_policy",
                "source_authority_ref",
                "family_disposition_ref",
                "family_dispositions",
            }
        ),
        "scope",
    )
    _str(scope["ungoverned_policy"], "scope.ungoverned_policy")
    _relative_posix_path(scope["source_authority_ref"], "scope.source_authority_ref")
    _relative_posix_path(scope["family_disposition_ref"], "scope.family_disposition_ref")
    for index, disposition in enumerate(
        _list(scope["family_dispositions"], "scope.family_dispositions")
    ):
        item = _dict(disposition, f"scope.family_dispositions[{index}]")
        _exact_keys(
            item,
            frozenset(
                {"family", "disposition", "required_operation_ids", "source_ref_ids", "rationale"}
            ),
            f"scope.family_dispositions[{index}]",
        )
        for field in ("family", "disposition", "rationale"):
            _str(item[field], f"scope.family_dispositions[{index}].{field}")
        for field in ("required_operation_ids", "source_ref_ids"):
            for value in _list(item[field], f"scope.family_dispositions[{index}].{field}"):
                _str(value, f"scope.family_dispositions[{index}].{field}")
    traceability = _list(raw["traceability"], "traceability")
    for index, raw_item in enumerate(traceability):
        item = _dict(raw_item, f"traceability[{index}]")
        _exact_keys(
            item,
            frozenset({"requirement_id", "authority_ref", "test_ref_ids"}),
            f"traceability[{index}]",
        )
        _str(item["requirement_id"], f"traceability[{index}].requirement_id")
        _str(item["authority_ref"], f"traceability[{index}].authority_ref")
        for value in _list(item["test_ref_ids"], f"traceability[{index}].test_ref_ids"):
            _str(value, f"traceability[{index}].test_ref_ids")
    operations = _operations(raw["operations"])
    operation_ids = {operation.operation_id for operation in operations}
    if operation_ids != {
        _str(value, "scope.operation_ids")
        for value in _list(scope["operation_ids"], "scope.operation_ids")
    }:
        raise ContractError("scope.operation_ids must match operations")
    for vector in vectors:
        if vector.operation_id not in operation_ids:
            raise ContractError(f"{vector.vector_id} references unknown operation")
    migration_raw = _dict(raw["legacy_argv_migration"], "legacy_argv_migration")
    migration: dict[str, str] = {}
    for index in range(1, 144):
        key = f"legacy:{index:03d}"
        value = migration_raw.get(key)
        if not isinstance(value, str):
            raise ContractError(f"legacy_argv_migration is missing {key}")
        migration[key] = value
    if set(migration_raw) != set(migration):
        raise ContractError("legacy_argv_migration must contain exactly legacy:001..legacy:143")
    source_refs = _source_refs(raw["source_refs"])
    if any(item.commit != target.commit for item in source_refs):
        raise ContractError("every source_refs commit must match target.commit")
    test_refs = _test_refs(raw["test_refs"])
    return ContractCatalog(
        target=target,
        operations=operations,
        source_refs=source_refs,
        test_refs=test_refs,
        enum_definitions=enum_definitions,
        validator_definitions=validator_definitions,
        binding_descriptors=binding_descriptors,
        test_vectors=vectors,
        legacy_argv_migration=migration,
        raw=raw,
    )


def validate_contract(path: pathlib.Path) -> ContractCatalog:
    contract = load_contract(path)
    if {item.enum_id for item in contract.enum_definitions} != {
        "issue_sort",
        "sort_direction",
        "autopilot_execution_mode",
    }:
        raise ContractError("v3 must define the three generated public enums")
    if len(contract.validator_definitions) == 0:
        raise ContractError("v3 must define validator definitions")
    if len({item.validator_id for item in contract.validator_definitions}) != len(
        contract.validator_definitions
    ):
        raise ContractError("validator definition IDs must be unique")
    descriptor_ids = {item.descriptor_id for item in contract.binding_descriptors}
    if len(descriptor_ids) != len(contract.binding_descriptors):
        raise ContractError("binding descriptor IDs must be unique")
    reserved = _GENERATED_NAMESPACE_RESERVED
    public_names = [item.public_name for item in contract.enum_definitions]
    binding_names = {
        item.descriptor_id.upper().replace(".", "_") + "_BINDING"
        for item in contract.binding_descriptors
    }
    if len(binding_names) != len(contract.binding_descriptors):
        raise ContractError("generated binding names must be unique")
    if len(public_names) != len(set(public_names)) or set(public_names) & (
        reserved | binding_names
    ):
        raise ContractError("generated enum public names collide with generated exports")
    if any(
        len({member.name for member in definition.members}) != len(definition.members)
        for definition in contract.enum_definitions
    ):
        raise ContractError("generated enum member names must be unique per enum")
    validator_names = [item.name for item in contract.validator_definitions]
    if set(validator_names) & (reserved | binding_names | set(public_names)):
        raise ContractError("generated validator names collide with generated exports")
    for name in set(validator_names):
        definitions = [item for item in contract.validator_definitions if item.name == name]
        if len({(item.parameter_name, item.body_kind) for item in definitions}) != 1:
            raise ContractError(f"generated validator name {name!r} has conflicting definitions")
    expected_descriptor_pairs = {
        (operation.operation_id, entrypoint.entrypoint_id)
        for operation in contract.operations
        for entrypoint in operation.entrypoints
    }
    actual_descriptor_pairs = {
        (descriptor.operation_id, descriptor.entrypoint_id)
        for descriptor in contract.binding_descriptors
    }
    if actual_descriptor_pairs != expected_descriptor_pairs:
        raise ContractError("binding descriptors must map one-to-one to operation entrypoints")
    signatures = _dict(
        _dict(contract.raw["catalogs"], "catalogs")["signatures"], "catalogs.signatures"
    )
    responses = _dict(
        _dict(contract.raw["catalogs"], "catalogs")["responses"], "catalogs.responses"
    )
    for operation in contract.operations:
        if operation.compatibility not in {"compatible", "intentionally_changed"}:
            raise ContractError(
                f"operation {operation.operation_id!r} has an invalid compatibility value"
            )
        source_ref_ids = {item.source_ref_id for item in contract.source_refs}
        test_ref_ids = {item.test_ref_id for item in contract.test_refs}
        if not set(operation.source_ref_ids) <= source_ref_ids:
            raise ContractError(
                f"operation {operation.operation_id!r} references an unknown source ref"
            )
        if not set(operation.test_ref_ids) <= test_ref_ids:
            raise ContractError(
                f"operation {operation.operation_id!r} references an unknown test ref"
            )
        for entrypoint in operation.entrypoints:
            if entrypoint.signature_id not in signatures:
                raise ContractError(
                    f"entrypoint {entrypoint.entrypoint_id!r} has an unknown signature"
                )
            if entrypoint.response_id not in responses:
                raise ContractError(
                    f"entrypoint {entrypoint.entrypoint_id!r} has an unknown response"
                )
            if entrypoint.binding_id not in descriptor_ids:
                raise ContractError(f"missing binding descriptor {entrypoint.binding_id!r}")
            descriptor = next(
                item
                for item in contract.binding_descriptors
                if item.descriptor_id == entrypoint.binding_id
            )
            if (descriptor.operation_id, descriptor.entrypoint_id) != (
                operation.operation_id,
                entrypoint.entrypoint_id,
            ):
                raise ContractError(
                    f"binding descriptor {descriptor.descriptor_id!r} has the wrong operation"
                )
            if not set(descriptor.validator_ids) <= {
                item.validator_id for item in contract.validator_definitions
            }:
                raise ContractError(
                    f"binding descriptor {descriptor.descriptor_id!r} references an unknown validator"
                )
    base_count = sum(":canonical" in vector.vector_id for vector in contract.test_vectors)
    variant_count = len(contract.test_vectors) - base_count
    if (base_count, variant_count) != (44, 11):
        raise ContractError(
            f"expected 44 entrypoint-base and 11 variant vectors, got {base_count}/{variant_count}"
        )
    return contract


def assert_result(assertion: ResultAssertion, result: object) -> None:
    """Apply the closed assertion carried by one approved test vector."""

    if assertion.kind == "none":
        if result is not None:
            raise AssertionError(f"expected None, got {result!r}")
        return
    expected_kind = assertion.expected.get("kind")
    if assertion.kind == "decoded_type":
        if expected_kind != "primitive" or not isinstance(assertion.expected.get("value"), str):
            raise AssertionError("decoded_type requires a primitive fully-qualified type name")
        actual = f"{type(result).__module__}.{type(result).__qualname__}"
        if actual != assertion.expected["value"]:
            raise AssertionError(f"expected {assertion.expected['value']}, got {actual}")
        return
    if expected_kind != "list":
        raise AssertionError("page_items requires a list expectation")
    from multica_py.models.common import Page

    if type(result) is not Page:
        raise AssertionError("page_items requires multica_py.models.common.Page")
    expected_items = assertion.expected.get("items")
    if not isinstance(expected_items, list):
        raise AssertionError("page_items requires an items list")
    expected_ids = tuple(
        item.get("value")
        for item in expected_items
        if isinstance(item, dict) and item.get("kind") == "primitive"
    )
    if len(expected_ids) != len(expected_items) or not all(
        isinstance(item, dict) and isinstance(item.get("value"), str) for item in expected_items
    ):
        raise AssertionError("page_items IDs must be primitive strings")
    actual_items = getattr(result, "items", ())
    actual_ids = tuple(getattr(item, "id", None) for item in actual_items)
    if actual_ids != expected_ids:
        raise AssertionError(f"expected page IDs {expected_ids}, got {actual_ids}")
