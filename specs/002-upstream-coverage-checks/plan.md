# Implementation Plan: Versioned Upstream CLI Contract and SDK Upgrade Workflow

**Branch**: `[main]` | **Date**: 2026-07-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-upstream-coverage-checks/spec.md`

## Summary

Replace the current command-name drift check with a versioned upstream CLI
contract workflow. The first increment builds a deterministic offline semantic
gate: schema v2, supported/candidate/observed state, semantic command/argument
and flag contracts, semantic diff, coverage levels, machine-readable reports,
and golden/mutation tests. Later increments add secure scheduled observation,
verified binary/source collection, upgrade bundles, and deeper SDK compatibility
contracts.

## Technical Context

**Language/Version**: Python 3.12 and 3.13

**Primary Dependencies**: Existing runtime dependency `msgspec`; standard library for maintainer tooling; existing test dependencies `pytest` and `pytest-cov`

**Storage**: Checked-in canonical JSON and Markdown artifacts under `src/multica_py/_generated/`, `tests/fixtures/provenance/`, `contracts/schema/`, `contracts/sdk-contract.yaml`, and `specs/`

**Testing**: `pytest`, strict mypy, Ruff format/check, focused unit/contract tests, golden fixtures, mutation fixtures, determinism tests, and workflow tests for no-write `--check`

**Target Platform**: Linux and macOS developer/CI environments; scheduled observer uses a controlled GitHub Actions environment when enabled

**Project Type**: Python SDK package with internal maintainer tooling and checked-in provenance artifacts

**Performance Goals**: Offline coverage/diff check over a 100-300 command contract completes in under 1 second; local binary contract collection completes in under 30 seconds for normal help trees; repeated canonicalization is byte-identical for unchanged inputs

**Constraints**: Blocking CI remains offline; checked-in baselines require full 40-character source commits; volatile observation metadata is excluded from semantic hashes; scheduled/networked observer cannot promote supported state; no runtime dependency growth; binary collection must run without repository secrets or user configuration

**Scale/Scope**: One upstream CLI contract family, one SDK coverage manifest, supported/observed/candidate state, one machine report schema, one upgrade bundle format, and tests covering semantic diff and coverage policy

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Source-Driven CLI Contract**: PASS. The plan strengthens the pinned upstream source contract and requires full commit, source/binary provenance, source evidence, and explicit maintainer promotion.
- **II. Thin Synchronous Wrapper**: PASS. The feature affects maintainer tooling and provenance, not runtime server APIs or Multica business logic.
- **III. Typed Public Surface**: PASS. Project-owned models are typed and validation-driven; generated or approved SDK changes require explicit contracts.
- **IV. Offline Testability and Provenance**: PASS. The first increment is an offline artifact gate. Networked observation is separate and non-blocking.
- **V. Secure Packaging and Release**: PASS. No new runtime dependency or release identity change is required; collector security policy prevents secret exposure.

No constitution violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/002-upstream-coverage-checks/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── constitution-reference.md
├── contracts/
│   ├── baseline-artifacts.md
│   ├── cli-contract.md
│   ├── implementation-oracles.md
│   ├── input-output-contracts.md
│   ├── maintainer-commands.md
│   ├── report-schema.md
│   ├── security-and-observer.md
│   └── upgrade-bundle.md
└── tasks.md
```

### Source Code (repository root)

```text
scripts/
├── upstream_contract.py           # thin maintainer CLI adapter
├── check_upstream_drift.py        # compatibility wrapper or deprecated shim
├── collect_upstream_inventory.py  # compatibility wrapper or deprecated shim
└── audit_source_links.py          # retain source-link validation

src/multica_py/_internal/upstream_contract/
├── __init__.py
├── models.py          # immutable typed domain models
├── schema.py          # decode/encode/migrations/validation/canonical JSON
├── provenance.py      # release, commit, checksum, binary provenance
├── source_evidence/   # AST visitors and detectors that emit facts/review items
├── collectors/
│   ├── binary.py      # executable/help/exporter collection
│   └── source.py      # declarative source evidence extraction
├── normalize.py       # canonicalization and semantic hash
├── diff.py            # supported-to-candidate semantic diff
├── coverage.py        # candidate-to-SDK impact and gate policy
├── suggestions.py     # manifest/test/task/upgrade suggestions
├── generator/         # deterministic generation from approved SDK contract
├── reporting.py       # human/JSON report renderers
├── promotion.py       # explicit promote/reject decision validation
├── observer.py        # release observation state and tracking identity
├── upgrade.py         # deterministic upgrade bundle writer
├── impact.py          # SDK impact mapping for semantic changes
└── files.py           # atomic read/write and no-write check helpers

contracts/
└── sdk-contract.yaml   # approved SDK contract and overrides, not raw evidence

tests/
├── contract/
│   ├── test_cli_manifest.py
│   ├── test_full_cli_coverage.py
│   └── test_upstream_inventory.py
├── fixtures/
│   └── upstream_contract/
│       ├── golden/
│       └── mutations/
└── unit/
    ├── test_upstream_contract_schema.py
    ├── test_upstream_contract_diff.py
    ├── test_upstream_contract_coverage.py
    ├── test_upstream_contract_reporting.py
    ├── test_upstream_contract_collector.py
    └── test_upstream_contract_security.py
```

**Structure Decision**: Introduce `src/multica_py/_internal/upstream_contract/`
instead of growing `manifest.py`. Domain models must not import subprocess,
GitHub, or filesystem adapters. Collectors return typed acquisition results;
normalization, diffing, policy, rendering, and CLI argument handling stay in
separate modules. Source evidence, approved SDK contract, and generator are
separate layers: extractors emit facts and review items; `sdk-contract.yaml`
contains maintainer-approved decisions; generators consume only the approved
contract. `scripts/upstream_contract.py` remains a thin adapter.

## Phased Delivery

### MVP-1: Reliable Offline Semantic Gate

- Schema v2 and migration from current manifest/inventory artifacts.
- Supported, observed, and candidate state model.
- Semantic command, argument, flag, alias, execution, and output metadata.
- Canonical serialization and semantic hashes.
- MVP-1a: supported baseline offline gate only.
- MVP-1b: candidate diff checks, activated only when candidate artifacts are
  explicitly supplied.
- MVP-1c: PromotionDecision validation and explicit promote/reject workflow.
- Supported-to-candidate diff and severity policy.
- Coverage levels, operation IDs, bindings, and explicit shared implementation.
- Machine report, readable summary budget, and exit-code taxonomy.
- PromotionDecision artifact validation for explicit promote/reject workflows.
- Golden, mutation, and determinism tests covering identical contracts,
  command added/removed, optional flag added, required argument added, flag
  removed/renamed/type changed, default changed, alias/rename/move,
  output field added/removed/type changed, hidden/deprecated transition,
  source/binary disagreement, malformed/unknown schema, collector timeout,
  duplicate/shared ownership, schema v1 migration, and same-input repeat runs.
- Dependency-ordered `tasks.md` with FR/SC traceability.

### MVP-2: Automated Discovery and Upgrade Preparation

- Scheduled/networked observer separate from blocking offline CI.
- Release checksum verification and collector security policy.
- Hermetic binary collection where runner support allows it.
- Idempotent tracking issue/PR behavior.
- Upgrade bundle with summary, diff, impact map, candidate contract, manifest suggestions, task/test suggestions, and changelog fragment.

### MVP-3: Deep SDK Compatibility

- Source/binary and exporter/fallback cross-check with the exact trust levels in
  `contracts/implementation-oracles.md`.
- Upstream collection strategy follows this fixed order: release asset
  `multica-cli-contract.json`, binary exporter
  `multica __contract --format json`, then help parser fallback only as
  non-promotable degraded evidence unless cross-checked into a higher trust
  level. Go helper is omitted from the active order until implemented.
- Source-evidence workflow for declarative Cobra facts.
- Approved SDK contract with parameter mapping, presence semantics, enum policy,
  constraints, argv tests, output fixtures, and runtime compatibility matrix.
  Production generation from the approved contract is deferred to feature 003;
  MVP-3 in-repo may stop at validation boundaries plus runtime matrix wiring.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| New internal upstream-contract package | Semantic contract, diff, provenance, coverage policy, reporting, and collectors have separate responsibilities | Extending `manifest.py` would mix parsing, policy, rendering, and IO, making future upstream changes risky |
| Separate scheduled observer | Maintainers need release awareness without blocking PR CI | Running latest upstream discovery in ordinary CI would violate offline reproducibility |

## Post-Design Constitution Re-Check

- **I. Source-Driven CLI Contract**: PASS. Contracts require source-driven semantic data, full upstream commit, source evidence, and explicit promotion.
- **II. Thin Synchronous Wrapper**: PASS. Tooling prepares SDK work but does not implement server behavior.
- **III. Typed Public Surface**: PASS. Typed internal models and approved SDK contracts are required before generated public changes.
- **IV. Offline Testability and Provenance**: PASS. MVP-1 is fully offline; observer is separated and non-blocking.
- **V. Secure Packaging and Release**: PASS. Runtime dependencies do not grow and collector security is explicit.
