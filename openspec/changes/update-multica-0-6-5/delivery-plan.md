## Delivery contract

- `planning_issue`: `MYL-534`
- `change_id`: `update-multica-0-6-5`
- `graph_revision`: `2`
- `delivery_mode`: `dag`
- `approved_base`: `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`
- `test_repository_url`: `https://github.com/maximchikAlexandr/multica-py`
- `estimate_authority`: custom properties `Estimate, hours`,
  `Estimate min, hours`, and `Estimate max, hours` on `MYL-534`; numeric totals
  are intentionally absent from this artifact.
- `estimate_basis`: remaining active developer effort for one experienced
  developer familiar with this Python SDK, without AI acceleration. Tests are
  not run to manufacture estimating evidence.
- `estimate_confidence`: medium; scope and source seams are inspectable and a
  lower-target planning package plus earlier upgrade history provide strong
  analogues, while the complete registry reconciliation, trusted live-gate
  alignment, and repair loops have no comparable measured execution history.
- `estimate_calibration`: uncalibrated; no historical active-hour measurements
  were available, so custom properties remain the sole numeric authority.

OpenSpec stores stable scope and topology only. Assignee, live status, review
state, and operational WIP remain in Multica issues.

## E2E verification contract

- `e2e_required`: `false`
- `reason`: every changed feature boundary owned by this Python SDK is
  deterministic command construction, validation, result decoding, redaction,
  or cleanup. The declared stand has no workflow-administration fixture,
  self-hosted VCS provider, alternate actors, or failure injector, so a live
  feature assertion would invent prerequisites. Exact lower-level fixtures are
  sufficient and mandatory. The existing prepared-target workflow remains a
  separate compatibility regression gate, not feature-specific E2E evidence.
- `visual_evidence`: none. The change adds typed SDK values, argv, and errors;
  it changes no SDK-owned terminal table, UI, progress display, or log layout.
  If implementation introduces such a presentation delta, planning SHALL be
  revised before implementation continues.
- `execution_gate`: planning SHALL run neither feature E2E nor live smoke. After
  implementation and human approval, an independent Tester SHALL dispatch only
  the provisioned trusted regression workflow.
- `actual_environment`: `.github/workflows/live-smoke.yml` SHALL be dispatched
  from the trusted default branch with `pr_number` for an open same-repository
  GitHub PR and `candidate_sha` equal to its current full head SHA. The protected
  repository configuration supplies `MULTICA_LIVE_TRUSTED_WORKFLOW_REF` and
  `MULTICA_LIVE_EXPECTED_REVIEWER_ID`; the protected `multica-live` runner
  supplies `MULTICA_LIVE_CLI`,
  `MULTICA_LIVE_SERVER_URL`, `MULTICA_LIVE_WORKSPACE_ID`, and
  `MULTICA_LIVE_PROFILE`. The trusted workflow SHALL set
  `MULTICA_LIVE_EXPECTED_VERSION` to the literal `0.6.5`, and
  `tests/live/conftest.py` SHALL enforce the same constant. No other parameter
  or fixture is assumed. The workflow SHALL continue to call `make live`.
- `setup_reset_failure`: the prepared profile is preauthenticated and the
  prepared workspace already contains the resources documented in
  `tests/live/README.md`. The suite creates uniquely named project/issue/comment/
  metadata records and deletes its project graph. The workflow traps and removes
  its raw runner log on success, assertion failure, or interruption. No actor,
  workflow, provider, network, or server-failure injection is available.
- `publication`: the trusted workflow SHALL preserve its existing sanitized
  artifact allowlist. Tester SHALL link the GitHub PR, candidate commit, workflow
  run, artifact, and relevant files in one English Multica comment and verify
  read-back. Private locations, credentials, raw logs, diagnostic JSON, and
  hashes remain outside Git and Multica attachments. All review and evidence
  links SHALL use GitHub PR terminology; no automation merges, closes, or
  deletes the PR or its branch.

### Coverage matrix

| Case | Decision and executable mechanism | Assertions and ownership | Evidence |
|---|---|---|---|
| C01 — provenance and closed inventories | Lower-level only: existing contract validator, mutation/closure tables, double render, generated check, and source-link audit. | Implementer proves exact identities, 209 nodes, 57 changed plus 139 retained responses, byte equality, and exclusions. | Candidate SHA and command/exit summary in Multica; no image. |
| C02 — property arrays and daemon commit | Lower-level only: frozen property/resource/system fixtures provide exact scalar/array argv, wire values, malformed/legacy responses, and a spy transport. The stand has no declared multi-value property-definition fixture. | Implementer proves order, duplicates, commas, presence, zero-I/O validation, full `cli_commit`, and legacy `None`. | Focused test and fixture links; no image because the SDK owns no presentation layer. |
| C03 — workflow identity and issue mutations | Lower-level only: project/issue component fixtures return UUID/null/omission, remap/handoff success, and typed conflict payloads; spies record complete argv and call count. The stand cannot create or reset workflows. | Implementer proves unchanged signatures, one call, authoritative decode, and no retry/client simulation. Backend transaction semantics are explicitly outside SDK acceptance. | Focused test and fixture links; no image. |
| C04 — wakeup diagnostics and self-hosted PR input | Lower-level only: wakeup command/response fixtures use literal self-hosted references plus failing/passing payloads. The SDK forwards and decodes; the stand's only provisioned PR gate is GitHub and supplies no self-hosted provider. | Implementer proves no provider rewrite/polling/synthesized pass and stale-error clearing from authoritative responses. | Focused test and fixture links; no image. |
| C05 — runtime privacy and binding conflicts | Lower-level only: table-driven 409/busy/auth transport responses and state-neutral spy transports; no alternate actor or bound-task fixture exists on the stand. | Implementer proves safe structured details, one call, no confirm/unbind/cancel/pause/retry, and no client-side mutation after rejection. | Focused test and fixture links; no image. |
| C06 — upload/network/server failures | Lower-level only: existing fake subprocess/transport/filesystem fixtures inject preflight, upload, network, and stable 500 failures and inspect call counts/temp paths. The stand provides no failure injector. | Implementer proves zero or one I/O as specified, no retry, redaction, accurate partial-effect boundary, and temp cleanup. | Focused test and fixture links; no image. |
| C07 — retained behavior and package exclusions | Lower-level only: discovery, canonical vectors, full non-live pytest, type/style, build/package, and forbidden-content gates. | Implementer proves retained behavior and absence of deferred/non-SDK surfaces and evidence files. | Gate summary in Multica; no image. |
| C08 — provisioned compatibility regression | Existing protected `live-smoke.yml` only, after implementation and human approval. Trusted default-branch controller verifies the open same-repository GitHub PR/current head, protected runner inputs, observed CLI `0.6.5`, then runs `make live`. | Implementer updates target/version assertions and workflow tests; Tester dispatches and inspects without editing. This smoke proves only its documented prepared-target public operations, not C02–C06 feature semantics. | GitHub PR/commit/workflow/artifact links plus commands/exits/assertions in Multica with read-back; no image. |

### Evidence acceptance

Tester SHALL post one final English Multica comment containing the candidate SHA,
test-code SHA, exact offline and trusted-live commands and exit codes, assertions,
failures or limitations, and GitHub PR/commit/workflow/artifact/file links. Tester
SHALL read back the comment and confirm each link is accessible before claiming
verification complete. No screenshots or generated HTML are required because
there is no approved user-visible presentation delta.

## Work package DAG

Only direct dependencies are listed. Stages are consecutive topological layers,
not WIP limits. Related tests, fixtures, snapshots, docs, and service files belong
to a WP when necessary for its deliverable unless an active sibling explicitly
owns that write zone.

### WP-01 — Approved contract foundation

- `id`: `WP-01`
- `stage`: `1`
- `depends_on`: none
- `task_coverage`: `1.1`, `1.2`, `1.3`, `1.4`, `1.5`, `1.6`
- `deliverable`: one strict, source-pinned `0.6.5` approved contract and
  deterministic generated projection that close every inventory, mapping,
  constraint, response, compatibility, and exclusion decision.
- `owned responsibility scope`: `contracts/sdk-contract.json`, strictly required
  schema/validator/generator changes under `contracts/schema/` and
  `tools/upstream_contract/`, the existing generated approved SDK projection,
  contract mutation/closure fixtures, and transient double-render verification.
- `critical shared files`: `contracts/sdk-contract.json`,
  `src/multica_py/_generated/approved_sdk.py`, contract schema and generator.
- `contract_surface`: exact release/source identities; `[0.6.0,0.6.6)` policy;
  all 209 command nodes and destinations; all 196 response verdicts; normalized
  validation constraints; explicit deferred/non-SDK surfaces.
- `definition_of_done/evidence`: source-aware validation, mutation/closure tests,
  two byte-identical renders, generated freshness, and source-link audit succeed;
  no raw evidence or transient output is tracked.
- `parallel_safety`: foundation is serialized because every later WP consumes
  its generated bindings and compatibility decisions.

### WP-02 — Property, project, and daemon model adaptations

- `id`: `WP-02`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `2.1`, `2.2`, `2.3`, `2.4`, `2.5`
- `deliverable`: existing property, project, issue-mutation, and daemon status
  surfaces implement the approved additive values without new subsystems.
- `owned responsibility scope`: property/project/system wire and entity models;
  issue-property and project/issue resource adapters; daemon status decoder;
  direct companion typing and immediately related fixtures needed during
  implementation, excluding the consolidated test matrices owned by WP-04.
- `critical shared files`: `src/multica_py/models/properties.py`,
  `src/multica_py/resources/issue_properties.py`, project wire/entity/resource
  modules, `src/multica_py/models/system.py`, and daemon resource decoding.
- `contract_surface`: immutable property arrays and presence; workflow identity
  and server-owned transitions; optional CLI commit; unchanged eager/command
  symmetry and no-retry semantics.
- `definition_of_done/evidence`: focused implementation checks prove exact argv,
  decoding, legacy omission, validation-before-I/O, binding/serialization, and
  no public workflow or daemon-identity abstraction.
- `parallel_safety`: writes only property/project/daemon seams; WP-03 owns wakeup,
  runtime/agent, transport-error, and upload seams.

### WP-03 — Wakeup, runtime privacy, and safe error adaptations

- `id`: `WP-03`
- `stage`: `2`
- `depends_on`: `WP-01`
- `task_coverage`: `2.6`, `2.7`, `2.8`
- `deliverable`: existing wakeup, runtime/agent, attachment, transport, and
  redaction boundaries implement provider-safe conditions and atomic safe errors.
- `owned responsibility scope`: issue-wakeup models/resources, runtime and agent
  resource error handling, attachment/process transport and centralized exception
  decoding, plus immediately related fixtures excluding WP-04's consolidated
  matrices, including every reclassified C02–C06 feature scenario.
- `critical shared files`: `src/multica_py/models/issue_wakeups.py`,
  `src/multica_py/resources/issue_wakeups.py`, runtime/agent/attachment resources,
  `_internal/transport.py`, and `exceptions.py` only where the approved existing
  boundary requires adjustment.
- `contract_surface`: stale diagnostic clearing; self-hosted PR conditions;
  structured privacy/binding conflicts; stable redaction; partial-effect/no-retry
  behavior; no confirm/cascade/provider SDK API.
- `definition_of_done/evidence`: focused checks prove authoritative decode,
  atomic rejected state, safe context, zero retry, temp cleanup, and retained
  public exception types.
- `parallel_safety`: write zone is disjoint from WP-02's property/project/daemon
  models; generated contract files remain exclusively WP-01-owned.

### WP-04 — Closed automated verification matrices

- `id`: `WP-04`
- `stage`: `3`
- `depends_on`: `WP-02`, `WP-03`
- `task_coverage`: `3.1`, `3.2`, `3.3`, `3.4`
- `deliverable`: existing unit/contract/component tables close every changed and
  retained mapping, model, error, discovery, source-link, and exclusion scenario.
- `owned responsibility scope`: focused tests under `tests/unit/`,
  `tests/contract/`, and `tests/component/`; shared operation cases and approved
  contract fixtures; no live-smoke, E2E script, workflow, or public docs edits.
- `critical shared files`: `tests/cases/operations.py`, relevant resource/model
  tables, `tests/contract/test_sdk_contract.py`, contract/source-link/compatibility
  assertions, and transport error cases.
- `contract_surface`: exact argv/wire/result vectors; 209/196 closure; public
  signatures/bindings; validation ownership; redaction/call counts; absence of
  deferred and non-SDK symbols.
- `definition_of_done/evidence`: all focused tables pass with one canonical case
  per approved operation, positive/negative presence coverage, and zero hidden
  allowlist or duplicate fixture hierarchy.
- `parallel_safety`: owns automated non-live tests only; siblings WP-05 and WP-06
  own the trusted live workflow and documentation respectively.

### WP-05 — Trusted GitHub PR live-smoke gate

- `id`: `WP-05`
- `stage`: `3`
- `depends_on`: `WP-02`, `WP-03`
- `task_coverage`: `3.5`
- `deliverable`: the existing protected live-smoke controller and prepared-target
  suite are aligned to CLI `0.6.5` and retain an executable, fail-closed GitHub
  PR/current-head compatibility regression after human approval.
- `owned responsibility scope`: `tests/live/conftest.py`,
  `tests/live/README.md`, directly related live-suite fixtures,
  `tests/unit/test_live_smoke_workflow.py`, and the trusted
  `.github/workflows/live-smoke.yml` controller adjustments.
- `critical shared files`: live-smoke workflow/controller and prepared-target
  fixtures; no unit/contract/component matrix or docs ownership.
- `contract_surface`: trusted default-branch dispatch; open same-repository GitHub
  PR and current full head SHA; fixed protected runner inputs; observed CLI
  `0.6.5`; existing `make live`; sanitized artifact; raw-log and run-owned project
  cleanup. No C02–C06 provider/actor/failure fixture is claimed.
- `definition_of_done/evidence`: controller tests prove fail-closed candidate
  identity, fixed parameter names, protected target/version, raw-log cleanup, and
  artifact allowlist. Actual live smoke remains unrun until human approval.
- `parallel_safety`: files are disjoint from WP-04 test matrices and WP-06 docs;
  Implementer owns all GitHub workflow/fixture edits, Tester edits none.

### WP-06 — Documentation and package contract

- `id`: `WP-06`
- `stage`: `3`
- `depends_on`: `WP-02`, `WP-03`
- `task_coverage`: `4.1`, `4.2`
- `deliverable`: consumer and maintainer documentation, examples, generated-doc
  assertions, exports, and package claims describe exactly the implemented direct
  upgrade, exclusions, evidence boundary, and rollback.
- `owned responsibility scope`: README, API/CLI coverage/compatibility/migration/
  contributing/service-usage/releasing docs, examples, public export checks,
  generated documentation checks, and package-content assertions.
- `critical shared files`: public documentation and packaging metadata/assertions;
  no runtime, contract generator, non-live matrix, or live workflow
  edits.
- `contract_surface`: direct `0.6.1 → 0.6.5` guidance, version bounds, new typed
  values, server-owned behavior, safe errors, exclusions, evidence handling, and
  coherent rollback.
- `definition_of_done/evidence`: typed examples and doc/package assertions agree
  with public signatures and generated metadata; packages advertise no excluded
  surface and contain no evidence artifacts.
- `parallel_safety`: documentation/package assertion zone is disjoint from WP-04
  and WP-05 sibling write zones.

### WP-07 — Exact-SHA acceptance and independent evidence

- `id`: `WP-07`
- `stage`: `4`
- `depends_on`: `WP-04`, `WP-05`, `WP-06`
- `task_coverage`: `5.1`, `5.2`, `5.3`
- `deliverable`: one clean candidate SHA passes the complete offline gate and,
  after human approval, receives independently read-back trusted GitHub PR
  compatibility-smoke evidence with scoped cleanup.
- `owned responsibility scope`: final integration repairs, complete repository
  gates, Git/package forbidden-content audit, exact command/exit evidence, Tester
  execution coordination, Multica link read-back, and documented live-suite
  cleanup. Directly related repair files remain within the originating WP's
  responsibility and SHALL be coordinated rather than silently cross-owned.
- `critical shared files`: repository-wide acceptance surface; no implementation
  begins and no live case runs before the explicit gates in this plan.
- `contract_surface`: strict OpenSpec, source-aware contract, deterministic
  generation, source links, type/style/tests/build/package, trusted live evidence,
  link accessibility, and non-destructive cleanup.
- `definition_of_done/evidence`: all mandatory offline commands succeed at one
  clean exact SHA; independent Tester publishes the required Multica-only
  evidence and verifies read-back; cleanup removes the run-owned project graph
  and raw log while the GitHub PR/branch/commits and sanitized artifact remain;
  no merge/close/delete occurs without separate authorization.
- `parallel_safety`: final integration starts only after all stage-3 deliverables
  complete and therefore owns no parallel sibling write zone.

## Stage and coverage proof

| WP | Stage | Direct dependencies | OpenSpec tasks |
|---|---:|---|---|
| `WP-01` | 1 | none | `1.1–1.6` |
| `WP-02` | 2 | `WP-01` | `2.1–2.5` |
| `WP-03` | 2 | `WP-01` | `2.6–2.8` |
| `WP-04` | 3 | `WP-02`, `WP-03` | `3.1–3.4` |
| `WP-05` | 3 | `WP-02`, `WP-03` | `3.5` |
| `WP-06` | 3 | `WP-02`, `WP-03` | `4.1–4.2` |
| `WP-07` | 4 | `WP-04`, `WP-05`, `WP-06` | `5.1–5.3` |

Every task `1.1–5.3` is assigned exactly once. Stage 2 exposes two independent
WP and stage 3 exposes three independent WP, so the graph has genuine parallel
frontiers and does not collapse to `single_wp_no_dag`.
