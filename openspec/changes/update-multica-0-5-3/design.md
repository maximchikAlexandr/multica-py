## Context

The implementation base is `origin/main` SHA
`b6431903945479d4b54915362a48b17543ff093c`, which already contains the approved
Multica `0.5.2` delivery. Its contract pins release `394535503`, peeled tag commit
`d45aba1cd7582bef9210b921bbb7dc198b48e1ee`, maximum-tested CLI `0.5.2`, and the
public models and request mappings added for that release. The replacement target
is stable `0.5.3`, release `395523214`, peeled tag commit
`ff8b285497809e084915016c40c2bc5e5991ffbc`; the only source interval under review
is `d45aba1cd7582bef9210b921bbb7dc198b48e1ee...ff8b285497809e084915016c40c2bc5e5991ffbc`.

The official Darwin ARM64 baseline archive, executable, and version JSON SHA-256
values are respectively
`7893b31e23cb58ef897b8d44c01b736acc33786aae70aa5d167f7a674b713cc3`,
`9f735a52685a958b739a616ec77d3003b3665e5686609d8e050bcd6dcb279984`, and
`4f3bd93112beb2c90090e9a8bef396d4c72db97e1e7f377a2bf7b00bc32c03cd`.
The target values are
`c41428158b87a8dba409542d55c869d5d86ca738a01ba6e0b4698b49cc94d718`,
`576fe10229b95a624bbdf12ae54054c5d7a58156ea4cffa41ccae6d161729565`, and
`67194f3de511d86a206d7656894705352f9c555794eb6c40166247a213163d9b`.
The unsigned target tag is accepted only when official release metadata, checksum
manifest, archive digest, executable identity, binary-reported commit, and peeled
source commit agree.

The exact source diff contains no changed file under `server/cmd/multica`, so both
public help trees contain the same 201 nodes and every positional, flag, default,
alias, accepted-value, presence, conflict, and destination mapping is retained.
All 22 unique upstream source files referenced by the 167-entry approved response
registry are unchanged, so fields, types, nullability, omission, envelopes,
pagination, timestamps, enums, and error decoding are retained. The relevant
semantic change occurs behind those response boundaries in
`server/pkg/agent/claude.go`: resumed sessions subtract a captured prior-session
baseline, preserve raw totals when the baseline is unusable, use appended cost
state on no-result exits when available, and discard the old baseline on rejected
resume. Existing SDK models already preserve the resulting numeric values.

## Goals / Non-Goals

**Goals:**

- Publish one implementation-ready contract for the direct `0.5.2` to `0.5.3`
  patch interval.
- Make target provenance, the zero CLI/wire delta, the usage semantic correction,
  and every exclusion reproducible and reviewable.
- Promote maximum-tested compatibility without changing the current public SDK
  surface or recomputing usage in Python.
- Deliver contract, generated metadata, focused fixtures, documentation, package
  claims, and verification evidence atomically after approval.

**Non-Goals:**

- Reimplementing any `0.5.2` duplicate, supplement, property, issue-list, model,
  adapter, or export work already present on `main`.
- Adding SDK baseline files, provider-session readers, counter subtraction, cache
  formulas, new usage models, or provider-specific public APIs.
- Exposing PR automation, issue timeline changes, daemon identity behavior,
  Telegram/media, mobile/localization, Grok steering, Antigravity events,
  attachment viewer behavior, or other upstream-only surfaces.
- Changing production code, the approved contract, tests, docs, or main specs on
  this planning branch.

## Decisions

### Treat `0.5.2` as complete baseline, not migration scope

The approved contract and current code are inspected at
`b6431903945479d4b54915362a48b17543ff093c`. Duplicate references, supplement
metadata, atomic issue-create properties, and `duplicate_of` list projection are
baseline invariants only. Their implementation tasks, designs, estimates, and work
packages are removed from this change. Replaying them was rejected because it
would duplicate merged code and create conflicting ownership.

### Record an unchanged public CLI and response surface

The contract target, release artifacts, compatibility bounds, source references,
command inventory, and response review move to `0.5.3`. The command audit records
201 retained nodes with no added, removed, renamed, moved, or help-changed nodes.
The response audit records all 167 supported entrypoints as wire-compatible. No
public Python symbol, signature, field, or operation changes. Inferring SDK work
from unrelated upstream repository churn was rejected because approved CLI and
response boundaries are the governing surface.

### Preserve corrected usage values without client-side accounting

Multica `0.5.3` performs per-run baseline subtraction before existing responses
are emitted. The SDK SHALL decode the returned values through the current
`TaskUsageData`, `IssueUsage`, and `RuntimeUsage` paths without new arithmetic.
Focused fixtures SHALL cover resumed multi-model and cache counters, baseline
reset or absence, corrupt snapshots, no-result fallback, rejected resume, and
agent/issue/runtime aggregates. Recomputing in Python was rejected because the
SDK has neither provider session files nor a reliable baseline and would risk
double subtraction.

### Keep the contract workflow authoritative and minimal

Implementation first reproduces ignored release/source/binary, command, gap, and
response evidence; then it updates and strictly validates the approved contract.
The generated runtime projection is rendered twice in isolation and compared byte
for byte before committing. Existing fixture tables and documentation are extended;
no new framework, runtime dependency, or abstraction is introduced.

## Risks / Trade-offs

- [The upgrade accidentally repeats merged `0.5.2` work] -> Diff every task and
  mutable scope against current `main`; permit only target/provenance, unchanged-
  surface review, usage semantics, docs, and release gates.
- [Corrected usage is subtracted twice] -> Add no SDK arithmetic and assert exact
  preservation of target-provided values.
- [A semantic server change is mistaken for a wire change] -> Record the backend
  source decision separately while keeping all 167 response shapes retained.
- [Compatibility is overstated] -> Pin release, commit, checksums, binary identity,
  all command nodes, and every approved response source before raising the maximum.
- [Unrelated target features leak into public SDK] -> Preserve explicit negative
  inventory and unchanged public-symbol/operation assertions.
- [Evidence leaks into Git or distributions] -> Keep source checkouts, binaries,
  collectors, audits, and transient render output ignored and audit both trees.

## Migration Plan

1. Refresh `origin/main`, require exact base
   `b6431903945479d4b54915362a48b17543ff093c`, and return to planning if the
   approved contract or target dependencies changed.
2. Reproduce `0.5.2...0.5.3` release, checksum, binary, source, command, gap, and
   response evidence in ignored storage.
3. Update and strictly validate `contracts/sdk-contract.json`; render twice to
   isolated paths and commit only the deterministic generated projection.
4. Extend existing usage, contract, provenance, compatibility, negative-inventory,
   documentation, and packaging fixtures without altering public models.
5. Update direct migration and release documentation, run the complete offline and
   package gates, and deliver one clean exact implementation commit.
6. Roll back contract, generated projection, fixtures, documentation, and package
   claims together to the approved `0.5.2` state if any gate fails.

## Open Questions

None. The base, target, unchanged surface, usage handling, exclusions, and
verification policy are fixed by this design.
