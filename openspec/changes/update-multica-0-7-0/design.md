## Context

The implementation baseline is draft PR #101, branch
`feat/MYL-474-update-multica-0.6.2`, exact head
`b1c350ce22941a66871f11e0c5830a6ec542878c`. Its approved contract targets
Multica `0.6.2` at `7ab92d7622ecd81d179a8d83ae2dea74835a5069` and already implements
list-property types and validation, `DaemonStatus.cli_commit`, wakeup
`last_error`, upload/network/server classification, search regressions, project
partial-update behavior, deterministic generation, packaging, and extensive
offline tests. PR #101 currently conflicts with `main`; it is implementation
base and evidence, not a merge-ready artifact.

The verified target remains Multica `0.7.0` at
`dbdbb299164347586e2650bb67684a490726a798`. Its closed inventory contains 209
CLI nodes and 196 supported response work items. The planning branch does not
merge, rebase, edit, close, or replace PR #101.

The approved Git integration target is exact `origin/main` snapshot
`a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`. The verified planning revision
published from `feat/MYL-557-update-multica-0.7.0` SHALL descend from that SHA
and carries the authoritative OpenSpec input into implementation composition.

## Goals / Non-Goals

**Goals:**

- Preserve accepted `0.6.2` behavior while composing PR #101 with exact
  integration target `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c` and advancing
  the approved contract to `0.7.0`.
- Implement only the remaining source-pinned delta through existing models,
  resources, transport errors, case tables, and the single contract generator.
- Close every affected scenario with deterministic lower-level, component,
  contract, package, or CI evidence at one candidate SHA.

**Non-goals:**

- Reimplementing or reverting accepted PR #101 behavior.
- Modifying PR #101, PR #103, their branches, issue statuses, or duplicate
  records as part of this planning revision.
- Adding workflow-management HTTP methods, daemon autostart methods, a new
  generator/registry, a live stand, live credentials, terminal captures, or
  image evidence.

## Decisions

### Decision 1: Use exact PR #101 head as the implementation baseline

Implementation SHALL begin from exact commit
`b1c350ce22941a66871f11e0c5830a6ec542878c`. Before any product edit, the first
implementation package SHALL merge the exact verified planning revision into
that branch with `--no-ff`. The resulting composition commit SHALL have PR #101
head as first parent and the verified planning revision as second parent. That
second parent SHALL descend from approved integration target
`a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`, so the merge brings in both the
fixed integration snapshot and the published OpenSpec input. Conflict resolution
SHALL not silently choose either side and SHALL preserve the accepted `0.6.2`
surface before any `0.7.0` adaptation proceeds.

The foundation SHALL prove all of the following on the composition commit:

- `HEAD^1` equals `b1c350ce22941a66871f11e0c5830a6ec542878c`;
- `HEAD^2` equals the exact planning SHA accepted by Plan Verifier and recorded
  in the implementation managed contract;
- `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c` is an ancestor of `HEAD^2` and `HEAD`;
- `openspec/changes/update-multica-0-7-0/` is byte-identical to `HEAD^2`.

Alternative: restart from `main` or replay selected PR commits. Rejected because
it would discard reviewed work or make preservation depend on an undocumented
commit selection.

### Decision 2: Rebase the approved contract conceptually from 0.6.2 to 0.7.0

`contracts/sdk-contract.json` remains the sole production generator input. Its
baseline provenance SHALL identify the accepted PR #101 `0.6.2` contract; target
provenance SHALL identify `0.7.0`. All 209 command nodes and 196 supported
response items SHALL receive one reviewed target decision, while an item whose
SDK behavior is already satisfied by PR #101 SHALL be marked retained and
covered by a regression reference rather than assigned new implementation.

Alternative: keep the old direct `0.6.1 → 0.7.0` plan. Rejected because it
double-counts accepted work and produces the wrong remaining estimate.

### Decision 3: Add only five remaining behavior groups

The remaining handwritten implementation SHALL be limited to:

1. reviewed property comparison operators through the existing ordered issue
   property predicate parser and argv/query adapter;
2. nullable project `workflow_id` and reviewed workflow-aware write outcomes;
3. the PR-conflict wakeup condition within the existing exactly-one model;
4. runtime `shared_with`, atomic privacy conflicts, blockers, and agent grant
   authorization through existing runtime/agent resources and typed errors;
5. the target workspace allowlist/conflict payload through the existing
   sanitized exception boundary.

PR #101 list-property normalization, daemon commit identity, wakeup diagnostics,
upload/network/server handling, search, and project partial-update semantics
SHALL remain unchanged except where a source-pinned `0.7.0` record explicitly
requires adaptation.

Alternative: carry every task from the former direct-upgrade plan. Rejected
because it would reimplement accepted behavior and obscure the remaining delta.

### Decision 4: Resolve conflicts in one foundation before parallel writes

The foundation package SHALL own baseline reconciliation, contract identifiers,
generated projection, and shared schemas. After it stabilizes those interfaces,
property/project, wakeup, and runtime/error packages MAY write disjoint domains
in parallel. Final integration owns shared tables, docs, packaging, and CI.

Alternative: let domain packages resolve shared contract conflicts independently.
Rejected because `contracts/sdk-contract.json` and generated projections are
high-conflict, single-owner files.

### Decision 5: Offline verification is sufficient

`e2e_required=false`. Each public behavior is a deterministic transformation or
typed decode/validation boundary already exercised with the repository's fake
CLI, frozen payloads, component transport, contract mutation checks, package
imports, and GitHub CI. No remaining acceptance criterion depends on a real
database, browser, external service, interactive TTY, or human-visible output.
The unavailable stand is therefore neither used nor replaced with invented
fixtures; environment-based and visual evidence requirements are removed.

Alternative: retain live or screenshot gates. Rejected because they add no
observable assertion beyond the named lower-level checks and the owner has made
the stand unavailable.

### Decision 6: Ponytail full gate

No new subsystem is needed. The existing contract/schema/generator, typed
models/resources, subprocess transport, fake CLI, frozen case tables, package
tests, and GitHub CI are necessary and retained. A branch-composition framework,
versioned resource layer, second registry, new E2E runner, identity provisioner,
renderer, evidence store, or workflow client is unnecessary and removed.

## Risks / Trade-offs

- **PR #101 conflicts with the exact integration target** → compose once in the
  foundation using the fixed parent contract above, assert
  accepted `0.6.2` signatures/fixtures before target adaptations, and forbid
  domain packages from independently resolving shared files.
- **A retained PR #101 behavior could be mistaken for remaining work** → map
  every target scenario to baseline evidence or a new task and count only the
  latter in the estimate.
- **The source target changes shared contract records** → stabilize identifiers
  and regenerate before parallel domain work begins.
- **No live stand is available** → require concrete fake-CLI/component/contract
  assertions for all remaining behaviors and fail CI on unclassified inventory,
  generated drift, private-data leakage, or incomplete package exports.

## Migration Plan

1. Create the implementation branch from exact PR #101 head. Merge the exact
   verified planning revision as second parent with `--no-ff`; verify its
   ancestry from `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`, preserve the
   OpenSpec subtree byte-for-byte, and prove accepted `0.6.2` behavior is intact.
2. Advance provenance, inventory, response decisions, mappings, compatibility,
   and the generated projection from the accepted `0.6.2` baseline to `0.7.0`.
3. Implement the disjoint remaining behavior groups against the stable contract.
4. Reconcile shared tables/docs and run focused then complete offline, contract,
   type, lint, package, and CI gates at one candidate SHA.
5. Roll back product commits normally. If the unmerged composition itself must
   be undone, use `git revert -m 1 <composition-sha>`; this
   returns the implementation line to exact PR #101 content without modifying
   PR #101, its branch, the planning branch, or either immutable parent SHA.

## Open Questions

None. Destructive cancellation of duplicate issues is a separate owner decision
and is not authorized or performed by this plan.
