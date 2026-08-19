from __future__ import annotations

import hashlib
import inspect
import json
import os
import pathlib
import subprocess
import tempfile
from dataclasses import dataclass, replace
from typing import cast

import pytest

from multica_py._generated import approved_sdk
from multica_py.entities.comments import Comment
from multica_py.models.common import Page
from multica_py.resources.squad_members import SquadMemberResource
from tools.upstream_contract.contract import (
    ContractError,
    ResultAssertion,
    assert_result,
    load_contract,
    validate_contract,
)
from tools.upstream_contract.evidence import ReleaseIdentity, collect
from tools.upstream_contract.generation import _validate_transient_projection, render_files

APPROVED = pathlib.Path("contracts/sdk-contract.json")

_SQUAD_MEMBER_OPERATION_IDS = (
    "squads.members.add",
    "squads.members.list",
    "squads.members.remove",
)
_SQUAD_MEMBER_DESCRIPTOR_NAMES = (
    "SQUAD_MEMBERS_ADD_BINDING",
    "SQUAD_MEMBERS_LIST_BINDING",
    "SQUAD_MEMBERS_REMOVE_BINDING",
)
_SQUAD_MEMBER_BUILDER_NAMES = (
    "_build_squad_members_add_argv",
    "_build_squad_members_list_argv",
    "_build_squad_members_remove_argv",
)


@dataclass(frozen=True)
class InvalidContractCase:
    case_id: str
    mutate: str


INVALID_CONTRACT_CASES = (
    InvalidContractCase("schema-version", "schema_version"),
    InvalidContractCase("vector-unknown-field", "vector_unknown_field"),
    InvalidContractCase("vector-id-mismatch", "vector_id_mismatch"),
    InvalidContractCase("naive-datetime", "naive_datetime"),
    InvalidContractCase("decoded-type", "decoded_type"),
    InvalidContractCase("generated-newline", "generated_newline"),
    InvalidContractCase("generated-parentheses", "generated_parentheses"),
    InvalidContractCase("generated-unicode", "generated_unicode"),
    InvalidContractCase("generated-keyword", "generated_keyword"),
    InvalidContractCase("source-ref-parent", "source_ref_parent"),
    InvalidContractCase("source-ref-commit", "source_ref_commit"),
    InvalidContractCase("request-tag", "request_tag"),
    InvalidContractCase("auxiliary-catalog-key", "auxiliary_catalog_key"),
    InvalidContractCase("validator-enum", "validator_enum"),
    InvalidContractCase("duplicate-descriptor", "duplicate_descriptor"),
    InvalidContractCase("descriptor-entrypoint", "descriptor_entrypoint"),
    InvalidContractCase("generated-namespace", "generated_namespace"),
    InvalidContractCase("generated-dataclass", "generated_dataclass"),
    InvalidContractCase("generated-strenum", "generated_strenum"),
    InvalidContractCase("generated-builtin-parameter", "generated_builtin_parameter"),
    InvalidContractCase("generated-enum-sunder", "generated_enum_sunder"),
    InvalidContractCase("convention-missing", "convention_missing"),
    InvalidContractCase("convention-category", "convention_category"),
    InvalidContractCase("convention-input-mode", "convention_input_mode"),
    InvalidContractCase("convention-typed-input", "convention_typed_input"),
    InvalidContractCase("stale-request-dto", "stale_request_dto"),
    InvalidContractCase("convention-presence", "convention_presence"),
    InvalidContractCase("convention-presence-empty", "convention_presence_empty"),
    InvalidContractCase("direct-request-mapping", "direct_request_mapping"),
    InvalidContractCase("missing-options", "missing_options"),
    InvalidContractCase("summary-response", "summary_response"),
    InvalidContractCase("duplicate-response-alias", "duplicate_response_alias"),
    InvalidContractCase("unapproved-response-alias", "unapproved_response_alias"),
    InvalidContractCase("raw-command-category", "raw_command_category"),
    InvalidContractCase("convention-command", "convention_command"),
    InvalidContractCase("response-extra", "response_extra"),
    InvalidContractCase("response-any", "response_any"),
    InvalidContractCase("response-category", "response_category"),
    InvalidContractCase("operation-evidence", "operation_evidence"),
    InvalidContractCase("nullable-clear-evidence", "nullable_clear_evidence"),
    InvalidContractCase("update-source-ref", "update_source_ref"),
    InvalidContractCase("mapping-presence-length", "mapping_presence_length"),
    InvalidContractCase("mapping-presence-unknown", "mapping_presence_unknown"),
    InvalidContractCase("duplicate-entrypoint", "duplicate_entrypoint"),
    InvalidContractCase("non-bijective-surface", "non_bijective_surface"),
)


def _mutated_contract(tmp_path: pathlib.Path, mutation: str) -> pathlib.Path:
    document = json.loads(APPROVED.read_text(encoding="utf-8"))
    if mutation == "schema_version":
        document["schema_version"] = 2
    elif mutation == "vector_unknown_field":
        vector = next(iter(document["catalogs"]["test_vectors"].values()))
        vector["unexpected"] = True
    elif mutation == "vector_id_mismatch":
        vector = next(iter(document["catalogs"]["test_vectors"].values()))
        vector["vector_id"] = "generated:wrong:default:canonical"
    elif mutation == "naive_datetime":
        vector = document["catalogs"]["test_vectors"][
            "generated:issues.comments.list:flat:canonical"
        ]
        next(item for item in vector["kwargs"] if item[0] == "since")[1]["value"] = (
            "2026-07-12T10:00:00"
        )
    elif mutation == "decoded_type":
        vector = document["catalogs"]["test_vectors"][
            "generated:issues.comments.add:default:canonical"
        ]
        vector["assertion"]["expected"]["value"] = "not.approved.Type"
    elif mutation == "generated_newline":
        document["catalogs"]["enum_definitions"][0]["public_name"] = "Safe\nName"
    elif mutation == "generated_parentheses":
        document["catalogs"]["validator_definitions"][0]["name"] = "validate(value)"
    elif mutation == "generated_unicode":
        document["catalogs"]["enum_definitions"][0]["members"][0]["name"] = "naïve"
    elif mutation == "generated_keyword":
        document["catalogs"]["binding_descriptors"][0]["descriptor_id"] = "class"
    elif mutation == "source_ref_parent":
        document["source_refs"][0]["path"] = "../outside.go"
    elif mutation == "source_ref_commit":
        document["source_refs"][0]["commit"] = "0" * 40
    elif mutation == "request_tag":
        vector = document["catalogs"]["test_vectors"][
            "generated:issues.comments.list:flat:canonical"
        ]
        vector["kwargs"][0][1]["kind"] = "request"
    elif mutation == "auxiliary_catalog_key":
        document["catalogs"]["types"]["extra"] = "extra"
    elif mutation == "validator_enum":
        next(
            item
            for item in document["catalogs"]["validator_definitions"]
            if item["body_kind"].startswith("one_of:")
        )["body_kind"] = "one_of:Unapproved"
    elif mutation == "duplicate_descriptor":
        document["catalogs"]["binding_descriptors"].append(
            document["catalogs"]["binding_descriptors"][0].copy()
        )
    elif mutation == "descriptor_entrypoint":
        document["catalogs"]["binding_descriptors"][0]["entrypoint_id"] = "wrong"
    elif mutation == "generated_namespace":
        document["catalogs"]["enum_definitions"][0]["public_name"] = "OPERATION_BINDINGS"
    elif mutation == "generated_dataclass":
        document["catalogs"]["enum_definitions"][0]["public_name"] = "dataclass"
    elif mutation == "generated_strenum":
        document["catalogs"]["validator_definitions"][0]["name"] = "StrEnum"
    elif mutation == "generated_builtin_parameter":
        document["catalogs"]["validator_definitions"][0]["parameter_name"] = "str"
    elif mutation == "generated_enum_sunder":
        document["catalogs"]["enum_definitions"][0]["members"][0]["name"] = "_ignore_"
    elif mutation.startswith("convention_"):
        entrypoint = document["operations"][0]["entrypoints"][0]
        if mutation == "convention_missing":
            del entrypoint["category"]
        elif mutation == "convention_category":
            entrypoint["category"] = "unknown"
        elif mutation == "convention_input_mode":
            entrypoint["input_mode"] = "object_only"
        elif mutation == "convention_typed_input":
            entrypoint["typed_input_id"] = "UnknownRequest"
        elif mutation == "convention_presence":
            entrypoint["presence_policy_ids"] = ["unknown_policy"]
        elif mutation == "convention_presence_empty":
            operation = next(
                item for item in document["operations"] if item["operation_id"] == "issues.list"
            )
            entrypoint = operation["entrypoints"][0]
            entrypoint["presence_policy_ids"] = []
        elif mutation == "convention_command":
            entrypoint["command_symbol"] = "not_a_command"
    elif mutation == "stale_request_dto":
        operation = next(
            item for item in document["operations"] if item["operation_id"] == "agents.create"
        )
        operation["entrypoints"][0]["typed_input_id"] = "AgentCreateRequest"
    elif mutation == "response_extra":
        document["catalogs"]["responses"]["unexpected"] = {
            "public_type_id": "Unexpected",
            "wire_type_id": None,
            "decoder_id": "decode_none",
            "success_exit_codes": [0],
            "malformed_output": "raise",
        }
    elif mutation == "response_any":
        document["catalogs"]["responses"]["action_result_none"]["public_type_id"] = "Any"
    elif mutation == "response_category":
        entrypoint = document["operations"][0]["entrypoints"][0]
        entrypoint["response_id"] = "page_comments"
        entrypoint["category"] = "retrieve"
    elif mutation == "direct_request_mapping":
        operation = next(
            item for item in document["operations"] if item["operation_id"] == "agents.create"
        )
        entrypoint = operation["entrypoints"][0]
        descriptor = next(
            item
            for item in document["catalogs"]["binding_descriptors"]
            if item["descriptor_id"] == entrypoint["binding_id"]
        )
        descriptor["mappings"] = [
            {"source": "request.name", "binding": "pos:0", "destination": "path:name"}
        ]
    elif mutation == "missing_options":
        document["catalogs"]["signatures"]["agent_get"] = "(agent_id: str) -> Agent"
    elif mutation == "summary_response":
        document["catalogs"]["responses"]["page_issues"]["public_type_id"] = "Page[IssueSummary]"
    elif mutation == "duplicate_response_alias":
        document["catalogs"]["responses"]["page_issues"]["aliases"].append("issue_search")
    elif mutation == "unapproved_response_alias":
        document["catalogs"]["responses"]["page_issues"]["aliases"].append("issue_lookup")
    elif mutation == "raw_command_category":
        entrypoint = next(
            entrypoint
            for operation in document["operations"]
            if operation["operation_id"] == "cli.command"
            for entrypoint in operation["entrypoints"]
        )
        entrypoint["category"] = "collection"
    elif mutation == "operation_evidence":
        document["operations"][0]["source_ref_ids"] = []
    elif mutation == "nullable_clear_evidence":
        field = document["catalogs"]["update_field_policies"]["issues.update"]["fields"][
            "description"
        ]
        field["clear"]["source_ref_ids"] = []
    elif mutation == "update_source_ref":
        document["catalogs"]["update_field_policies"]["projects.update"]["fields"]["name"][
            "source_ref_ids"
        ] = ["missing-source-ref"]
    elif mutation == "mapping_presence_length":
        document["catalogs"]["mapping_presence"]["project_update"].pop()
    elif mutation == "mapping_presence_unknown":
        document["catalogs"]["mapping_presence"]["project_update"][0] = "unknown-policy"
    elif mutation == "duplicate_entrypoint":
        operation = next(item for item in document["operations"] if len(item["entrypoints"]) > 1)
        operation["entrypoints"][1]["entrypoint_id"] = operation["entrypoints"][0]["entrypoint_id"]
    elif mutation == "non_bijective_surface":
        document["operations"].pop()
    destination = tmp_path / f"{mutation}.json"
    destination.write_text(json.dumps(document), encoding="utf-8")
    return destination


@pytest.mark.parametrize("case", INVALID_CONTRACT_CASES, ids=lambda case: case.case_id)
def test_closed_contract_rejects_invalid_rows(
    case: InvalidContractCase, tmp_path: pathlib.Path
) -> None:
    with pytest.raises(ContractError):
        validate_contract(_mutated_contract(tmp_path, case.mutate))


def test_v3_catalogs_are_closed() -> None:
    contract = validate_contract(APPROVED)
    assert len(contract.test_vectors) == 89
    assert sum(":variant:" not in vector.vector_id for vector in contract.test_vectors) == 76
    assert sum(":variant:" in vector.vector_id for vector in contract.test_vectors) == 13
    assert {item.public_name for item in contract.enum_definitions} == {
        "IssueSort",
        "SortDirection",
        "AutopilotExecutionMode",
    }
    assert all(item.parameter_name.isidentifier() for item in contract.validator_definitions)


def test_failed_pilot_rollback_binds_descriptors_to_manual_resource() -> None:
    spec = pathlib.Path("openspec/specs/upstream-contract/spec.md").read_text(encoding="utf-8")
    assert "only when the pilot's stop/go decision succeeds" in spec
    assert "the rollback SHALL be the normative terminal state" in spec
    assert "generation SHALL remain descriptor-only" in spec

    rendered_runtime = render_files(APPROVED)[0].content.decode("utf-8")
    generated_operation_ids = {binding.operation_id for binding in approved_sdk.OPERATION_BINDINGS}
    assert set(_SQUAD_MEMBER_OPERATION_IDS) <= generated_operation_ids
    for descriptor_name in _SQUAD_MEMBER_DESCRIPTOR_NAMES:
        assert descriptor_name in rendered_runtime
        assert hasattr(approved_sdk, descriptor_name)
    for builder_name in _SQUAD_MEMBER_BUILDER_NAMES:
        assert builder_name not in rendered_runtime
        assert not hasattr(approved_sdk, builder_name)

    resource_source = inspect.getsource(SquadMemberResource)
    assert all(builder_name not in resource_source for builder_name in _SQUAD_MEMBER_BUILDER_NAMES)
    assert '("squad", "member", "list", squad_id)' in resource_source
    assert '("squad", "member", "add", squad_id, member_id)' in resource_source
    assert '("squad", "member", "remove", squad_id, member_id)' in resource_source
    assert resource_source.count("validate_nonblank(squad_id)") == 3


def test_public_conventions_and_response_catalog_are_typed_and_closed() -> None:
    contract = validate_contract(APPROVED)
    entrypoints = tuple(
        entrypoint for operation in contract.operations for entrypoint in operation.entrypoints
    )
    assert len(entrypoints) == sum(len(operation.entrypoints) for operation in contract.operations)
    assert all(entrypoint.command_symbol.endswith("_command") for entrypoint in entrypoints)
    assert all(
        entrypoint.category
        in {
            "retrieve",
            "create",
            "update",
            "collection",
            "action",
            "process",
            "scalar",
            "mapping",
        }
        for entrypoint in entrypoints
    )
    assert {
        "page_agent",
        "page_comments",
        "page_project",
        "page_workspace",
        "action_result_none",
        "action_result_str",
        "action_result_repository_mutation_result",
        "action_result_runtime_update_result",
    } <= contract.response_by_id.keys()
    assert all("any" not in response.public_type_id.lower() for response in contract.responses)
    assert all("IssueSummary" not in response.public_type_id for response in contract.responses)
    catalogs = cast("dict[str, object]", contract.raw["catalogs"])
    presence = cast("dict[str, object]", catalogs["presence"])
    assert set(presence) == {
        "omit",
        "nullable_clear",
        "required_nonnull",
        "empty_present",
        "empty_collection_clear",
        "false_present",
        "zero_present",
    }
    bindings = cast("dict[str, object]", catalogs["bindings"])
    mapping_presence = cast("dict[str, object]", catalogs["mapping_presence"])
    assert all(
        len(cast("list[object]", cast("dict[str, object]", bindings[key])["mappings"]))
        == len(cast("list[object]", value))
        for key, value in mapping_presence.items()
    )


def test_simplified_direct_surface_and_bound_response_aliases() -> None:
    document = json.loads(APPROVED.read_text(encoding="utf-8"))
    catalogs = document["catalogs"]
    removed_dtos = {
        "AgentCreateRequest",
        "AgentUpdateRequest",
        "AutopilotTriggerCreate",
        "AutopilotTriggerUpdate",
        "AutopilotUpdateRequest",
        "CommentListFlatRequest",
        "CommentListRecentRequest",
        "CommentListThreadRequest",
        "IssueAssignmentRequest",
        "IssueCreateRequest",
        "IssueReorderRequest",
        "IssueUpdateRequest",
        "LabelUpdateRequest",
        "MetadataListRequest",
        "MetadataSetRequest",
        "ProjectCreateRequest",
        "ProjectResourceAddLocalDirectoryRequest",
        "ProjectResourceUpdateLocalDirectoryRequest",
        "ProjectUpdateRequest",
        "RuntimeUpdate",
        "SkillCreateRequest",
        "SkillUpdateRequest",
        "UserProfileUpdate",
    }
    entrypoints = tuple(
        entrypoint
        for operation in document["operations"]
        for entrypoint in operation["entrypoints"]
    )
    migrated = tuple(
        entrypoint
        for entrypoint in entrypoints
        if entrypoint["public_symbol"]
        in {
            "multica_py.resources.agents.AgentResource.create",
            "multica_py.resources.agents.AgentResource.update",
            "multica_py.resources.autopilots.AutopilotResource.trigger_add",
            "multica_py.resources.autopilots.AutopilotResource.trigger_update",
            "multica_py.resources.autopilots.AutopilotResource.update",
            "multica_py.resources.issue_comments.IssueCommentResource.list_flat",
            "multica_py.resources.issue_comments.IssueCommentResource.list_thread",
            "multica_py.resources.issue_comments.IssueCommentResource.list_recent",
            "multica_py.resources.issues.IssueResource.assign",
            "multica_py.resources.issues.IssueResource.create",
            "multica_py.resources.issues.IssueResource.reorder",
            "multica_py.resources.issues.IssueResource.update",
            "multica_py.resources.issue_metadata.IssueMetadataResource.query",
            "multica_py.resources.issue_metadata.IssueMetadataResource.set_typed",
            "multica_py.resources.labels.LabelResource.update",
            "multica_py.resources.projects.ProjectResource.create",
            "multica_py.resources.projects.ProjectResource.update",
            "multica_py.resources.project_resources.ProjectResourceCollection.add_local_directory",
            "multica_py.resources.project_resources.ProjectResourceCollection.update_local_directory",
            "multica_py.resources.runtimes.RuntimeResource.update",
            "multica_py.resources.skills.SkillResource.create",
            "multica_py.resources.skills.SkillResource.update",
            "multica_py.resources.users.UserResource.profile_update",
        }
    )
    assert len(migrated) == 23
    assert all(item["typed_input_id"] is None for item in migrated)
    assert all(item["input_mode"] == "direct" for item in migrated)
    assert all(not item["presence_policy_ids"] for item in migrated)
    assert all(
        "OperationOptions" in catalogs["signatures"][item["signature_id"]] for item in migrated
    )
    assert not any(item.get("typed_input_id") in removed_dtos for item in entrypoints)
    assert not removed_dtos & set(catalogs["update_field_policies"])
    assert not any(
        source == "request" or source.startswith("request.")
        for binding in catalogs["bindings"].values()
        for source, _binding, _destination in binding["mappings"]
    )

    operation_ids = {item["operation_id"] for item in document["operations"]}
    assert {
        "issues.unassign",
        "issues.move_to_top",
        "issues.move_to_bottom",
        "issues.move_before",
        "issues.move_after",
        "projects.issues.create",
        "cli.command",
        "issues.refresh",
        "projects.refresh",
    } <= operation_ids
    assert document["scope"]["local_only_symbols"] == [
        "multica_py.resources.issues.Issue.permalink",
        "multica_py.resources.projects.Project.permalink",
    ]
    assert catalogs["responses"]["page_issues"]["public_type_id"] == "Page[Issue]"
    assert catalogs["responses"]["page_issues"]["aliases"] == ["issue_search"]
    assert validate_contract(APPROVED).response_by_id["page_issues"].aliases == ("issue_search",)
    assert all(
        "options: OperationOptions | None = None" in signature
        for signature in catalogs["signatures"].values()
    )
    assert "IssueSummary" not in catalogs["types"]


def test_update_field_policies_are_explicit_and_source_pinned() -> None:
    contract = validate_contract(APPROVED)
    policies = {model.model_id: model for model in contract.update_field_policies}
    assert set(policies) == {
        "projects.update",
        "agents.update",
        "skills.update",
        "issues.update",
        "autopilots.update",
        "autopilots.trigger_update",
        "labels.update",
        "projects.resources.update_local_directory",
        "runtimes.update",
        "users.profile_update",
    }
    issue = {field.field_name: field for field in policies["issues.update"].fields}
    assert issue["assignee_id"].clear_kind == "composite"
    assert len(issue["assignee_id"].clear_mapping) >= 2
    assert issue["parent_id"].clear_mapping == ("--parent", "empty-string")
    assert all(field.source_ref_ids for model in policies.values() for field in model.fields)
    assert all(
        field.clear_source_ref_ids
        for model in policies.values()
        for field in model.fields
        if field.nullable or field.clear_kind != "none"
    )


def test_current_target_and_source_refs_are_pinned_to_v0428() -> None:
    contract = load_contract(APPROVED)
    assert contract.target.version == "0.4.28"
    assert contract.target.tag == "v0.4.28"
    assert contract.target.commit == "38c992ad0a757434fb51584fa34e3bc57d1b78e1"
    assert contract.target.release_id == "371790559"
    assert (
        contract.target.release_provenance_ref
        == ".devlocal/upstream-contract/v0.4.20..v0.4.28/release/release-verification.json"
    )
    assert {ref.commit for ref in contract.source_refs} == {contract.target.commit}
    stale_commit = "93342d04a7a9f788fec921e5aa736f86c7f22d8f"
    assert stale_commit not in {ref.commit for ref in contract.source_refs}
    assert stale_commit not in APPROVED.read_text(encoding="utf-8")
    assert all(
        ref.commit != "ecbdbda09e7b2be56cd9ccc55cee1ee360222d18" for ref in contract.source_refs
    )


def test_v0420_delta_source_refs_cover_copy_search_and_runtime_delete() -> None:
    contract = load_contract(APPROVED)
    refs = {ref.source_ref_id: ref for ref in contract.source_refs}
    assert {
        "S-AGENT-COPY-CMD",
        "S-AGENT-COPY-FLAGS",
        "S-AGENT-COPY-RUN",
        "S-AGENT-PERMISSIONS",
        "S-AGENT-MAX-CONCURRENCY",
        "S-ISSUE-SEARCH-CMD",
        "S-ISSUE-SEARCH-FLAGS",
        "S-ISSUE-SEARCH-RUN",
        "S-ISSUE-SEARCH-RESPONSE",
        "S-ISSUE-SEARCH-QUERY",
        "S-ISSUE-SEARCH-ENCODE",
        "S-RUNTIME-DELETE-CMD",
        "S-RUNTIME-DELETE-RUN",
        "S-RUNTIME-DELETE-CONFLICT",
    } <= refs.keys()
    assert refs["S-AGENT-COPY-RUN"].path == "server/cmd/multica/cmd_agent_copy.go"
    assert refs["S-ISSUE-SEARCH-RESPONSE"].path == "server/internal/handler/issue.go"
    assert "unbind-agents-and-delete" in refs["S-RUNTIME-DELETE-RUN"].symbol


def test_v0420_governs_copy_search_and_rejects_external_tag_commands(
    tmp_path: pathlib.Path,
) -> None:
    document = json.loads(APPROVED.read_text(encoding="utf-8"))
    operations = {item["operation_id"]: item for item in document["operations"]}
    assert {"agents.copy", "issues.search", "autopilots.trigger"} <= operations.keys()
    assert document["catalogs"]["bindings"]["agent_copy"]["command"] == ["agent", "copy"]
    assert document["catalogs"]["bindings"]["issue_search"]["command"] == [
        "issue",
        "search",
    ]
    assert document["catalogs"]["bindings"]["autopilot_trigger"]["command"] == [
        "autopilot",
        "trigger",
    ]
    assert len(document["catalogs"]["mapping_presence"]["agent_copy"]) == 14
    assert document["catalogs"]["responses"]["page_issues"]["malformed_output"] == (
        "accept_issues_envelope_or_legacy_array_via_handwritten_adapter"
    )
    errors = next(item for item in document["source_refs"] if item["source_ref_id"] == "S-ERRORS")
    assert {"KindConflict", "KindValidation", "Request conflict: ", "请求冲突\uff1a"} <= set(
        errors["symbol"].split("/")
    )
    assert not any(
        command == ["tag", "external"] for command in document["catalogs"]["bindings"].values()
    )

    mutated = json.loads(json.dumps(document))
    mutated["catalogs"]["bindings"]["autopilot_trigger"]["command"] = [
        "autopilot",
        "run",
    ]
    path = tmp_path / "autopilot-run.json"
    path.write_text(json.dumps(mutated), encoding="utf-8")
    with pytest.raises(ContractError, match="disagrees with binding"):
        validate_contract(path)


def test_tagged_values_preserve_datetime_offset_and_unset() -> None:
    contract = load_contract(APPROVED)
    flat = contract.vector_by_id["generated:issues.comments.list:flat:canonical"]
    assert flat.args == ()
    since = dict(flat.kwargs)["since"]
    assert since == {"kind": "datetime", "value": "2026-07-12T10:00:00+00:00"}
    update = contract.vector_by_id["generated:projects.update:default:canonical"]
    assert update.args == ({"kind": "primitive", "value": "pr_1"},)
    assert update.kwargs == ()


def test_result_assertion_algorithms() -> None:
    none = ResultAssertion("assert:none", "none", {"kind": "primitive", "value": None})
    assert_result(none, None)
    with pytest.raises(AssertionError):
        assert_result(none, "not-none")

    decoded = ResultAssertion(
        "assert:decoded",
        "decoded_type",
        {"kind": "primitive", "value": "multica_py.entities.comments.Comment"},
    )
    assert_result(decoded, Comment(id="c1", body="body"))
    with pytest.raises(AssertionError):
        assert_result(decoded, object())

    page = ResultAssertion(
        "assert:page",
        "page_items",
        {
            "kind": "list",
            "items": [
                {"kind": "primitive", "value": "c1"},
                {"kind": "primitive", "value": "c2"},
            ],
        },
    )
    assert_result(page, Page(items=(Comment(id="c1", body=""), Comment(id="c2", body=""))))
    with pytest.raises(AssertionError):
        assert_result(page, Page(items=(Comment(id="c1", body=""),)))


def test_render_is_independent_of_evidence() -> None:
    first = render_files(APPROVED)
    evidence = pathlib.Path(tempfile.gettempdir()) / "upstream-evidence.json"
    evidence.write_text('{"review_items":["changed"]}\n', encoding="utf-8")
    try:
        second = render_files(APPROVED)
    finally:
        evidence.unlink(missing_ok=True)
    assert [(item.path, item.content) for item in first] == [
        (item.path, item.content) for item in second
    ]


def test_collector_layer_does_not_import_socket() -> None:
    from tools.upstream_contract import evidence

    source = pathlib.Path(evidence.__file__).read_text(encoding="utf-8")
    assert "import socket" not in source
    assert "socket.socket" not in source


def test_collect_writes_review_items_and_never_contract(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "cmd.go").write_text(
        'package cmd\nvar command = cobra.Command{Use: "list", RunE: run}\n',
        encoding="utf-8",
    )
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    subprocess.run(["git", "init", "-q", str(source)], check=True, env=git_env)
    subprocess.run(["git", "-C", str(source), "add", "cmd.go"], check=True, env=git_env)
    subprocess.run(
        ["git", "-C", str(source), "commit", "-q", "-m", "source"], check=True, env=git_env
    )
    commit = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (source / "cmd.go").write_text("package cmd\n", encoding="utf-8")
    binary = tmp_path / "multica"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    version = tmp_path / "version.json"
    version.write_text('{"version":"0.4.9"}\n', encoding="utf-8")
    output = tmp_path / "evidence"
    collect(
        source_checkout=source,
        binary=binary,
        identity=ReleaseIdentity(
            tag="v0.4.9",
            version="0.4.9",
            commit=commit,
            release_id="test",
            asset_name="multica",
            sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            os="darwin",
            arch="arm64",
            version_output_sha256=hashlib.sha256(version.read_bytes()).hexdigest(),
        ),
        version_output=version,
        output_dir=output,
    )
    assert (output / "evidence.json").is_file()
    evidence = json.loads((output / "evidence.json").read_text(encoding="utf-8"))
    assert {item["kind"] for item in evidence["facts"]} == {"cobra_use"}
    review = json.loads((output / "review-items.json").read_text(encoding="utf-8"))
    assert review["items"]
    assert {item["code"] for item in review["items"]} <= {
        "UNKNOWN_PATTERN",
        "UNRESOLVED_HELPER",
        "DYNAMIC_ENUM",
        "IMPERATIVE_VALIDATION",
        "PRESENCE_SENSITIVE",
        "UNRESOLVED_MAPPING",
    }
    assert not (output / "contracts" / "sdk-contract.json").exists()


def test_collect_rejects_tracked_output(tmp_path: pathlib.Path) -> None:
    from tools.upstream_contract.evidence import _is_forbidden_output

    assert _is_forbidden_output(pathlib.Path("contracts"))
    assert not _is_forbidden_output(tmp_path)


def test_collector_marks_imperative_and_presence_patterns_for_review(
    tmp_path: pathlib.Path,
) -> None:
    from tools.upstream_contract.evidence import _collect_facts

    source = tmp_path / "cmd.go"
    source.write_text(
        "\n".join(
            (
                "package cmd",
                "func run() { if flag { } }",
                'changed := cmd.Flags().Changed("project")',
                'values := append([]string{}, "open")',
                "var command = cobra.Command{RunE: run}",
                "var checked = cobra.Command{Args: cobra.ExactArgs(1)}",
                'cmd.Flags().StringVar(&name, "name", "", "")',
                "cmd.AddCommand(buildCommand())",
                "var custom = cobra.Command{Args: customValidator}",
            )
        ),
        encoding="utf-8",
    )
    facts, review_items = _collect_facts(tmp_path)
    assert {item["code"] for item in review_items} == {
        "DYNAMIC_ENUM",
        "IMPERATIVE_VALIDATION",
        "PRESENCE_SENSITIVE",
        "UNKNOWN_PATTERN",
        "UNRESOLVED_HELPER",
    }
    assert {item["kind"] for item in facts} == {"cobra_args"}


@dataclass(frozen=True)
class ExtractorPatternCase:
    case_id: str
    source: str
    expected_fact_kinds: frozenset[str]
    review_code: str


EXTRACTOR_PATTERN_CASES = (
    ExtractorPatternCase("dynamic-use", "Use: makeUse(),", frozenset(), "UNKNOWN_PATTERN"),
    ExtractorPatternCase("dynamic-aliases", "Aliases: aliases(),", frozenset(), "UNKNOWN_PATTERN"),
    ExtractorPatternCase(
        "dynamic-exact-args",
        "Args: cobra.ExactArgs(computeCount()),",
        frozenset(),
        "UNKNOWN_PATTERN",
    ),
    ExtractorPatternCase(
        "dangerous-helper", "RunE: dangerousHelper,", frozenset(), "UNRESOLVED_HELPER"
    ),
    ExtractorPatternCase("comment", '// Use: "not-a-command",', frozenset(), ""),
    ExtractorPatternCase(
        "literal-exact-args", "Args: cobra.ExactArgs(1),", frozenset({"cobra_args"}), ""
    ),
)


@pytest.mark.parametrize("case", EXTRACTOR_PATTERN_CASES, ids=lambda case: case.case_id)
def test_collector_fails_closed_for_nonliteral_cobra_forms(
    case: ExtractorPatternCase, tmp_path: pathlib.Path
) -> None:
    from tools.upstream_contract.evidence import _collect_facts

    (tmp_path / "cmd.go").write_text(f"package cmd\n{case.source}\n", encoding="utf-8")
    facts, review_items = _collect_facts(tmp_path)
    assert {item["kind"] for item in facts} == case.expected_fact_kinds
    assert (case.review_code in {item["code"] for item in review_items}) == bool(case.review_code)


@dataclass(frozen=True)
class EnumValidatorCase:
    case_id: str
    validator: str
    value: str
    valid: bool


ENUM_VALIDATOR_CASES = (
    EnumValidatorCase("issue-valid", "validate_issue_status", "done", True),
    EnumValidatorCase("issue-invalid", "validate_issue_status", "unknown", False),
    EnumValidatorCase("project-valid", "validate_project_status", "completed", True),
    EnumValidatorCase("project-invalid", "validate_project_status", "unknown", False),
)


@pytest.mark.parametrize("case", ENUM_VALIDATOR_CASES, ids=lambda case: case.case_id)
def test_generated_one_of_validators_check_closed_membership(case: EnumValidatorCase) -> None:
    from multica_py._generated import approved_sdk

    validator = getattr(approved_sdk, case.validator)
    if case.valid:
        validator(case.value)
    else:
        with pytest.raises(ValueError):
            validator(case.value)


@dataclass(frozen=True)
class TransientProjectionCase:
    case_id: str
    path_index: int
    content: bytes


@pytest.mark.parametrize(
    "case",
    (
        TransientProjectionCase("missing-operation", 0, b"# Approved SDK\n"),
        TransientProjectionCase("bad-compatibility", 1, b"{}\n"),
        TransientProjectionCase("bad-provenance", 2, b"{}\n"),
    ),
    ids=lambda case: case.case_id,
)
def test_transient_projection_validation_rejects_invalid_content(
    case: TransientProjectionCase,
) -> None:
    contract = validate_contract(APPROVED)
    rendered = render_files(APPROVED)[case.path_index + 1]
    with pytest.raises(ContractError):
        _validate_transient_projection(contract, replace(rendered, content=case.content))


def test_source_validation_rejects_symlink_escape(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.upstream_contract import cli
    from tools.upstream_contract.contract import SourceRef

    checkout = tmp_path / "checkout"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q", str(checkout)], check=True)
    (checkout / "tracked.go").write_text("package checkout_symbol\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(checkout), "add", "tracked.go"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "source",
        ],
        check=True,
    )
    commit = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    outside = tmp_path / "outside.go"
    outside.write_text("symbol\n", encoding="utf-8")
    (checkout / "inside.go").symlink_to(outside)
    clean_catalog = replace(
        validate_contract(APPROVED),
        target=replace(validate_contract(APPROVED).target, commit=commit),
        source_refs=(SourceRef("S", "repo", commit, "tracked.go", "checkout_symbol", 1, 1),),
    )
    monkeypatch.setattr(cli, "validate_contract", lambda _: clean_catalog)
    (checkout / "tracked.go").write_text("package dirty\n", encoding="utf-8")
    cli._source_validate(APPROVED, checkout)
    escaped_catalog = replace(
        clean_catalog,
        source_refs=(SourceRef("S", "repo", commit, "inside.go", "symbol", 1, 1),),
    )
    monkeypatch.setattr(cli, "validate_contract", lambda _: escaped_catalog)
    with pytest.raises(ContractError, match="escapes source checkout"):
        cli._source_validate(APPROVED, checkout)
