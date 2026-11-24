## Context

The exact SDK planning base is `b268e3bec0436fe51727fda50583344f57663284` (tree `6fb22297ab62a86b591dc058fdc7a03b107c97fd`). Its approved contract targets Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`. The target is stable Multica `0.12.1`, release `455946845`, at `fc8028d761707b506cec498385f31fcebbbff598`. Verified binary-help evidence expands the command tree from `209` to `276` nodes and the pinned source review classifies all `196` supported response entrypoints, of which `118` require adaptation.

The repository already has the required seams: one human-approved JSON contract, one deterministic Python projection, typed resource/model/decoder layers, frozen operation case tables, fake-CLI component fixtures, gated live smoke tests, and Make/CI release gates. The change must use those seams. Collector evidence, release notes, and source diffs inform review but never generate production behavior directly.

## Goals / Non-Goals

**Goals:**

- Define one direct `0.7.1` to `0.12.1` upgrade with exact source, release, archive, executable, help-tree, and response provenance.
- Preserve the existing `0.6.2` floor, set maximum tested to `0.12.1`, and fail closed at the exclusive `0.12.2` ceiling until another review.
- Give every target command and supported response exactly one policy decision and corresponding implementation/test/doc action.
- Replace removed `issue rerun` with typed `issue rerun-task` while keeping deferred upstream families out of the public SDK.
- Prove presence, nullability, open-enum, pagination, conflict, replay, redaction, cancellation, and typed-error semantics at the lowest sufficient layer, with narrow isolated live checks only where server interaction is material.

**Non-Goals:**

- Intermediate deliveries for `0.7.2` through `0.12.0`.
- Automatic exposure of all 68 added commands or the eight source-only names.
- A second contract format, generator, compatibility registry, transport, test runner, or UI automation framework.
- Public support for deferred Inbox, View, Workflow, quick-action, batch/status-management, project-management, chat-wakeup, `doc`, or `environment` families.
- Committing collector evidence, archives, binaries, logs, screenshots, diagnostic JSON, hashes, or environment-specific output.

## Decisions

### 1. Preserve one compatibility lineage and fail closed after the reviewed target

The approved contract will preserve `min_cli_version=0.6.2`, set `max_tested_cli_version=0.12.1`, and use `0.12.2` as the exclusive ceiling. The complete direct interval remains auditable through the exact `0.7.1` baseline and `0.12.1` target source/artifact identities.

The alternative of raising the floor to `0.7.1` is rejected because the dossier proves changes above the floor but does not prove that already-supported `0.6.2` callers must be dropped. An open-ended ceiling is rejected because upstream releases after `0.12.1` have not been reviewed.

### 2. The approved JSON contract owns every inventory and response decision

`contracts/sdk-contract.json` will account for all 276 target nodes, all baseline nodes, every argument/flag/default/alias/presence rule, the eight source-only names, and all 196 supported response rows. Every item receives a closed disposition and exact source/test references. Validation will reject mismatched totals, pending rows, duplicate identities, unresolved mappings, mixed provenance, or production generation from evidence.

The existing render/check path remains the only generator path. The committed Python projection is refreshed once from the approved contract; transient projections remain outside Git.

### 3. Add only the reviewed replacement operation

The public `IssueResource.rerun`/bound equivalent and `issues.rerun` contract row will be removed because target public help removes `issue rerun`. The SDK will add `rerun_task`/`rerun_task_command` on the existing issue resource and bound issue using target `issue rerun-task` arguments, optional values, presence rules, result model, and typed errors. Migration documentation will identify the replacement and the direct-upgrade behavior.

All other added command families stay `defer` unless already represented by an approved operation that merely needs adaptation. Hidden or ungrouped commands remain non-SDK-surface. This keeps the change limited to one replacement rather than turning an upstream inventory refresh into an unreviewed API expansion.

### 4. Adapt responses in existing domain seams

Changed responses will be implemented in the existing resource/model/decoder locations and frozen case tables. The design groups them by ownership, not by intermediate release:

- shared command/wire/transport foundation: target structs and decoding helpers in `src/multica_py/_internal/wire_models.py` and `src/multica_py/_internal/decoders.py`, reusable presence/constraint and literal-content primitives, and sanitized 400/409/413/499 handling in `src/multica_py/_internal/transport.py` are completed once before parallel domain work;
- issue state: `rerun_task`, issue `description_revision`, issue merge conflicts, and issue-local command validation;
- collaboration state: comment replay/idempotency, project progress/activity projections, skill revision/base-revision conflicts, all workspace response changes including guest membership/project visibility, requester/subscriber and status payload changes outside the issue resource;
- operational state: configuration limits, daemon log controls, runtime/profile fields, usage windows, autopilot/run outcome, attachment dimensions, and other approved retained operation changes;
- shared boundaries: pagination, omission versus explicit null/false/zero/empty, unknown valid upstream values, and standard 400/409/413/499 error decoding.

The implementation will extend current frozen models or introduce the smallest domain type required by an approved response. Stage-2 packages consume the predecessor command/wire/transport foundation and SHALL NOT edit its shared files. Each domain package applies only its own reviewed builder constraints and mappings. Central public-operation discovery and shared test registries are reconciled only by the stage-3 integrator after all domain packages finish. It will not add version-specific wrappers. Open upstream-owned strings remain open; closed SDK enums change only when the approved contract names the exact values and compatibility policy.

### 5. Presence, conflict, replay, and redaction are first-class contracts

Patch-style inputs will use the repository's existing unset/presence mechanisms so omission remains distinct from `None`, empty string, zero, and `False`. Revision-aware issue/comment/skill operations will preserve explicit expected/base revision behavior and map stale writes to the centralized typed conflict. Comment replay will require stable idempotency identity and no duplicate logical comment. Guest projections will expose only target-authorized fields and must not leak `project_ids` to guest callers.

Cancellation status 499 and retained 400/409/413 behavior continue through the shared sanitized typed-error boundary. No domain adapter may bypass shared transport error decoding.

### 6. Verification uses existing layers plus four narrow live cases

Unit/contract tests own exact argv/body/model/error matrices. Fake-CLI component tests own cross-resource decoding, pagination, and deterministic conflict/replay fixtures. Existing source-link, contract, typing, lint, package, documentation, and operation-completeness gates remain authoritative.

Four material gaps require the isolated project stand because a fixture alone cannot prove real target CLI/server interaction: issue description revision conflict, comment idempotent replay, skill base-revision conflict, and guest/project-progress visibility. A reusable gated live module under `tests/live/` will extend the existing `prepared_client` harness and its `MULTICA_LIVE_*` configuration. `tests/live/conftest.py` will change its exact prepared target from `0.7.0` to `0.12.1`; `tests/live/README.md` will document the existing five variables plus a guest profile and a dedicated resettable guest-visible project. The non-guest owner creates UUID-named run-owned issues in that same prepared project, both actors read the same project/workspace state, and cleanup deletes those issues and proves the prepared project returned to its empty baseline; membership and the prepared project are never mutated. `.github/workflows/live-smoke.yml` will receive an explicit target-`0.12.1` disposition. Local execution binds `MULTICA_LIVE_CLI=multica-test`, the isolated `multica-test` profile/daemon, the prepared workspace, and UUID-derived test names. It will not use the primary Multica profile or daemon and will not introduce a second runner or configuration namespace. Tester uses a fresh checkout and the existing live namespace/cleanup pattern.

The SDK consumes JSON and this change does not intentionally alter human-visible terminal tables, logs, progress, summaries, or browser UI. Before/after PNGs are therefore not required. If implementation changes visible output, verification stops until a planning revision defines baseline/candidate text and real Mac PNG capture with a confirmed renderer.

### 7. Delivery is exact-SHA and evidence stays outside Git

Implementation and test commits follow natural durable results. The published candidate is pushed normally; local HEAD and remote branch SHA must match before independent verification. Automated local suites expected to exceed, or reaching, ten minutes move unsplit to GitHub Actions on that exact revision. Tester publishes commands, exits, assertions, links, provenance, and any actual images/logs only to Multica and reads the comment/attachments back. Cleanup removes only run-owned local stand data and diagnostics; it preserves branch, commits, CI links, and Multica evidence.

## Risks / Trade-offs

- The `118` changed response rows span many domains. A single contract/command/wire/transport predecessor owns shared schemas, validation primitives, decoders, and typed errors; central registries wait for integration; disjoint issue, collaboration, and operational packages own all remaining domain files.
- Preserving the `0.6.2` floor increases regression scope. Existing operation-level compatibility gates and frozen baseline fixtures constrain that risk.
- Replacing `rerun` is a public compatibility change. The removal is unavoidable against target public help, so migration docs and a focused replacement operation are preferred over retaining a broken command or exposing the hidden compatibility node.
- Live conflict/redaction checks depend on isolated stand readiness and permissions. A readiness gate blocks attempt consumption; unavailable required infrastructure is reported as unverified rather than converted into a fixture-only PASS.
- Source review remains the authority where release notes omit migration details. Exact pins and link audits reduce drift but do not make later releases implicitly compatible.

## Migration Plan

1. Land the complete approved contract and deterministic generated projection.
2. Adapt the replacement command and changed domain responses with focused lower-level tests.
3. Update documentation and CI source pin, publish one candidate revision, and run required offline/CI gates.
4. Run the isolated live cases and independent exact-revision review; publish and read back Multica evidence.
5. Release documentation directs users from `issues.rerun(...)` to `issues.rerun_task(...)` and describes revision/conflict and guest visibility semantics.

Rollback reverts the implementation/test/documentation commits and restores the prior approved `0.7.1` contract/projection. No persisted SDK data migration is introduced.

## Open Questions

None. Added families not explicitly approved here are deferred, and the compatibility/deprecation, E2E, evidence, and rollback policies are fixed by this design.
