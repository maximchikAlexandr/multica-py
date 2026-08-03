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


@dataclass(frozen=True)
class BaselineScenario:
    title: str
    when: str
    then: str


@dataclass(frozen=True)
class BaselineRequirement:
    relative_path: str
    title: str
    statement: str
    source_ids: str
    scenarios: tuple[BaselineScenario, ...]


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
        "The SDK MUST expose managed processes with bounded concurrency, timeout\ncancellation, escalation, and descendant cleanup. A root client and views\nderived through `with_*()` MUST share exactly one `ProcessSemaphore` while\nremaining otherwise independent clients with distinct immutable configuration,\ntransport, services, and close behavior.",
        "Timed processes clean up descendants",
        "the timeout process case expires",
        "parent and descendant are absent",
        "",
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
        "The approved contract MUST be the only generator input and MUST render one\ncommitted runtime module plus deterministic transient projections. Bound\nentities, operation identifiers, loader closures, response adapters, validators,\nand compatibility metadata MUST NOT be generated from evidence, heuristic\nsuggestions, or upgrade bundles directly.",
        "Rendering is deterministic",
        "rendered twice from the same approved contract",
        "all relative paths and bytes are identical",
        "",
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
        "CI MUST run Ruff, configured mypy, offline pytest, statement and branch coverage, contract check, package validation, and approved release validation through `uv`. Coverage acceptance MUST include named gates for process lifecycle code and individually selected critical resource modules so that aggregate package coverage cannot conceal their regression.",
        "Pull requests run offline quality and release checks",
        "a pull request runs",
        "job outcomes, not workflow-text tests, decide acceptance.",
        "001:FR-051\u2013FR-059C,005:FR-011\u2013FR-017",
    ),
    BaselineCase(
        "openspec/specs/verification-and-release/spec.md",
        "Canonical operation coverage",
        "Every supported public SDK resource method MUST have exactly one canonical\nsuccess operation row with complete transport behavior. The expected method\nset MUST be derived from public discovery and compared for exact equality to\ncanonical rows with no allowlist. Case-count constants and legacy fingerprint\ncounts MUST be changed in the same commit as their added/removed rows and MUST\nequal the lengths computed from the final case tables; historic literals\n117/146/29/143 are not post-change requirements.",
        "Public methods have canonical operation coverage",
        "`discovered_public_methods` is compared to `{case.sdk_method for case in OPERATION_CASES if case.is_canonical}`",
        "the sets are equal, every supported method has one canonical row, removed methods have none, and stored count constants equal the computed table partitions",
        "",
    ),
    BaselineCase(
        "openspec/specs/verification-and-release/spec.md",
        "Focused process and offline checks",
        "Offline tests MUST use stdlib and pytest, keep exact argv assertions including operations with dynamic temporary paths, retain exactly three real-process cases, and use deterministic synchronization or subprocess test doubles for additional lifecycle branches.",
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
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Agent skills decode as typed AgentSkill objects",
        "agent get/list contains assigned skill objects",
        "`AgentData.skill_refs` preserves typed `AgentSkill` values and `Agent.skills` remains the lazy relation name",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Agent with no skills decodes to empty tuple",
        "agent get/list omits embedded skills",
        "`AgentData.skill_refs == ()` and no relation cache is seeded",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Agent archived_at null decodes to None",
        "`archived_at` is null or omitted",
        "`AgentData.archived_at` is `None`",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Agent archived_at RFC3339 decodes to datetime",
        "`archived_at` is a valid RFC3339 value",
        "`AgentData.archived_at` is the corresponding timezone-aware `datetime`",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Assigned skills read returns typed AgentSkill",
        "`Agent.skills.all()` loads",
        "`agent skills list <agent-id> --output json` returns `tuple[AgentSkill, ...]`",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Squad leader_id decodes",
        "a squad response contains `leader_id`",
        "`SquadData.leader_id` preserves it",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Squad leader_id absent decodes to None",
        "a squad response omits `leader_id` or contains null",
        "`SquadData.leader_id` is `None`",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Squad archived_at null decodes to None",
        "a squad response omits `archived_at` or contains null",
        "`SquadData.archived_at` is `None`",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Squad archived_at RFC3339 decodes to datetime",
        "a squad response contains an RFC3339 `archived_at`",
        "`SquadData.archived_at` is the corresponding timezone-aware `datetime`",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Existing minimal squad fixture still decodes",
        "a minimal legacy squad fixture omits optional fields",
        "it decodes with the documented defaults",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Squad member list emits exact argv",
        "the squad member relation loads",
        'transport receives `("squad", "member", "list", <squad-id>, "--output", "json")`',
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Squad member list returns typed members",
        "the CLI returns squad member records",
        "each item is a typed `SquadMember`",
        "",
    ),
    BaselineCase(
        "openspec/specs/sdk-surface/spec.md",
        "Executor fields and squad member decoding",
        "The SDK SHALL decode upstream executor fields and squad members. `AgentData`\nSHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;\n`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural\n`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and\n`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be\n`LazyCollection[SquadMember]` backed by `squad member list`.",
        "Squad member list with multiple roles preserves each",
        "multiple squad members have distinct roles",
        "identity, type, role, and response order are preserved",
        "",
    ),
)
BASELINE_PATHS: tuple[str, ...] = (
    "openspec/specs/sdk-surface/spec.md",
    "openspec/specs/subprocess-transport/spec.md",
    "openspec/specs/upstream-contract/spec.md",
    "openspec/specs/verification-and-release/spec.md",
)


def _requirements_from_cases(cases: tuple[BaselineCase, ...]) -> tuple[BaselineRequirement, ...]:
    requirements: list[BaselineRequirement] = []
    for case in cases:
        scenario = BaselineScenario(case.scenario_title, case.when, case.then)
        if requirements and (
            requirements[-1].relative_path,
            requirements[-1].title,
        ) == (case.relative_path, case.title):
            requirement = requirements[-1]
            requirements[-1] = BaselineRequirement(
                requirement.relative_path,
                requirement.title,
                requirement.statement,
                requirement.source_ids,
                (*requirement.scenarios, scenario),
            )
        else:
            requirements.append(
                BaselineRequirement(
                    case.relative_path,
                    case.title,
                    case.statement,
                    case.source_ids,
                    (scenario,),
                )
            )
    return tuple(requirements)


BASELINE_REQUIREMENTS = _requirements_from_cases(BASELINE_CASES)
HEADING_RE: re.Pattern[str] = re.compile(
    r"^(## Purpose|## Requirements|### Requirement: .+|#### Scenario: .+)$"
)


def _read_baseline(relative_path: str) -> str:
    return (BASELINE_ROOT / relative_path).read_text(encoding="utf-8")


def _heading_titles(document: str, prefix: str) -> tuple[str, ...]:
    return tuple(
        line.removeprefix(prefix) for line in document.splitlines() if line.startswith(prefix)
    )


def _requirement_section(document: str, title: str) -> str:
    _, separator, section = document.partition(f"### Requirement: {title}\n")
    assert separator
    return section.partition("\n### Requirement: ")[0]


def _assert_ordered_subsequence(expected: tuple[str, ...], actual: tuple[str, ...]) -> None:
    remaining = list(expected)
    for title in actual:
        if remaining and title == remaining[0]:
            remaining.pop(0)
    assert not remaining


def _validate_baseline_document(
    document: str, requirements: tuple[BaselineRequirement, ...]
) -> None:
    headings = [line for line in document.splitlines() if line.startswith("#")]
    assert headings
    assert document.count("## Purpose") == 1
    assert document.count("## Requirements") == 1
    assert headings[:2] == ["## Purpose", "## Requirements"]
    assert all(HEADING_RE.fullmatch(line) for line in headings)
    expected_titles = tuple(requirement.title for requirement in requirements)
    actual_titles = _heading_titles(document, "### Requirement: ")
    _assert_ordered_subsequence(expected_titles, actual_titles)
    for requirement in requirements:
        section = _requirement_section(document, requirement.title)
        assert section.startswith(requirement.statement)
        _assert_ordered_subsequence(
            tuple(scenario.title for scenario in requirement.scenarios),
            _heading_titles(section, "#### Scenario: "),
        )


@pytest.mark.parametrize("relative_path", BASELINE_PATHS, ids=BASELINE_PATHS)
def test_baseline_heading_grammar(relative_path: str) -> None:
    document = _read_baseline(relative_path)
    requirements = tuple(
        requirement
        for requirement in BASELINE_REQUIREMENTS
        if requirement.relative_path == relative_path
    )
    _validate_baseline_document(document, requirements)


def test_baseline_scenarios_belong_to_owning_requirement() -> None:
    requirements = (
        BaselineRequirement(
            "baseline.md",
            "Source",
            "source statement",
            "",
            (
                BaselineScenario("First", "first", "first"),
                BaselineScenario("Second", "second", "second"),
            ),
        ),
        BaselineRequirement(
            "baseline.md",
            "Target",
            "target statement",
            "",
            (BaselineScenario("Third", "third", "third"),),
        ),
    )
    moved_document = """## Purpose
## Requirements
### Requirement: Source
source statement
#### Scenario: First
- **WHEN** first
- **THEN** first

### Requirement: Target
target statement
#### Scenario: Second
- **WHEN** second
- **THEN** second

#### Scenario: Third
- **WHEN** third
- **THEN** third
"""

    with pytest.raises(AssertionError):
        _validate_baseline_document(moved_document, requirements)


@pytest.mark.parametrize(
    "requirement", BASELINE_REQUIREMENTS, ids=tuple(item.title for item in BASELINE_REQUIREMENTS)
)
def test_baseline_requirement_traceability(requirement: BaselineRequirement) -> None:
    document = _read_baseline(requirement.relative_path)
    section = _requirement_section(document, requirement.title)
    assert document.count(f"### Requirement: {requirement.title}") == 1
    assert section.startswith(requirement.statement)
    for scenario in requirement.scenarios:
        block = (
            f"#### Scenario: {scenario.title}\n"
            f"- **WHEN** {scenario.when}\n"
            f"- **THEN** {scenario.then}"
        )
        if requirement.source_ids:
            block += f"\n<!-- Source IDs: {requirement.source_ids} -->"
        assert block in section
