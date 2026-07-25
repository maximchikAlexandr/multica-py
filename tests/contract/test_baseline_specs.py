"""Verify the four retained historical baseline specifications."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass(frozen=True)
class BaselineCase:
    relative_path: str
    title: str
    statement: str
    scenario_title: str
    when: str
    then: str
    source_ids: str


BASELINE_ROOT = Path(__file__).parents[2]
BASELINE_CASES: tuple[BaselineCase, ...] = (
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Synchronous resource client",
        "The SDK MUST expose one synchronous `MulticaClient` with stateless domain resources and immutable typed models.",
        "Resource calls remain stateless",
        "a consumer calls a resource method",
        "no model performs hidden I/O or Active Record persistence.",
        "001:FR-001,FR-002,FR-003,FR-004,FR-005",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Public resource surface",
        "The SDK MUST retain every public resource method present in the canonical operation table.",
        "Public methods have canonical rows",
        "a public resource method exists",
        "one canonical operation row covers it.",
        "001:FR-018\u2013FR-031,005:FR-019\u2013FR-025",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Closed public types",
        "The SDK MUST use immutable `msgspec` models and closed public enums or primitive unions without public `Any`.",
        "Structured output stays closed and typed",
        "structured output is decoded",
        "it is a typed model or documented closed primitive.",
        "001:FR-033\u2013FR-039",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Distribution boundary",
        "The distribution MUST remain `multica-py`, import as `multica_py`, include `py.typed`, and import without a CLI.",
        "Clean installation imports without a CLI",
        "installed cleanly",
        "`import multica_py` succeeds before a CLI invocation.",
        "001:FR-006A\u2013FR-006D,FR-047\u2013FR-050B",
    ),
    BaselineCase(
        "openspec/specs/subprocess-transport/spec.md",
        "CLI-only transport",
        "The SDK MUST invoke Multica through one shell-free controlled subprocess transport.",
        "Resource calls use the controlled subprocess",
        "a resource runs a command",
        "exact argv, cwd, profile, workspace, environment, stdin, and timeout reach that transport.",
        "001:FR-006\u2013FR-010,FR-015",
    ),
    BaselineCase(
        "openspec/specs/subprocess-transport/spec.md",
        "Managed process lifecycle",
        "The SDK MUST expose managed processes with bounded concurrency, timeout cancellation, escalation, and descendant cleanup.",
        "Timed processes clean up descendants",
        "the timeout process case expires",
        "parent and descendant are absent.",
        "001:FR-016\u2013FR-017B,005:FR-004\u2013FR-006,006:FR-008\u2013FR-010",
    ),
    BaselineCase(
        "openspec/specs/subprocess-transport/spec.md",
        "Decode and diagnostics",
        "The SDK MUST decode supported structured output, map reliable failures to typed errors, and redact secrets from diagnostics.",
        "Failures expose typed redacted diagnostics",
        "malformed output or nonzero exit occurs",
        "the diagnostic has redacted command context and the documented error type.",
        "001:FR-011\u2013FR-014,FR-040\u2013FR-044",
    ),
    BaselineCase(
        "openspec/specs/upstream-contract/spec.md",
        "Pinned source authority",
        "The approved contract MUST cite full pinned source commits and locations, while extraction records only declared declarative facts.",
        "Unknown patterns require review",
        "extraction sees an unknown pattern",
        "it emits a review item and changes no approved behavior.",
        "001:FR-032A\u2013FR-032G,002:FR-001,FR-002,FR-027",
    ),
    BaselineCase(
        "openspec/specs/upstream-contract/spec.md",
        "Verified evidence",
        "Evidence collection MUST record verified binary identity, release identity, ordered declarative facts, and review items outside version control.",
        "Collection records verified evidence",
        "collection succeeds",
        "its two files satisfy the schemas in `generation.md`.",
        "002:FR-003,FR-004,FR-012,FR-023,FR-032",
    ),
    BaselineCase(
        "openspec/specs/upstream-contract/spec.md",
        "Reviewed mapping semantics",
        "Every approved mapping MUST state source evidence, destination, five-state presence, enum policy, and normalized constraints with positive and negative evidence.",
        "Mappings state reviewed semantics",
        "a mapping is incomplete or unresolved",
        "validation fails.",
        "002:FR-028,007:FR-009,FR-010",
    ),
    BaselineCase(
        "openspec/specs/upstream-contract/spec.md",
        "Deterministic generation",
        "The approved contract MUST be the only generator input and MUST render one committed runtime module plus deterministic transient projections.",
        "Rendering is deterministic",
        "rendered twice",
        "all relative paths and bytes are identical.",
        "002:FR-017,FR-018,007:FR-012\u2013FR-014",
    ),
    BaselineCase(
        "openspec/specs/upstream-contract/spec.md",
        "Generated compatibility",
        "The generated runtime module MUST provide the tested CLI interval from the approved target version.",
        "Compatibility uses the generated interval",
        "a client reads default policy",
        "it uses generated minimum and exclusive next-patch maximum versions.",
        "002:FR-025,FR-033",
    ),
    BaselineCase(
        "openspec/specs/upstream-contract/spec.md",
        "Git promotion",
        "A reviewed Git merge changing the approved contract and runtime projection MUST be the only promotion action.",
        "Git review promotes the contract",
        "a PR is merged",
        "no candidate, supported, observer, or journal state is written.",
        "002:FR-030,007:FR-011",
    ),
    BaselineCase(
        "openspec/specs/verification-and-release/spec.md",
        "Offline quality and release",
        "CI MUST run Ruff, configured mypy, offline pytest, coverage, contract check, package validation, and approved release validation through `uv`.",
        "Pull requests run offline quality and release checks",
        "a pull request runs",
        "job outcomes, not workflow-text tests, decide acceptance.",
        "001:FR-051\u2013FR-059C,005:FR-011\u2013FR-017",
    ),
    BaselineCase(
        "openspec/specs/verification-and-release/spec.md",
        "Canonical operation coverage",
        "Every public SDK method MUST have exactly one canonical success operation row with complete transport behavior.",
        "Public methods have canonical operation coverage",
        "`discovered_public_methods` is compared to `{case.sdk_method for case in OPERATION_CASES if case.is_canonical}`",
        "the sets are equal, with 111 unique canonical methods, 135 unique case IDs, and 24 noncanonical variants.",
        "001:FR-060\u2013FR-066,004:FR-004\u2013FR-008,FR-017,006:FR-011\u2013FR-013",
    ),
    BaselineCase(
        "openspec/specs/verification-and-release/spec.md",
        "Focused process and offline checks",
        "Offline tests MUST use stdlib and pytest, keep exact argv assertions, and retain exactly three real-process cases.",
        "Offline checks keep focused process cases",
        "the process module is collected",
        "IDs are `bytes-env`, `text-stdin`, and `timeout-tree-cleanup`.",
        "004:FR-006,FR-015,FR-016,005:FR-002,FR-005,FR-006,006:FR-009",
    ),
    BaselineCase(
        "openspec/specs/verification-and-release/spec.md",
        "Prepared-target live smoke",
        "Live smoke MUST run separately against a prepared CLI/profile/workspace and clean uniquely named resources through the SDK.",
        "Prepared targets run live smoke",
        "live smoke is selected",
        "five fixed scenarios run without backend provisioning or direct HTTP.",
        "003:FR-001,FR-002,FR-007,FR-014,FR-022,FR-029,FR-030",
    ),
    BaselineCase(
        "openspec/specs/verification-and-release/spec.md",
        "Maintainer documentation",
        "Documentation MUST describe CLI installation/authentication, compatibility, and approved upstream review.",
        "Maintainers can follow approved upstream review",
        "a maintainer follows it",
        "they validate, collect, render, and check without a promotion state machine.",
        "001:FR-067\u2013FR-075",
    ),
)

BASELINE_ROOT = Path(__file__).parents[2]
BASELINE_PATHS: tuple[str, ...] = (
    "openspec/specs/sdk-surface/spec.md",
    "openspec/specs/subprocess-transport/spec.md",
    "openspec/specs/upstream-contract/spec.md",
    "openspec/specs/verification-and-release/spec.md",
)
HEADING_RE: re.Pattern[str] = re.compile(
    r"^(## ADDED Requirements|### Requirement: .+|#### Scenario: .+)$"
)


def _read_baseline(relative_path: str) -> str:
    return (BASELINE_ROOT / relative_path).read_text(encoding="utf-8")


def _heading_titles(document: str, prefix: str) -> tuple[str, ...]:
    return tuple(
        line.removeprefix(prefix) for line in document.splitlines() if line.startswith(prefix)
    )


@pytest.mark.parametrize("relative_path", BASELINE_PATHS, ids=BASELINE_PATHS)
def test_baseline_heading_grammar(relative_path: str) -> None:
    document = _read_baseline(relative_path)
    headings = [line for line in document.splitlines() if line.startswith("#")]
    assert headings
    assert document.count("## ADDED Requirements") == 1
    assert headings[0] == "## ADDED Requirements"
    assert all(HEADING_RE.fullmatch(line) for line in headings)
    expected = tuple(case for case in BASELINE_CASES if case.relative_path == relative_path)
    assert _heading_titles(document, "### Requirement: ") == tuple(case.title for case in expected)
    assert _heading_titles(document, "#### Scenario: ") == tuple(
        case.scenario_title for case in expected
    )


@pytest.mark.parametrize("case", BASELINE_CASES, ids=tuple(case.title for case in BASELINE_CASES))
def test_baseline_requirement_traceability(case: BaselineCase) -> None:
    document = _read_baseline(case.relative_path)
    block = (
        f"### Requirement: {case.title}\n"
        f"{case.statement}\n"
        f"#### Scenario: {case.scenario_title}\n"
        f"- **WHEN** {case.when}\n"
        f"- **THEN** {case.then}\n"
        f"<!-- Source IDs: {case.source_ids} -->"
    )
    assert document.count(f"### Requirement: {case.title}") == 1
    assert document.count(f"#### Scenario: {case.scenario_title}") == 1
    assert block in document
