## Delivery contract

- `planning_issue`: `MYL-534`
- `change_id`: `update-multica-0-6-5`
- `graph_revision`: `1`
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
  analogues, while the complete registry reconciliation, provider-backed E2E,
  and repair loops have no comparable measured execution history.
- `estimate_calibration`: uncalibrated; no historical active-hour measurements
  were available, so custom properties remain the sole numeric authority.

OpenSpec stores stable scope and topology only. Assignee, live status, review
state, and operational WIP remain in Multica issues.

## E2E verification contract

- `e2e_required`: `true`
- `reason`: real project-workflow remap/handoff, self-hosted pull-request wakeup,
  runtime privacy/binding atomicity, and partial upload behavior span CLI,
  backend state, subprocess/filesystem, and provider boundaries that lower-level
  fixtures cannot prove. Changed daemon/property/project output also requires
  genuine macOS before/after captures.
- `execution_gate`: planning SHALL NOT execute these cases. An independent
  Tester SHALL run them only after implementation and human approval.
- `environment`: the repository-owned driver SHALL use the project-described
  isolated Multica test stand through injected `MULTICA_E2E_*` parameters. It
  SHALL allocate run-unique SDK checkouts, CLI profiles, daemon instances,
  Compose project, database, ports, and fixture names and SHALL NOT use the main
  Multica profile, daemon, containers, or reference checkout.
- `repository_assets`: Implementer owns `scripts/e2e/myl534_verify.sh`,
  `scripts/render_terminal.swift`, required fixtures, and CI/live-smoke changes.
  Tester only executes and inspects them and reports findings.
- `publication`: development commits contain scripts, fixtures, generated
  product output, tests, and documentation only. Actual text, PNGs, logs,
  diagnostic JSON, hashes, commands/exits, assertions, private locations, and
  credentials SHALL be published only in the final Multica Tester comment.
  Tester SHALL read the comment back and verify attachments and links.

### Coverage matrix

| Case | OpenSpec requirement/scenario | Verification gap / local E2E decision | Affected public boundary | Local test script | Independent Tester steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| C01 | Upstream contract: exact provenance, closed 209/196 inventories, normalized constraints; verification: reproducible audits | No local E2E. Source-aware validation, mutation/closure tests, deterministic render, and source-link audit are sufficient because behavior is repository-local and deterministic. | `contracts/sdk-contract.json`, generator, public discovery | `make contract`, focused contract/unit commands invoked by the driver preflight | Inspect baseline/target identities and counts; independently run strict validation, double render, generated check, and source-link audit at candidate SHA. | Extend `contract-check`, compatibility matrix, and existing mutation/closure fixtures. | Exact release/tag/archive/executable/source facts; 209 nodes; 57+139 response closure; byte-identical renders; excluded surfaces absent. | Multica-only command/exit summary and candidate SHA; no image. |
| C02 | SDK surface: multi-value property presence/order; daemon CLI commit; changed-output evidence | Local E2E required for actual CLI encoding/decoding and visible output across CLI/backend/SDK; fixtures cannot prove the installed binary and backend agree. | Existing issue-property create/set/list commands and daemon status local-control response | `scripts/e2e/myl534_verify.sh c02` plus focused pytest tables | With equivalent disposable issue/property fixtures, run baseline CLI/SDK and candidate CLI/SDK; set values containing order, duplicate, comma, empty/null cases; read back through public SDK; run daemon status; inspect public state separately from automatic assertions. | Extend property/daemon unit-resource tables and protected live smoke; no new framework/job. | One compact JSON array reaches CLI; immutable order/duplicates preserved; invalid member has zero I/O; target full `cli_commit`; legacy omission/null/empty becomes `None`. | `c02-properties-before.txt/png`, `c02-properties-after.txt/png`, `c02-daemon-before.txt/png`, `c02-daemon-after.txt/png`; actual tested language preserved. |
| C03 | SDK surface: project workflow UUID/null and workflow-aware issue mutation/remap/handoff | Local E2E required because workflow validation and task handoff are an atomic server transaction not observable from offline adapters alone. | Existing project get/list and issue create/status/update/project-move CLI-backed operations | `scripts/e2e/myl534_verify.sh c03` | Provision one default-workflow and one named-workflow disposable project using the stand's documented fixture mechanism; execute public SDK get/create/status/update/move actions; independently list/get issue and task state; reset between baseline/candidate. | Extend project/issue unit/component tables and protected live smoke. | UUID vs null/omission; no signature/argv drift; allowed transition remaps once; invalid transition has one typed error, no retry; returned status/assignee/run handoff matches independent read. | `c03-project-before.txt/png`, `c03-project-after.txt/png`, IDs and assertions in Multica only. |
| C04 | SDK surface: stale wakeup diagnostic clearing and self-hosted `--until-pr` | Local E2E required because provider resolution and persisted wakeup state cross backend and VCS integration boundaries. | Existing issue-wakeup create/update/check-in/get/list operations and condition input | `scripts/e2e/myl534_verify.sh c04` | Create disposable issue/wakeup against a disposable self-hosted test PR fixture; observe a controlled failing check and `last_error`; make the condition pass; independently get/list the wakeup and verify error clearing; disable/delete fixture. | Extend wakeup unit/resource tables; add a protected live-smoke row only when the trusted runner supplies the provider fixture. | Self-hosted reference is not rejected by SDK; passing check is authoritative; stale error clears; no SDK polling, provider rewrite, or synthesized pass. | Commands/exits, provider-safe references, before/after sanitized JSON in Multica; no decorative image because user-facing layout is unchanged. |
| C05 | SDK surface: runtime privacy structured conflict and agent binding lock | Local E2E required because blocker counts, authorization, and atomic cancel/pause/unbind behavior depend on persisted runtime/agent/task state. | Existing runtime update/delete and agent create/update CLI-backed operations | `scripts/e2e/myl534_verify.sh c05` | Create a disposable runtime/agent/task binding with unique names; attempt public-to-private and locked binding mutations as allowed and unauthorized test actors; independently read runtime, agent, and task state; clean only run-owned resources. | Extend runtime/agent/error unit tables; protected live smoke may consume only pre-authorized disposable fixtures. | Structured 409/busy/auth details are safe; no automatic confirm, unbind, cancel, pause, retry, or partial repeat; authoritative state is unchanged after rejection. | Sanitized error text, state assertions, commands/exits in Multica; no image. |
| C06 | SDK surface: upload/network/stable 500 errors and partial-side-effect boundary | Local E2E required for real multipart/filesystem/process cleanup and observable post-failure server state. | Existing attachment upload/download and issue/comment attachment mutation paths | `scripts/e2e/myl534_verify.sh c06` | Use a disposable issue and stand-supported failure fixture to produce pre-upload rejection, upload/network failure, and stable server error; inspect issue/attachment state separately; verify temp cleanup and no retry; remove run-owned records. | Extend attachment/transport/component error tables and existing package/forbidden-content gates. | Safe error context only; zero I/O for local validation; one attempted upload where expected; no retry; actual partial effect is reported accurately; temp files removed. | Sanitized actual error text, state reads, commands/exits in Multica; no image unless final user-visible summary changes during implementation. |
| C07 | Verification: all retained behavior and excluded surfaces | No local E2E. Existing contract, discovery, canonical vectors, full non-live pytest, type/style, package, and forbidden-content gates are sufficient. | Public Python namespace, package contents, all retained operations | Driver preflight invokes repository gates | Inspect excluded workflow/autostart/confirm/internal symbols and package contents independently. | Existing CI, package-test, and compatibility jobs extended with required assertions. | 139 unchanged response items retain behavior; deferred/non-SDK surfaces absent; distributions contain no evidence. | Multica-only gate summary; no image. |

### Script, capture, and cleanup contract

`scripts/e2e/myl534_verify.sh` SHALL accept an exact candidate SHA, an empty
run directory, checksum-pinned CLI `0.6.1` and `0.6.5` inputs, and injected test
environment parameters. It SHALL verify repository and binary identities before
mutation, record the exact product revision separately from the script/evidence
revision, refuse the main profile/daemon/Compose project, run only selected case
IDs, and install a trap before creating state. Assertions SHALL use public SDK/
CLI reads; setup-only calls SHALL use the stand's documented authenticated test
fixture mechanism and SHALL NOT become SDK surface.

`scripts/render_terminal.swift` SHALL render captured UTF-8 text deterministically
on macOS. Baseline and candidate captures SHALL use the same fixture semantics,
locale, width, and output mode. Redirection limitations for ANSI, TTY, and
progress SHALL be reported honestly. Text and images SHALL preserve the tested
output language; planning and Tester explanations SHALL be English.

Cleanup SHALL remove the run-owned Compose project and volumes, database,
profiles, daemons, ports, fixtures, and staging directory on success, assertion
failure, or interruption. It SHALL preserve the test branch, MR, commits,
repository scripts, and linked product artifacts. No automation SHALL close,
merge, or delete that branch/MR without a separate instruction.

### Evidence acceptance

Tester SHALL post one final English Multica comment containing the candidate SHA,
test-code SHA, exact case commands and exit codes, per-case assertions, failures
or limitations, and links to the MR/commits/files. The required PNG files SHALL
be actual attachments, not local paths. Raw logs, diagnostic JSON, hashes, and
sanitized text MAY be attachments; none enters Git. Tester SHALL read back the
comment and confirm every required attachment/link is accessible before claiming
verification complete.

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
  matrices.
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
  own live/scripts/workflow and documentation respectively.

### WP-05 — Independent E2E and CI live-smoke assets

- `id`: `WP-05`
- `stage`: `3`
- `depends_on`: `WP-02`, `WP-03`
- `task_coverage`: `3.5`, `3.6`, `3.7`
- `deliverable`: one repository-owned isolated verification driver, real macOS
  text renderer, and protected live-smoke extensions capable of producing the
  C02–C06 evidence contract after human approval.
- `owned responsibility scope`: `scripts/e2e/myl534_verify.sh`,
  `scripts/render_terminal.swift`, their deterministic tests/fixtures,
  `tests/live/`, `tests/unit/test_live_smoke_workflow.py`, and the trusted
  `.github/workflows/live-smoke.yml` controller adjustments.
- `critical shared files`: live-smoke workflow/controller and prepared-target
  fixtures; no unit/contract/component matrix or docs ownership.
- `contract_surface`: exact revision/binary verification, isolated profiles/
  daemons/Compose/database/ports/fixtures, selected-case execution, real text/PNG
  capture, evidence provenance, failure-safe cleanup, and trusted candidate gate.
- `definition_of_done/evidence`: script self-checks and protected workflow tests
  prove fail-closed candidate identity, main-environment refusal, trap cleanup,
  deterministic rendering, case selection, and no evidence committed. Actual
  live cases remain unrun until human approval.
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
  no runtime, contract generator, non-live matrix, live workflow, or E2E script
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
  after human approval, receives independently read-back C02–C06 evidence with
  scoped cleanup and preserved MR/commits.
- `owned responsibility scope`: final integration repairs, complete repository
  gates, Git/package forbidden-content audit, exact command/exit evidence, Tester
  execution coordination, Multica comment/attachment read-back, and disposable
  stand cleanup. Directly related repair files remain within the originating WP's
  responsibility and SHALL be coordinated rather than silently cross-owned.
- `critical shared files`: repository-wide acceptance surface; no implementation
  begins and no live case runs before the explicit gates in this plan.
- `contract_surface`: strict OpenSpec, source-aware contract, deterministic
  generation, source links, type/style/tests/build/package, live evidence,
  attachment/link accessibility, and non-destructive cleanup.
- `definition_of_done/evidence`: all mandatory offline commands succeed at one
  clean exact SHA; independent Tester publishes the required Multica-only
  evidence and verifies read-back; cleanup removes disposable state while the
  evidence MR/branch/commits remain; no merge/close/delete occurs without separate
  authorization.
- `parallel_safety`: final integration starts only after all stage-3 deliverables
  complete and therefore owns no parallel sibling write zone.

## Stage and coverage proof

| WP | Stage | Direct dependencies | OpenSpec tasks |
|---|---:|---|---|
| `WP-01` | 1 | none | `1.1–1.6` |
| `WP-02` | 2 | `WP-01` | `2.1–2.5` |
| `WP-03` | 2 | `WP-01` | `2.6–2.8` |
| `WP-04` | 3 | `WP-02`, `WP-03` | `3.1–3.4` |
| `WP-05` | 3 | `WP-02`, `WP-03` | `3.5–3.7` |
| `WP-06` | 3 | `WP-02`, `WP-03` | `4.1–4.2` |
| `WP-07` | 4 | `WP-04`, `WP-05`, `WP-06` | `5.1–5.3` |

Every task `1.1–5.3` is assigned exactly once. Stage 2 exposes two independent
WP and stage 3 exposes three independent WP, so the graph has genuine parallel
frontiers and does not collapse to `single_wp_no_dag`.
