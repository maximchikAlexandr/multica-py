from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
from dataclasses import dataclass, replace
from typing import cast

import pytest

from multica_py.models.common import Page
from multica_py.models.issue_activity import Comment
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
    assert len(contract.test_vectors) == 37
    assert sum(":variant:" not in vector.vector_id for vector in contract.test_vectors) == 26
    assert sum(":variant:" in vector.vector_id for vector in contract.test_vectors) == 11
    assert tuple(contract.legacy_argv_migration) == tuple(
        f"legacy:{index:03d}" for index in range(1, 144)
    )
    assert {item.public_name for item in contract.enum_definitions} == {
        "IssueSort",
        "SortDirection",
        "AutopilotExecutionMode",
    }
    assert all(item.parameter_name.isidentifier() for item in contract.validator_definitions)


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
        {"kind": "primitive", "value": "multica_py.models.issue_activity.Comment"},
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
    evidence = pathlib.Path("/private/tmp/upstream-evidence.json")
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
