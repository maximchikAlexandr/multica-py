## Delivery contract

- **Task key:** `MYL-656`
- **Change:** `update-multica-0-8-2`
- **Approved SDK base:** `b268e3bec0436fe51727fda50583344f57663284`
- **Upstream range:** `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0..b7f8efcaae6c5f3273c0038252b5d10c81b41068`
- **Planning scope:** OpenSpec-only; implementation begins only after independent
  plan verification and the human implementation gate.
- **Estimate authority:** exact optimistic, weighted, and pessimistic totals are
  stored only in planning issue properties `Estimate min, hours`,
  `Estimate, hours`, and `Estimate max, hours`. This document records confidence,
  assumptions, evidence, and the topology selected from the weighted property.

## Scope and contract seams

The change closes the audited 235-node target command tree and 196 baseline
response entrypoints. Mandatory repairs cover rerun-task migration, issue search,
PR auto-complete, attachment binding, additive models, precision, and private
authorization. Approved additions cover issue statuses, project members,
workflows/project workflows, saved views, and runtime concurrency. Deferred and
non-SDK behavior remains absent exactly as specified.

Existing seams are authoritative:

- `contracts/sdk-contract.json` and `scripts/upstream_contract.py` own reviewed
  mappings, validation, generation, and source links;
- `src/multica_py/_generated/approved_sdk.py` is the committed deterministic
  projection, never a hand-edited second source;
- explicit resources, `BaseResource`, `Command`, `CliTransport`, `Unset`, and
  frozen `msgspec.Struct` models own the public SDK behavior;
- shared operation/resource/component tables own exact argv, decoding, presence,
  malformed payload, and error cases;
- `scripts/e2e/verify_multica_test.py`, `tests/live/`, and
  `.github/workflows/live-smoke.yml` own isolated live verification.

## E2E decision

`e2e_required=true`.

Lower-level contract, unit, component, and package tests are sufficient for
deterministic argv, five-state presence, decoder/error behavior, byte-stable
generation, and exclusions. They are not sufficient for the remaining risks:
real server lifecycle and cleanup for new mutable catalogs, private-project
authorization across two identities, run-targeted rerun against an actual task,
file upload/binding across CLI and service, and visible baseline/candidate CLI
output. Those gaps require a focused independent walkthrough on the isolated
test target described by the project. The plan uses `multica-test` only and
never the primary profile, daemon, checkout, database, or containers.

## Verification matrix

| Case | OpenSpec requirement/scenario | Gap and local E2E decision | Public operation/schema | Repository script | Independent Tester actions | CI disposition | Assertions | Artifacts/images |
|---|---|---|---|---|---|---|---|---|
| E01 | upstream authority; compatibility; retained additive fields | Live required for exact target identity and real retained decoding | `version`; project/issue reads; additive issue/task/attachment models | extend `scripts/e2e/verify_multica_test.py` | From a fresh candidate checkout, confirm exact SDK SHA and wrapper-owned CLI `0.8.2`; inspect one retained project/issue/task read without target overrides | protected `live-smoke` plus lower-level compatibility/model tests | exact CLI and SDK revisions; no primary profile; reviewed optional fields decode without invented values | sanitized manifest/stdout/stderr/cleanup hashes in Multica; no image because retained output is not the visible delta |
| E02 | issue-status lifecycle and conflict | Live required for create/update/list/get/archive state and occupied-archive conflict | issue-status create/update/list/get/archive; status model and 409 error | add focused status lifecycle to isolated walkthrough | Create a uniquely keyed custom status, create a disposable issue using it, prove archive conflict, move/delete disposable data, archive status, and read back terminal state | lower-level table cases in ordinary CI; lifecycle local-only because workspace status mutation needs isolated service | exact open icon/category values; occupied archive fails without data loss; cleanup removes all test-owned rows | English status summary; baseline `0.7.1` help absence and candidate lifecycle output text + `issue-status-before.png` / `issue-status-after.png` |
| E03 | project members and private fail-closed behavior | Live required for cross-identity authorization and relation visibility | project member list/add/remove; private project access | add project/member scenario using prepared secondary test identity | Readiness confirms a disposable project and secondary test member; add member, verify visibility under that identity, remove member, then prove not-found/omission and delete project | lower-level argv/decoder/error cases in ordinary CI; private identity local-only | membership identities remain distinct; removal hides project and related rows; no personal data captured | sanitized IDs and assertions in Multica; no screenshot because semantics are state/auth, not changed output |
| E04 | workflow/project workflow, saved views, concurrency | Live required for dry-run/no-write, persisted workflow/view evaluation, and reversible runtime setting | workflow CRUD/handoff; project workflow get/set; view list/get/issues; runtime concurrency | add disposable workflow/view/project scenario and dedicated-runtime restore guard | Create a uniquely named workflow and view; prove dry-run leaves project unchanged; apply and read back; evaluate view; set then restore/clear concurrency only on the dedicated test runtime; delete owned objects | protected live smoke for public lifecycle; lower-level file/range/presence cases in ordinary CI | step file cleaned; dry-run no write/run; map repeatability; view cursor page; concurrency `1..50` and `none`; original runtime setting restored | workflow/view baseline help and candidate output text + `workflow-view-before.png` / `workflow-view-after.png`; cleanup manifest |
| E05 | legacy rerun replacement | Live required because task ID resolution, safe reuse/fresh behavior, and task-row response cross process/service boundaries | issue rerun-task; task row | add prepared test-agent task creation and rerun scenario | Trigger a disposable task through the isolated workspace, capture its full ID, rerun once safely and once fresh, inspect returned task identity/parent relation, then clean owned issue/project while preserving run evidence | lower-level full/prefix/fresh argv cases in ordinary CI; protected live smoke for full-ID path | short prefix without issue fails pre-I/O; full ID succeeds; fresh returns a distinct task; no issue-targeted alias | actual `0.7.1` issue-rerun output and `0.8.2` rerun-task output text + `rerun-before.png` / `rerun-after.png` |
| E06 | attachment/comment literal path and binding | Live required for multipart/file upload plus service-side binding; failure cleanup remains lower-level | attachment upload; issue comment add/update binding | add one Unicode/space-containing fixture generated outside Git and test-owned comment lifecycle | Create disposable project/issue, upload and bind the generated file by literal path, read comment/attachment, download/compare hash, delete project, and inspect cleanup | happy path protected live smoke; binding-failure and redaction cases in ordinary CI | one upload path; bytes/hash preserved; no local path/secret in result or diagnostics; cleanup on every exit | Multica attachment/file links and sanitized hash/command/exit evidence; no decorative image |
| E07 | PR auto-complete atomic/partial behavior and private malformed errors | Lower-level sufficient; a prepared PR/provider and induced second-write failure would add external state without closing a unique gap | issue create/update PR auto-complete; transport errors | no local live script | Independently inspect table cases and fake-CLI component fixtures; do not mutate a real PR | ordinary contract/unit/component CI | create malformed value performs no write; create atomic response only; update partial failure is reported; malformed errors stay generic | test/fixture/CI links in Multica; no image |
| E08 | 235 commands, 196 responses, deterministic generation, exclusions | Lower-level sufficient because source/contract bytes and public discovery are deterministic | approved contract/schema/generated module | existing contract/source-link/check commands | Independently compare inventories, run double render in transient directories, and inspect forbidden symbols | `contract-check`, ordinary quality/types/package jobs | exact counts and unique dispositions; byte-identical render; evidence-only mutation changes no production bytes | commands, exits, hashes, diff/file links in Multica; no image |

Every affected scenario is mapped by E01–E08 or the named lower-level rows in
tasks 1.1–7.3. E07 and E08 are explicit lower-level decisions, not omitted E2E.

## Scripts, fixtures, and ownership

Implementer SHALL extend, not replace, the repository-native verification paths:

- `scripts/e2e/verify_multica_test.py` remains wrapper-owned, exact-version,
  output-outside-Git, sanitized, and failure-cleaning. It gains the selected
  E01–E06 scenarios, test-owned fixtures, and an explicit restoration ledger.
- `tests/live/test_smoke.py` and its shared live fixtures gain the smallest
  public SDK calls needed by protected CI. They do not duplicate every local
  lifecycle branch.
- unit tests for the script/workflow prove exact `0.8.2` preflight, path/profile
  isolation, resource ownership, sanitizer allowlists, interruption cleanup,
  candidate-SHA authorization, and runtime-setting restoration.
- table-driven contract/unit/component tests implement E07/E08 and all
  deterministic negative cases. Tester does not edit these fixtures; findings
  return to Implementer.

No new runner framework is permitted. Real output, logs, JSON diagnostics,
hashes, commands, exits, and images are evidence in Multica, not tracked test
fixtures. JSON enters Git only when it is an actual generated contract or test
fixture for the product behavior being verified.

## Readiness and attempt gate

Before a live attempt, Tester SHALL prove all of the following:

1. candidate checkout is clean and `HEAD` equals the reviewed full SHA;
2. `multica-test version --output json` reports exact `0.8.2` and resolves to
   the isolated wrapper; no primary profile/server/workspace overrides exist;
3. focused contract/unit/component results for the candidate are available;
4. the isolated target is reachable through the project-provided configuration,
   and the disposable primary/secondary identities plus dedicated runtime have
   been provisioned without exposing their URL or identity in Git;
5. unique name prefix, resource ledger, original runtime concurrency, output
   directory outside Git, cleanup callbacks, and attempt identifier are ready;
6. the macOS renderer is actually available and can convert captured UTF-8 text
   to PNG at fixed locale, width, font, and no-color/table settings. If ANSI,
   TTY, or progress state cannot be preserved, the text and PNG are labelled as
   non-interactive renders and that limitation is reported.

Failure of any readiness item consumes no live attempt and blocks complete
verification. Automated suites follow the workspace ten-minute local limit;
manual agent-driven walkthrough and capture are not automated suites and may
continue as long as needed.

## Independent walkthrough and image contract

Tester SHALL perform fresh public actions after the automated/focused checks;
rerunning the script alone is not an independent walkthrough. The Tester reads
back server state through separate SDK calls and, where meaningful, the CLI
table output. Baseline and candidate captures use official verified Darwin
arm64 `0.7.1` and `0.8.2` binaries, equivalent fixtures, English output, fixed
terminal width, non-interactive mode, and reset between revisions.

Mandatory image pairs are:

- `issue-status-before.png` / `issue-status-after.png`;
- `workflow-view-before.png` / `workflow-view-after.png`;
- `rerun-before.png` / `rerun-after.png`.

The corresponding UTF-8 text files are mandatory. A baseline command absent in
`0.7.1` is captured as the genuine help/error result, never reconstructed.
Images preserve the tested output language; captions and findings are English.
The renderer task belongs to Implementer with a readiness assertion, while
Tester owns actual capture and independent interpretation.

## Evidence publication and cleanup

Tester SHALL post one final Multica comment at the exact candidate revision and
read it back. It contains PR, commit, file, and CI links; case outcomes; commands
and exit codes; hashes; assertions; limitations; cleanup; and all mandatory PNG
attachments. Private URLs, hostnames, credentials, profile names, personal data,
raw environment dumps, and unredacted output are excluded.

Cleanup deletes only test-owned project/issues/status/workflow/view/attachments,
restores or clears the dedicated runtime concurrency to its recorded original
state, and preserves the evidence MR/branch/commits. It does not merge/close the
PR, delete branches, remove non-test data, or automate additional live attempts.

## Estimate calibration

The estimate measures remaining active developer-hours for one experienced
developer familiar with this Python SDK and Multica CLI contract workflow,
without AI acceleration. Tests are not run for estimation. Evidence consists of
the complete OpenSpec package, exact base source, current contract/generator,
resource/model/transport seams, shared tests, live scripts, and CI workflows.
Confidence is medium: the code and acceptance surface are inspectable, while the
large contract reconciliation, cross-identity live setup, and reversible runtime
verification create bounded uncertainty. Unattended CI, approvals, and external
environment waiting are excluded from active hours.

## Delivery mode and topology

The authoritative `Estimate, hours` property is above the multi-package
threshold. `delivery_mode=dag` is therefore selected because the shared contract
foundation unlocks three natural, non-conflicting resource fronts that can run
at the same time. The complete stage mapping is:

| WP ID | Stage | Direct `depends_on` | OpenSpec task coverage |
|---|---:|---|---|
| `WP-01-contract-foundation` | 1 | none | 1.1–1.5 |
| `WP-02-mandatory-repairs` | 2 | `WP-01-contract-foundation` | 2.1–2.5 |
| `WP-03-status-members` | 2 | `WP-01-contract-foundation` | 3.1–3.4 |
| `WP-04-workflows-views-concurrency` | 2 | `WP-01-contract-foundation` | 4.1–4.5 |
| `WP-05-live-verification-support` | 3 | `WP-02-mandatory-repairs`, `WP-03-status-members`, `WP-04-workflows-views-concurrency` | 6.1–6.3 |
| `WP-06-integration-release` | 4 | `WP-05-live-verification-support` | 5.1–5.5, 7.1–7.3 |

Stages are consecutive and topological: every predecessor has a lower stage.
The stage-2 frontier contains three independent packages, so the graph passes
the parallel-front check. WIP limits are operational and are not encoded as
additional dependencies.

### WP-01-contract-foundation

- **Deliverable:** one reviewed `0.8.2` contract foundation with complete
  provenance, 235 command dispositions, 196 response conclusions, normalized
  mappings/constraints, schema validation, source links, and byte-stable
  generated projection.
- **Owned responsibility scope:** `contracts/sdk-contract.json`, contract schema,
  `scripts/upstream_contract.py`, source-link/contract validators, generated
  approved SDK projection, and contract-focused tests/fixtures. Directly coupled
  contract snapshots and generator documentation are included.
- **Critical shared files:** this package exclusively writes the approved
  contract and generated projection. Downstream siblings consume them read-only.
- **Contract surface:** exact release/source/binary authority; operation IDs;
  argv/destination/presence/constraint/response decisions; compatibility
  metadata; supported/deferred/non-SDK dispositions.
- **DoD/evidence:** strict contract/schema/source-link checks close exact counts;
  duplicate/missing/unresolved rows fail; two transient renders are byte-equal;
  evidence-only input cannot alter production bytes.
- **Parallel safety:** stage 1 is the sole foundation writer and has no sibling.

### WP-02-mandatory-repairs

- **Deliverable:** all retained compatibility repairs: run-targeted rerun,
  search filters, PR auto-complete behavior, attachment binding, additive
  response models, precision, and private-project errors.
- **Owned responsibility scope:** existing issue/comment/attachment resources,
  retained issue/task/attachment wire and public model modules, transport error
  safe-field handling, domain unit/component tests, and migration fragments
  specific to the removed rerun API. Related fixtures follow this package.
- **Critical shared files:** it SHALL NOT write the approved contract/generated
  projection, `MulticaClient`, package-wide exports, shared canonical operation
  registry, aggregate docs, E2E scripts, or CI workflows.
- **Contract surface:** tasks 2.1–2.5 and corresponding public-cli-parity,
  sdk-surface, and subprocess-transport scenarios.
- **DoD/evidence:** exact argv and pre-I/O rejection tables, typed task-row and
  additive decoders, PR partial-failure cases, one-path attachment cleanup, and
  reviewed private/not-found/malformed errors pass focused checks.
- **Parallel safety:** write zone is existing issue/attachment/error code and
  domain tests; it does not overlap WP-03 or WP-04 modules.

### WP-03-status-members

- **Deliverable:** typed issue-status catalog and project-member subresource with
  lifecycle, conflict, identity, private access, and focused test coverage.
- **Owned responsibility scope:** new issue-status and project-member resource,
  model/wire modules and domain tests/fixtures. Project-member integration stays
  behind a package-private seam until WP-06 registers shared exports.
- **Critical shared files:** no edits to `MulticaClient`, project aggregate
  registration, package exports, approved/generated contract, shared canonical
  operation registry, aggregate docs, E2E scripts, or CI.
- **Contract surface:** tasks 3.1–3.4; open status/icon/category values; occupied
  archive conflict; distinct membership/user identities; fail-closed private
  project behavior.
- **DoD/evidence:** explicit eager/command methods, exact argv, frozen models,
  focused canonical/boundary/malformed/error rows, and typed checks pass without
  a new abstraction or dependency.
- **Parallel safety:** new domain modules/tests are disjoint from WP-02 and WP-04;
  all shared registration is deferred to WP-06.

### WP-04-workflows-views-concurrency

- **Deliverable:** typed workflow/project-workflow, saved-view, and runtime
  concurrency operations with file-channel safety and focused tests.
- **Owned responsibility scope:** new workflow/view resource and model/wire
  modules, `RuntimeResource` concurrency methods, owned temporary-step helper
  reuse, and domain tests/fixtures. Shared registration remains deferred.
- **Critical shared files:** no edits to `MulticaClient`, package exports,
  approved/generated contract, shared canonical operation registry, aggregate
  docs, E2E scripts, or CI.
- **Contract surface:** tasks 4.1–4.5; repeatable maps, dry-run no-write,
  instruction-file presence, cursor/field paging, concurrency `1..50|none`,
  cleanup/redaction.
- **DoD/evidence:** exact argv and range/presence tables, deterministic temporary
  JSON cleanup, malformed response/error cases, dry-run assertions, and focused
  typing pass.
- **Parallel safety:** workflow/view/new-model files plus the runtime-only method
  zone do not overlap the issue/status/member modules owned by stage-2 siblings.

### WP-05-live-verification-support

- **Deliverable:** repository-native exact-`0.8.2` isolated walkthrough,
  protected live-smoke support, macOS before/after capture path, and their
  deterministic unit assertions.
- **Owned responsibility scope:** `scripts/e2e/verify_multica_test.py`,
  `tests/live/`, E2E/workflow unit tests, `.github/workflows/live-smoke.yml`, and
  directly related fixtures/readiness documentation.
- **Critical shared files:** product resources/models, approved/generated
  contract, aggregate client exports, canonical registry, migration docs, and
  package-wide release gates remain read-only.
- **Contract surface:** tasks 6.1–6.3 and cases E01–E06, including exact SHA/CLI,
  isolated identities/runtime, restoration ledger, sanitizer allowlist, genuine
  baseline/candidate text, renderer readiness, and PNG capture.
- **DoD/evidence:** script/workflow unit checks prove fail-closed readiness,
  cleanup/restoration, primary-profile isolation, SHA authorization, and
  evidence allowlists. No live run or image is claimed during implementation of
  the support code.
- **Parallel safety:** stage 3 starts only after every product front is complete;
  it owns verification harness files exclusively.

### WP-06-integration-release

- **Deliverable:** one clean candidate integrating all resource fronts with
  shared client/exports/canonical registry, aggregate docs/tests/CI/package
  gates, independent live evidence, and exact-SHA release proof.
- **Owned responsibility scope:** `MulticaClient`, package/model/resource exports,
  shared canonical operation registry, aggregate compatibility/migration docs,
  cross-domain contract/component/package tests, ordinary CI source/compatibility
  gates, final OpenSpec-preservation checks, and Multica evidence publication.
  Directly related snapshots and packaging metadata are included.
- **Critical shared files:** no active sibling exists at stage 4; this package
  is the sole reconciler of all shared registration, documentation, canonical
  coverage, and release files.
- **Contract surface:** tasks 5.1–5.5 and 7.1–7.3; complete scenario closure,
  exact compatibility bounds, package imports, offline/CI gates, E07/E08, and
  evidence/cleanup contracts.
- **DoD/evidence:** strict OpenSpec and contract/source/render checks, focused and
  complete permitted automated gates, package/import checks, exact-SHA CI, E01–
  E08 independent outcomes, mandatory PNG attachments, clean Git status, and
  byte-identical verified planning subtree are read back successfully.
- **Parallel safety:** final single writer after WP-05; integration conflicts are
  resolved here rather than in parallel siblings.

## Coverage and dependency audit

Tasks 1.1–7.3 are covered exactly once by the six packages above. Dependencies
are direct only: stage-2 packages depend on the shared foundation; live support
depends on all product fronts; final integration depends on live support and
therefore transitively on all product fronts. No sibling has overlapping
critical shared-file ownership, and directly related tests, fixtures, snapshots,
docs, or service files follow the package that owns their behavior unless this
contract explicitly reserves the shared aggregate to WP-06.
