## Context

The repository implements a typed Python SDK over a separately installed
Multica CLI. Public behavior is governed by `contracts/sdk-contract.json`,
rendered into `src/multica_py/_generated/approved_sdk.py`, and realized through
explicit resources using `BaseResource` and `CliTransport`. The exact SDK base
is `b268e3bec0436fe51727fda50583344f57663284`; the reviewed upstream range is
`aec9b0b1699939a6d993da9ca2ebd2c62900a8e0..b7f8efcaae6c5f3273c0038252b5d10c81b41068`.

The issue audit closes 235 target help nodes and 196 baseline response
entrypoints. It identifies mandatory compatibility repairs, five CLI-backed
resource families suitable for support, and process/UI/source-only behavior
that must not become SDK surface. Existing tests require table-driven additions
to shared case containers and exact argv/transport assertions.

## Goals / Non-Goals

**Goals:**

- publish one source-pinned, deterministic `0.8.2` approved contract;
- repair incompatible retained operations before adding new resource families;
- reuse existing typed resources, models, transport, errors, generator, tests,
  documentation, and CI seams;
- preserve open upstream-owned values, five-state presence, private-project
  fail-closed behavior, local-path/secret redaction, and package compatibility;
- make implementation and independent verification partitionable without
  conflicting sibling write zones.

**Non-Goals:**

- direct HTTP access or an SDK transport other than the Multica CLI;
- automatic promotion from collected evidence or extractor output;
- public support for `environment`, hidden commands, daemon force/watchdog
  controls, UI/Desktop/Connected Apps, or upstream server implementation;
- a second operation registry, generic workflow engine, command-specific test
  framework, evidence database, or committed live logs/screenshots;
- implementation, test execution, or status changes during planning.

## Decisions

### Decision 1: Repair and freeze the contract foundation first

One predecessor updates provenance, the complete command/response disposition,
contract schema entries, shared models, and deterministic generated projection.
All feature packages consume that reviewed foundation. The contract remains the
only generator input; evidence and suggestions stay review-only.

Alternative: let each resource package edit the contract independently. Rejected
because shared operation inventories, generated bindings, compatibility bounds,
and model fields would create conflicting writes and inconsistent decisions.

### Decision 2: Support all reviewed CLI-backed candidate families

Issue statuses, project members, workflows/project workflows, saved views, and
runtime concurrency are approved because each has a stable public CLI command,
reviewed argv/response mapping, and a natural existing resource seam. The SDK
uses explicit methods and typed `msgspec.Struct` models; open upstream-owned
category/icon/status strings remain strings unless the contract proves a closed
enum.

Alternative: ship only mandatory repairs. Rejected because the task explicitly
requires a reviewed `0.8.2` SDK update and the audited public families have no
unresolved transport or safety dependency.

### Decision 3: Keep unsafe or ambiguous process controls out

The attached-but-ungrouped `environment` command, daemon force/watchdog changes,
hidden `probe-runtimes`, and hidden/deprecated issue rerun are `defer` or
`not_sdk_surface`. A future change needs upstream public-help exposure and, for
process controls, an ownership/signalling safety design.

Alternative: expose every discovered source command. Rejected because source
presence is evidence, not approval, and these paths can control local processes
or are intentionally hidden.

### Decision 4: Replace issue rerun instead of aliasing incompatible semantics

The legacy `IssueResource.rerun(issue_id)` mapping is removed with migration
documentation. A new run-targeted operation accepts a run ID, permits short
prefixes only with issue scope, supports `fresh`, and returns the target task
row. No compatibility alias pretends an issue ID is a run ID.

Alternative: retain the old name and reinterpret its argument. Rejected because
it would silently change identifier semantics and result shape.

### Decision 5: Reuse resource ownership and presence primitives

Top-level catalogs receive explicit client resources; project member and project
workflow operations remain project subresources. Existing `Unset` semantics
represent omit versus explicit clear, existing command/file helpers own
temporary inputs, and `CliTransport` remains the single redaction/error boundary.

Alternative: build a generic command adapter or dynamic registry. Rejected
because it duplicates the generated descriptor layer and weakens typed public
signatures and pre-I/O validation.

### Decision 6: Split implementation by non-overlapping resource write zones

After the foundation, independent packages may implement issue-status/project
member, workflow/view, and retained issue/attachment repairs in parallel. A final
integration package owns shared client exports, compatibility/docs, complete
tests, package/release gates, and live evidence reconciliation. Shared contract,
generated, client-registration, and documentation files are owned only by the
foundation or final integration package, never by parallel siblings.

Alternative: one large implementation package. Rejected if the authoritative
estimate exceeds the topology threshold because three natural resource fronts
can proceed independently after one shared predecessor.

### Decision 7: Ponytail full gate

Every material addition closes a unique requirement or risk through an existing
seam:

- contract/provenance and generated bindings use
  `contracts/sdk-contract.json` and `scripts/upstream_contract.py`; the current
  `0.7.1` inventory is insufficient because target command and response closure
  differs;
- new typed resources use `src/multica_py/resources/_base.py`, explicit client
  registration, and `msgspec.Struct`; current resources are insufficient because
  no public methods/models represent the new CLI families;
- safe errors and literal argv use `CliTransport`; current mappings are
  insufficient for new private-project/error shapes and file-backed workflow
  inputs;
- tests extend shared operation/resource/component tables; current rows are
  insufficient for new canonical methods, presence rules, malformed payloads,
  and regressions;
- independent live evidence extends the repository-native E2E script and
  protected workflow; current strict `0.7.0` preflight cannot verify `0.8.2`.

No additional abstraction, dependency, registry, transport, or test framework
has a distinct requirement or uncovered risk, so none is planned.

## Risks / Trade-offs

- **Large shared contract can become a merge hotspot** → one foundation package
  owns contract/schema/generated writes; siblings consume it read-only.
- **Open upstream values can drift** → keep categories/icons/status strings open
  while validating only source-proven closed ranges and required fields.
- **PR auto-complete update is not atomic** → expose the reviewed partial failure
  honestly and test both writes; do not claim rollback.
- **Private-project behavior can reveal existence** → preserve exact omission or
  not-found semantics and admit only reviewed safe error fields.
- **Workflow step files can leak content or paths** → use owned temporary files,
  existing redaction, and cleanup on every exit path.
- **Live target or renderer may be unavailable** → readiness blocks an attempt
  and complete verification; it does not downgrade the required evidence.
- **Parallel resource packages may need shared exports** → they deliver private
  modules/models and focused tests; final integration alone changes shared
  registration, exports, docs, and package-wide inventories.

## Migration Plan

1. Replace the approved contract provenance/inventory and render the generated
   foundation from exact `0.8.2` source.
2. Implement resource families and retained-operation repairs against that
   immutable foundation in their assigned write zones.
3. Integrate client/export/model registration, migration documentation,
   compatibility bounds, complete canonical coverage, package checks, and live
   verification scripts.
4. Run strict OpenSpec, source-link, deterministic render, offline, type, lint,
   compatibility, package, and exact-SHA CI gates; publish live evidence only in
   Multica.
5. Roll back by reverting the implementation commits together; do not hand-edit
   generated output or retain a mixed `0.7.1`/`0.8.2` contract.

## Open Questions

None. Public/deferred dispositions, compatibility migration, E2E requirement,
and package topology are fixed by this change and its delivery plan.
