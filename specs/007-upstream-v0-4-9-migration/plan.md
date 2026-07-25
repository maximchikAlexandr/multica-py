# Implementation Plan: Upstream v0.4.9 Migration

**Branch**: `upstream-v0-4-9-migration` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from
`/specs/007-upstream-v0-4-9-migration/spec.md`

## Summary

Migrate the 16 operation IDs governed by `contracts/sdk-contract.json` from the
historical live baseline `v0.3.10` to exact upstream `v0.4.9` at commit
`ecbdbda09e7b2be56cd9ccc55cee1ee360222d18` without automatically expanding the
public SDK to the target's 35 new command paths. Replace the flat approved
contract with a closed schema-v2 operation model, generate seven deterministic
SDK/metadata/test artifacts only from that contract, integrate approved
bindings and validators into handwritten resources, repair candidate and
promotion identity, and enforce one fail-closed cross-artifact coherence gate.
Fifteen governed operations remain compatible; `issues.comments.list` is an
intentional public change to the target's paired cursor contract. Live
acceptance follows offline acceptance and uses categorized results, a
provider-correct runtime predicate, fail-closed mutation, and exactly ten
full-smoke repetitions.

## Technical Context

**Language/Version**: Python 3.12 and 3.13; mypy checks production code
strictly against Python 3.12 semantics.

**Primary Dependencies**: Runtime `msgspec>=0.19,<2`; stdlib JSON, hashing,
path, subprocess, and temporary-file facilities for contract generation and
validation; no new runtime or test dependency.

**Storage**: Repository-owned JSON/TOML/Python/Markdown artifacts. The approved
contract is `contracts/sdk-contract.json`; active semantic state is under
`src/multica_py/_generated/`; live evidence is file-based.

**Testing**: pytest with table-driven cases in `tests/cases/`, generic unit argv
and component fake-CLI runners, offline contract/coherence tests, live smoke and
extended profiles, Ruff, strict mypy, package checks, and the five-stage test
architecture/baseline gate.

**Target Platform**: Linux and macOS on Python 3.12/3.13. Live acceptance uses
the exact release assets and backend platform digests in release provenance.

**Project Type**: Single-package synchronous Python SDK wrapping a controlled
Multica CLI subprocess, plus maintainer contract/provenance tooling.

**Performance Goals**: Byte-identical deterministic generation; generator
`--check` performs no writes; the default suite remains offline and
CI-suitable; stability requires 10/10 full-smoke passes.

**Constraints**: Exact target source outranks secondary evidence. Only the
approved contract drives public generation. No `Any` in typed APIs, new runtime
dependency, shell invocation, secret leakage, heuristic fallback, automatic
public promotion, or live acceptance before contract/coherence gates pass.

**Scale/Scope**: Exactly 16 governed operation IDs, 15 compatible and one
intentionally changed; 11 upstream families classified; 35 target additions
remain unapproved; seven governed generated outputs; one canonical candidate,
one canonical supported contract, and one target provenance.

## Constitution Check

*GATE: evaluated before research and re-evaluated after Phase 1 design.*

| Principle | Design impact | Pre-research | Post-design |
| --- | --- | --- | --- |
| I. Source-Driven CLI Contract | Every governed operation contains full-commit source references, exact command/destination mappings, presence outcomes, and test references. Exact source controls conflicts; degraded help remains suggestion-only. | PASS | PASS |
| II. Thin Synchronous Wrapper | Resources continue to call the installed CLI. Generated bindings and validators encode approved CLI behavior; no server API client or business workflow is introduced. | PASS | PASS |
| III. Typed Public Surface | Schema-v2, generated enums/validators/bindings, cursor/page models, and live outcomes use closed typed structures. Unknown fields and unclassified states fail closed. | PASS | PASS |
| IV. Offline Testability and Provenance | Deterministic generated cases, fake CLI, coherence checks, JUnit/coverage/mutation artifacts, and exact provenance provide offline acceptance. Live results are separately categorized. | PASS | PASS |
| V. Secure Packaging and Release | Existing controlled transport and redaction remain. Provenance binds checksums/digests; generation adds no dependency; release identity must agree across artifacts before support is claimed. | PASS | PASS |

**Quality gates**: Ruff format/check, mypy for `src`, `tests`, `scripts`, and
`tools`, complete non-live pytest, generator check, upstream state/coherence
check, five-stage architecture/baseline checks with mandatory
JUnit/coverage/mutation inputs, package checks, then categorized live gates.

**Gate result**: PASS before and after design. There are no constitution
violations and no justified exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/007-upstream-v0-4-9-migration/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── HANDOFF.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── approved-sdk-contract-v2.md
│   ├── operation-decisions.md
│   ├── generation-and-provenance.md
│   ├── live-acceptance.md
│   ├── requirement-traceability.md
│   └── upstream-family-disposition.md
└── tasks.md                         # dependency-ordered implementation tasks
```

### Source Code (repository root)

```text
contracts/
├── sdk-contract.json                # schema-v2 approval authority
└── multica-live-target.toml          # exact accepted live target

src/multica_py/
├── enums.py                          # re-export approved generated enums
├── models/
├── resources/
├── _generated/                       # governed and semantic projections
└── _internal/upstream_contract/
    ├── generator/                    # closed models, validation, rendering
    ├── state.py
    ├── promotion.py
    ├── provenance.py
    ├── coverage.py
    └── cli.py

scripts/
├── upstream_contract.py
└── check_coverage.py

tests/
├── cases/
│   ├── argv_data.py
│   ├── operations.py
│   └── operations.py
├── fixtures/provenance/
├── unit/
├── component/
├── contract/
└── live/

.github/workflows/
├── ci.yml
└── live-smoke.yml
```

**Structure Decision**: Retain the single-package SDK and existing test
architecture. Add the generator inside the existing internal upstream-contract
package. Keep sequencing/decoding handwritten and integrate generated bindings,
validators, enums, signatures, cases, documentation, and
compatibility/provenance projections. Keep live acceptance in the prepared
target smoke suite, so production SDK code never depends on tests or scripts.

## Exact Implementation Ownership

This ownership is binding; do not introduce alternate modules.

| File | Exact responsibility |
| --- | --- |
| `src/multica_py/_internal/upstream_contract/generator/schema.py` | Own all closed schema-v2 structs and catalog reference types |
| `src/multica_py/_internal/upstream_contract/generator/validation.py` | Own `load_approved_contract()` and `validate_approved()` |
| `src/multica_py/_internal/upstream_contract/generator/renderer.py` | Define frozen `GeneratedOutput(path: pathlib.Path, content: bytes)` and render the seven exact manifest outputs |
| `src/multica_py/_internal/upstream_contract/generator/writer.py` | Define same-directory staged output writes and non-writing complete diff reporting |
| `src/multica_py/_internal/upstream_contract/generator/__init__.py` | Export only approved contract load/validate/render/write/check API |
| `src/multica_py/_internal/upstream_contract/coherence.py` | Define `validate_supported_target(repo_root) -> None` for active files and `validate_promotion_projection(repo_root, projected_outputs) -> None` for in-memory promotion bytes; raise `InvalidArtifactError` when any compared artifact is invalid |
| `src/multica_py/_internal/upstream_contract/cli.py` | Add `cmd_generate`; add `generate --approved PATH [--check]`; call coherence validation from `cmd_check`; reject evidence and candidate files as `--approved` inputs |
| `src/multica_py/_internal/upstream_contract/models.py` | Extend `PromotionDecision` with `approved_contract_hash`, `target_version`, `target_tag`, `target_commit`, `release_provenance_ref`, and `release_provenance_hash`; do not store these identities in arbitrary resolution dictionaries |
| `src/multica_py/_internal/upstream_contract/state.py` | Validate canonical refs, existence, decoded kind/identity, and recomputed semantic hashes in `validate_state`; clear candidate only through successful `replace_supported` |
| `src/multica_py/_internal/upstream_contract/promotion.py` | Implement only the lock/journal/backup/replace/rollback/recovery transaction specified in `generation-and-provenance.md` |
| `tests/live/test_smoke.py` | Execute the five prepared-target smoke scenarios through the public SDK |
| `scripts/check_coverage.py` | Enforce coverage thresholds from the merged report. |

New focused test modules are fixed to:

- `tests/unit/test_upstream_contract_generator.py`;
- `tests/unit/test_upstream_contract_coherence.py`;
- `tests/unit/test_live_outcomes.py`;
- `tests/unit/test_live_runtime_readiness.py`.

Extend, rather than duplicate, the existing state, promotion, provenance,
compatibility-report, live-support, and bootstrap test modules.

The three mutation cases target these exact nodes after their canonical rows are
updated:

- `tests/unit/resources/test_operations.py::test_operation_argv[projects.update]`;
- `tests/unit/resources/test_operations.py::test_operation_argv[labels.get]`;
- `tests/unit/test_transport.py::test_exit_code_maps_to_exception[exit-4-notfound]`.

Mutation execution uses offline nodes and does not perform live environment
bootstrap. Live smoke and repeat remain separate later gates.

## Implementation Phases and Gates

### Phase A — Approval authority

1. Verify the pinned source checkout and every family/operation source ref,
   then replace the flat contract model in
   `src/multica_py/_internal/upstream_contract/generator/schema.py` with the
   closed schema-v2 model in
   [approved-sdk-contract-v2.md](./contracts/approved-sdk-contract-v2.md).
2. Validate the complete feature seed, then byte-copy it to
   `contracts/sdk-contract.json`; no contract fact is authored during
   implementation.
3. Validate unique scope/operation/entrypoint identifiers, closed fields,
   complete presence outcomes, command-step references, enums, constraints,
   full-commit source refs, and resolving test refs.

**Gate A**: schema validation passes; exactly 16 unique operation IDs exist;
15 are `compatible`, one is `intentionally_changed`; no unresolved review
item, unknown field, or new operation ID exists.

### Phase B — Deterministic generation and public integration

4. Implement deterministic rendering and same-directory staged writes under
   `src/multica_py/_internal/upstream_contract/generator/`; expose `generate`
   and `generate --check` through `scripts/upstream_contract.py`.
5. Generate the seven outputs specified in
   [generation-and-provenance.md](./contracts/generation-and-provenance.md).
6. Re-export generated enums, import generated bindings/validators in governed
   handwritten resources, and keep multi-step issue creation and decoding
   handwritten.
7. Implement selected public fixes: issue sort/direction; composite comment
   cursor/page types; invalid flat paging removal; non-empty issue/comment/
   project inputs; project empty-update rejection; preserved project-resource
   presence semantics and timeout/error mapping.
8. Add table rows before distinct tests. Preserve complete expected argv and
   positive/negative constraint coverage.

**Gate B**: generator `--check` reports zero differences and no writes; Ruff,
mypy, focused unit/component/contract tests, and completeness guards pass.

### Phase C — Candidate, promotion, and coherence

9. Stage the existing help-degraded evidence only through
   `validate --source-checkout`; bind it to the approved/source-validated
   contract with trust `approved-contract-bound`, never `verified`.
10. Validate canonical paths, existence, strict decode, kind, target identity,
    and recomputed semantic hashes.
11. Require a pre-existing real-maintainer decision bound to candidate hash,
    approved hash, exact target, provenance, previous identity, and review ref;
    automation never creates it. Clear candidate only after commit.
12. Add one fail-closed validator used by `upstream_contract check` and an
    offline contract test.
13. Only after generator, state, promotion dry-check, and coherence validation
    are green, update supported semantic state, CLI manifest metadata, coverage
    bindings, and `contracts/multica-live-target.toml` to exact `v0.4.9`.

**Gate C**: canonical references resolve; hashes and target identity agree; all
16 projections agree exactly; unrelated coverage remains unchanged; none of the
35 additions is accidentally approved.

### Phase D — Interpretable live harness

14. Keep live acceptance to the five prepared-target smoke scenarios in
    `tests/live/test_smoke.py`.
15. Leave backend lifecycle, credentials, workspace preparation, and provider
    readiness to the prepared environment owner.
19. Produce the mutation result first, then require offline JUnit, coverage
    JSON, and that mutation JSON as explicit final-baseline inputs; missing or
    unreadable input is invalid.

**Gate D**: focused offline harness tests pass for runtime cardinality, every
result category, malformed/missing JUnit, wrong mutation node/fingerprint,
source restoration, and repeat prerequisites.

### Phase E — Acceptance

20. Run the full offline sequence in [quickstart.md](./quickstart.md), including
    all five architecture/baseline stages with mandatory final artifacts.
21. Run target smoke and extended; each must pass with exact target fingerprint,
    reached operations, green cleanup, and redacted diagnostics.
22. Verify the already-produced mutation summary is exactly 3/0/0.
23. Run exactly ten full-smoke repetitions and require 10/10 passes with no
    managed leftovers.

No later phase starts while the preceding gate is red. An environment,
authentication, or invalid-run result is inconclusive, not a product pass or
target regression.

## Complexity Tracking

No constitution violations.
