## ADDED Requirements

### Requirement: Current operation IDs own independent payload fingerprints
The offline regression guard SHALL store immutable SHA-256 fingerprints keyed directly by every currently guarded `OperationCase.id`. Expected fingerprints SHALL be literal test data and SHALL NOT be computed from implementation, generated bindings, the approved contract, or the operation table during the test. Legacy sequential IDs, both legacy-to-current migration maps, the approved-contract `legacy_argv_migration` field, its loader field/closed-key validation, and migration-only tests SHALL be removed. Manual operation cases SHALL retain a non-null provenance/source reference without recreating a migration map.

#### Scenario: Every guarded current case matches its literal fingerprint
- **WHEN** the payload tuple for a guarded current operation case is hashed
- **THEN** its hash equals the literal value stored under that exact current case ID

#### Scenario: Payload mutation is detected independently
- **WHEN** resource, method, args, kwargs, transport method, exact argv, stdin, timeout, or stdout changes without an intentional literal fingerprint update
- **THEN** the regression test fails

#### Scenario: Fingerprint coverage is closed
- **WHEN** the current fingerprint fixture and guarded case inventory are compared
- **THEN** their keys are exactly equal, all keys resolve to unique current operation cases, and no `legacy:NNN` key or migration lookup remains

### Requirement: Simplification proceeds through phase gates
The implementation SHALL use `e719de13442841c64ed96855c5227bbe5e173f10` as the immutable behavior baseline and record `2ff0fd954851b9125ea3adba39696c00a57e8eab` as the current planning commit whose parent/merge-base is that baseline. Implementation SHALL start at the planning commit or a plan-only descendant; no gate SHALL require the implementation checkout's `HEAD` to equal the baseline. The implementation SHALL establish a recorded baseline, then complete and verify Phase 0 cleanup, Phase 1 options, Phase 2 entities, Phase 3 shared relation state, Phase 4 command encapsulation, and Phase 5 generator pilot in order. Each phase SHALL run its focused tests plus Ruff check/format, `mypy src`, `mypy tests`, offline pytest, collection-only marker verification, approved-contract validation/check, and `git diff --check` at the current phase tip, comparing the resulting evidence with the pinned baseline before the next phase begins. Contract validation SHALL use the pinned upstream checkout recorded by the approved contract. A failing gate SHALL stop later phases until corrected.

#### Scenario: Baseline is recorded before implementation
- **WHEN** implementation starts at planning commit `2ff0fd954851b9125ea3adba39696c00a57e8eab` or a plan-only descendant
- **THEN** required offline, type, style, contract, collection, and diff gates are recorded from the pinned baseline `e719de13442841c64ed96855c5227bbe5e173f10` before production changes, and the implementation tip remains a descendant of the planning commit

#### Scenario: Live tests remain excluded from offline collection
- **WHEN** `pytest -m "not live" --collect-only` runs after any phase
- **THEN** no `tests/live/*` node is collected

#### Scenario: Dead-code cleanup preserves active guardrails
- **WHEN** compatibility models/helpers and executable resolver code are deleted
- **THEN** generated min/max version enforcement, `check_version_from_config`, transport error mapping, and their runtime tests remain

#### Scenario: No unrelated cleanup enters a phase
- **WHEN** a phase diff is reviewed
- **THEN** it introduces no new dependency and contains only that phase's implementation, tests, generated artifacts, and required contract/spec updates

### Requirement: Public and behavioral invariants remain closed
Offline verification SHALL prove after the final phase that every CLI-backed eager operation retains one typed public `*_command() -> Command[T]` sibling and delegates through `Command.run()`, command construction validates before I/O, and public signatures/return types, exact argv, result decoding, redaction, stdin, timeout, cwd/environment, immutable config snapshots, compatibility preflight, shared semaphore, exception mapping, temporary cleanup, and process lifecycle are unchanged. Entity equality/hash/repr/serialization/detach/rebind and relation cache/concurrency/retry/refresh/invalidation/pagination semantics SHALL be asserted through public behavior.

#### Scenario: Public eager and command inventory is unchanged
- **WHEN** final public discovery, canonical operation rows, and approved entrypoints are compared to the baseline
- **THEN** the inventories and normalized eager/command signatures are identical

#### Scenario: Command preview remains passive
- **WHEN** representative eager, cached, composite, paginated, temporary-file, and generated-pilot commands expose `.commands`, `repr`, or `str` before `run()`
- **THEN** no subprocess, network, filesystem materialization, or other I/O occurs and secrets remain redacted

#### Scenario: Entity and relation matrices retain behavior
- **WHEN** table-driven public tests exercise field classification, round trips, cache hits, concurrent waiters, retry, failed refresh, invalidate, offset/cursor traversal, and progress limits
- **THEN** results, errors, metadata, and subprocess counts match the baseline contracts

### Requirement: Relation lifecycle follow-up requires a separate decision
After Phases 2 through 4, the implementer SHALL remeasure private entity-to-resource calls, `_set_runtime` usage, invalidation callbacks, concepts, and files touched per relation. This change SHALL NOT implement a repository-wide relation lifecycle rewrite. A future pilot MAY cover exactly one complex relation only after an explicit new decision records remaining material duplication and success criteria based on deleted helpers/callbacks and reduced change surface.

#### Scenario: Remeasurement finds no material duplication
- **WHEN** the post-Phase-4 measurements do not justify another abstraction
- **THEN** no relation-lifecycle pilot is created and the decision is recorded

#### Scenario: Remeasurement supports a pilot
- **WHEN** material duplication remains and one complex relation can test the hypothesis
- **THEN** implementation stops at a documented follow-up proposal rather than adding the pilot or a universal relation framework to this change
