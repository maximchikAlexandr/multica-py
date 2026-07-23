from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MutationSeverityCase:
    """One upstream contract mutation and its expected severity classification.

    Attributes:
        mutation_file: JSON fixture under tests/fixtures/upstream_contract/mutations/.
        must_contain: Severities that must appear in the diff.
        must_not_contain: Severities that must not appear in the diff.
        unresolved_breaking: Expected unresolved_breaking flag, or None to skip.
        id: pytest.param id.
    """

    mutation_file: str
    must_contain: tuple[str, ...]
    must_not_contain: tuple[str, ...]
    unresolved_breaking: bool | None
    id: str


MUTATION_SEVERITY_CASES: tuple[MutationSeverityCase, ...] = (
    MutationSeverityCase(
        mutation_file="required-flag-added.json",
        must_contain=("breaking",),
        must_not_contain=(),
        unresolved_breaking=True,
        id="required-flag-added",
    ),
    MutationSeverityCase(
        mutation_file="help-text-changed.json",
        must_contain=(),
        must_not_contain=("breaking", "additive", "potentially_breaking", "mismatch"),
        unresolved_breaking=None,
        id="help-text-changed",
    ),
    MutationSeverityCase(
        mutation_file="command-added.json",
        must_contain=("additive",),
        must_not_contain=(),
        unresolved_breaking=None,
        id="command-added",
    ),
    MutationSeverityCase(
        mutation_file="command-removed.json",
        must_contain=("breaking",),
        must_not_contain=(),
        unresolved_breaking=None,
        id="command-removed",
    ),
    MutationSeverityCase(
        mutation_file="optional-flag-added.json",
        must_contain=("additive",),
        must_not_contain=("breaking",),
        unresolved_breaking=None,
        id="optional-flag-added",
    ),
)
