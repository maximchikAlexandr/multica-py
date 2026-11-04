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

The test repository is the project repository configured in the Multica
project description. Public artifacts SHALL refer to the isolated environment
through parameter names, not its private URL or hostname. The Tester SHALL use
the isolated project test profile/CLI, its own checkout, resources, database
state, and ports; the primary Multica profile, daemon, and data are forbidden.

## Verification case matrix

| Case | OpenSpec requirement/scenario | Remaining gap and decision | Public boundary | Script / entry command | Independent Tester steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| `E2E-01` | Workflow lifecycle, handoff replacement, project default/set mapping, dry-run/conflict | Real persistence, resolution by id/name/default, mapping plan, and structured conflict require server state; local E2E selected | SDK workflow/project methods invoking CLI `0.8.0`; workflow/project API operations behind the CLI | Extend `tests/live/test_smoke.py`; focused entry `uv run pytest tests/live/test_smoke.py -k workflow -vv` with existing live fixtures | In a fresh checkout, create a uniquely named workflow and disposable project, get/list/update it, set a handoff, dry-run project mapping, apply mapping, read back `workflow_id`, reset to default, and delete all disposable records | Extend existing `live-smoke.yml` on the trusted exact candidate when its protected target provides CLI `0.8.0`; otherwise report readiness blocker, never lower the expected version | Exact candidate and CLI versions; typed fields; open strings; no-op update rejected pre-I/O; dry-run changes no state; conflict is structured; set/reset persist; cleanup succeeds | Sanitized command/exit/assertion transcript and object IDs in Multica only; no image because the SDK has no changed rendered UI/table output |
| `E2E-02` | Runtime concurrency set/clear and definition decoding | Real PATCH persistence and null clearing cross CLI/server/model layers; local E2E selected | `RuntimeResource.concurrency` and `runtime list` through CLI `0.8.0` | Extend `tests/live/test_smoke.py`; focused entry `uv run pytest tests/live/test_smoke.py -k runtime_concurrency -vv` | Select only the Tester's isolated runtime, record the original value, set a safe valid limit, read it back, clear to `none`, read back null, and restore the exact original value in `finally` | Extend existing protected live-smoke job if the isolated CI fixture exposes a disposable runtime; otherwise local-only with recorded reason | Exact `1..50` behavior; null round trip; unrelated runtime fields unchanged; invalid values produce zero I/O; restoration verified | Sanitized before/after JSON field projection, commands, exits, and restoration proof in Multica only; no image because no SDK rendering changes |
| `E2E-03` | Task-targeted rerun, fresh mode, comment steering receipts/races, foreign-chat privacy | Task resolution, new task identity, queued/coalesced/deferred/blocked/steered outcomes, permission checks, and race fallback require the scheduler; local E2E selected | Issue/task/comment SDK methods through isolated CLI/server | Extend `tests/live/test_smoke.py` only for deterministic rerun/steering paths; focused entry `uv run pytest tests/live/test_smoke.py -k 'rerun_task or steering' -vv` | Create a disposable issue and short bounded task, rerun by full id and scoped prefix with/without fresh mode, verify distinct task identity, steer an eligible active run, observe the returned outcome, verify attachment conflict locally, then remove disposable issue data allowed by the environment | Deterministic rerun path may extend live-smoke CI; race/permission variants remain independent local walkthrough because CI cannot guarantee timing or multiple principals | Canonical task result; issue scoping; fresh flag; no legacy action result; receipt state preserved; attachments rejected with steering; unauthorized/foreign data not disclosed | Sanitized issue/task/comment IDs, state timeline, commands, exits, outcome receipts, and cleanup result in Multica only; no images because terminal rendering is unchanged and receipts are machine-readable |
| `E2E-04` | Forced daemon stop exact-child safety | PID/profile validation, graceful timeout, and exact-child termination cannot be proven by fake CLI alone; isolated manual E2E selected | SDK daemon stop through `multica-test` and its dedicated daemon/profile | Use existing test service controls plus focused SDK invocation; no unattended destructive runner is added | Confirm the selected PID is the isolated test daemon and differs from the primary daemon; exercise graceful stop/start, then an approved force path against only the dedicated child; test a mismatch/refusal fixture; restore the isolated daemon and verify readiness | Local-only; CI runners must not force-stop their controlling/shared daemon | Default stop unchanged; force emits one flag; exact isolated child only; mismatch/refusal does not signal or clean locally; service restores healthy; primary daemon untouched | Sanitized PID relationship assertion, commands, exits, readiness proof, and cleanup in Multica only; no raw private paths/hostnames and no image because process state is asserted textually |
| `LOW-01` | Literal attachment paths, credits/runtime malformed payloads, property/skill limits, skill-source errors, repo warning, privacy fallbacks | Existing shared argv/decode/component/transport tables close the behavior without live state; no local E2E | Fake CLI, model decoder, contract mutation, and transport process fixtures | `make test` plus focused existing test modules selected by implementer | Independently inspect exact case rows and run focused tests; compare command previews for a comma-containing path and warning fixture | Ordinary CI `quality`, `types`, `contract-check`, `compatibility`, and package jobs | Repeated literal argv; exact integer/null semantics; all boundary pairs; stdout/stderr separation; sanitized errors; excluded symbols absent | Test/CI links, commands, exits, and assertions in Multica only; no images |

## Test implementation ownership

The Implementer owns all tracked contract, focused feature, shared integration,
CI, and release-gate test changes, including extensions to
`tests/live/test_smoke.py`, shared fixtures, fake-CLI tables, CI version/source
pins, and directly related documentation. The Tester SHALL not edit those
files. The Tester independently runs or inspects the published exact revision,
records findings, and requests a new product revision when a defect is found.

No parallel runner, browser framework, snapshot library, or E2E evidence
directory is added. The existing pytest/live-smoke infrastructure and project
test environment are sufficient.

## Readiness and attempt contract

Before any live attempt, the Tester SHALL verify:

1. the product checkout is the exact published candidate SHA and clean;
2. the CLI reports exact target version `0.8.0` and expected commit prefix;
3. the isolated test profile, daemon, project resources, database, and ports are
   selected and the primary Multica profile/daemon are not referenced;
4. focused offline/contract tests and source-of-truth checks passed on the same
   candidate or have a linked CI result;
5. disposable workflow/project/issue/task names are unique and cleanup actions
   are known before mutation;
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
the plan must be revised before verification to require baseline/candidate text
and Mac PNG renders made with bundled `scripts/render_terminal.swift`, with
locale, width, output mode, ANSI/TTY limitations, revision, command, and exit
status recorded honestly.

## Cleanup and preservation

Cleanup SHALL delete disposable workflows, projects, issues, comments, and test
tasks where the isolated environment supports deletion; restore the original
runtime concurrency; restart and health-check the isolated test daemon; and
leave the primary Multica environment untouched. Cleanup SHALL preserve the
evidence branch/PR/commits and their links. The branch or PR SHALL not be closed,
merged, or deleted without separate authority. Cleanup failures are reported as
verification failures with the remaining resource identity, never hidden by a
later successful command.

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
  changelog/releasing docs, live-smoke integration, final conflict resolution,
  and evidence publication. It may repair predecessor code only through explicit
  findings attributed to the owning WP contract and SHALL rerun affected gates.
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
