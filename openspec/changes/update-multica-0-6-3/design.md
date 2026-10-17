## Context

The merged SDK baseline is `origin/main` at `a96eecf3e12a88dd7b4d56e1aafae3285fb0990c`, with an approved Multica 0.6.1 contract at upstream commit `2ea01ae4ef55de4310b99af192d2dbd367832883`. Stable Multica 0.6.3 is pinned to `18fa9f728a9e25f2465df2789631edb2a75442ad`. Draft PR #101 and PR #103 are review evidence only and are neither a base nor a dependency.

The existing architecture already separates reviewed `contracts/sdk-contract.json`, deterministic generation, handwritten resource/wire adapters, table-driven tests, and untracked evidence. This change crosses those layers but does not require a new runtime subsystem.

## Goals / Non-Goals

**Goals:**

- Certify one direct 0.6.1-to-0.6.3 upgrade with complete, reproducible CLI and response dispositions.
- Add the smallest typed changes for multi-value properties, project workflow identity/behavior, daemon commit identity, and reviewed diagnostics.
- Preserve older compatible output where the current minimum remains 0.6.0.
- Keep contract generation, tests, docs, package claims, and rollback coherent at one exact SHA.

**Non-Goals:**

- Implement workflow-management HTTP APIs, daemon autostart, or daemon-claim-only fields.
- Merge, close, stack on, or reuse draft PR #101/#103 as an implementation baseline.
- Track raw evidence, audit JSON, screenshots, logs, source checkouts, or release assets.
- Add dependencies, a second generator, a second fixture framework, polling/retry orchestration, or a client-side workflow engine.

## Decisions

### 1. Advance the approved contract as one atomic direct upgrade

Update target provenance, release artifacts, compatibility metadata, CLI inventory, response catalog, source links, mappings, and test references in the approved contract. Render the existing generated module twice into transient locations, compare bytes, then refresh the tracked projection through the existing renderer.

Alternative: land 0.6.2 first or stack on draft work. Rejected because neither draft is an approved effective baseline, and the verified target help surface is unchanged between 0.6.2 and 0.6.3.

### 2. Extend property values without closing the upstream type namespace

Keep `PropertyDefinition.type` and `PropertyValue.type` as strings. Extend only the property-value annotation/wire decoder to accept immutable string tuples, and extend `IssuePropertyResource.set[_command]` from `str` to `str | tuple[str, ...]`. Strings pass through for legacy comma-separated syntax; tuples use compact JSON-array encoding. Decode multi-value arrays strictly, preserving order and duplicates and distinguishing null from empty.

Alternative: add a public `PropertyType` enum or a generic recursive JSON type. Rejected because upstream types are intentionally open and recursive objects are not valid values for these reviewed property kinds.

### 3. Treat workflow behavior as server-owned, with additive project identity

Add `workflow_id: str | None` to the existing project wire/entity, defaulting omission to `None`. Keep issue create/status/update/project-move signatures and command construction unchanged. Extend fixtures and result assertions to prove the server-owned validation, status remap, assignment, and run-handoff outcomes; surface conflicts once without retry or simulation.

Alternative: introduce workflow resources or client-side status mapping. Rejected because 0.6.3 has no public workflow CLI and local replication would drift from the authoritative transaction.

### 4. Add daemon commit as one optional decoded field

Add `cli_commit: str | None` to `DaemonStatus` and normalize omitted, null, and empty legacy values to `None`; preserve a nonempty full SHA. Reuse the existing daemon status resource and decoder.

Alternative: add a separate version/identity model or command. Rejected because the field is additive output of the current command.

### 5. Reuse exception and redaction boundaries

Represent wakeup diagnostics, upload failures, and stable 500 messages through existing command exceptions, redaction, and partial-side-effect behavior. Add source-linked fixtures and exact assertions instead of response-specific exception classes.

Alternative: create new diagnostic exception types. Rejected because callers need stable actionable context, not a parallel hierarchy.

### 6. Keep verification layered and evidence external

Implement exact table rows in existing unit/contract/component suites, extend live smoke only for cross-component behavior that lower layers cannot prove, and preserve all runtime outputs/images in Multica comments. Git contains reusable scripts/fixtures only when needed for the verified function, never captured evidence.

Alternative: add a bespoke E2E harness. Rejected because current fake CLI, contract checks, package tests, and protected live workflow already cover the required layers.

## Ponytail Gate

No new subsystem is required. The only plausible additions were a workflow client, property enum/conversion layer, daemon identity service, diagnostic exception hierarchy, and E2E framework; existing approved-contract, resource, wire-model, exception, and test-table mechanisms cover each need, so all are removed from scope.

## Risks / Trade-offs

- [Draft overlap] PR #101/#103 may later publish overlapping code → implement from exact main, compare behavior only, and resolve future overlap through normal review rather than dependency.
- [Open upstream strings] property types may grow again → preserve open string types and validate only the reviewed value shape.
- [Legacy decoder variation] 0.6.0/0.6.1 output omits new fields → defaults and explicit legacy fixtures prevent accidental minimum-version inflation.
- [Server-owned workflow semantics] offline fixtures cannot prove a real transaction → combine exact fixture coverage with a narrowly scoped independent live walkthrough after human approval.
- [Evidence leakage] source/audit/live material can contain private paths or hosts → stage outside Git, sanitize only publication copies, attach through Multica, and audit tracked/package contents.

## Migration Plan

1. Update the approved contract from the exact 0.6.1 baseline using the pinned 0.6.3 source and verified release identities.
2. Refresh deterministic generated output, then implement the bounded handwritten model/resource/decoder changes.
3. Extend existing case tables, focused live smoke coverage, compatibility documentation, and package claims.
4. Run all offline gates at one clean candidate SHA; after human authorization, collect independent live evidence against exact CLI 0.6.3.
5. Roll back the contract, generated output, handwritten changes, fixtures, tests, and documentation together if any mandatory gate fails.

## Open Questions

None. Workflow-management endpoints remain outside the SDK and daemon autostart remains deferred; changing either decision requires a new approved OpenSpec revision.
