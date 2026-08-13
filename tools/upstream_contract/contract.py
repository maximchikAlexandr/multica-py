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
from typing import Protocol, cast


class ContractError(ValueError):
    """Raised when an approved contract is not a closed valid v3 document."""


class _HasId(Protocol):
    id: str | None


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
    }
)
_ENUM_TYPES = frozenset(
    {"IssueStatus", "ProjectStatus", "IssueSort", "SortDirection", "AutopilotExecutionMode"}
)
_DECODED_TYPES = frozenset(
    {
        "multica_py.models.common.Page",
        "builtins.dict",
        "multica_py.models.issues.IssueChildrenResult",
        "multica_py.models.project_resources.ProjectResourceRecord",
        "multica_py.models.autopilots.Autopilot",
        "multica_py.models.autopilots.AutopilotListPage",
        "multica_py.models.autopilots.AutopilotRun",
        "multica_py.models.autopilots.AutopilotRunListPage",
        "multica_py.models.issues.IssueListPage",
        "multica_py.resources.agents.Agent",
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
        "multica_py.resources.autopilots.Autopilot",
        "multica_py.resources.autopilots.AutopilotRun",
        "multica_py.resources.issues.Issue",
        "multica_py.resources.issue_comments.Comment",
        "multica_py.resources.projects.Project",
    }
)
_OPERATION_CATEGORIES = frozenset(
    {
        "retrieve",
        "create",
        "update",
        "collection",
        "action",
        "process",
        "scalar",
        "mapping",
    }
)
_INPUT_MODES = frozenset({"direct", "dual_required", "dual_optional"})
_TYPED_INPUT_IDS = frozenset(
    {
        "IssueListFilter",
    }
)
_PRESENCE_POLICY_IDS = frozenset(
    {
        "empty_collection_clear",
        "empty_present",
        "false_present",
        "nullable_clear",
        "omit",
        "required_nonnull",
        "zero_present",
    }
)
_UPDATE_PRESENCE_VALUES = frozenset({"omit", "reject", "emit", "not_applicable"})
_UPDATE_CLEAR_KINDS = frozenset({"none", "flag", "dedicated_flag", "composite", "empty_collection"})
_UPDATE_POLICY_FIELDS = {
    "projects.update": frozenset({"name", "description"}),
    "agents.update": frozenset({"name", "description"}),
    "skills.update": frozenset({"name", "description"}),
    "issues.update": frozenset(
        {"title", "description", "priority", "assignee_id", "project_id", "parent_id"}
    ),
    "autopilots.update": frozenset(
        {
            "title",
            "description",
            "agent",
            "priority",
            "status",
            "execution_mode",
            "project_id",
            "issue_title_template",
            "subscribers",
        }
    ),
    "autopilots.trigger_update": frozenset({"title", "kind"}),
    "labels.update": frozenset({"name", "color"}),
    "projects.resources.update_local_directory": frozenset({"local_path"}),
    "runtimes.update": frozenset({"target_version", "wait"}),
    "users.profile_update": frozenset({"description"}),
}
_RESPONSE_CATALOG_IDS = frozenset(
    {
        "action_result_none",
        "action_result_repository_mutation_result",
        "action_result_runtime_update_result",
        "action_result_str",
        "cli_result",
        "bytes",
        "agent",
        "agent_skills",
        "agent_tasks",
        "attachment_result",
        "autopilot",
        "autopilot_list_page",
        "autopilot_run",
        "autopilot_run_list_page",
        "autopilot_trigger",
        "comment",
        "comment_page",
        "comment_thread_page",
        "comments",
        "issue",
        "issue_children_result",
        "issue_list_page",
        "labels",
        "linked_pull_requests",
        "metadata_entries",
        "none",
        "mapping_config",
        "page_agent",
        "page_agent_skills",
        "page_agent_tasks",
        "page_comments",
        "page_daemon_disk_usage",
        "page_issues",
        "page_issue_usage",
        "page_labels",
        "page_linked_pull_requests",
        "page_project",
        "page_project_resources",
        "page_repository_records",
        "page_run_messages",
        "page_runtime_activity",
        "page_runtime_definitions",
        "page_runtime_usage",
        "page_skill",
        "page_skill_files",
        "page_squad",
        "page_squad_members",
        "page_subscribers",
        "page_task_runs",
        "page_workspace",
        "page_workspace_members",
        "path",
        "project",
        "project_resource",
        "project_resources",
        "repository_mutation_result",
        "repository_records",
        "run_messages",
        "runtime_activity",
        "runtime_definition",
        "runtime_definitions",
        "runtime_update_result",
        "runtime_usage",
        "scalar_str",
        "skill",
        "skill_file",
        "skill_files",
        "squad",
        "squad_members",
        "subscribers",
        "task_runs",
        "process",
        "user_profile",
        "workspace",
        "workspace_members",
    }
)
_RESPONSE_ALIASES = frozenset({"issue_search"})
_BODY_KINDS = frozenset(
    {"nonblank", "nonnegative_int", "positive_int", "project_update", "resource_update"}
)
_VALIDATOR_ENUM_IDS = frozenset({"IssueStatus", "ProjectStatus", "AutopilotExecutionMode"})
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
            "issue_search_result_wire",
            "page_issues",
            "issue_pull_requests_result_wire",
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
            "cli_result",
            "operation_options",
        }
    ),
    "signatures": frozenset(
        {
            "agent_avatar",
            "agent_copy",
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
            "issue_search",
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
            "cli_command",
            "issues_unassign",
            "issues_move_to_top",
            "issues_move_to_bottom",
            "issues_move_before",
            "issues_move_after",
            "project_issue_create",
            "issues_refresh",
            "issues_update_bound",
            "issues_assign_bound",
            "issues_unassign_bound",
            "issues_set_status_bound",
            "issues_move_to_top_bound",
            "issues_move_to_bottom_bound",
            "issues_move_before_bound",
            "issues_move_after_bound",
            "projects_refresh",
            "projects_update_bound",
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
            "decode_comment",
            "decode_comment_page",
            "decode_comment_thread_page",
            "decode_comments",
            "decode_issue",
            "decode_issue_children",
            "decode_issue_list_page",
            "decode_issue_search",
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
            "decode_cli_result",
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
            "positive_int:max_concurrent_tasks",
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
            "nonblank:query",
            "nonblank:daemon_id",
            "nonblank:local_path",
            "nonblank:resource_id",
            "nonblank:runtime",
            "nonblank:skill_id",
            "nonblank:squad_id",
            "nonblank:source_agent_id",
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
_MANUAL_SIGNATURE_IDS = frozenset(
    {
        "agents_archive_manual",
        "agents_create_manual",
        "agents_restore_manual",
        "agents_update_manual",
        "attachments_download_bytes_manual",
        "attachments_upload_bytes_manual",
        "auth_login_manual",
        "auth_logout_manual",
        "auth_status_manual",
        "configuration_get_manual",
        "configuration_set_manual",
        "configuration_show_manual",
        "daemon_disk_usage_manual",
        "daemon_logs_manual",
        "daemon_restart_manual",
        "daemon_start_manual",
        "daemon_status_manual",
        "daemon_stop_manual",
        "issues_assign_manual",
        "issues_comments_reply_manual",
        "issues_comments_resolve_manual",
        "issues_comments_unresolve_manual",
        "issues_deprioritize_manual",
        "issues_metadata_query_manual",
        "issues_metadata_set_typed_manual",
        "issues_reorder_manual",
        "issues_update_manual",
        "issues_usage_manual",
        "labels_create_manual",
        "labels_delete_manual",
        "labels_update_manual",
        "maintenance_update_manual",
        "maintenance_version_manual",
        "projects_delete_manual",
        "setup_cloud_manual",
        "setup_self_host_manual",
        "skills_create_manual",
        "skills_delete_manual",
        "skills_import_from_url_manual",
        "skills_update_manual",
        "workspaces_switch_manual",
        "workspaces_unwatch_manual",
        "workspaces_watch_manual",
    }
)
_AUXILIARY_CATALOG_KEYS["signatures"] = (
    _AUXILIARY_CATALOG_KEYS["signatures"] | _MANUAL_SIGNATURE_IDS
)
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
class PublicConvention:
    category: str
    response_id: str
    typed_input_id: str | None
    input_mode: str
    presence_policy_ids: tuple[str, ...]
    command_symbol: str


@dataclass(frozen=True)
class ResponseCatalogEntry:
    response_id: str
    public_type_id: str
    wire_type_id: str | None
    decoder_id: str
    success_exit_codes: tuple[int, ...]
    malformed_output: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class UpdateFieldPolicy:
    field_name: str
    nullable: bool
    source_ref_ids: tuple[str, ...]
    presence: tuple[tuple[str, str], ...]
    clear_kind: str
    clear_source_ref_ids: tuple[str, ...]
    clear_mapping: tuple[str, ...]


@dataclass(frozen=True)
class UpdateModelPolicy:
    model_id: str
    source_ref_ids: tuple[str, ...]
    fields: tuple[UpdateFieldPolicy, ...]


@dataclass(frozen=True)
class Entrypoint:
    entrypoint_id: str
    public_symbol: str
    signature_id: str
    binding_id: str
    response_id: str
    errors: str
    convention: PublicConvention

    @property
    def category(self) -> str:
        return self.convention.category

    @property
    def typed_input_id(self) -> str | None:
        return self.convention.typed_input_id

    @property
    def input_mode(self) -> str:
        return self.convention.input_mode

    @property
    def presence_policy_ids(self) -> tuple[str, ...]:
        return self.convention.presence_policy_ids

    @property
    def command_symbol(self) -> str:
        return self.convention.command_symbol


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
    responses: tuple[ResponseCatalogEntry, ...]
    update_field_policies: tuple[UpdateModelPolicy, ...]
    test_vectors: tuple[TestVector, ...]
    raw: dict[str, object]

    @property
    def operation_ids(self) -> frozenset[str]:
        return frozenset(item.operation_id for item in self.operations)

    @property
    def vector_by_id(self) -> dict[str, TestVector]:
        return {item.vector_id: item for item in self.test_vectors}

    @property
    def response_by_id(self) -> dict[str, ResponseCatalogEntry]:
        return {item.response_id: item for item in self.responses}


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
    else:  # pragma: no cover - guarded by the closed kind check above
        raise ContractError(f"{label}.kind has no materialization path")
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


def _public_convention(value: object, label: str) -> PublicConvention:
    item = _dict(value, label)
    _exact_keys(
        item,
        frozenset(
            {
                "category",
                "response_id",
                "typed_input_id",
                "input_mode",
                "presence_policy_ids",
                "command_symbol",
            }
        ),
        label,
    )
    category = _str(item["category"], f"{label}.category")
    if category not in _OPERATION_CATEGORIES:
        raise ContractError(f"{label}.category is not a closed operation category")
    response_id = _contract_identifier(item["response_id"], f"{label}.response_id")
    if response_id not in _RESPONSE_CATALOG_IDS:
        raise ContractError(f"{label}.response_id is not an approved response")
    if response_id.startswith("action_result_") and category != "action":
        raise ContractError(f"{label} assigns an action response to a non-action category")
    if response_id.startswith("page_") and category != "collection":
        raise ContractError(f"{label} assigns a page response to a non-collection category")
    typed_input_value = item["typed_input_id"]
    if typed_input_value is None:
        typed_input_id = None
    else:
        typed_input_id = _str(typed_input_value, f"{label}.typed_input_id")
        if typed_input_id not in _TYPED_INPUT_IDS:
            raise ContractError(f"{label}.typed_input_id is not an approved request type")
    input_mode = _str(item["input_mode"], f"{label}.input_mode")
    if input_mode not in _INPUT_MODES:
        raise ContractError(f"{label}.input_mode is not a closed input mode")
    policy_ids = tuple(
        _contract_identifier(policy, f"{label}.presence_policy_ids[{index}]")
        for index, policy in enumerate(
            _list(item["presence_policy_ids"], f"{label}.presence_policy_ids")
        )
    )
    if len(set(policy_ids)) != len(policy_ids):
        raise ContractError(f"{label}.presence_policy_ids must not contain duplicates")
    if not set(policy_ids) <= _PRESENCE_POLICY_IDS:
        raise ContractError(f"{label}.presence_policy_ids contains an unknown policy")
    if typed_input_id is None:
        if input_mode != "direct" or policy_ids:
            raise ContractError(
                f"{label} without typed input must be direct and have no presence policies"
            )
    elif input_mode == "direct" or not policy_ids:
        raise ContractError(
            f"{label} with typed input must use a dual mode and non-empty presence policies"
        )
    command_symbol = _str(item["command_symbol"], f"{label}.command_symbol")
    parts = command_symbol.split(".")
    if len(parts) < 2 or any(not _PYTHON_IDENTIFIER.fullmatch(part) for part in parts):
        raise ContractError(f"{label}.command_symbol must be fully-qualified")
    if not parts[-1].endswith("_command"):
        raise ContractError(f"{label}.command_symbol must name a *_command sibling")
    return PublicConvention(
        category,
        response_id,
        typed_input_id,
        input_mode,
        policy_ids,
        command_symbol,
    )


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
                        "category",
                        "typed_input_id",
                        "input_mode",
                        "presence_policy_ids",
                        "command_symbol",
                    }
                ),
                "entrypoint",
            )
            convention = _public_convention(
                {
                    key: ep[key]
                    for key in (
                        "category",
                        "response_id",
                        "typed_input_id",
                        "input_mode",
                        "presence_policy_ids",
                        "command_symbol",
                    )
                },
                f"entrypoint[{ep_index}].convention",
            )
            public_symbol = _str(ep["public_symbol"], "entrypoint.public_symbol")
            if convention.command_symbol != f"{public_symbol}_command":
                raise ContractError("entrypoint.command_symbol must match its public symbol")
            if convention.response_id != _str(ep["response_id"], "entrypoint.response_id"):
                raise ContractError("entrypoint.response_id disagrees with its convention")
            entrypoints.append(
                Entrypoint(
                    entrypoint_id=_str(ep["entrypoint_id"], "entrypoint.entrypoint_id"),
                    public_symbol=_str(ep["public_symbol"], "entrypoint.public_symbol"),
                    signature_id=_str(ep["signature_id"], "entrypoint.signature_id"),
                    binding_id=_str(ep["binding_id"], "entrypoint.binding_id"),
                    response_id=_str(ep["response_id"], "entrypoint.response_id"),
                    errors=_str(ep["errors"], "entrypoint.errors"),
                    convention=convention,
                )
            )
        if not entrypoints:
            raise ContractError(f"operations[{index}] must approve at least one entrypoint")
        if len({entrypoint.entrypoint_id for entrypoint in entrypoints}) != len(entrypoints):
            raise ContractError(f"operations[{index}] repeats an entrypoint ID")
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


def _response_catalog(value: object) -> tuple[ResponseCatalogEntry, ...]:
    responses = _dict(value, "catalogs.responses")
    if set(responses) != _RESPONSE_CATALOG_IDS:
        raise ContractError("catalogs.responses must contain exactly the approved response IDs")
    entries: list[ResponseCatalogEntry] = []
    aliases_seen: set[str] = set()
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
                | ({"aliases"} if "aliases" in item else set())
            ),
            f"catalogs.responses[{key!r}]",
        )
        response_id = _contract_identifier(key, f"catalogs.responses key {key!r}")
        public_type_id = _str(item["public_type_id"], f"catalogs.responses[{key!r}].public_type_id")
        if (
            not public_type_id
            or "any" in public_type_id.lower()
            or "issuesummary" in public_type_id.lower()
            or public_type_id
            in {
                "object",
                "typing.Any",
            }
        ):
            raise ContractError(f"catalogs.responses[{key!r}] exposes a public Any type")
        wire_type_value = item["wire_type_id"]
        wire_type_id = (
            None
            if wire_type_value is None
            else _str(wire_type_value, f"catalogs.responses[{key!r}].wire_type_id")
        )
        decoder_id = _str(item["decoder_id"], f"catalogs.responses[{key!r}].decoder_id")
        success_exit_codes = tuple(
            _int(code, f"catalogs.responses[{key!r}].success_exit_codes[{index}]")
            for index, code in enumerate(
                _list(item["success_exit_codes"], f"catalogs.responses[{key!r}].success_exit_codes")
            )
        )
        if not success_exit_codes:
            raise ContractError(f"catalogs.responses[{key!r}] must approve an exit code")
        malformed_output = _str(
            item["malformed_output"], f"catalogs.responses[{key!r}].malformed_output"
        )
        aliases_value = item.get("aliases", [])
        aliases = tuple(
            _contract_identifier(alias, f"catalogs.responses[{key!r}].aliases[{index}]")
            for index, alias in enumerate(
                _list(aliases_value, f"catalogs.responses[{key!r}].aliases")
            )
        )
        if len(set(aliases)) != len(aliases):
            raise ContractError(f"catalogs.responses[{key!r}].aliases must not contain duplicates")
        unapproved = set(aliases) - _RESPONSE_ALIASES
        if unapproved:
            raise ContractError(
                f"catalogs.responses[{key!r}].aliases contains unapproved aliases: "
                f"{', '.join(sorted(unapproved))}"
            )
        duplicate_aliases = aliases_seen.intersection(aliases)
        if duplicate_aliases:
            raise ContractError(
                "response aliases must be unique: " + ", ".join(sorted(duplicate_aliases))
            )
        aliases_seen.update(aliases)
        entries.append(
            ResponseCatalogEntry(
                response_id,
                public_type_id,
                wire_type_id,
                decoder_id,
                success_exit_codes,
                malformed_output,
                aliases,
            )
        )
    return tuple(entries)


def _update_field_policies(value: object) -> tuple[UpdateModelPolicy, ...]:
    models = _dict(value, "catalogs.update_field_policies")
    if set(models) != set(_UPDATE_POLICY_FIELDS):
        raise ContractError(
            "catalogs.update_field_policies must contain exactly the approved update models"
        )
    result: list[UpdateModelPolicy] = []
    for model_id, raw_model in models.items():
        model = _dict(raw_model, f"update_field_policies[{model_id!r}]")
        _exact_keys(model, frozenset({"source_ref_ids", "fields"}), f"update model {model_id}")
        model_source_refs = tuple(
            _str(item, f"update model {model_id}.source_ref_ids[{index}]")
            for index, item in enumerate(
                _list(model["source_ref_ids"], f"update model {model_id}.source_ref_ids")
            )
        )
        fields = _dict(model["fields"], f"update model {model_id}.fields")
        if set(fields) != _UPDATE_POLICY_FIELDS[model_id]:
            raise ContractError(f"update model {model_id} must list its exact approved fields")
        parsed_fields: list[UpdateFieldPolicy] = []
        for field_name, raw_field in fields.items():
            field = _dict(raw_field, f"update field {model_id}.{field_name}")
            _exact_keys(
                field,
                frozenset({"nullable", "source_ref_ids", "presence", "clear"}),
                f"update field {model_id}.{field_name}",
            )
            nullable = _bool(field["nullable"], f"update field {model_id}.{field_name}.nullable")
            source_ref_ids = tuple(
                _str(item, f"update field {model_id}.{field_name}.source_ref_ids[{index}]")
                for index, item in enumerate(
                    _list(
                        field["source_ref_ids"],
                        f"update field {model_id}.{field_name}.source_ref_ids",
                    )
                )
            )
            presence = _dict(field["presence"], f"update field {model_id}.{field_name}.presence")
            _exact_keys(
                presence,
                frozenset({"omitted", "null", "empty", "zero", "false"}),
                f"update field {model_id}.{field_name}.presence",
            )
            presence_values = tuple(
                (
                    key,
                    _str(
                        presence[key],
                        f"update field {model_id}.{field_name}.presence.{key}",
                    ),
                )
                for key in ("omitted", "null", "empty", "zero", "false")
            )
            if any(value not in _UPDATE_PRESENCE_VALUES for _, value in presence_values):
                raise ContractError(
                    f"update field {model_id}.{field_name} has an unknown presence mapping"
                )
            clear = _dict(field["clear"], f"update field {model_id}.{field_name}.clear")
            _exact_keys(
                clear,
                frozenset({"kind", "source_ref_ids", "mapping"}),
                f"update field {model_id}.{field_name}.clear",
            )
            clear_kind = _str(clear["kind"], f"update field {model_id}.{field_name}.clear.kind")
            if clear_kind not in _UPDATE_CLEAR_KINDS:
                raise ContractError(
                    f"update field {model_id}.{field_name} has an unknown clear kind"
                )
            clear_source_refs = tuple(
                _str(item, f"update field {model_id}.{field_name}.clear.source_ref_ids[{index}]")
                for index, item in enumerate(
                    _list(
                        clear["source_ref_ids"],
                        f"update field {model_id}.{field_name}.clear.source_ref_ids",
                    )
                )
            )
            clear_mapping = tuple(
                _str(item, f"update field {model_id}.{field_name}.clear.mapping[{index}]")
                for index, item in enumerate(
                    _list(clear["mapping"], f"update field {model_id}.{field_name}.clear.mapping")
                )
            )
            if nullable and (clear_kind == "none" or not clear_source_refs or not clear_mapping):
                raise ContractError(
                    f"nullable update field {model_id}.{field_name} lacks distinct clear evidence"
                )
            if not nullable and (
                clear_kind not in {"none", "empty_collection"}
                or (clear_kind == "none" and (clear_source_refs or clear_mapping))
                or (
                    clear_kind == "empty_collection"
                    and (not clear_source_refs or not clear_mapping)
                )
            ):
                raise ContractError(
                    f"non-nullable update field {model_id}.{field_name} has a clear mapping"
                )
            if clear_kind == "composite" and len(clear_mapping) < 2:
                raise ContractError(
                    f"composite clear for {model_id}.{field_name} must contain multiple steps"
                )
            if clear_kind == "empty_collection" and presence_values[2][1] != "emit":
                raise ContractError(
                    f"collection clear for {model_id}.{field_name} must preserve an empty value"
                )
            parsed_fields.append(
                UpdateFieldPolicy(
                    field_name,
                    nullable,
                    source_ref_ids,
                    presence_values,
                    clear_kind,
                    clear_source_refs,
                    clear_mapping,
                )
            )
        result.append(UpdateModelPolicy(model_id, model_source_refs, tuple(parsed_fields)))
    return tuple(result)


def _closed_auxiliary_catalogs(catalogs: dict[str, object]) -> tuple[ResponseCatalogEntry, ...]:
    """Validate retained contract metadata before any generator can observe it."""

    for name in ("types", "signatures", "decoders", "validators"):
        values = _dict(catalogs[name], f"catalogs.{name}")
        if set(values) != _AUXILIARY_CATALOG_KEYS[name]:
            raise ContractError(f"catalogs.{name} must contain exactly the approved keys")
        for key, value in values.items():
            _str(key, f"catalogs.{name} key")
            _str(value, f"catalogs.{name}[{key!r}]")
    presence_catalog = _dict(catalogs["presence"], "catalogs.presence")
    if set(presence_catalog) != _PRESENCE_POLICY_IDS:
        raise ContractError("catalogs.presence must contain exactly the normalized policy IDs")
    for name in ("binding_source_refs", "mapping_presence"):
        values = _dict(catalogs[name], f"catalogs.{name}")
        if set(values) != _AUXILIARY_CATALOG_KEYS["signatures"]:
            raise ContractError(f"catalogs.{name} must contain exactly the binding keys")
        for key, value in values.items():
            _str(key, f"catalogs.{name} key")
            for index, item in enumerate(_list(value, f"catalogs.{name}[{key!r}]")):
                _str(item, f"catalogs.{name}[{key!r}][{index}]")
    bindings_for_presence = _dict(catalogs["bindings"], "catalogs.bindings")
    mapping_presence = _dict(catalogs["mapping_presence"], "catalogs.mapping_presence")
    for key, value in mapping_presence.items():
        policies = _list(value, f"catalogs.mapping_presence[{key!r}]")
        mappings = _list(
            _dict(bindings_for_presence[key], f"catalogs.bindings[{key!r}]")["mappings"],
            f"catalogs.bindings[{key!r}].mappings",
        )
        if len(policies) != len(mappings):
            raise ContractError(
                f"catalogs.mapping_presence[{key!r}] must map every binding field exactly once"
            )
        for index, policy in enumerate(policies):
            if (
                _str(policy, f"catalogs.mapping_presence[{key!r}][{index}]")
                not in _PRESENCE_POLICY_IDS
            ):
                raise ContractError(
                    f"catalogs.mapping_presence[{key!r}] references an unknown policy"
                )
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
    return _response_catalog(catalogs["responses"])


def _validate_direct_bindings(catalog: ContractCatalog) -> None:
    """Reject request-object plumbing from direct-only public entry points.

    Direct signatures are the approved public schema after the SDK migration.
    Keeping this check at the approved-contract boundary prevents an old
    ``request.*`` mapping from silently surviving while runtime code is being
    migrated in later stages.
    """

    descriptors = {item.descriptor_id: item for item in catalog.binding_descriptors}
    signatures = _dict(
        _dict(catalog.raw["catalogs"], "catalogs")["signatures"], "catalogs.signatures"
    )
    raw_bindings = _dict(
        _dict(catalog.raw["catalogs"], "catalogs")["bindings"], "catalogs.bindings"
    )
    for operation in catalog.operations:
        for entrypoint in operation.entrypoints:
            signature = _str(
                signatures[entrypoint.signature_id],
                f"catalogs.signatures[{entrypoint.signature_id!r}]",
            )
            if "options: OperationOptions | None = None" not in signature:
                raise ContractError(
                    f"{operation.operation_id}.{entrypoint.entrypoint_id} signature must carry "
                    "the final optional OperationOptions parameter"
                )
            if entrypoint.input_mode != "direct":
                continue
            if re.search(r"\brequest(?:[._\s]|$)", signature):
                raise ContractError(
                    f"{operation.operation_id}.{entrypoint.entrypoint_id} direct signature "
                    "must not mention a request object"
                )
            descriptor = descriptors[entrypoint.binding_id]
            stale = [
                source
                for source, _binding, _destination in descriptor.mappings
                if source == "request" or source.startswith("request.")
            ]
            binding = _dict(
                raw_bindings[entrypoint.binding_id],
                f"catalogs.bindings[{entrypoint.binding_id!r}]",
            )
            for index, raw_mapping in enumerate(
                _list(binding["mappings"], f"catalogs.bindings[{entrypoint.binding_id!r}].mappings")
            ):
                mapping = _list(
                    raw_mapping,
                    f"catalogs.bindings[{entrypoint.binding_id!r}].mappings[{index}]",
                )
                if mapping and (
                    _str(mapping[0], "binding mapping source") == "request"
                    or _str(mapping[0], "binding mapping source").startswith("request.")
                ):
                    stale.append(_str(mapping[0], "binding mapping source"))
            stale.extend(
                constraint
                for constraint in _list(
                    binding["constraints"],
                    f"catalogs.bindings[{entrypoint.binding_id!r}].constraints",
                )
                if _str(constraint, "binding constraint").startswith("request.")
            )
            if stale:
                raise ContractError(
                    f"{operation.operation_id}.{entrypoint.entrypoint_id} contains stale "
                    f"request mappings: {', '.join(stale)}"
                )
            if operation.operation_id == "cli.command":
                if entrypoint.category != "action" or entrypoint.response_id != "cli_result":
                    raise ContractError("cli.command must remain an action returning cli_result")
                if descriptor.command or descriptor.mappings:
                    raise ContractError("cli.command must use dynamic argv without fixed mappings")


def load_contract(path: pathlib.Path) -> ContractCatalog:
    try:
        raw_value = cast("object", json.loads(path.read_text(encoding="utf-8")))
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
            "update_field_policies",
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
    responses = _closed_auxiliary_catalogs(catalogs)
    update_field_policies = _update_field_policies(catalogs["update_field_policies"])
    enum_definitions = _enum_definitions(catalogs["enum_definitions"])
    validator_definitions = _validator_definitions(catalogs["validator_definitions"])
    binding_descriptors = _binding_descriptors(catalogs["binding_descriptors"])
    vectors_raw = _dict(catalogs["test_vectors"], "catalogs.test_vectors")
    vectors = tuple(_parse_vector(value, key) for key, value in vectors_raw.items())
    if len(vectors) != 58:
        raise ContractError(f"expected 58 test vectors, got {len(vectors)}")
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
                "local_only_symbols",
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
    for index, symbol in enumerate(_list(scope["local_only_symbols"], "scope.local_only_symbols")):
        _str(symbol, f"scope.local_only_symbols[{index}]")
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
    if len(operation_ids) != len(operations):
        raise ContractError("operations IDs must be unique")
    if operation_ids != {
        _str(value, "scope.operation_ids")
        for value in _list(scope["operation_ids"], "scope.operation_ids")
    }:
        raise ContractError("scope.operation_ids must match operations")
    for vector in vectors:
        if vector.operation_id not in operation_ids:
            raise ContractError(f"{vector.vector_id} references unknown operation")
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
        responses=responses,
        update_field_policies=update_field_policies,
        test_vectors=vectors,
        raw=raw,
    )


def validate_contract(path: pathlib.Path) -> ContractCatalog:
    contract = load_contract(path)
    _validate_direct_bindings(contract)
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
    binding_catalog = _dict(
        _dict(contract.raw["catalogs"], "catalogs")["bindings"], "catalogs.bindings"
    )
    for descriptor in contract.binding_descriptors:
        binding = _dict(binding_catalog[descriptor.descriptor_id], "catalogs.bindings entry")
        catalog_command = tuple(
            _str(value, "catalog binding command")
            for value in _list(binding["command"], "catalog binding command")
        )
        if catalog_command != descriptor.command:
            raise ContractError(
                f"binding descriptor {descriptor.descriptor_id!r} disagrees with binding catalog"
            )
    signatures = _dict(
        _dict(contract.raw["catalogs"], "catalogs")["signatures"], "catalogs.signatures"
    )
    responses = _dict(
        _dict(contract.raw["catalogs"], "catalogs")["responses"], "catalogs.responses"
    )
    response_aliases = {
        alias: response.response_id for response in contract.responses for alias in response.aliases
    }
    if response_aliases.get("issue_search") != "page_issues":
        raise ContractError("issue_search must be the approved alias of page_issues")
    for operation in contract.operations:
        if operation.compatibility not in {"compatible", "intentionally_changed"}:
            raise ContractError(
                f"operation {operation.operation_id!r} has an invalid compatibility value"
            )
        source_ref_ids = {item.source_ref_id for item in contract.source_refs}
        test_ref_ids = {item.test_ref_id for item in contract.test_refs}
        if not operation.source_ref_ids or not operation.test_ref_ids:
            raise ContractError(
                f"operation {operation.operation_id!r} must have source and test evidence"
            )
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
    source_ref_ids = {item.source_ref_id for item in contract.source_refs}
    for model in contract.update_field_policies:
        if not set(model.source_ref_ids) <= source_ref_ids:
            raise ContractError(f"update model {model.model_id!r} references an unknown source ref")
        for field in model.fields:
            if not set(field.source_ref_ids) <= source_ref_ids:
                raise ContractError(
                    f"update field {model.model_id}.{field.field_name} references an unknown source ref"
                )
            if not set(field.clear_source_ref_ids) <= source_ref_ids:
                raise ContractError(
                    f"clear mapping {model.model_id}.{field.field_name} references an unknown source ref"
                )
    descriptors_by_pair = {
        (descriptor.operation_id, descriptor.entrypoint_id): descriptor
        for descriptor in contract.binding_descriptors
    }
    raw_catalogs = _dict(contract.raw["catalogs"], "catalogs")
    raw_bindings = _dict(raw_catalogs["bindings"], "catalogs.bindings")
    for vector in contract.test_vectors:
        descriptor = descriptors_by_pair[(vector.operation_id, vector.entrypoint_id)]
        command = tuple(vector.expected_argv[: len(descriptor.command)])
        if command != descriptor.command:
            binding = _dict(
                raw_bindings[descriptor.descriptor_id],
                f"catalogs.bindings[{descriptor.descriptor_id!r}]",
            )
            constraints = tuple(
                _str(item, "binding.constraint")
                for item in _list(binding["constraints"], "binding.constraints")
            )
            read_ids = tuple(
                item.removeprefix("all_unset_reads:")
                for item in constraints
                if item.startswith("all_unset_reads:")
            )
            empty_request = not vector.kwargs and all(
                item.get("kind") != "request" or item.get("fields") == [] for item in vector.args
            )
            read_descriptor = next(
                (
                    item
                    for item in contract.binding_descriptors
                    if item.operation_id in read_ids and item.entrypoint_id == vector.entrypoint_id
                ),
                None,
            )
            if (
                not empty_request
                or len(read_ids) != 1
                or read_descriptor is None
                or tuple(vector.expected_argv[: len(read_descriptor.command)])
                != read_descriptor.command
            ):
                raise ContractError(
                    f"{vector.vector_id} disagrees with binding {descriptor.descriptor_id!r}"
                )
    base_count = sum(":canonical" in vector.vector_id for vector in contract.test_vectors)
    variant_count = len(contract.test_vectors) - base_count
    if (base_count, variant_count) != (46, 12):
        raise ContractError(
            f"expected 46 entrypoint-base and 12 variant vectors, got {base_count}/{variant_count}"
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
    expected_item_dicts = [
        cast("dict[str, object]", item) for item in expected_items if isinstance(item, dict)
    ]
    if len(expected_item_dicts) != len(expected_items) or not all(
        item.get("kind") == "primitive" and isinstance(item.get("value"), str)
        for item in expected_item_dicts
    ):
        raise AssertionError("page_items IDs must be primitive strings")
    expected_ids = tuple(cast("str", item["value"]) for item in expected_item_dicts)
    page = cast("Page[_HasId]", result)
    actual_ids = tuple(item.id for item in page.items)
    if actual_ids != expected_ids:
        raise AssertionError(f"expected page IDs {expected_ids}, got {actual_ids}")
