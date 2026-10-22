## Context

The merged SDK baseline is exact `origin/main` commit
`a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`, with an approved Multica `0.6.1`
contract at upstream commit `2ea01ae4ef55de4310b99af192d2dbd367832883`.
Stable Multica `0.6.5` is pinned to
`654b8ca954034f8181eb6bbb4fc298dede760156`. Draft PR #101/#103 and the
lower-target MYL-495 planning branch are useful comparison evidence only; none
is a merged, non-draft baseline or implementation dependency.

The repository already separates reviewed `contracts/sdk-contract.json`,
deterministic generation, handwritten resources/wire adapters, frozen
table-driven tests, protected live smoke, and untracked evidence. The upgrade
crosses those existing seams but introduces no product subsystem or dependency.

## Goals / Non-Goals

**Goals:**

- Certify one direct `0.6.1 → 0.6.5` upgrade with complete reproducible CLI,
  argument/flag, and response dispositions.
- Add the smallest typed adaptations for multi-value properties, project
  workflow identity/behavior, daemon commit identity, wakeup/provider behavior,
  runtime privacy conflicts, and safe errors.
- Preserve compatible output and explicit field-level minimums while the SDK
  minimum remains `0.6.0`.
- Keep contract generation, tests, E2E evidence, documentation, package claims,
  rollback, and exact-SHA publication coherent.

**Non-Goals:**

- Workflow-management HTTP APIs, runtime revoke-confirm HTTP API, daemon
  autostart, daemon CA registration payloads, or UI-only workflow behavior.
- Merging, closing, stacking on, or modifying draft PR #101/#103 or MYL-495.
- Tracking raw evidence, audit JSON, images, logs, upstream source, archives, or
  binaries.
- A property enum, recursive JSON abstraction, workflow client/engine, daemon
  identity service, diagnostic exception hierarchy, second generator, or second
  test framework.

## Decisions

### 1. Advance the approved contract as one atomic direct upgrade

Update target provenance, release artifacts, compatibility metadata, all command
and argument dispositions, all response verdicts, source links, mappings,
constraints, and test references in the approved contract. Render twice into
transient locations, compare bytes, then refresh the tracked generated module
through the current renderer.

Alternative: land `0.6.2`, `0.6.3`, or `0.6.4` separately or stack on draft
work. Rejected because none is the effective baseline and the verified target
public help surface is already covered by one direct reconciliation.

### 2. Extend property values without closing the upstream type namespace

Keep property type identifiers open strings. Extend the existing property value
shape to immutable string tuples and `IssuePropertyResource.set[_command]` to a
scalar string or tuple. Scalars retain legacy syntax; tuples use one compact
JSON array. Decode arrays strictly while preserving order, duplicates, null,
empty, and commas.

Alternative: a `PropertyType` enum or generic recursive JSON value. Rejected:
both create surface not required by the reviewed values and would age poorly.

### 3. Treat workflow semantics as server-owned

Add `workflow_id: str | None` to existing project wire/entity models. Keep issue
mutation signatures and command construction intact; prove authoritative
validation, remap, assignment, and run handoff through fixtures and focused live
checks. Surface conflicts once without retry or simulation.

Alternative: workflow resources or client-side status mapping. Rejected because
there is no approved public CLI and the transaction is server-owned.

### 4. Keep additive status and diagnostics in existing models

Add one optional `cli_commit` field to `DaemonStatus`; extend existing wakeup,
runtime/agent conflict, upload/network, and command-error fixtures. Preserve
open safe error text and centralized redaction.

Alternative: daemon identity models, provider-specific wakeup logic, or new
exception classes. Rejected because existing commands and boundaries already
carry the reviewed information.

### 5. Normalize every imperative mapping constraint

Represent mapping rules using `requires`, `conflicts_with`, `exactly_one`,
`at_least_one`, `required_together`, or a named validator with positive and
negative references. Trace every argument/flag through its actual transport
destination rather than inferring from names.

Alternative: retain prose-only rules for implementer interpretation. Rejected
because the contract must fail closed and generate deterministic validation.

### 6. Keep verification layered and evidence external

Extend existing unit/contract/component tables for deterministic behavior and
use one focused local driver only for real cross-component workflow, wakeup,
runtime-conflict, and upload/error observations. The driver uses the isolated
test repository/stand from project configuration, unique profile/daemon/Compose/
database/port state, and failure-safe cleanup. Actual text is rendered on macOS
with the bundled `scripts/render_terminal.swift`; outputs and images are posted
only to Multica.

Alternative: duplicate lower-level assertions in a new framework or commit
runtime evidence. Rejected because the existing suites own assertions and Git
must remain free of environment evidence.

## Ponytail Gate

`ponytail full` finds no necessary new product subsystem. Each candidate has an
existing alternative and is removed: property enum/conversion layer → open type
strings plus the existing decoder; workflow client/engine → existing project and
issue operations; daemon identity service → optional field on `DaemonStatus`;
provider adapter → existing wakeup condition; diagnostic hierarchy → existing
typed/redacted command errors; second generator/test framework → current contract
renderer and frozen case tables. Two verification files remain necessary rather
than product abstractions: a thin `scripts/e2e/myl534_verify.sh` orchestrator for
pinned acquisition/isolation/cleanup and the bundled dependency-free
`scripts/render_terminal.swift` required for real macOS before/after PNGs.

## Risks / Trade-offs

- [Draft/lower-target overlap] later publication may overlap implementation →
  compare behavior during review but implement from exact main and never stack.
- [Open upstream values] future property/error variants may appear → preserve
  open strings and validate only reviewed shapes.
- [Legacy omission] old CLI output lacks new fields → use explicit omitted/null/
  empty fixtures and optional defaults.
- [Server-owned transactions] offline fixtures cannot prove atomic live effects →
  require isolated independent walkthroughs after human approval.
- [Privacy and evidence leakage] logs and hosts may be sensitive → use unique
  disposable state, redaction assertions, Multica-only publication, and Git/
  package forbidden-content audits.
- [Partial upload effects] transport can fail after mutation → document the
  boundary, assert no automatic retry, and verify cleanup without claiming undo.

## Migration Plan

1. Update the exact `0.6.1` contract baseline to pinned `0.6.5` provenance,
   inventories, mappings, normalized constraints, response verdicts, and bounds.
2. Validate and double-render before refreshing the generated projection.
3. Implement bounded existing-model/resource/decoder changes and extend current
   case tables, CI fixtures, live-smoke driver, and documentation.
4. Run all offline gates at one clean candidate SHA; after human authorization,
   run independent isolated verification and publish Multica-only evidence.
5. Roll back contract, generated output, handwritten code, tests, scripts, and
   documentation together if any mandatory gate fails.

## Open Questions

None. Deferred/non-SDK surfaces, public input shapes, compatibility bounds,
validation ownership, E2E evidence, and rollback are fixed. Changing any of them
requires a new planning revision before implementation.
