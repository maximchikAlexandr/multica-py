from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
from dataclasses import dataclass, replace
from typing import cast

import pytest

from multica_py.models.common import Page
from multica_py.resources.issue_comments import Comment
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
    InvalidContractCase("migration-key", "migration_key"),
    InvalidContractCase("generated-newline", "generated_newline"),
    InvalidContractCase("generated-parentheses", "generated_parentheses"),
    InvalidContractCase("generated-unicode", "generated_unicode"),
    InvalidContractCase("generated-keyword", "generated_keyword"),
    InvalidContractCase("source-ref-parent", "source_ref_parent"),
    InvalidContractCase("source-ref-commit", "source_ref_commit"),
    InvalidContractCase("request-field-order", "request_field_order"),
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
    InvalidContractCase("convention-presence", "convention_presence"),
    InvalidContractCase("convention-presence-empty", "convention_presence_empty"),
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
        vector["args"][0]["fields"][1][1]["value"] = "2026-07-12T10:00:00"
    elif mutation == "decoded_type":
        vector = document["catalogs"]["test_vectors"][
            "generated:issues.comments.add:default:canonical"
        ]
        vector["assertion"]["expected"]["value"] = "not.approved.Type"
    elif mutation == "migration_key":
        del document["legacy_argv_migration"]["legacy:001"]
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
    elif mutation == "request_field_order":
        vector = document["catalogs"]["test_vectors"][
            "generated:issues.comments.list:flat:canonical"
        ]
        vector["args"][0]["fields"] = list(reversed(vector["args"][0]["fields"]))
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
            entrypoint = document["operations"][3]["entrypoints"][0]
            entrypoint["presence_policy_ids"] = []
        elif mutation == "convention_command":
            entrypoint["command_symbol"] = "not_a_command"
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
    elif mutation == "operation_evidence":
        document["operations"][0]["source_ref_ids"] = []
    elif mutation == "nullable_clear_evidence":
        field = document["catalogs"]["update_field_policies"]["IssueUpdateRequest"]["fields"][
            "description"
        ]
        field["clear"]["source_ref_ids"] = []
    elif mutation == "update_source_ref":
        document["catalogs"]["update_field_policies"]["ProjectUpdateRequest"]["fields"]["name"][
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


def test_v3_catalogs_and_legacy_mapping_are_closed() -> None:
    contract = validate_contract(APPROVED)
    assert len(contract.test_vectors) == 58
    assert sum(":variant:" not in vector.vector_id for vector in contract.test_vectors) == 46
    assert sum(":variant:" in vector.vector_id for vector in contract.test_vectors) == 12
    assert tuple(contract.legacy_argv_migration) == tuple(
        f"legacy:{index:03d}" for index in range(1, 144)
    )
    assert {item.public_name for item in contract.enum_definitions} == {
        "IssueSort",
        "SortDirection",
        "AutopilotExecutionMode",
    }
    assert all(item.parameter_name.isidentifier() for item in contract.validator_definitions)


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


def test_update_field_policies_are_explicit_and_source_pinned() -> None:
    contract = validate_contract(APPROVED)
    policies = {model.model_id: model for model in contract.update_field_policies}
    assert set(policies) == {
        "ProjectUpdateRequest",
        "AgentUpdateRequest",
        "SkillUpdateRequest",
        "IssueUpdateRequest",
        "AutopilotUpdateRequest",
        "AutopilotTriggerUpdate",
        "LabelUpdateRequest",
        "ProjectResourceUpdateLocalDirectoryRequest",
        "RuntimeUpdate",
        "UserProfileUpdate",
    }
    issue = {field.field_name: field for field in policies["IssueUpdateRequest"].fields}
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


def test_current_target_and_source_refs_are_pinned_to_v0420() -> None:
    contract = load_contract(APPROVED)
    assert contract.target.version == "0.4.20"
    assert contract.target.tag == "v0.4.20"
    assert contract.target.commit == "93342d04a7a9f788fec921e5aa736f86c7f22d8f"
    assert contract.target.release_id == "366120041"
    assert (
        contract.target.release_provenance_ref
        == ".devlocal/upstream-contract/v0.4.9..v0.4.20/release/release-verification.json"
    )
    assert {ref.commit for ref in contract.source_refs} == {contract.target.commit}
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
    assert document["catalogs"]["responses"]["issue_search"]["malformed_output"] == (
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
    assert flat.args[0]["kind"] == "request"
    fields = cast("list[list[object]]", flat.args[0]["fields"])
    since = fields[1][1]
    assert since == {"kind": "datetime", "value": "2026-07-12T10:00:00+00:00"}
    update = contract.vector_by_id["generated:projects.update:default:canonical"]
    assert update.args[1]["fields"] == []


def test_result_assertion_algorithms() -> None:
    none = ResultAssertion("assert:none", "none", {"kind": "primitive", "value": None})
    assert_result(none, None)
    with pytest.raises(AssertionError):
        assert_result(none, "not-none")

    decoded = ResultAssertion(
        "assert:decoded",
        "decoded_type",
        {"kind": "primitive", "value": "multica_py.resources.issue_comments.Comment"},
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
