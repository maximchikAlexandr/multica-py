# Research: Upstream v0.4.9 Migration

## Research Scope

This research closes every design decision required to migrate the 16 operation
IDs governed by `contracts/sdk-contract.json` from the historical live target
`v0.3.10` to exact upstream `v0.4.9` at
`ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`.

The current repository at `e348d18` is authoritative for SDK structure and test
architecture. The evidence package under
`.devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9/` is authoritative for
the collected release and target-source evidence. The checked-out upstream
target source is authoritative when an evidence summary and source disagree.

No design question remains open after this document. Every rejected alternative
is recorded only to prevent an implementer from selecting it later.

For the full implementation-grade handoff — exact file/symbol maps, target
source traces, test authorities, pipeline defects, live-harness root causes,
acceptance commands, current session state, and remaining Spec Kit work — see
[HANDOFF.md](./HANDOFF.md).

## Decision 1: Migration Contract Boundary

**Decision**: `contracts/sdk-contract.json` schema version 2 will govern exactly
the following 16 existing operation IDs:

1. `issues.comments.add`
2. `issues.comments.delete`
3. `issues.comments.list`
4. `issues.create`
5. `issues.labels.add`
6. `issues.labels.list`
7. `issues.labels.remove`
8. `issues.list`
9. `issues.set_status`
10. `projects.create`
11. `projects.resources.add_local_directory`
12. `projects.resources.list`
13. `projects.resources.remove`
14. `projects.resources.update_local_directory`
15. `projects.set_status`
16. `projects.update`

The contract is an approved typed-operation subset, not an inventory of every
public/raw/process operation currently present in the SDK. Existing operations
outside this set remain unchanged by this migration. Their presence in source
or `upstream_coverage.json` does not grant them schema-v2 approval.

**Rationale**: The current contract has 22 flat parameter rows but 16 unique
operation IDs. The repository's semantic coverage contains 108 operation
decisions, most at `raw` or `process` coverage. Replacing that 108-operation
inventory with 16 rows would remove unrelated existing public behavior and
violate the migration scope.

**Rejected alternatives**:

- Treat all 108 coverage decisions as approved schema-v2 operations: rejected
  because evidence and approval are not available for that expansion.
- Require generated public operation IDs to equal the 16-ID set: rejected
  because it would delete or invalidate unrelated existing SDK operations.
- Keep schema version 1 and repeat operation metadata on every parameter row:
  rejected because repeated compatibility outcomes, source commits, and
  response/error contracts can drift within one operation.

## Decision 2: Approved Contract Schema

**Decision**: Replace the flat schema-v1 rows with schema-v2 operation objects.
Each operation contains:

- one unique `operation_id`;
- one compatibility outcome;
- one or more public entrypoints;
- exact target command binding and output mode for each entrypoint;
- ordered execution steps when an SDK call invokes more than one CLI command;
- complete public signatures;
- complete accepted parameter mappings;
- exact path/query/JSON body/header/multipart/local-control destinations;
- explicit omitted/null/empty/zero/false outcomes;
- enum policy, values, aliases, and deprecated values;
- normalized constraints;
- response and error contracts;
- full-commit, symbol, and line-range source references;
- existing test references that must resolve to files;
- an operation-level rationale.

Unknown fields are rejected at every level. The allowed destination values and
constraint categories remain closed enums. `local_control` is used only when a
value does not reach an upstream HTTP request.

**Rationale**: The current `ApprovedOperation` cannot represent the required
operation outcome, parameter destination, response/error behavior, exact source
commit, multiple entrypoints, composite cursor, or multi-command issue creation.

**Rejected alternatives**:

- Store decisions in a second sidecar file: rejected because it creates two
  approval authorities.
- Store arbitrary dictionaries for new fields: rejected because weak
  implementers and validators would not have a closed model.
- Infer response, error, or destination fields during generation: rejected
  because generation must not make review decisions.

The exact schema and validation invariants are defined in
`contracts/approved-sdk-contract-v2.md`.

## Decision 3: Compatibility Outcomes for the 16 Operations

**Decision**:

- `issues.comments.list` is `intentionally_changed` because the public advanced
  pagination API currently emits target-invalid `--limit` and scalar
  `--before` arguments. It will move to the target's composite cursor.
- The other 15 operations are `compatible`.
- No operation is `explicitly_unsupported`.
- `issues.set_status` and `projects.set_status` are compatible operations with
  corrected contract metadata. Their public implementations already emit the
  correct target commands.

**Rationale**: Exact target source proves all 16 command families exist. Only
advanced comment pagination requires a public signature/result change to
represent target truth.

**Rejected alternatives**:

- Classify the two status operations as intentionally changed: rejected because
  both the current Python SDK and both upstream versions use `status`; only
  stale contract metadata says `set-status`.
- Add a `set-status` fallback or runtime command probe: rejected because neither
  baseline nor target source declares that command.
- Mark advanced comment pagination unsupported: rejected because the target has
  a complete source-backed replacement.

The operation-by-operation decision and acceptance matrix is defined in
`contracts/operation-decisions.md`.

## Decision 4: Status Bindings

**Decision**:

- `issues.set_status` binds only to
  `issue status <id> <status>`.
- `projects.set_status` binds only to
  `project status <id> <status>`.

No alias, fallback, migration branch, or feature probe is permitted.

**Rationale**:

- Target `cmd_issue.go:219-227` declares `status <id> <status>` and
  `cmd_issue.go:1423-1454` sends the resolved status in the issue update body.
- Target `cmd_project.go:54-59` declares `status <id> <status>` and
  `cmd_project.go:487-520` sends the project status update.
- Baseline `v0.3.10` source also declares `status`.
- Current Python resources and canonical argv cases already use `status`.

**Rejected alternative**: Preserve schema-v1 `set-status` for backward
compatibility. Rejected because it describes no verified upstream command and
would make generated metadata contradict working code.

## Decision 5: Issue List Surface

**Decision**: Preserve all existing `IssueListFilter` fields and add exactly:

- `sort: IssueSort | None`;
- `direction: SortDirection | None`.

`IssueSort` is a strict enum with values `position`, `title`, `created_at`,
`start_date`, `due_date`, and `priority`. `SortDirection` is a strict enum with
values `asc` and `desc`.

Validation rules:

- omitted `sort` and `direction` emit neither flag;
- `sort` without `direction` emits only `--sort`;
- `direction` requires `sort`;
- `direction` is invalid when `sort` is `position`;
- existing status remains a strict `IssueStatus`;
- existing optional fields remain omitted only when `None`;
- `limit=None` omits `--limit`;
- `limit<=0` remains representable and reaches the target flag; target source
  treats it as no positive limit. The SDK does not invent a stricter range.

No project, offset, metadata, date, or new filtering field is added in this
migration.

**Rationale**: The specification explicitly requires positive and negative
coverage for the target sort/direction relationship. Other target list fields
are not required to preserve the existing 16-operation surface.

**Rejected alternatives**:

- Add every target issue-list flag: rejected as unapproved public expansion.
- Accept free-form sort/direction strings: rejected because the target choices
  are closed and source-confirmed.
- Reject non-positive limits locally: rejected because target source does not
  reject them and existing SDK inputs must not acquire an invented constraint.

## Decision 6: Comment List and Composite Cursor

**Decision**: Add these public models:

- `CommentCursor(before: str, before_id: str)`;
- `CommentPage(items: tuple[Comment, ...], next_cursor: CommentCursor | None)`;
- `CommentThreadPage(items: tuple[CommentThread, ...], next_cursor:
  CommentCursor | None)`.

Both cursor fields must be non-empty.

Entrypoint contracts:

- `list(issue_id)` remains unchanged and returns `tuple[Comment, ...]`.
- `list_flat(CommentListFlatRequest)` supports only `issue_id` and optional
  `since`. The obsolete `cursor` and `limit` fields are removed because target
  default/flat mode has no valid paging equivalent. It returns `CommentPage`
  with `next_cursor=None`.
- `list_thread(CommentListThreadRequest)` supports `issue_id`, `thread_id`,
  optional `limit`, optional composite `cursor`, and optional `since`.
  `limit` maps to `--tail`, accepts zero, rejects negative values, and is
  required when `cursor` is present.
- `list_recent(CommentListRecentRequest)` supports `issue_id`, required positive
  `limit` with default 10, optional composite `cursor`, and optional `since`.
- A cursor emits `--before <before> --before-id <before_id>` atomically.
- The stderr parser accepts only:
  `Next thread cursor: --before VALUE --before-id ID` and
  `Next reply cursor: --before VALUE --before-id ID`.
  A partial or malformed pair is an output-shape error, not `None`.

**Rationale**: Target `cmd_issue.go:510-519` and `1756-1890` require paired
`--before`/`--before-id`. `--before` is legal only with `--recent` or
`--thread` plus `--tail`. There is no target `--limit` flag.

**Rejected alternatives**:

- Concatenate the timestamp and UUID into one opaque string: rejected because it
  loses source semantics and requires an invented escaping format.
- Keep scalar `cursor` and infer `before_id`: rejected because the UUID cannot
  be derived from the timestamp.
- Keep `list_flat.limit` and slice locally: rejected because the SDK must not
  reimplement upstream pagination.
- Silently ignore the obsolete fields: rejected because that would change
  caller intent without an error.

## Decision 7: Other Issue and Comment Semantics

**Decision**:

- `IssueCreateRequest.title` must be non-empty.
- `InlineDescription(text="")` means description omitted and emits no
  `--description`.
- File and stdin description channels remain explicit discriminated variants;
  no new attachment/file public fields are added.
- `label_ids` remain ordered post-create `issue label add` steps followed by one
  `issue get` refresh. The contract records this non-atomic command sequence.
- `IssueCommentResource.add` rejects an empty body before spawning the CLI and
  otherwise preserves `--content`.
- Comment delete remains `None` on success.
- Comment response shape errors continue to fail through the existing decode
  error path.

**Rationale**: These rules reflect existing public shapes while matching target
input-channel and non-empty-content validation.

**Rejected alternatives**:

- Add target attachment upload to the public contract: rejected as a separate
  extension decision.
- Make issue creation transactional in the SDK: rejected because the thin CLI
  wrapper must not reimplement server workflows.
- Treat malformed comment JSON as an empty list: rejected because that hides a
  target incompatibility.

## Decision 8: Label Operations

**Decision**: Preserve all three label entrypoints and tuple return types.
Duplicate add and absent-relation remove remain successful idempotent outcomes
when target identifiers are valid. Malformed or wrong-scope responses fail
through existing validation/not-found/decode classifications.

If the target's post-mutation refresh returns `{}` instead of a label list, the
SDK raises the existing output-shape/decode error. It does not issue an
unapproved fallback refetch and does not reinterpret `{}` as an empty list.

**Rationale**: This is the only fail-closed behavior that preserves response
truth without adding a hidden second command.

**Rejected alternatives**:

- Convert `{}` to `()`: rejected because it falsely states that no labels exist.
- Automatically call label list after malformed mutation output: rejected
  because it changes command count and can hide a server defect.

## Decision 9: Project and Project Resource Semantics

**Decision**:

- Project create keeps only `name` and optional `description`.
- Project create rejects an empty name.
- Empty project-create description means omitted and emits no flag.
- Project update keeps `name` and `description`.
- `Unset` means not provided.
- Empty string is emitted and clears the target field.
- `description=None` remains locally rejected.
- An update with both fields `Unset` is locally rejected before subprocess
  execution.
- Project resource add keeps required local path and daemon ID plus optional
  label.
- Add-resource label `None` or `""` both mean omitted.
- Project resource update remains a required local-path update; label-only and
  daemon-only updates are not added.
- Project resource remove remains `None` on success.

**Rationale**: These are the complete current public fields for the approved
operations and their exact target presence semantics.

**Rejected alternatives**:

- Add all new project fields: rejected as unnecessary public expansion.
- Interpret `description=None` as clear: rejected because current public
  behavior explicitly rejects it and empty string already represents clear.
- Expand resource update to every target partial field: rejected because the
  migration does not approve new request fields.

## Decision 10: Transport Timeout and Error Compatibility

**Decision**:

- Preserve `ClientConfig.timeout` as the SDK subprocess outer deadline.
- Preserve `timeout=None` as no SDK process-kill deadline.
- Do not copy the target CLI's 30-second HTTP timeout into SDK defaults.
- Do not parse or own `MULTICA_HTTP_TIMEOUT`; the child process naturally
  inherits it through the existing controlled environment.
- Preserve semantic exit mapping:
  network `2`, authentication `3`, not-found `4`, validation `5`.
- Generic exit `1`, including conflict, rate limiting, and server failures,
  remains `CommandExecutionError` unless exact CLI exit behavior proves a
  different stable category.
- Add acceptance rows that distinguish SDK process timeout from CLI
  `NetworkError`.

**Rationale**: The SDK controls a subprocess, not the upstream HTTP client. A
second HTTP timeout policy in the SDK would duplicate CLI behavior and violate
the thin-wrapper principle.

**Rejected alternatives**:

- Change SDK default timeout to 30 seconds: rejected because this is a CLI HTTP
  timeout, not a subprocess deadline.
- Add a new rate-limit exception based on stderr prose: rejected because exact
  stable exit classification is not source-backed.

## Decision 11: Deterministic Generator

**Decision**: Implement a real generator under
`src/multica_py/_internal/upstream_contract/generator/`. Its only decision input
is a decoded and validated `contracts/sdk-contract.json`. Evidence bundles,
candidate contracts, manifest suggestions, and source-delta files are never
accepted generator inputs.

Generated outputs:

1. `src/multica_py/_generated/approved_sdk_contract.json`
2. `src/multica_py/_generated/approved_sdk_bindings.py`
3. `src/multica_py/_generated/approved_sdk_enums.py`
4. `src/multica_py/_generated/approved_sdk_validators.py`
5. `src/multica_py/_generated/approved_sdk_api.pyi`
6. `src/multica_py/_generated/approved_sdk_compatibility.json`
7. `docs/generated/approved-sdk-v0.4.9.md`
8. `tests/cases/generated/approved_sdk_cases.py`
9. `tests/fixtures/provenance/approved-sdk-v0.4.9.json`

Handwritten resources import generated command bindings and validators.
`multica_py.enums` re-exports the generated approved enums. Complex command
sequencing and response decoding remain in handwritten resources but are
verified against generated entrypoint/signature and case metadata.

The generator exposes:

```text
uv run python scripts/upstream_contract.py generate \
  --approved contracts/sdk-contract.json
```

and a non-writing exact-byte gate:

```text
uv run python scripts/upstream_contract.py generate \
  --approved contracts/sdk-contract.json \
  --check
```

All outputs are rendered in memory before any write. A write run writes
same-directory temporary files, then replaces destinations in a fixed order.
`--check` reports every missing, extra, or byte-different governed output and
returns non-zero without writing.

**Rationale**: The current `generator` package only loads and validates the
contract and has no production caller. It does not currently generate SDK code
or metadata.

**Rejected alternatives**:

- Continue manual synchronization: rejected because it cannot meet the single
  approved contract requirement.
- Generate entire resource modules: rejected because those modules contain
  unrelated operations outside the 16-ID migration boundary.
- Use source-delta or candidate contract as generator input: rejected because
  they are evidence, not approval.
- Add a template dependency: rejected because deterministic stdlib rendering is
  sufficient and runtime dependencies must remain unchanged.

The output contract and consistency rules are defined in
`contracts/generation-and-provenance.md`.

## Decision 12: Semantic Candidate Identity and Promotion

**Decision**:

- Candidate state always references the canonical path
  `src/multica_py/_generated/upstream_candidate_contract.json`.
- A caller-supplied `--output` receives a byte-identical convenience copy but is
  never written into state.
- State validation requires the canonical referenced file to exist, decode,
  match state kind/version/tag/commit, and reproduce the recorded semantic hash.
- Supported state always references
  `src/multica_py/_generated/upstream_supported_contract.json`.
- A promotion decision binds the semantic candidate hash, approved contract
  hash, target identity, and release provenance reference.
- Promotion cannot proceed until generator `--check`, candidate validation, and
  cross-artifact validation are green.
- After successful promotion, candidate state is cleared. Historical evidence
  remains in the evidence package and review record, not active state.

**Rationale**: Current collection can record a custom output path in state and
current validation checks containment but not file existence or semantic
identity.

**Rejected alternatives**:

- Accept any repository-contained contract path: rejected because filename and
  kind drift caused the recorded candidate mismatch.
- Repair dangling paths manually: rejected because collection must produce a
  valid canonical state.
- Promote semantic state before approving SDK contract identity: rejected
  because supported state could then describe a different public contract.

## Decision 13: Cross-Artifact Consistency

**Decision**: Add one fail-closed validator invoked by
`upstream_contract check` and an offline contract test. It verifies:

- exact target version/tag/commit across approved SDK contract, generated
  approved compatibility projection, semantic supported contract, generated
  supported state, CLI manifest metadata, and live target;
- approved contract hash and reference in generated/promotion metadata;
- canonical supported/candidate references and semantic hashes;
- all 16 approved operation IDs appear exactly once in the approved
  compatibility projection;
- the corresponding 16 semantic coverage decisions use approved bindings;
- unrelated existing coverage decisions remain outside schema-v2 approval;
- none of the 35 target additions becomes newly approved merely because it is
  present in evidence or current raw SDK source;
- CLI archive/version and backend manifest/platform digests match approved
  release provenance.

Any mismatch is an invalid artifact and a blocking error, never a warning.

**Rationale**: Existing checks validate fragments independently and do not
compare the live target with supported state or approved contract.

**Rejected alternative**: Add pairwise checks to multiple test modules.
Rejected because pairwise checks can leave a transitive contradiction and give
weak implementers no single acceptance gate.

## Decision 14: Runtime Readiness Root Cause

**Decision**: Fix `poll_runtime_online()` before rerunning baseline or target
live gates:

- reuse the exact `provider == "opencode"` predicate used by
  `find_online_opencode_runtime`;
- require exactly one online/ready/active `opencode` runtime for the selected
  daemon;
- do not count online `codex`, `cursor`, or `openclaw` runtimes as duplicates;
- retain other-provider runtimes only in redacted diagnostics;
- report zero or multiple matching opencode runtimes as
  `environment_unready/runtime_readiness`.

**Rationale**: Saved baseline and candidate diagnostics contain four online
runtimes for different providers. Current code first finds the one opencode
runtime and then incorrectly requires exactly one online runtime across all
providers, so it can never become ready.

**Rejected alternatives**:

- Increase the timeout: rejected because the predicate can never pass with the
  observed valid environment.
- Stop other providers: rejected because they are valid peers and not the
  readiness target.
- Treat the shared failure as a `v0.4.9` regression: rejected because the defect
  is target-independent harness logic.

## Decision 15: Live Outcome and Compatibility Report

**Decision**: Introduce schema-v2 categorized live results:

- `passed`
- `product_failure`
- `environment_unready`
- `authentication_limited`
- `invalid_run`

Every result records stage, pytest exit code, collected/started/completed/failed
counts, target node when applicable, exception type, normalized message,
target fingerprint, and artifact paths.

Compatibility comparison emits a target regression only when:

1. the candidate category is `product_failure`;
2. the tested operation was reached;
3. baseline/control does not share the same normalized
   category/stage/exception fingerprint.

Environment, authentication, and invalid-run outcomes are inconclusive and can
never become product passes or regressions.

**Rationale**: Current report logic labels every pinned non-zero exit as a
regression and cannot isolate the identical baseline/candidate readiness
failure.

**Rejected alternatives**:

- Classify solely by pytest exit code: rejected because setup and collection
  failures share non-zero exits.
- Compare message strings only: rejected because paths, durations, and IDs make
  messages unstable.

## Decision 16: Fail-Closed Mutation Gate

**Decision**: For each mutation case:

1. preflight that pytest imports in the exact interpreter;
2. run the unmodified target test with unique JUnit output;
3. require exactly the intended node to collect, start, complete, and pass;
4. apply one mutation;
5. run the same node with unique JUnit output;
6. require the node to start and fail for the expected assertion/public
   exception fingerprint;
7. reject pytest exits 2, 3, 4, or 5, setup errors, absent/unparseable JUnit,
   zero collection, wrong-node failures, or missing dependencies as
   `invalid_run`;
8. restore the source and verify its original hash.

Gate exit codes:

- `0`: every clean control passed and every mutation was killed as expected;
- `1`: at least one mutation survived;
- `2`: the gate itself was invalid.

**Rationale**: Current mutation logic treats any non-zero subprocess result,
including `No module named pytest`, as a killed mutation.

**Rejected alternatives**:

- Check only that pytest is importable: rejected because setup failures can
  still prevent target execution.
- Accept any assertion failure: rejected because an unrelated failure does not
  prove the protected invariant.

## Decision 17: Stability Repeat

**Decision**:

- Migration stability mode requires exactly `--repeat 10`.
- It requires a readable preceding smoke report with category `passed` and the
  exact same target fingerprint.
- Each repetition runs the full `live_smoke` profile under `tests/live`.
- Each repetition has a unique run ID, JUnit, categorized result, diagnostics,
  cleanup audit, and elapsed time.
- The runner stops after the first product/environment/auth/invalid failure.
- Success requires 10/10 categorized passes and zero managed leftovers.

**Rationale**: Current repeat runs only one sandbox test, accepts zero runs, and
does not verify a preceding successful smoke.

**Rejected alternatives**:

- Keep repeating only the sandbox test: rejected because the acceptance
  criterion says smoke, not one smoke node.
- Run repeat after a non-green smoke: rejected because the result would not
  prove stable compatibility.

## Decision 18: Offline Quality Artifacts

**Decision**:

- CI must explicitly produce offline JUnit, coverage JSON, and mutation result
  files before the final baseline gate.
- An explicitly supplied missing file is a hard invalid-input error.
- Final baseline comparison requires all three files; it cannot silently skip
  them.
- `scripts/check_test_architecture.py` and `tests/quality-baseline.json` are
  present in current `main`; their absence in the older evidence package is a
  historical blocker already resolved by feature 006.

**Rationale**: Current CI produces coverage and mutation output, but the
five-stage baseline command does not pass them to `check_test_baseline`, so
optional branches can be skipped.

**Rejected alternative**: Keep optional file semantics for final. Rejected
because a green gate would not prove the required dimensions.

## Decision 19: New Upstream Family Disposition

**Decision**: Use the specification classification without promotion:

- required compatibility: `issue-existing-changes`,
  `transport-error-contract`;
- required subset plus extension candidates: `issue-new-commands`;
- required subset plus CLI-only: `project-and-root-registration`;
- required subset plus deferred extension:
  `attachments-and-client-transport`;
- separate extension candidates: `chat-read`, `workspace-properties`;
- CLI-only/local plus deferred extension: `runtime-and-local-control`;
- deferred owner decisions: `workspace-repository-management`,
  `agent-settings-and-skills`, `skills-squads-and-autopilots`.

Existing raw wrappers outside the 16-ID contract are not removed, modified, or
newly approved by this migration. No evidence package field can promote them.

**Rationale**: Public source existence, raw coverage, and approved typed
contract status are distinct states.

**Rejected alternative**: Delete existing raw wrappers because their families
are out of migration scope. Rejected because out of scope means unchanged, not
removed.

The complete family table is in
`contracts/upstream-family-disposition.md`.

## Decision 20: Implementation Order

**Decision**: Implementation must follow this fixed dependency order:

1. schema-v2 contract models and validation;
2. exact 16-operation contract migration;
3. deterministic generator and generated-output check;
4. public bindings/enums/validators/signature integration;
5. operation-specific compatibility fixes and table-driven offline cases;
6. canonical candidate state and promotion identity;
7. cross-artifact consistency validator;
8. live-target provenance update;
9. runtime-readiness and categorized result fixes;
10. fail-closed mutation gate;
11. full-smoke repeat gate;
12. offline gates;
13. target smoke, target extended, mutation, then repeat 10.

No later step may be started while the preceding gate is red.

**Rationale**: This order prevents generated or supported metadata from getting
ahead of approved behavior and prevents live evidence from being interpreted
through a known-broken harness.

**Rejected alternative**: Update live target first and repair behavior after
live failures. Rejected because it temporarily claims unsupported compatibility
and makes failure interpretation ambiguous.
