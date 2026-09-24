## Delivery mode

`single_wp_no_dag`

The authoritative `Estimate, hours` property on planning issue `MYL-259`
selects the mandatory single-work-package mode. The estimate covers remaining
active developer effort for one experienced developer familiar with this Python
SDK and its upstream-contract workflow, without AI acceleration. Confidence is
medium: the issue/task changes have direct local analogues and the repository
contains a recent adjacent upgrade, while approved-contract fixture churn and
full-gate repair remain bounded sources of uncertainty. The authoritative
weighted, optimistic, and pessimistic totals exist only in the planning issue
properties and were read back after write.

## WP-01 — Direct Multica 0.5.2 contract, adaptation, and release

- `id`: `WP-01`
- `task_coverage`: all OpenSpec tasks `1.1` through `5.4`, exactly once
- `deliverable`: One atomic implementation that promotes the reviewed Multica
  target from `0.5.1` to `0.5.2`, preserves duplicate issue and supplement task
  metadata, supports ordered atomic create-time properties, keeps excluded
  REST/timeline/file surfaces absent, and publishes matching contract, generated
  runtime, tests, documentation, package, and verification evidence at one clean
  commit.
- `owned responsibility scope`: Exact release/source/binary verification in
  ignored storage; complete command and response reconciliation;
  `contracts/sdk-contract.json` and strictly needed schema/validator support;
  deterministic generated runtime; issue and task wire/public models and
  adapters; issue list/create mappings and public exports; directly related
  unit, contract, component, provenance, compatibility, source-link,
  live-gated, and packaging fixtures; public and migration documentation;
  build/package checks; final repository evidence. Directly related tests,
  fixtures, snapshots, docs, generated support files, and narrowly required
  verification repairs are included. Production scope excludes supplement and
  duplicate mutation resources, issue timeline APIs, create attachment inputs,
  new dependencies, backend provisioning, and tracked collector or binary
  evidence.
- `contract surface`: Exact `v0.5.2` commit
  `d45aba1cd7582bef9210b921bbb7dc198b48e1ee`, release `394535503`, comparison
  from `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, reviewed official archive,
  executable, checksum, and version identities; compatibility interval
  `[0.4.42,0.5.3)` with unchanged retained-operation minimums; 201-to-201
  command reconciliation with three changed help nodes and five classified
  source-only names; all 167 supported response work items; immutable
  `DuplicateIssueReference` through canonical issue responses; `duplicate_of`
  list projection; supplement capability/comment IDs/permission through
  `AgentTask` and `TaskRun`; ordered `IssuePropertyAssignment` create input;
  explicit legacy omission/null/empty/false/malformed behavior; stable existing
  pagination, labels, metadata, properties, task fields, operation inventories,
  and composite label semantics; negative excluded-surface guarantees.
- `DoD / evidence`: Independent identities and digests agree; strict pinned-
  source contract validation, deterministic double render, contract check,
  source-link audit, and strict OpenSpec validation exit zero; command and
  response totals reconcile; table-driven issue, task, and property cases prove
  presence, null, empty, false, order, malformed, exact argv, validation timing,
  atomicity, binding, and unchanged behavior; negative inventory guards prove
  excluded surfaces remain absent; README/API/compatibility/migration/changelog/
  live/release guidance and package assertions agree; Ruff, mypy source/tests,
  focused suites, full non-live pytest, non-live collect-only, build, isolated
  package validation, and diff checks pass; prepared live status is reported
  separately; tracked/package audits contain no archives, binaries, `.devlocal`,
  collector/audit evidence, or transient renders; final tree is clean at the
  reported exact SHA.
- `execution rationale`: The authoritative estimate requires one implementation
  unit. Contract identity, generated metadata, response models, create mapping,
  shared global fixtures, compatibility claims, documentation, and packaging
  form one atomic invariant; a single owner prevents partial target promotion
  and keeps rollback at the prior approved contract/model/documentation state.

## Task coverage audit

`WP-01` covers every checkbox in `tasks.md`: contract and evidence `1.1–1.5`,
generated/response implementation `2.1–2.5`, atomic property creation `3.1–3.4`,
table-driven verification and documentation `4.1–4.5`, and final delivery
`5.1–5.4`. There are no uncovered or duplicate task IDs.
