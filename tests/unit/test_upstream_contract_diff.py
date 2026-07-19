from __future__ import annotations

import pathlib

from multica_py._internal.upstream_contract import diff as diff_module
from multica_py._internal.upstream_contract import schema

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"
MUTATIONS = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "mutations"
BASELINE = FIXTURES / "supported-cli-contract-baseline.json"


def test_diff_summary_severity_counts() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(FIXTURES / "candidate-cli-contract-v2.json")
    diff = diff_module.diff_contracts(before, after)
    summary = diff.summary
    assert summary["total"] == len(diff.changes)
    for change in diff.changes:
        assert summary[change.severity] >= 1


def test_required_flag_addition_is_breaking() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "required-flag-added.json")
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "breaking" in severities
    assert diff.unresolved_breaking is True


def test_help_text_only_is_doc_only() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "help-text-changed.json")
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert all(s in ("doc_only", "provenance_only") for s in severities)


def test_command_added_is_additive() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "command-added.json")
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "additive" in severities


def test_command_removed_is_breaking() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "command-removed.json")
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "breaking" in severities


def test_optional_flag_added_is_additive() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "optional-flag-added.json")
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "additive" in severities
    assert "breaking" not in severities


def test_diff_summary_sums_match_changes() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(FIXTURES / "candidate-cli-contract-v2.json")
    diff = diff_module.diff_contracts(before, after)
    counts = dict.fromkeys(diff_module.SEVERITIES, 0)
    counts["total"] = 0
    for change in diff.changes:
        counts[change.severity] += 1
        counts["total"] += 1
    assert counts == diff.summary


def test_rename_heuristic_emits_suggestion_without_changing_identity() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "command-renamed.json")
    diff = diff_module.diff_contracts(before, after)
    rename_changes = [
        change for change in diff.changes if change.kind == "command_moved_or_renamed"
    ]
    assert rename_changes
    assert all(change.suggested_action == "review" for change in rename_changes)
    assert all(not change.affected_operations for change in rename_changes)


def test_rename_suggestion_does_not_change_operation_identity() -> None:
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "command-added.json")
    diff = diff_module.diff_contracts(before, after)
    assert all(c.suggested_action == "review" for c in diff.changes)


def test_diff_severity_table_known_categories() -> None:
    for severity in (
        "provenance_only",
        "doc_only",
        "additive",
        "potentially_breaking",
        "breaking",
        "mismatch",
    ):
        assert severity in diff_module.SEVERITIES


def test_required_argument_change_is_breaking() -> None:
    from multica_py._internal.upstream_contract.models import (
        ArgumentContract,
        ArtifactMeta,
        Baseline,
        CommandContract,
        ExecutionContract,
        ObservationMeta,
        OutputContract,
        SemanticCLIContract,
    )

    before = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("agent", "create"),
                use="create",
                args=ArgumentContract(min=0, max=0),
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    after = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("agent", "create"),
                use="create",
                args=ArgumentContract(min=1, max=1),
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "breaking" in severities


def test_deprecation_added_is_potentially_breaking() -> None:
    from multica_py._internal.upstream_contract.models import (
        ArgumentContract,
        ArtifactMeta,
        Baseline,
        CommandContract,
        ExecutionContract,
        ObservationMeta,
        OutputContract,
        SemanticCLIContract,
    )

    before = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("agent", "list"),
                use="list",
                args=ArgumentContract(),
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    after = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("agent", "list"),
                use="list",
                args=ArgumentContract(),
                execution=ExecutionContract(),
                output=OutputContract(),
                deprecated="use agents.query instead",
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "potentially_breaking" in severities


def test_enum_widening_is_potentially_breaking() -> None:
    from multica_py._internal.upstream_contract.models import (
        ArgumentContract,
        ArtifactMeta,
        Baseline,
        CommandContract,
        ExecutionContract,
        FlagContract,
        ObservationMeta,
        OutputContract,
        SemanticCLIContract,
    )

    before = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("issue", "list"),
                use="list",
                args=ArgumentContract(),
                execution=ExecutionContract(),
                output=OutputContract(),
                flags=(
                    FlagContract(
                        name="status",
                        type="string",
                        enum=("open", "closed"),
                    ),
                ),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    after = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("issue", "list"),
                use="list",
                args=ArgumentContract(),
                execution=ExecutionContract(),
                output=OutputContract(),
                flags=(
                    FlagContract(
                        name="status",
                        type="string",
                        enum=("open", "closed", "archived"),
                    ),
                ),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "potentially_breaking" in severities


def test_default_value_change_is_potentially_breaking() -> None:
    from multica_py._internal.upstream_contract.models import (
        ArgumentContract,
        ArtifactMeta,
        Baseline,
        CommandContract,
        ExecutionContract,
        FlagContract,
        ObservationMeta,
        OutputContract,
        SemanticCLIContract,
    )

    before = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("issue", "list"),
                use="list",
                args=ArgumentContract(),
                execution=ExecutionContract(),
                output=OutputContract(),
                flags=(FlagContract(name="status", type="string", default="open"),),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    after = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("issue", "list"),
                use="list",
                args=ArgumentContract(),
                execution=ExecutionContract(),
                output=OutputContract(),
                flags=(FlagContract(name="status", type="string", default="closed"),),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "potentially_breaking" in severities


def test_alias_added_is_additive() -> None:
    from multica_py._internal.upstream_contract.models import (
        ArgumentContract,
        ArtifactMeta,
        Baseline,
        CommandContract,
        ExecutionContract,
        ObservationMeta,
        OutputContract,
        SemanticCLIContract,
    )

    before = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("issue", "list"),
                use="list",
                args=ArgumentContract(),
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    after = SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="x", version="0", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
        ),
        commands=(
            CommandContract(
                path=("issue", "list"),
                use="list",
                aliases=("ls",),
                args=ArgumentContract(),
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    diff = diff_module.diff_contracts(before, after)
    severities = [c.severity for c in diff.changes]
    assert "additive" in severities
