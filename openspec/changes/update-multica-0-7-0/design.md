## Context

The source snapshot is `origin/main` at
`a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`. Its approved contract targets
Multica `0.6.1` at `2ea01ae4ef55de4310b99af192d2dbd367832883`
and sets `max_tested_cli_version` to `0.6.1`. The verified stable target is
Multica `0.7.0` at `dbdbb299164347586e2650bb67684a490726a798`.
Draft PRs for `0.6.2` and unrelated controller work are neither a published
baseline nor a branch dependency.

The upstream audit is closed: the target has 209 CLI nodes (four additions, no
removals, six changed nodes) and 196 supported response work items (60 changed,
136 unchanged). Each reviewed argument or flag must still be traced through the
pinned `RunE` path to path, query, JSON, header, multipart, stdin, file, or local
control. Evidence and enum candidates never approve public SDK behavior by
themselves.

## Goals / Non-Goals

**Goals:**

- Certify a direct `0.6.1` to `0.7.0` migration with exact release, asset,
  checksum, binary, source, mapping, response, test, and documentation
  provenance.
- Preserve the approved-contract-only generation boundary and fail closed on an
  unresolved mapping, presence rule, response item, or inventory verdict.
- Add the smallest typed surface necessary for the reviewed `adapt` decisions,
  using existing request models, resources, decoders, transport errors, case
  tables, and live-smoke infrastructure.
- Keep retained operations behaviorally and structurally compatible.

**Non-goals:**

- No public workflow-management HTTP client and no `daemon autostart` resource.
- No public API inferred solely from release notes, source extraction, evidence,
  or a matching upstream name.
- No intermediate SDK releases, new transport, new test framework, database
  migration, or dependency.
- No modification, merge, close, or reuse of draft PR #101 or #103 as a base.

## Decisions

### Decision 1: Direct migration from the effective baseline

The approved contract SHALL replace the target with `0.7.0` and SHALL preserve
`0.6.1` as the direct comparison and minimum reviewed migration baseline. The
compatibility policy SHALL accept the reviewed interval through `0.7.0` and use
the next exclusive semver ceiling produced by the existing generator.

Why: no non-draft intermediate SDK upgrade is published, and the complete
source/binary audit already covers every release through `0.7.0`.

Alternative: stack the draft lower-version branches. Rejected because their
state is not an approved baseline and would introduce unverified merge-order
dependencies.

### Decision 2: One closed approved-contract reconciliation

`contracts/sdk-contract.json` remains the sole production input. The target
provenance, release artifacts, command inventory, response registry, mappings,
constraints, presence policies, fixtures, documentation actions, and source
references SHALL be updated together. The generator SHALL render only the
existing committed runtime module and transient ignored projections.

Each argument and flag SHALL identify its real destination. Presence-sensitive
fields SHALL state omitted, null, empty, zero, and false behavior. Constraints
SHALL be normalized as `requires`, `conflicts_with`, `exactly_one`,
`at_least_one`, `required_together`, enum/range, or a named validator, with
positive and negative cases.

Alternative: generate from the collected evidence bundle. Rejected because it
would bypass review and violate the established trust boundary.

### Decision 3: Extend existing property value and filter paths

`multi_text` and `multi_url` SHALL reuse the existing property definition/value
models and JSON-value decoding boundary. Values SHALL preserve array order,
duplicates, explicit empty arrays, and the reviewed null/omission distinction.
Issue property comparison filters SHALL extend the existing ordered predicate
model with reviewed operators and deterministic query/argv encoding; reserved,
ill-typed, or unsupported combinations SHALL fail before transport.

Alternative: add a generic untyped property escape hatch. Rejected because the
SDK already has a closed typed property model and validation boundary.

### Decision 4: Add fields and semantics to their existing resource models

- Project responses SHALL expose nullable `workflow_id`. Project create/update
  writes SHALL preserve omitted versus explicit null/empty semantics and SHALL
  validate workflow-aware transitions before transport where the CLI contract
  provides a deterministic validator.
- Daemon status SHALL expose optional `cli_commit`; old or omitted payloads SHALL
  decode to the documented legacy value without weakening other required fields.
- Wakeup create/update SHALL admit the reviewed PR-conflict condition, retain
  exactly-one condition validation, and decode diagnostics plus stale-error
  clearing without inventing a second wakeup state model.
- Runtime definitions SHALL expose `shared_with`. Runtime update/delete and
  agent create/update SHALL reuse existing conflict/error types for explicit
  grants, atomic privacy revocation, busy blockers, and authorization failures.

Alternative: create version-specific `V070` resources and models. Rejected
because every change is an additive or presence-sensitive extension of an
existing public concept.

### Decision 5: Centralize reviewed error changes at the current boundary

Upload/network failures, sanitized stable-server failures, workspace allowlist
errors, and structured conflicts SHALL be decoded by the current transport and
resource-specific adapters. Public exceptions SHALL expose only reviewed code,
status, message, and structured safe context; backend details, private URLs,
hostnames, paths, credentials, and personal data SHALL remain redacted.

Alternative: return raw CLI stderr or payload mappings. Rejected because it
would leak implementation details and break the current typed exception policy.

### Decision 6: Preserve explicit exclusions

The four `daemon autostart` command nodes SHALL be recorded as `defer` because
they are local-control candidates needing separate public policy. Workflow
management endpoints SHALL be `not_sdk_surface` because no public CLI operation
exists. Claim metrics, Qoder/runtime ownership, daemon internals, and UI changes
SHALL remain `not_sdk_surface` unless they alter one of the reviewed responses
above.

### Decision 7: Verification uses tables plus one isolated live lifecycle

Existing frozen case tables SHALL gain rows rather than parallel suites. Offline
tests SHALL prove exact argv, mapping, presence, ordering, duplicates, nulls,
validators, decode behavior, errors, exports, and compatibility. The existing
live-smoke boundary SHALL be extended for the exact `0.7.0` candidate and an
isolated test profile/workspace. Tester evidence SHALL be published in Multica,
not committed; genuine changed terminal output SHALL have before/after text and
PNG renders from the bundled `scripts/render_terminal.swift`.

## Ponytail full gate

No new subsystem is necessary. The required alternatives already exist:
approved contract/schema and generator, typed models/resources, centralized
transport errors, frozen test tables, GitHub CI, and live-smoke infrastructure.
All are retained and extended in place. A second registry, versioned resource
layer, workflow client, daemon-control abstraction, test framework, or evidence
store is removed from the design.

## Risks / Trade-offs

- The contract JSON is a shared high-conflict file. A foundation package owns
  it before resource packages begin; siblings consume its stable identifiers.
- Presence and error semantics changed across several upstream releases. Closed
  tables and source-pinned positive/negative vectors trade authoring volume for
  deterministic review.
- Live infrastructure may expose only a subset of destructive/privacy paths.
  Required lower-level fixtures remain release gates; unavailable necessary live
  evidence is a verification blocker, not a reason to claim coverage.
- The direct version jump makes compatibility assumptions visible. Any discovered
  constraint requiring an intermediate migration requires an OpenSpec revision.

## Migration Plan

1. Update and validate the approved provenance, inventory, response registry,
   mapping, constraint, compatibility, and generator contract.
2. Implement disjoint resource/model adaptations against the stable contract.
3. Regenerate projections, reconcile tables/docs, and run focused then complete
   offline/type/lint/package gates.
4. Publish the exact candidate revision and run the isolated `0.7.0` live
   lifecycle with independent inspection and evidence.
5. Release only after human approval and all compatibility gates; no persisted
   SDK data migration or rollback transform is required.

Rollback is a normal Git revert of the implementation change and its generated
projection. It SHALL restore the prior compatibility ceiling and docs together;
partial rollback of generated or handwritten pieces is forbidden.
