## Delivery mode

`single_wp_no_dag`

The authoritative `Estimate, hours` property on planning issue `MYL-226`
selects the mandatory single-work-package mode. The estimate covers remaining
active developer effort for one experienced developer familiar with this Python
SDK and its upstream-contract workflow, without AI acceleration. Confidence is
medium: the two model additions have direct local analogues and the repository
has recent upgrade history, while contract reconciliation, generated fixture
churn, and full-gate repair remain bounded sources of uncertainty. The
authoritative weighted, optimistic, and pessimistic totals exist only in the
planning issue properties and were read back after write.

## WP-01 — Direct Multica 0.5.1 contract, adaptation, and release

- `id`: `WP-01`
- `task_coverage`: all OpenSpec tasks `1.1` through `5.4`, exactly once
- `deliverable`: One atomic implementation that promotes the reviewed Multica
  target from `0.5.0` to `0.5.1`, preserves optional `wakeup_id` and `call_id`
  response data, keeps every `issue wakeup` command deferred, and publishes
  matching contract, generated runtime, tests, documentation, package, and
  verification evidence at one clean commit.
- `owned responsibility scope`: Exact release/source/binary verification in
  ignored storage; complete command and response reconciliation;
  `contracts/sdk-contract.json` and strictly needed schema/validator support;
  deterministic generated runtime; task-run and run-message wire/public models
  and adapters; directly related unit, contract, component, provenance,
  compatibility, source-link, live-gated, and packaging fixtures; public and
  migration documentation; build/package checks; final repository evidence.
  Directly related tests, fixtures, snapshots, docs, generated support files,
  and narrowly required verification repairs are included. Production scope
  excludes wakeup resources/operations, runtime-profile APIs, new dependencies,
  backend provisioning, and tracked collector or binary evidence.
- `contract surface`: Exact `v0.5.1` commit
  `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, release `392880229`, Darwin
  ARM64 archive SHA-256
  `85c5e6d8f9af4c3cfef9a6632a94b682ca09afb1e62900a8565eab5bb26a12ec`,
  executable SHA-256
  `a7223c87c3da4b77afa8b0941504678c30a2770dd1d03df5f2325301360ed588`,
  and official checksum-manifest SHA-256
  `cf71aab5b40ed16e89c5f826109deace7b4b92198ef1147dd1608e4aea396800`;
  compatibility interval `[0.4.42,0.5.2)` with unchanged operation minimums;
  194-to-201 command reconciliation; seven explicit wakeup deferrals;
  runtime-profile `not_sdk_surface`; updater/workdir retained dispositions;
  all 167 supported response entrypoints; the shared optional open-string
  `wakeup_id` field through the existing `AgentTask` projection on `agents.tasks`
  and `TaskRun` projection on `issues.runs`; optional open-string
  `RunMessage.call_id` on `issues.run_messages`; present, omitted/legacy, and
  malformed response semantics; stable operation/resource/signature inventories.
- `DoD / evidence`: Independent identities and digests agree; strict pinned-
  source contract validation, deterministic double render, contract check,
  source-link audit, and strict OpenSpec validation exit zero; exact command,
  operation, and response totals reconcile; table-driven model/resource tests
  prove present, omitted/legacy, malformed, ordering, serialization, and
  unchanged transport behavior; negative inventory guards prove no wakeup or
  runtime-profile public surface; README/API/migration/changelog/live guidance
  and package assertions agree; Ruff, mypy source/tests, focused suites, full
  non-live pytest, non-live collect-only, build, package validation, and diff
  checks pass; prepared live status is reported separately; tracked/package
  audits contain no archives, binaries, `.devlocal`, collector/audit evidence,
  or transient renders; final tree is clean at the reported exact SHA.
- `execution rationale`: The work is deliberately one implementation unit.
  Contract identity, generated metadata, model fields, global fixtures,
  compatibility claims, documentation, and packaging share atomic invariants;
  a single owner prevents partial promotion and keeps rollback at the prior
  approved contract/model/documentation commit.

## Task coverage audit

`WP-01` covers every checkbox in `tasks.md`: contract and evidence `1.1–1.5`,
generated/model implementation `2.1–2.4`, table-driven verification `3.1–3.4`,
documentation/package alignment `4.1–4.3`, and final delivery `5.1–5.4`.
There are no uncovered or duplicate task IDs.
