## Delivery contract

- Planning issue: `MYL-640`
- OpenSpec change: `update-multica-0-8-0`
- Approved SDK base: `b268e3bec0436fe51727fda50583344f57663284`
- Upstream baseline: Multica `0.7.1` / `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`
- Upstream target: Multica `0.8.0` / `9b1ab4f9eed9153a94719596eb8a728d2770f065`
- Delivery mode and work-package topology are derived below from the root
  issue's `Estimate, hours` property after the required estimate read-back.
- Numeric estimate totals are authoritative only in the root issue properties
  `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours`; this file
  intentionally does not duplicate them.

The implementer SHALL use the exact approved base and one normal feature branch.
No task may consume the planning-only `0.7.2` branch as a code base or generator
input. Evidence from that issue may be reproduced and reviewed for the
intermediate release only.

## Scope and task coverage rules

OpenSpec `tasks.md` is the authoritative implementation checklist. Every task
identifier SHALL be owned exactly once by the final work-package topology. An
owner also owns directly related tests, fixtures, snapshots, generated code,
documentation, and service files unless this plan assigns that responsibility
to a different active sibling. Shared contracts and generated foundations SHALL
be completed before parallel public-surface work begins.

Implementation output is product code and ordinary development artifacts only.
Collectors, release archives/binaries, gap/response audits, transient render
output, raw logs, diagnostic JSON, hashes, screenshots, command transcripts,
and other verification evidence SHALL remain outside Git and be published only
in the final Multica evidence comment.

## E2E decision

`e2e_required=true`.

The new workflow/project-workflow, runtime-concurrency, rerun-task/steering, and
forced-daemon-stop contracts cross the SDK process boundary into real CLI,
server state, task scheduling, permissions, and daemon lifecycle. Unit,
component, contract, and generated-argv tests are necessary but cannot alone
prove server persistence/conflict behavior, race receipts, or exact-child
shutdown safety. The selected live cases are limited to those remaining gaps;
literal attachment argv, numeric model decoding, limits, diagnostics, privacy
fallbacks, and warning-channel separation are sufficiently proven at lower
levels unless a live case observes them incidentally.

No separate evidence or test repository is used. The product GitHub repository
is an attached Multica project resource, not a URL supplied by the project
description; all tracked SDK tests, fixtures, CI changes, and the minimal live
orchestration helper SHALL stay in that product repository. The project
description supplies only the local stand path, Compose project, fixed local
ports, and dedicated `multica-test` profile/daemon. Public artifacts SHALL
refer to those values through parameter names, not disclose private hostnames,
tokens, or profile data.

The Tester SHALL create a clean product checkout at the exact candidate SHA.
The fixed stand is shared infrastructure, so the tracked helper
`scripts/e2e/verify_multica_0_8_0.py` SHALL obtain an atomic exclusive lease in
the configured stand root before mutation and refuse an existing lease. While
holding it, the helper SHALL verify Compose project identity and readiness on
the configured API/frontend ports, namespace every mutable record with a
run-id, and use only the dedicated test CLI/profile. It SHALL NOT launch a
second stack on the fixed ports, reset the shared database, or reference the
primary Multica profile/daemon. Only supported public CLI resource operations
define the teardown boundary; an issue that the public CLI cannot delete is
cancelled and reported as a retained namespaced fixture rather than removed
through an unreviewed HTTP route. Cleanup releases only the caller-owned lease
after restoration checks.

## Verification case matrix

| Case | OpenSpec requirement/scenario | Remaining gap and decision | Public boundary | Script / entry command | Independent Tester steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| `E2E-01` | `Workflow commands preserve upstream identity and presence` — `Workflow update requires an explicit change`, `Project reset uses explicit default`, `Handoff replacement preserves unspecified fields`; `Workflow resources use typed open contracts` — `Workflow list and get decode future values`, `Create and update preserve optional fields`, `Mapping conflict remains structured` | Real persistence, resolution by id/name/default, mapping plan, and structured conflict require server state; live E2E selected | Public CLI: `workflow list/get/create/update/delete`, `workflow handoff set`, `project workflow get/set`; SDK models: workflow/page/handoff/mapping-plan/conflict results. OpenAPI operation/schema IDs: `N/A` — the approved product base contains no OpenAPI document or generated HTTP client, and the reviewed SDK boundary is the public CLI | Implementer extends `tests/live/test_smoke.py`; exact focused entry under the leased wrapper: `uv run python scripts/e2e/verify_multica_0_8_0.py run --case E2E-01 --candidate-sha "$CANDIDATE_SHA" --run-id "$RUN_ID"` | With the helper-provided client, create a run-namespaced workflow and disposable project, get/list/update, replace one handoff field, dry-run mapping, apply it, read back `workflow_id`, reset to `default`, then delete the disposable project and workflow in `finally` | Extend `live-smoke.yml` only when its protected target provides exact CLI `0.8.0`; otherwise report readiness blocked and never lower the expected version | Exact candidate/CLI versions; typed open fields; no-op update is zero-I/O; dry-run leaves state unchanged; conflict stays structured; set/reset persist; teardown succeeds | Sanitized commands/exits/assertions and object IDs in Multica only; no image because no rendered output changes |
| `E2E-02` | `Runtime concurrency is typed and bounded` — `Concurrency limit is set`, `Concurrency limit is cleared`, `Invalid concurrency is zero-I/O` | Real persistence and null clearing cross CLI/server/model layers; live E2E selected | Public CLI: `runtime concurrency <runtime-id> <limit\|none>` and `runtime list`; SDK model: runtime definition. OpenAPI operation/schema IDs: `N/A` — no OpenAPI source exists at the approved product base and no HTTP operation is an SDK contract | Implementer extends `tests/live/test_smoke.py`; entry under the leased wrapper: `uv run python scripts/e2e/verify_multica_0_8_0.py run --case E2E-02 --candidate-sha "$CANDIDATE_SHA" --run-id "$RUN_ID" --runtime-id "$MULTICA_LIVE_RUNTIME_ID"` | Verify the configured runtime belongs to the leased test workspace, capture its original value, set a safe valid limit, read back, clear to `none`, read back null, and restore the exact original value in `finally`; refuse an absent or shared/non-test runtime | Extend protected live-smoke only if it exposes an explicitly disposable runtime; otherwise local-only with reason | Exact `1..50` behavior; null round trip; unrelated fields unchanged; invalid inputs produce zero I/O; restoration verified | Sanitized before/after field projection, commands, exits, and restoration proof in Multica only; no image |
| `E2E-03` | `Rerun migration targets task runs explicitly` — `Scoped rerun resolves one task`; `Comment steering is explicit and receipt-preserving` — `Selected runs are steered in caller order`, `Steering and attachments conflict before I/O`, `Active steering is distinct from explicit steering`; `Target limits and diagnostics adapt existing operations` — `Privacy behavior remains fail closed` | Task identity, live eligibility, receipt races, member permission, and privacy fallback require the scheduler; live E2E selected, while multi-principal denial remains lower-level because the stand fixture exposes one authenticated client | Public CLI: `issue create`, `issue runs --active`, `issue rerun-task`, `issue comment add --steer`, `issue status cancelled`, and `issue assign --unassign`; SDK results: canonical task run and comment trigger/steering receipts. OpenAPI operation/schema IDs: `N/A` — the product base has no OpenAPI document/client and unreviewed server routes are excluded | Implementer extends `tests/live/test_smoke.py`; entry under the leased wrapper: `uv run python scripts/e2e/verify_multica_0_8_0.py run --case E2E-03 --candidate-sha "$CANDIDATE_SHA" --run-id "$RUN_ID" --project-id "$MULTICA_LIVE_PROJECT_ID" --agent-id "$MULTICA_LIVE_AGENT_ID"` | Preflight proves the single client is a member and the configured disposable agent is visible/eligible to that member. Create one run-namespaced issue in the prepared project, assigned to that agent, with a bounded instruction to inspect one repository fixture and return a fixed token. Poll with a bounded deadline until its active task reports `can_supplement=true`; submit explicit steering for that exact task and record whether the race yields a steer receipt or a documented queued/coalesced/deferred fallback after task completion. Wait for terminal state, rerun by full id and issue-scoped prefix with/without fresh mode, and verify distinct task identity. In `finally`, unassign and cancel the issue; because public CLI `0.8.0` has no issue-delete action, retain the cancelled namespaced issue and report its ID instead of calling an unreviewed route | Deterministic rerun may extend live-smoke CI; timing/receipt walkthrough stays independent local verification. A missing eligible agent/member permission or absent steerable window is readiness blocked, not PASS | Canonical task result; issue scope/fresh flag; ordered receipts; race fallback is observable; attachment conflict is zero-I/O; foreign data is not disclosed; retained fixture is cancelled and identified | Sanitized issue/task/comment IDs, bounded state timeline, receipt, commands/exits, and retained-fixture result in Multica only; no image |
| `E2E-04` | `Forced daemon stop remains an upstream safety operation` — `Default stop remains graceful`, `Forced stop uses one reviewed flag`; `Force-stop safety stays outside the SDK process layer` — `CLI refusal is not bypassed` | PID/profile validation, graceful timeout, exact-child termination, and refusal cannot be proven by fake CLI alone; isolated manual E2E selected | Public CLI: `daemon status/start/stop --force`; SDK: daemon stop eager/lazy command. OpenAPI operation/schema IDs: `N/A` — daemon lifecycle is a local process boundary, not HTTP/OpenAPI | Implementer adds the daemon case to the same tracked helper; exact entry: `uv run python scripts/e2e/verify_multica_0_8_0.py run --case E2E-04 --candidate-sha "$CANDIDATE_SHA" --run-id "$RUN_ID"`. The helper invokes only the configured `multica-test` wrapper and scrubs primary-run `MULTICA_TASK_*`, `MULTICA_AGENT_ID`, `MULTICA_DAEMON_PORT`, `MULTICA_TOKEN`, and primary URL/workspace variables from its child environment so the wrapper selects its fixed dedicated profile | Under the exclusive stand lease, capture primary and test daemon status and refuse equal PID/profile identity. Gracefully stop the test daemon, launch `multica-test daemon start --foreground --no-auto-reload` as a recorded `Popen` child, wait until status PID equals that child, call SDK `stop(force=True)`, and prove only that child exits. With no test daemon running, start a harmless recorded sentinel child, temporarily place only its PID in the dedicated profile PID fixture, call force-stop, require refusal and sentinel survival, then restore the fixture. In `finally`, terminate only still-live recorded child handles after rechecking they differ from the primary daemon PID, restore the original PID file, restart the dedicated test daemon if it was initially running, and poll status readiness; never kill by executable name | Local-only; CI runners SHALL NOT force-stop their controlling/shared daemon | Default stop unchanged; one force flag; foreground PID equals owned child; primary PID remains alive/unchanged; mismatch refuses and sentinel survives; PID fixture is restored; dedicated daemon readiness returns | Sanitized PID relationship, commands/exits, refusal, restart/readiness, and failure-cleanup proof in Multica only; no private paths/hostnames and no image |
| `LOW-01` | `Repeated attachment paths remain literal argv values` — `Commas remain part of one path`, `Multiple paths preserve order`, `Invalid path input fails before execution`; `Task usage credits preserve integer precision` — `Credits are absent or null`, `Credits preserve exact magnitude`; `Target limits and diagnostics adapt existing operations` — `Boundary tables cover both sides`, `Repository warning does not claim freshness`, `Privacy behavior remains fail closed`; `CLI warnings and structured errors retain channel boundaries` — `Stale-checkout warning preserves success result`, `Workflow conflict remains a failure result`; `Task-only and hidden surfaces remain excluded` — `Exclusions cannot leak into generation` | Existing shared argv/decode/component/transport tables close the behavior without live state; no live E2E | Fake CLI, model decoder, contract mutation, and transport fixtures. OpenAPI operation/schema IDs: `N/A` — no live HTTP boundary is selected and the repository contains no OpenAPI source | `make test` plus focused existing table modules selected by Implementer | Inspect exact case rows and run focused tests; compare previews for comma-containing paths and warning fixtures | Ordinary CI `quality`, `types`, `contract-check`, `compatibility`, and package jobs | Literal repeated argv; integer/null precision; both sides of boundaries; stdout/stderr separation; sanitized errors; excluded symbols absent | Test/CI links, commands, exits, and assertions in Multica only; no images |

## Test implementation ownership

The Implementer owns all tracked contract, focused feature, shared integration,
CI, and release-gate test changes, including extensions to
`tests/live/test_smoke.py`, shared fixtures, fake-CLI tables, CI version/source
pins, and the single stdlib orchestration helper
`scripts/e2e/verify_multica_0_8_0.py`. That helper owns lease/preflight,
case selection, bounded waits, child-process identity checks, restoration, and
cleanup; it SHALL NOT contain product behavior or collect evidence into Git.
The Tester SHALL not edit those files. The Tester independently runs or
inspects the published exact revision, records findings, and requests a new
product revision when a defect is found.

No parallel runner, browser framework, snapshot library, or E2E evidence
directory is added. The helper is a narrow safety wrapper around existing
pytest/live-smoke, SDK, public CLI, and stand controls, not a second test
framework.

## Readiness and attempt contract

Before any live attempt, the Tester SHALL verify:

1. the product checkout is the exact published candidate SHA and clean;
2. the CLI reports exact target version `0.8.0` and expected commit prefix;
3. the stand-root lease is owned by this run; Compose project and configured
   fixed ports are ready; the dedicated test profile/daemon and namespaced
   database records are selected; and primary Multica identity is excluded;
4. focused offline/contract tests and source-of-truth checks passed on the same
   candidate or have a linked CI result;
5. disposable workflow/project/issue/task names carry the run-id and cleanup or
   explicit cancelled-fixture retention is known before mutation;
6. the original runtime concurrency value and isolated daemon PID/profile are
   captured for restoration.

Each live attempt SHALL target one named gap. A failing attempt is diagnosed
from preserved evidence and cheaper deterministic checks before another attempt.
PASS remains valid only for the same product revision and materially identical
fixtures. A new revision requires an impact assessment and rerun of affected
cases only. Automated local suites are stopped at the workspace time limit and
continued through existing GitHub Actions on the exact published revision; the
suite SHALL not be split to evade the limit. Manual walkthroughs are not subject
to that automated-suite limit.

## Evidence and image contract

The Tester final comment SHALL include the exact product SHA, test-code SHA when
different, CLI version/commit, sanitized fixture identities, commands and exit
codes, per-case assertions, cleanup results, and commit/MR/file/CI links. The
comment and its attachments SHALL be read back after posting.

No before/after PNG is required: the SDK change adds typed methods and model
fields but does not change a rendered SDK CLI table, log formatter, progress
view, terminal summary, or browser UI. Real structured/text outputs are required
for each case. If implementation unexpectedly changes visible terminal output,
the plan must be revised before verification to name a real, available capture
mechanism, its Implementer-owned task, baseline/candidate text, locale, width,
output mode, ANSI/TTY limitations, revision, command, and exit status. No
capture script is assumed at the approved base.

## Cleanup and preservation

Cleanup SHALL delete disposable workflows/projects where the public CLI
supports deletion, unassign and cancel the E2E-03 issue, restore the original
runtime concurrency and daemon PID fixture, restart and health-check the
dedicated test daemon, release the owned stand lease, and leave the primary
Multica environment untouched. Tasks, comments, and the cancelled issue are
retained when the public CLI has no supported delete action; their namespaced
identities SHALL be reported. Cleanup SHALL preserve evidence branch/PR/commits
and links. The branch or PR SHALL not be closed, merged, or deleted without
separate authority. Cleanup failures are verification failures with the
remaining resource identity, never hidden by a later successful command.

## Estimate conclusion

The root issue estimate properties were populated by the required
`estimate-openspec` review and read back successfully. The headline property is
above the multi-package threshold. Confidence is **medium**: acceptance and
source paths are inspectable and strong upstream-update analogues exist, but the
new workflow family, scheduler race evidence, daemon lifecycle verification,
and volume of reviewed contract rows create bounded integration uncertainty.
The estimate is not calibrated to measured developer time; local history is
used as scope evidence only, not as an elapsed-time benchmark. Tests were not
run for the estimate.

Material effort drivers are the large reviewed contract/generator baseline,
the new workflow model/resource family, three independent existing-resource
adaptation areas, shared case-table reconciliation, live exact-target readiness,
and likely review/fix iterations. External waits for protected live-smoke
readiness, CI queues, human approval, or unavailable exact-target infrastructure
are excluded from active developer-hours and remain delivery risks.

## Work-package topology

- `delivery_mode=dag`
- Stages are contiguous topological layers. Every predecessor has a lower stage
  than its dependent.
- Stage map: `WP-01 -> 1`, `WP-02 -> 2`, `WP-03 -> 2`, `WP-04 -> 2`,
  `WP-05 -> 3`.
- Stage 2 is the verified execution frontier: its three siblings share only the
  read-only approved contract/generator output and have distinct critical write
  zones. WIP limits are operational policy and are not encoded as dependencies.

### WP-01 — Approved 0.8.0 contract foundation

- `stage`: `1`
- `depends_on`: none
- OpenSpec task coverage: `1.1`, `1.2`, `1.3`, `1.4`, `1.5`, `1.6`
- Deliverable: reproduced ignored evidence; reviewed `0.8.0` contract/schema;
  deterministic generated inventory; exact compatibility/source/CI pins; and
  closure/source-link/mutation/exclusion checks that all later WPs consume.
- Owned responsibility scope: `contracts/sdk-contract.json`, its schema and
  generator/validator under `tools/upstream_contract/`, generated approved SDK
  inventory, provenance inventory fixture, contract-specific tests, and exact
  source/version pins in CI. Directly related fixtures and generated outputs
  belong to this WP. It SHALL not implement public resource methods.
- Contract surface: operation IDs, public command dispositions, response
  registry/model names, field presence, constraints, errors, source URLs,
  compatibility range, and generated target paths are frozen for successors.
- DoD/evidence: all task rows complete; reproduced evidence reconciles; contract
  validate/render/check/source-link and double-regeneration checks pass; target
  tree/response closure is exact; worktree is clean except its intended product
  commit; commit/file/test links and exits are recorded for final handoff.
- Parallel-safety rationale: this sole predecessor owns every shared generated
  contract artifact, preventing sibling WPs from racing on the generator input
  or generated inventory.

### WP-02 — Workflow and project-workflow surface

- `stage`: `2`
- `depends_on`: `WP-01`
- OpenSpec task coverage: `2.1`, `2.2`, `2.3`, `2.4`, `2.5`
- Deliverable: typed workflow models/resource, handoff operations, project
  workflow get/set, client binding, and focused workflow tests on the frozen
  approved contract.
- Owned responsibility scope: new workflow model/wire/resource modules,
  `src/multica_py/client.py`, workflow-related portions of
  `src/multica_py/resources/projects.py` and project entities/wires, and focused
  workflow/project-workflow tests. Shared cross-feature operation registries,
  package-root reconciliation, common docs, and generated contract files belong
  to `WP-05` or `WP-01` and are read-only here.
- Contract surface: eager/lazy signatures; workflow reference resolution;
  immutable model fields; open status/handler/actor strings; file/mapping/dry-run
  presence semantics; structured conflicts; project default reset behavior.
- DoD/evidence: all approved workflow operations have focused exact-argv,
  decode, malformed, unknown-value, file secrecy, conflict, and zero-I/O tests;
  client/project bindings work against the contract; focused lint/type/test
  commands pass; exact commit and files are reported.
- Parallel-safety rationale: new workflow modules and project/client bindings do
  not overlap the runtime/issue files owned by `WP-03` or the
  comment/daemon/transport files owned by `WP-04`.

### WP-03 — Runtime, task usage, rerun, and issue attachment surface

- `stage`: `2`
- `depends_on`: `WP-01`
- OpenSpec task coverage: `3.1`, `3.2`, `3.3`, `3.4`, `3.5`, `4.3`
- Deliverable: runtime concurrency and response field, task credit decoding,
  explicit rerun-task migration, literal repeated issue attachment arguments,
  and focused tests for this entire issue/runtime write zone.
- Owned responsibility scope: runtime and issue-activity models/wires/decoders,
  `src/multica_py/resources/runtimes.py`,
  `src/multica_py/resources/issues.py`, issue entity forwarding needed for these
  operations, and focused runtime/task/rerun/attachment tests. It owns
  `resources/issues.py` exclusively among stage-2 siblings. Shared discovery
  registries and common docs remain read-only.
- Contract surface: exact concurrency validation and `none` clearing;
  `credits_micros` precision/presence; rerun-task signatures/result and removed
  legacy symbols; repeated literal attachment argv and normalization.
- DoD/evidence: omission/null/boundary/malformed cases, exact argv, zero-I/O
  failures, removed-symbol assertions, task binding, and comma/multi-path cases
  pass under focused lint/type/tests; no legacy rerun row or CSV attachment
  behavior remains in this WP's owned modules.
- Parallel-safety rationale: grouping the attachment task here makes the shared
  `resources/issues.py` write zone exclusive; the other stage-2 siblings have
  no authority to modify it.

### WP-04 — Comment steering, daemon force-stop, diagnostics, and transport

- `stage`: `2`
- `depends_on`: `WP-01`
- OpenSpec task coverage: `4.1`, `4.2`, `4.4`, `4.5`, `4.6`
- Deliverable: steering inputs and receipts, force-stop flag with preserved
  process-safety boundary, adapted validation/diagnostics/privacy behavior,
  stale-checkout warning separation, and focused component/process/contract
  coverage.
- Owned responsibility scope: `src/multica_py/resources/issue_comments.py`,
  `daemon.py`, repositories/skills/properties resources directly implicated by
  target diagnostics, existing transport/process/exception code only where the
  reviewed warning/error contract requires it, and focused tests for these
  paths. `resources/issues.py`, workflow/project files, generated contract
  files, shared discovery registries, and common docs are read-only.
- Contract surface: ordered `--steer`, `--steer-active`, attachment conflict,
  outcome receipt states, `daemon stop --force`, no SDK signaling/cleanup,
  boundary/error codes, privacy redaction, stdout/stderr warning separation.
- DoD/evidence: focused exact-argv, receipt, race-fallback fixture, graceful and
  refusal safety, boundary, privacy, warning-success, malformed, forbidden
  process-action, lint, and type checks pass; no second validator/transport or
  SDK-side process termination exists.
- Parallel-safety rationale: this sibling's critical write zone is disjoint
  from workflow/project files and the runtime/issue resource zone. Contract and
  shared registries are consumed read-only until final integration.

### WP-05 — Integrated discovery, documentation, E2E, and release proof

- `stage`: `3`
- `depends_on`: `WP-02`, `WP-03`, `WP-04`
- OpenSpec task coverage: `5.1`, `5.2`, `5.3`, `5.4`, `5.5`
- Deliverable: one reconciled candidate with all shared discovery/case tables,
  exports, documentation, packaging, exact-source/offline/CI gates, independent
  E2E evidence, clean-tree proof, and normal publication.
- Owned responsibility scope: shared operation/component/public-discovery
  registries, package root/exports, cross-feature compatibility and packaging
  checks, README and common API/CLI/compatibility/migration/service/contributing/
  changelog/releasing docs, live-smoke integration,
  `scripts/e2e/verify_multica_0_8_0.py` and its focused tests, final conflict
  resolution, and evidence publication. It may repair predecessor code only
  through explicit findings attributed to the owning WP contract and SHALL
  rerun affected gates.
- Contract surface: complete public operation closure, package/export boundary,
  documented migration/exclusions, exact target compatibility claim, live case
  contract, release/rollback and evidence identity.
- DoD/evidence: predecessor commits are incorporated; strict OpenSpec and every
  planned focused/full gate pass or the exact CI readiness blocker is reported;
  `E2E-01..04` and `LOW-01` have exact-revision outcomes; tracked-tree exclusion
  proof is clean; normal push succeeds; local and remote SHAs match; PR/commit/
  file/CI/evidence links and cleanup read-back are published without merge,
  force, or branch deletion.
- Parallel-safety rationale: this fan-in begins only after all stage-2 siblings
  finish, so it is the sole owner of deliberately shared registries, docs,
  exports, and final integration files.

## Frontier audit

After `WP-01`, `WP-02`, `WP-03`, and `WP-04` have no dependency on one another
and their critical write zones are disjoint as specified above. At least three
independent WPs can therefore run concurrently at stage 2. `WP-05` is a genuine
fan-in over all three results. The graph is not a linear chain and does not
collapse to `single_wp_no_dag`.

## Estimate evidence and calibration

The estimate uses one experienced developer familiar with this Python/CLI
repository, without AI acceleration, and measures active developer-hours for
remaining implementation, tests, review fixes, and attended verification.
Unattended CI time, approval queues, and external readiness waits are separate.
Confidence, assumptions, and source evidence are recorded with the issue
properties; numeric totals remain only in those properties.
