## Delivery mode

`single_wp_no_dag`

The authoritative `Estimate, hours` property on planning issue `MYL-267`
selects the mandatory single-work-package mode. The estimate covers remaining
active developer effort for one experienced developer familiar with this Python
SDK and its upstream-contract workflow, without AI acceleration. Confidence is
high and calibration is uncalibrated: the current `0.5.2` implementation is an
exact local baseline, the public CLI and all approved response source files are
unchanged, and the remaining semantic, contract, fixture, documentation, and
package work follows established repository paths. Exact weighted, optimistic,
and pessimistic totals exist only in the planning issue properties and are read
back after write.

## WP-01 — Direct Multica 0.5.3 patch contract and release

- `id`: `WP-01`
- `task_coverage`: all OpenSpec tasks `1.1` through `3.3`, exactly once
- `deliverable`: One atomic implementation that promotes the approved Multica
  target from `0.5.2` to `0.5.3`, records the unchanged command and response
  surfaces, preserves corrected resumed-session usage through existing models,
  and publishes matching contract, generated metadata, focused fixtures,
  documentation, package claims, and verification evidence at one clean commit.
- `owned responsibility scope`: Exact release/source/binary verification in
  ignored storage; complete command, gap, and response reconciliation;
  `contracts/sdk-contract.json` and only strictly required validator/generator
  support; deterministic generated runtime; existing usage, contract, provenance,
  compatibility, operation, response, source-link, negative-inventory, live-gated,
  and packaging fixtures; public and migration documentation; build/package
  checks; final repository evidence. Directly related tests, fixtures, snapshots,
  docs, generated support files, and narrowly required verification repairs are
  included. Production scope excludes new public models, signatures, operations,
  response fields, request inputs, relations, dependencies, SDK usage arithmetic,
  backend provisioning, and tracked evidence.
- `contract surface`: Repository base
  `b6431903945479d4b54915362a48b17543ff093c`; exact `v0.5.2` to `v0.5.3`
  source interval; target release `395523214` and peeled commit
  `ff8b285497809e084915016c40c2bc5e5991ffbc`; reviewed official archives,
  executables, checksums, version identities, and unsigned-tag evidence; retained
  `0.4.42` floor, maximum-tested `0.5.3`, exclusive `0.5.4` ceiling, and unchanged
  operation/field minimums; 201 retained public command nodes; all 167 approved
  response entrypoints wire-compatible; corrected target-provided resumed Claude
  usage; explicit exclusion of unrelated upstream features.
- `DoD / evidence`: Independent identities agree; strict pinned-source contract
  validation, deterministic double render, generated check, source-link audit,
  and strict OpenSpec validation exit zero; command and response coverage
  reconciles completely; existing table-driven fixtures prove exact usage values,
  fallback cases, unchanged public inventories, compatibility, and negative scope;
  README/API/compatibility/migration/changelog/live/release guidance and package
  assertions agree; Ruff, mypy source/tests, focused suites, full non-live pytest,
  non-live collect-only, build, isolated package validation, and diff checks pass;
  prepared live status is reported separately; tracked/package audits contain no
  archives, binaries, source checkouts, `.devlocal`, collector/audit evidence, or
  transient renders; final tree is clean at the reported exact SHA.
- `execution rationale`: The authoritative estimate requires one implementation
  unit. Contract identity, generated metadata, semantic fixtures, global
  compatibility claims, documentation, and packaging are a small atomic invariant;
  splitting them would add coordination without an independent mutable frontier.

## Task coverage audit

`WP-01` covers every checkbox in `tasks.md`: contract and evidence `1.1–1.5`,
deterministic generation and focused verification `2.1–2.3`, and documentation,
full gates, packaging, and delivery `3.1–3.3`. There are no uncovered or duplicate
task IDs, dependencies, stages, or managed DAG edges.
