## MODIFIED Requirements

### Requirement: Canonical operation coverage

Every supported public SDK resource method MUST have exactly one canonical
success operation row with complete transport behavior. The expected
method set MUST be derived from public discovery and compared for exact
equality to canonical rows with no allowlist. Case-count constants and
legacy fingerprint counts MUST be changed in the same commit as their
added/removed rows and MUST equal the lengths computed from the final
case tables; historic literals 117/146/29/143 are not post-change
requirements. Every CLI-executing canonical method MUST also have a
matching typed `*_command()` method and a command-preview test case; the
completeness gate MUST fail closed when a new public CLI-executing method
is added without a command form and command-preview case. Methods that
perform no CLI subprocess are excluded from the command-coverage
requirement.

#### Scenario: Public methods have canonical operation coverage

- **WHEN** `discovered_public_methods` is compared to
  `{case.sdk_method for case in OPERATION_CASES if case.is_canonical}`
- **THEN** the sets are equal, every supported method has one canonical
  row, removed methods have none, and stored count constants equal the
  computed table partitions

#### Scenario: CLI-executing methods have command coverage

- **WHEN** the canonical method set is inspected for command preview
  coverage
- **THEN** every CLI-executing canonical method has a matching typed
  `*_command()` method and a command-preview test case, and local-only
  methods are excluded

#### Scenario: New uncovered CLI-executing method fails the gate

- **WHEN** a new public CLI-executing method is added without a
  `*_command()` sibling and command-preview case
- **THEN** the offline completeness gate fails

### Requirement: Focused process and offline checks

Offline tests MUST use stdlib and pytest, keep exact argv assertions
including operations with dynamic temporary paths, retain exactly three
real-process cases, and use deterministic synchronization or subprocess
test doubles for additional lifecycle branches. CLI-routing tests MUST
assert commands through the public `*_command()` feature instead of
reconstructing expected transport calls through a separate path. The
existing table-driven `OperationCase` inventory remains the source for
coverage; the SDK SHALL NOT create a parallel command-preview case
hierarchy. For every `OperationCase`, the routing assertion SHALL:
construct the matching `*_command()` without subprocess I/O, assert the
complete `command.commands` tuple (executable + global args + shell
quoting), call `command.run()`, assert result decoding and side effects,
and assert the transport received argv, execution mode, stdin, and
timeout derived from that same plan, normalizing only already-declared
dynamic runtime positions. Transport-only tests MAY continue to test
`CliTransport` directly; tests unrelated to CLI routing do not need
artificial command assertions.

#### Scenario: Offline checks keep focused process cases

- **WHEN** the process module is collected
- **THEN** IDs are `bytes-env`, `text-stdin`, and `timeout-tree-cleanup`.

#### Scenario: Dynamic argv remains exact

- **WHEN** an operation creates a temporary file or directory path
- **THEN** only the declared dynamic argv position is normalized and the
  complete remaining argv, transport method, stdin, and timeout are
  compared exactly

#### Scenario: Routing tests use the public command preview

- **WHEN** a CLI-routing `OperationCase` runs
- **THEN** it constructs the matching `*_command()`, asserts
  `command.commands`, calls `command.run()`, asserts the result, and
  asserts the transport received argv/execution-mode/stdin/timeout from
  the same plan, instead of reconstructing expected argv through a
  separate path

#### Scenario: No parallel command-preview case hierarchy

- **WHEN** command-preview coverage is added
- **THEN** it extends the existing `OperationCase` table and shared
  fixtures rather than creating a parallel case type or file

### Requirement: Complete relation roadmap verification

Offline verification MUST cover every relation in the 33-relation matrix,
every corrected drift operation, all five loading strategies, bound/
snapshot typing, exact argv and response shapes, subprocess counts,
immutable replacement, presence, per-entity lazy state/refresh/
invalidation, concurrency, prefetch bounds, and public migration
behavior using stdlib and pytest. It MUST also cover command forms for
every CLI-loading relation entry point, including cache-hit
(`commands == ()`), forced refresh, offset/cursor `page_command()`, and
prefetch routing through `all_command().run()` under concurrency.

#### Scenario: Matrix has traceable coverage

- **WHEN** relation coverage is audited
- **THEN** each of the 33 relations maps to an approved operation,
  requirement scenario, table-driven success case, negative/error case
  where applicable, and implementation test reference

#### Scenario: Drift fixes have positive and negative proof

- **WHEN** any of the 19 drift dispositions changes argv, decoding,
  validation, presence, or removes a method
- **THEN** focused fixtures prove the supported behavior and reject the
  legacy incompatible behavior

#### Scenario: Repeated relation tests are rows

- **WHEN** another parent/relation call-and-assert case is added
- **THEN** coverage grows through frozen dataclass case rows and shared
  fixtures before a new test function or file is considered

#### Scenario: Exact transport behavior is asserted

- **WHEN** lazy, paged, cached, refreshed, invalidated, retried, and
  prefetched cases run
- **THEN** they assert complete argv, transport method, stdin, timeout,
  and exact subprocess count through the public command preview path

#### Scenario: Presence and replacement are adversarially tested

- **WHEN** compact, explicit-empty, complete embedded, and richer
  follow-up payloads are decoded across workspace scopes
- **THEN** tests distinguish missing from empty, seed only complete
  fields, and prove list/get return distinct immutable wrappers without
  cross-wrapper state

#### Scenario: Pagination cannot run forever

- **WHEN** offset or cursor fixtures return empty, repeated, malformed,
  or no-progress continuation state
- **THEN** a bounded call count and typed error are asserted and no
  partial complete result is cached

#### Scenario: Relation command forms are verified

- **WHEN** relation command-preview coverage is audited
- **THEN** cache-hit (`commands == ()`), forced refresh,
  `OffsetLazyCollection.page_command`, `CursorLazyCollection.page_command`,
  and prefetch routing through `all_command().run()` under concurrency
  are each covered by focused cases

## ADDED Requirements

### Requirement: Command preview focused coverage

Offline verification MUST cover focused command-preview cases using
stdlib and pytest: no-I/O command construction; one-command,
multi-command, `run_text`, `run_bytes`, and `spawn` plans; global args
and shell quoting; token redaction without changing executed argv; stdin
and timeout preservation; runtime path and result-reference resolution;
cache hit (`commands == ()`) and forced refresh; offset/cursor
pagination and failure guards; prefetch calling relation command plans
under concurrency; command/config snapshot behavior; and failures
stopping a composite plan at the correct step. These cases MUST extend
the existing frozen-dataclass case tables (`OperationCase` and the
relation case containers) rather than creating a parallel hierarchy.

#### Scenario: No-I/O command construction is verified

- **WHEN** a `*_command()` is constructed for any covered case
- **THEN** no `CliTransport` method is called and no subprocess is
  spawned

#### Scenario: Composite failure stops at the correct step

- **WHEN** a composite plan case fails at a defined step
- **THEN** the case asserts the exception type, that no later step
  executed, and that completed steps were not rolled back or repeated

#### Scenario: Snapshot behavior is verified

- **WHEN** a constructed `Command` outlives a later client/config change
- **THEN** the case asserts `command.commands` and the executed argv
  reflect the snapshotted configuration, not the later value

#### Scenario: Runtime placeholders are verified

- **WHEN** a local-I/O wrapper case (`upload_bytes`/`download_bytes`)
  runs
- **THEN** the case asserts the placeholder appears in preview, the
  resolved path reaches the transport during `run()`, the return value
  decodes correctly, and the temporary directory is removed on success
  and failure