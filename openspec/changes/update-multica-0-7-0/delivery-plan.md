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

The changed public contract crosses the Python SDK, the real Multica `0.7.0`
binary, daemon/server behavior, persistence, and structured errors. Unit,
component, contract, and package tests are sufficient for deterministic argv,
presence, decoding, redaction, and compatibility logic, but cannot prove the
live response/error lifecycle. Changed daemon-status text also requires genuine
before/after capture. The local test environment is the isolated project stand
described by Multica project metadata; the primary Multica profile, daemon,
containers, checkout, and data are forbidden.

### Readiness and attempt control

Before a live attempt, Tester SHALL prove:

1. product checkout and implementation PR head equal the candidate SHA;
2. test-script commit is identified separately when it differs from product SHA;
3. CLI binary reports `0.7.0` and matches the approved target provenance;
4. the isolated profile, workspace, daemon, database, ports, and checkout belong
   to the project stand, not the primary environment;
5. focused offline contract/resource tests and required CI checks are green on
   the candidate;
6. fixtures are disposable and cleanup commands are known to succeed.

A failed readiness gate consumes no live attempt. A PASS remains valid only for
the same product revision and material fixtures. After a revision change,
Tester records an impact assessment and reruns affected cases only. Automatic
local suites obey the workspace ten-minute cap; longer suites run in GitHub
Actions on the exact published revision. Agent-driven walkthrough steps are
manual verification and are not represented as automated suite results.

### Verification matrix

| Case | Requirement / scenario | Gap and decision | Public boundary | Repeatable script | Independent Tester steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| E2E-01 | Array property values; comparison filters | Real persistence and CLI query composition are not proven by fake transport | SDK issue property set/list and issue list through CLI/API | `tests/live/test_multica_070.py -k property_arrays_and_comparisons` via existing live runner | Create disposable properties/issues; set ordered duplicate and empty arrays; query equality/comparisons; inspect returned typed values and server state; delete fixtures | Add table rows to existing offline property/resource tests in `quality` and `contract-check`; live remains protected `live-smoke` | order, duplicates, empty/null policy, operator semantics, exit status, cleanup | command/result text, tested SHA, fixture IDs, assertions, cleanup status; no image because machine-readable data is sufficient |
| E2E-02 | Project workflow presence; daemon `cli_commit` | Real nullable workflow projection and binary/daemon identity cross components | SDK project create/get/update and daemon status | `tests/live/test_multica_070.py -k project_workflow_or_daemon_status` | Read baseline `0.6.1` daemon status and candidate `0.7.0` status with equivalent width/locale/output; create/read/update a disposable project; inspect raw JSON and typed values | Extend existing project/daemon unit and component cases; protected live job runs candidate path | omitted/null/present workflow behavior, no workflow-management API, exact `cli_commit`, legacy decode | baseline/candidate raw text; `daemon-status-061.png`, `daemon-status-070.png`; revision/locale/width/output-mode manifest in Multica |
| E2E-03 | Wakeup PR conflicts and diagnostics | Condition registration, server evaluation, and stale-error clearing require live coordination | SDK wakeup create/get/update/disable against disposable issue/PR fixture | `tests/live/test_multica_070.py -k wakeup_pr_conflicts` | Create isolated issue and approved PR-conflict wakeup; inspect condition and diagnostics; force a safe conflict/no-conflict transition if fixture permits; disable and inspect cleanup | Exact argv and decode rows in offline wakeup tests; live lifecycle in protected job | exactly-one validation pre-I/O, condition round-trip, diagnostic presence/clear, no duplicate wakeup, cleanup | sanitized commands, response excerpts, issue/PR links, exit statuses, assertions; image only if human-readable diagnostics differ visibly |
| E2E-04 | Runtime sharing, revoke blockers, agent authorization | Authorization and atomic revoke semantics require real identities and persisted grants | SDK runtime list/update/delete and agent create/update | `tests/live/test_multica_070.py -k runtime_sharing_and_privacy` | With disposable authorized identities, inspect sharing; exercise allowed agent write; attempt blocked revoke and denied write; prove sharing unchanged; remove fixtures | Offline runtime/agent/conflict/redaction tables remain mandatory; protected live job uses safe pre-provisioned identities | ordered safe identity projection, structured blocker code/context, denied grant, atomic no-change, no retry, cleanup | sanitized JSON excerpts and assertions in Multica only; no personal data or private hostname; no image unless output format visibly changed |
| E2E-05 | Upload/network/server/allowlist errors | Real boundary is needed for at least one safe reproducible structured error; destructive/private failures stay fixture-tested | SDK attachment or skill upload and workspace write | `tests/live/test_multica_070.py -k structured_errors` | Trigger only documented disposable/safe invalid operations; inspect exception type/code/status/context and redaction; confirm no retry or partial resource | All error shapes covered offline in transport/component fixtures; live proves only safe reproducible representatives | stable mapping, generic fallback, secret/URL/host/path redaction, no partial mutation, exit status | sanitized exception text, commands, assertions, cleanup status; raw logs/diagnostic JSON remain Multica attachments only |
| E2E-06 | Direct compatibility and package surface | Installed artifacts plus real target binary are not proven by source-tree imports | wheel and sdist installed in fresh environment; SDK compatibility probe | `tests/live/test_multica_070.py -k packaged_candidate` after existing package build | Install candidate wheel in isolated environment, import without CLI, then point to verified target CLI and execute representative read calls | Existing `package-test` matrix plus compatibility jobs; live only for exact target probe | clean import, public exports, `max_tested_cli_version`, representative retained/adapted calls, no transient evidence in package | package filename/hash, candidate SHA, commands/exit codes, assertions; no decorative images |

### Scripts, fixtures, and ownership

- Implementer owns `tests/live/test_multica_070.py`, additions to existing
  frozen unit/component/contract tables, minimal fake-CLI fixtures, and required
  GitHub workflow adjustments. Tester verifies them and SHALL NOT edit product
  CI tests or fixtures.
- The live script SHALL reuse `tests/live/conftest.py`, existing markers and
  runner, accept environment/profile identifiers already supported by the live
  harness, record product and test-code revisions, and implement failure-safe
  cleanup. It SHALL not introduce a second runner or hardcode private URLs,
  hostnames, credentials, identities, or workspace IDs.
- Disposable fixtures: uniquely prefixed project, issue, property definitions,
  wakeup, upload payload, and only project-approved runtime/agent identities.
  Cleanup removes created server resources and local transient files while
  preserving the evidence PR/branch/commits. It SHALL NOT merge, close, or
  delete the evidence branch without separate instruction.
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

For changed terminal output on macOS, Tester SHALL capture actual baseline and
candidate text with equivalent fixtures, locale, width, and output mode, then
render PNGs using the bundled `scripts/render_terminal.swift` from
`openspec-e2e-testing`. The images and raw text retain the product language;
Tester-authored explanations are English. Renders SHALL be labeled as renders,
not terminal screenshots. ANSI, TTY, interactive, and progress limitations are
reported rather than simulated. Missing required baseline/candidate text or PNG
blocks completion.

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
| `WP-06-runtime-privacy` | 3 | `WP-01-contract-foundation`, `WP-05-error-boundary` |
| `WP-07-integration-release` | 4 | `WP-02-property-surface`, `WP-03-project-daemon`, `WP-04-wakeup-conflicts`, `WP-05-error-boundary`, `WP-06-runtime-privacy` |

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
- All dependency edges are direct. Every predecessor has a lower stage than its
  dependent; stages 1 through 4 are contiguous.
- Stage 2 contains four independently writable packages, so the graph has a
  genuine parallel frontier. WIP limits are operational policy, not DAG edges.
- Responsibility scopes include directly related tests, fixtures, snapshots,
  docs and service files unless an active sibling explicitly owns the shared
  file; they are not exhaustive file allowlists.
