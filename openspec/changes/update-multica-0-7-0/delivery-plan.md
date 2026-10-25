## Delivery contract

- Change: `update-multica-0-7-0`
- Planning issue: `MYL-557`
- Approved base: `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`
- Target: Multica `0.7.0` at
  `dbdbb299164347586e2650bb67684a490726a798`
- Test repository: `https://github.com/maximchikAlexandr/multica-py`
- Estimate source: the authoritative `Estimate, hours`, `Estimate min, hours`,
  and `Estimate max, hours` properties on `MYL-557`; numeric totals are not
  duplicated here.
- Estimate basis: remaining active work for one experienced developer familiar
  with the stack, without AI acceleration. Confidence is medium: the source,
  contract, tests, and closed upstream audit are inspectable, while the size of
  contract reconciliation and live privacy/error fixtures retains bounded
  uncertainty. This is evidence-based but not calibrated from comparable
  historical upgrade durations.

## E2E decision

`e2e_required=true`.

The remaining live gap is deliberately narrow: prove that the candidate SDK
performs its strict version preflight and a disposable project lifecycle against
the real Multica `0.7.0` stand, and capture the changed daemon-status output.
Deterministic contract, mapping, presence, decoder, validator, redaction,
retained-parity and failure behavior is fully covered at lower levels because
the declared five-value live harness has no PR fixture, workflow catalog,
property-definition authority, secondary identities, runtime-grant provisioning,
or controlled error injector. The plan SHALL NOT invent those prerequisites.

The project-declared test repository is
`https://github.com/maximchikAlexandr/multica-py`. The isolated stand supplies
only `MULTICA_LIVE_CLI`, `MULTICA_LIVE_EXPECTED_VERSION`,
`MULTICA_LIVE_SERVER_URL`, `MULTICA_LIVE_WORKSPACE_ID`, and
`MULTICA_LIVE_PROFILE`; the candidate harness SHALL keep that exact interface
and update its fixed prepared target to `0.7.0`. The primary Multica profile,
daemon, containers, checkout, and data are forbidden.

### Readiness and attempt control

Before a live attempt, Tester SHALL prove:

1. product checkout and implementation PR head equal the candidate SHA;
2. test-script commit is identified separately when it differs from product SHA;
3. all five declared live values are nonempty, the resolved CLI is executable,
   and `"$MULTICA_LIVE_CLI" version --output json` reports `0.7.0`;
4. `MULTICA_LIVE_SERVER_URL`, workspace and profile identify the project stand
   described in project metadata; the frontend/API readiness probes for that
   stand succeed without printing their private values;
5. focused offline contract/resource tests and required CI checks are green on
   the candidate;
6. the unique project prefix is unused and project create/delete succeeds in a
   readiness fixture that is deleted before the measured case;
7. for CAP-01, both verified CLI binaries and a verified local path to the
   required `scripts/render_terminal.swift` are supplied as execution inputs.

`CAPTURE-INPUT-BLOCKER`: neither the published repository nor the project
description declares the `openspec-e2e-testing` repository, package, URL, or a
local `scripts/render_terminal.swift` path. The renderer interface SHALL NOT be
guessed or downloaded from an undeclared source. CAP-01 and therefore complete
E2E verification remain blocked until the execution assignment supplies a
verified local renderer path. Tester SHALL first run the supplied script's
documented help/usage and record the actual render commands. A missing baseline
`0.6.1` binary is the same kind of pre-attempt material-input blocker. These
blockers consume no live attempt and do not relax the mandatory captures.

A failed readiness gate consumes no live attempt. A PASS remains valid only for
the same product revision and material fixtures. After a revision change,
Tester records an impact assessment and reruns affected cases only. Automatic
local suites obey the workspace ten-minute cap; longer suites run in GitHub
Actions on the exact published revision. Agent-driven walkthrough steps are
manual verification and are not represented as automated suite results.

### Live case contract

| Case | Remaining live gap | Entry command | Setup / reset | Independent Tester action | Assertions | Failure-safe cleanup | Evidence |
|---|---|---|---|---|---|---|---|
| LIVE-01 | Strict `0.7.0` preflight plus real SDK/CLI/server persistence | `uv run pytest -o addopts="" -q -rP -m live_smoke tests/live/test_multica_070.py -k target_preflight_and_project_roundtrip` with the five declared env values | Verify exact product SHA and CLI version; generate `multica-py-live-<uuid>`; test registers project deletion in `ExitStack` immediately after create; no shared fixture is changed | From a fresh client, create project, get it, update name/description, get again, then inspect that the returned IDs/values agree before deletion | preflight accepts only `0.7.0`; public command/eager paths reach the real boundary; persisted update is visible; every command exits successfully | `finally` invokes `prepared_client.projects.delete_command(project.id).run()`; after interruption, use the captured ID with `"$MULTICA_LIVE_CLI" project delete "$PROJECT_ID" --output json`, then confirm get returns not-found | sanitized pytest output, product/test SHA, CLI version-output hash, project ID, commands/exit codes and cleanup assertion in Multica only |
| LIVE-02 | Real target daemon-status additive field | `uv run pytest -o addopts="" -q -rP -m live_smoke tests/live/test_multica_070.py -k daemon_status_cli_commit` | Read-only case; verify resolved CLI first; no server fixture and no reset | Run the SDK daemon status command and separately inspect `"$MULTICA_LIVE_CLI" daemon status --output json` | typed `cli_commit` equals the reviewed target commit form; required legacy fields remain decodable | none beyond deleting local sanitized staging after upload | sanitized JSON/text, command exit codes, candidate SHA; no image from this machine-readable case |
| CAP-01 | Mandatory visible before/after daemon-status comparison | After `CAPTURE-INPUT-BLOCKER` is resolved: run `"$BASELINE_CLI" daemon status` and `"$MULTICA_LIVE_CLI" daemon status` with `LC_ALL=C`, identical width and non-JSON mode; invoke the supplied renderer exactly as its documented usage states | Verify baseline reports `0.6.1`, candidate reports `0.7.0`, renderer path is supplied and inspected, and daemon state is equivalent; capture into a private staging directory | Compare the actual text for semantic changes, render both captures, open both PNGs, and check labels/readability | genuine baseline/candidate text exists; both PNGs represent those exact files; provenance, width, locale, output mode and ANSI/TTY limitations are recorded | read-only commands; upload sanitized text/PNG to Multica, verify attachments, then remove private staging files | `daemon-status-061.txt`, `daemon-status-070.txt`, `daemon-status-061.png`, `daemon-status-070.png`; missing input or capture blocks completion |

### Complete delta-scenario traceability

The following matrix maps every affected scenario in all four delta specs. `LL`
means a deterministic lower-level/CI assertion is sufficient; only the cases
with a named live gap use the stand.

| Delta requirement / scenario | Verification assignment | Concrete command / assertion |
|---|---|---|
| Upstream — Provenance is complete | LL-CONTRACT | `uv run pytest -o addopts="" -q tests/contract/test_sdk_contract.py tests/unit/test_upstream_contract.py`; assert target/release/tag/commit/artifact digests and baseline role |
| Upstream — An inventory item is absent or duplicated | LL-CONTRACT | same mutation tables reject missing/duplicate CLI or response verdicts and mismatched totals |
| Upstream — Deferred commands remain non-public | LL-PARITY | `uv run pytest -o addopts="" -q tests/unit/test_coverage_gate.py tests/unit/resources/test_operations.py tests/contract/test_public_invariants.py`; discovery/export sets exclude autostart symbols |
| Upstream — Names match without traced behavior | LL-CONTRACT | contract mutation case removes source/destination/constraint trace and strict loader rejects it |
| Upstream — Reviewed endpoints are accepted | LL-COMPAT + LIVE-01 | `make compat` proves interval edges; LIVE-01 proves target preflight at the real boundary |
| Upstream — A version exceeds the reviewed ceiling | LL-COMPAT | `make compat`; strict/warn cases assert exclusive-ceiling behavior without subprocess I/O |
| Upstream — Evidence contains a candidate change | LL-CONTRACT | run render twice from approved contract while evidence-only candidate is present in fixture; bytes/public discovery stay unchanged |
| SDK — An array property round-trips | LL-PROPERTY | `uv run pytest -o addopts="" -q tests/unit/resources/test_properties.py tests/unit/resources/test_issues.py`; encode/decode table preserves order, duplicates and empty arrays |
| SDK — An invalid array value is supplied | LL-PROPERTY | same table asserts wrong container/element/URL/null fails before mocked transport |
| SDK — Ordered comparisons are valid | LL-PROPERTY | exact argv/query rows preserve predicate and operator order |
| SDK — A comparison is ambiguous or unsupported | LL-PROPERTY | operator/type/value negative rows assert stable pre-I/O errors |
| SDK — Workflow is omitted or null | LL-PROJECT | `uv run pytest -o addopts="" -q tests/unit/resources/test_project_relations.py tests/unit/resources/test_operations.py`; decode rows preserve absent versus null |
| SDK — A workflow-aware write is invalid | LL-PROJECT | create/update vectors assert validation or typed upstream error and unchanged unrelated argv fields |
| SDK — Target status includes a commit | LL-DAEMON + LIVE-02 | operation/decode row checks exact target payload; LIVE-02 checks the real target |
| SDK — Legacy status omits the commit | LL-DAEMON | legacy empty/omitted/malformed fixture table checks optional policy |
| SDK — A PR-conflict wakeup is constructed | LL-WAKEUP | `uv run pytest -o addopts="" -q tests/unit/resources/test_issue_wakeups_v2.py`; create/update eager/command rows assert exact argv/result |
| SDK — Conditions conflict | LL-WAKEUP | exactly-one negative table proves pre-I/O rejection |
| SDK — A stale diagnostic is cleared | LL-WAKEUP | omitted/null/empty diagnostic fixture rows assert presence distinction |
| SDK — Sharing identities are returned | LL-RUNTIME | `uv run pytest -o addopts="" -q tests/unit/resources/test_runtimes.py tests/unit/resources/test_operations.py`; ordered safe identity and legacy omission rows |
| SDK — Privacy revocation is blocked | LL-RUNTIME | structured conflict fixtures assert blocker context, no retry and no local partial mutation |
| SDK — An agent write lacks an explicit grant | LL-RUNTIME | agent create/update error vectors assert typed authorization failure and redaction |
| SDK — A reviewed failure occurs | LL-ERROR | `uv run pytest -o addopts="" -q tests/unit/test_transport.py tests/component/test_transport_errors.py tests/unit/resources/test_attachments.py tests/unit/resources/test_skills.py tests/unit/resources/test_workspace_relations_extra.py`; approved mappings and redaction |
| SDK — An unknown error occurs | LL-ERROR | malformed/unreviewed fixtures remain generic command failures without new public type or retry |
| Parity — Target help inventory is checked offline | LL-PARITY | closed inventory/discovery equality asserts all target nodes/flags and reviewed delta totals |
| Parity — Upstream-only behavior is discovered | LL-PARITY | defer/not-surface fixture rows produce no operation, model, resource or export |
| Parity — A retained operation drifts | LL-PARITY | exact signature/argv/validator/decoder/return discovery fails on retained mutation |
| Verification — Coverage reconciliation runs | LL-COVERAGE | `uv run pytest -o addopts="" -q tests/unit/test_coverage_gate.py tests/contract/test_public_invariants.py`; every supported item maps once to verdict/test/docs action |
| Verification — A deterministic gate detects drift | LL-GATES | run `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json`, `uv run python scripts/audit_source_links.py`, and a second transient render comparison; any diff fails |
| Verification — The isolated lifecycle succeeds | LIVE-01 + LIVE-02 + CAP-01 | each case records exact product/test revisions, material inputs, commands, exits, assertions and cleanup; CAP-01 must be unblocked |
| Verification — Revision or environment identity differs | LL-HARNESS | `uv run pytest -o addopts="" -q tests/unit/test_live_smoke_workflow.py`; harness tests reject SHA/version/five-env mismatch before live collection, while readiness checks reject stand identity mismatch |
| Verification — Visible output is compared | CAP-01 | genuine equivalent baseline/candidate text and mandatory PNG attachments |
| Verification — Required capture is unavailable | CAP-01 blocker assertion | absence of either binary, renderer path, text or PNG records `blocked`/incomplete and forbids PASS or synthetic substitution |

### Lower-level and CI entry commands

Implementer SHALL add the rows/fixtures named above and run focused commands in
their owning WPs. WP-07 then runs the consolidated gates on the exact candidate:

```text
uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json
uv run python scripts/audit_source_links.py
uv run pytest -o addopts="" -q tests/unit/test_upstream_contract.py tests/contract/test_sdk_contract.py tests/unit/test_coverage_gate.py tests/contract/test_public_invariants.py
uv run pytest -o addopts="" -q tests/unit/resources/test_properties.py tests/unit/resources/test_issues.py tests/unit/resources/test_project_relations.py tests/unit/resources/test_issue_wakeups_v2.py tests/unit/resources/test_runtimes.py tests/unit/test_transport.py tests/component/test_transport_errors.py
make compat
make package
```

The complete offline suite, types and lint run in the existing GitHub `quality`,
`types`, `lint`, `compatibility`, `contract-check`, and `package-test` jobs on the
published exact revision when their local automated duration is expected to
exceed the workspace limit. No new CI framework or private dependency is added.

### Scripts, fixtures, and ownership

- Implementer owns `tests/live/test_multica_070.py`, additions to existing
  frozen unit/component/contract tables, minimal fake-CLI fixtures, and required
  GitHub workflow adjustments. Tester verifies them and SHALL NOT edit product
  CI tests or fixtures.
- The live script SHALL reuse `tests/live/conftest.py`, the existing three
  module markers and runner, retain exactly the five declared env inputs, update
  the prepared target to `0.7.0`, record product/test-code revisions, and use
  immediate `ExitStack` cleanup. It SHALL not add identity, PR, workflow,
  property-catalog, runtime-grant, or error-injection assumptions.
- The only mutable measured fixture is a uniquely named disposable project in
  LIVE-01. LIVE-02 and CAP-01 are read-only. Cleanup removes that project and
  private local staging while preserving the evidence branch/commits. It SHALL
  NOT merge, close, or delete the evidence branch without separate instruction.
- Tests and real functional outputs produced by the tested Git utility SHALL be
  separated into distinct commits when both exist; when no functional-output
  commit exists, a second commit is not required. Genuine tool-created commits
  retain their original identity and are linked, not renamed for evidence.

### Independent evidence publication

Tester SHALL publish one final Multica comment with read-back that contains the
implementation PR/MR, exact product and test-code SHAs, relevant commit/file
links, case-level commands and exit codes, assertions, cleanup results, and image
attachments. Actual images, raw output/log attachments, diagnostic JSON, hashes,
provenance, and test results belong only in Multica and SHALL NOT be committed.
JSON enters Git only when JSON generation itself is the product behavior under
test.

For changed terminal output on macOS, CAP-01 governs actual baseline/candidate
text, identical capture conditions and the required `scripts/render_terminal.swift`.
Because its source/path and CLI are not declared, `CAPTURE-INPUT-BLOCKER` is a
material input gate, not permission to invent a download or command. Once the
verified script is supplied, Tester uses its documented interface, records the
exact command, opens both outputs, and publishes the genuine pair. Images and
raw text retain the product language; authored explanations are English.
Renders are labeled as renders, not terminal screenshots. ANSI, TTY,
interactive and progress limitations are reported rather than simulated.
Missing required input, text or PNG blocks completion.

## Work-package topology

`delivery_mode=dag`. The authoritative `Estimate, hours` property exceeds the
policy threshold and the graph has a real four-package parallel frontier at
stage 2. Stages are topological layers, numbered consecutively. This file stores
scope and topology only; live status and assignee do not belong in OpenSpec.

Complete stage mapping:

| WP | Stage | Direct `depends_on` |
|---|---:|---|
| `WP-01-contract-foundation` | 1 | none |
| `WP-02-property-surface` | 2 | `WP-01-contract-foundation` |
| `WP-03-project-daemon` | 2 | `WP-01-contract-foundation` |
| `WP-04-wakeup-conflicts` | 2 | `WP-01-contract-foundation` |
| `WP-05-error-boundary` | 2 | `WP-01-contract-foundation` |
| `WP-06-runtime-privacy` | 3 | `WP-05-error-boundary` |
| `WP-07-integration-release` | 4 | `WP-02-property-surface`, `WP-03-project-daemon`, `WP-04-wakeup-conflicts`, `WP-06-runtime-privacy` |

### WP-01-contract-foundation

- **OpenSpec task coverage:** 1.1, 1.2, 1.3, 1.4, 1.5, 1.6.
- **Deliverable:** one strictly validated `0.7.0` approved contract and
  deterministic generated projection, including closed CLI/response decisions,
  exact mappings, compatibility, and fail-closed contract tests.
- **Owned responsibility scope:** `contracts/sdk-contract.json`, its schema,
  `tools/upstream_contract/`, generated approved runtime, contract-specific
  tests/fixtures and ignored transient rendering. This package exclusively owns
  the shared contract identifiers and generated file until completion.
- **Contract surface:** operation IDs, response IDs, mapping/presence/constraint
  records, provenance, compatibility bounds, inventory and response-registry
  verdicts consumed by every downstream package.
- **DoD / evidence:** strict loader/schema/source-link validation; target and
  response totals reconcile; two renders are byte-identical; generated check and
  focused contract tests pass; no evidence artifact is tracked.
- **Parallel safety:** predecessor by design; it freezes shared contract data
  before siblings write disjoint handwritten modules.

### WP-02-property-surface

- **OpenSpec task coverage:** 2.1, 2.2, 2.3, 2.4.
- **Deliverable:** typed multi-value property round trips and reviewed comparison
  filters with complete presence/operator regression coverage.
- **Owned responsibility scope:** property models/resources, issue property and
  issue-list filter adapters, related exports, domain tests/fixtures/docs snippets.
  Shared operation inventory tables remain WP-01/WP-07 responsibility.
- **Contract surface:** `multi_text`, `multi_url`, array value typing, ordered
  predicate operators, exact argv/query encoding and pre-I/O validation.
- **DoD / evidence:** positive/negative frozen rows cover order, duplicates,
  empty/null/omitted values, URLs, operator/type compatibility, legacy equality,
  eager/command parity, and exact transport calls.
- **Parallel safety:** no project, daemon, wakeup, runtime, or centralized error
  files are written; contract identifiers are read-only after WP-01.

### WP-03-project-daemon

- **OpenSpec task coverage:** 3.1, 3.2, 3.3.
- **Deliverable:** nullable project workflow projection/write semantics and
  optional daemon CLI commit identity with legacy compatibility.
- **Owned responsibility scope:** project and daemon public/wire models,
  resources, decoders, exports, and their domain tests/fixtures.
- **Contract surface:** `Project.workflow_id`, workflow-aware create/update
  presence and validation, `DaemonStatus.cli_commit` legacy/target decoding.
- **DoD / evidence:** focused type/unit/component cases cover omitted, null,
  empty, present, malformed and legacy payloads; no workflow-management method
  is exported.
- **Parallel safety:** files are disjoint from property, wakeup, runtime and
  centralized transport error ownership.

### WP-04-wakeup-conflicts

- **OpenSpec task coverage:** 4.1, 4.2, 4.3.
- **Deliverable:** PR-conflict wakeup create/update support and reviewed
  diagnostic clearing semantics.
- **Owned responsibility scope:** wakeup models, enums, resource adapters and
  wakeup-specific case tables/fixtures; it does not alter generic transport
  errors.
- **Contract surface:** exactly-one condition validation, eager/command argv
  parity, diagnostic omitted/null/empty behavior and legacy self-host responses.
- **DoD / evidence:** positive and negative create/update rows prove exact argv,
  pre-I/O conflict rejection, typed decode and stale `last_error` clearing.
- **Parallel safety:** wakeup-only modules and tests do not overlap sibling
  resource files; shared contract records are read-only.

### WP-05-error-boundary

- **OpenSpec task coverage:** 6.1, 6.2, 6.3.
- **Deliverable:** stable centralized decoding for reviewed server/network,
  upload and workspace allowlist errors with safe context and generic fallback.
- **Owned responsibility scope:** transport/exception primitives, attachment and
  skill upload adapters, workspace adapters, related component/unit fixtures and
  redaction tests. It owns shared error types consumed by WP-06.
- **Contract surface:** status/code/message/context mapping, fallback behavior,
  redaction, retry policy and partial-mutation guarantees.
- **DoD / evidence:** fixture matrix covers every approved shape plus malformed
  payloads and proves URLs, hosts, paths, credentials, personal data and backend
  details are absent from public exceptions.
- **Parallel safety:** runtime and agent behavior is excluded; WP-06 depends on
  this package instead of editing the same error primitives concurrently.

### WP-06-runtime-privacy

- **OpenSpec task coverage:** 5.1, 5.2, 5.3, 5.4.
- **Deliverable:** runtime sharing projection, atomic privacy revoke conflicts,
  busy blockers and agent runtime authorization behavior using WP-05 errors.
- **Owned responsibility scope:** runtime and agent models/resources/decoders,
  bound behavior, domain tests and fixtures. Shared transport/exception files
  are read-only.
- **Contract surface:** `shared_with`, safe identity shape/order, explicit grants,
  atomic revoke, structured 409 blockers, no retry and legacy omission.
- **DoD / evidence:** focused rows prove allowed/denied/revoked/malformed paths,
  no partial mutation, safe blocker context, stable exception identity, bound
  behavior and compatibility.
- **Parallel safety:** starts only after WP-05 fixes the shared error contract;
  it does not write property, project, daemon or wakeup zones.

### WP-07-integration-release

- **OpenSpec task coverage:** 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6.
- **Deliverable:** coherent docs/migration, reconciled shared test tables and CI,
  package proof, isolated live verification contract execution and release-ready
  evidence on one consolidated candidate revision.
- **Owned responsibility scope:** compatibility/API/migration/release docs and
  changelog, shared operation/coverage tables, GitHub workflows, package/live
  tests and fixtures, final generated reconciliation and evidence publication.
  Direct fixes in predecessor-owned behavior return to that owner before this
  package reconsolidates.
- **Contract surface:** user migration, retained/deferred/non-surface policy,
  offline/CI/package gates, exact-SHA live runner and the evidence contract above.
- **DoD / evidence:** focused and complete offline/type/lint/package gates pass;
  strict contract/render checks pass; CI covers the exact published revision;
  Tester publishes read-back-confirmed case evidence and required before/after
  PNG attachments in Multica; Git is free of transient/private evidence.
- **Parallel safety:** final join only after all direct predecessors complete;
  it owns cross-domain reconciliation so no sibling concurrently edits shared
  tables, workflows or docs.

## Coverage and graph checks

- Every task 1.1 through 8.6 appears in exactly one WP.
- The listed edges are the transitive reduction: WP-06 reaches WP-01 through
  WP-05, and WP-07 reaches WP-05 through WP-06 and WP-01 through its stage-2/3
  predecessors. No direct edge is transitively redundant. Every predecessor has
  a lower stage than its dependent; stages 1 through 4 are contiguous.
- Stage 2 contains four independently writable packages, so the graph has a
  genuine parallel frontier. WIP limits are operational policy, not DAG edges.
- Responsibility scopes include directly related tests, fixtures, snapshots,
  docs and service files unless an active sibling explicitly owns the shared
  file; they are not exhaustive file allowlists.
