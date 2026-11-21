## Context

The repository at planning base `b268e3bec0436fe51727fda50583344f57663284` approves Multica `0.7.1` and generates one committed runtime projection from `contracts/sdk-contract.json`. Existing source seams already separate the approved contract, deterministic renderer, explicit typed resources, private wire structs/decoders, shared transport errors, frozen operation cases, compatibility policy, and ordinary CI/package gates.

The verified target is Multica `0.11.1` release `451169000` at `e1fe10d6694848e35dd1aa00e08cd11d93e545ac`. The direct audit expands help from 209 to 263 nodes, finds 55 additions, one removal, 31 changed nodes, and closes all 196 supported response work items as 102 changed and 94 unchanged. Release notes do not provide a breaking/migration guarantee, so pinned source and verified binary evidence remain authoritative.

## Goals / Non-Goals

**Goals:**

- Advance one approved contract and generated projection directly from `0.7.1` to `0.11.1` with exact provenance and source links.
- Adapt every changed retained SDK operation through current models/resources/adapters and close every command/response decision with tests and documentation.
- Preserve stable public method names where the operation remains supported, including mapping `IssueResource.rerun` to target `issue rerun-task`.
- Preserve the proven compatibility floor and existing validation/error/packaging architecture.
- Produce exact-revision offline and CI evidence suitable for independent verification.

**Non-Goals:**

- Publishing chat wakeups, inbox, issue batch/delete/PR linking, issue-status, view, workflow, project-management, runtime-concurrency, or other newly discovered families.
- Adding HTTP bypasses, a second transport, runtime dispatch registry, compatibility registry, generator, validation framework, dependency, or E2E framework.
- Treating release notes, extractor output, or source similarity as automatic public API approval.
- Materializing WP children, running implementation, or opening an implementation PR before human approval. After READY, Plan Verifier may create exactly one child `implementation_parent` in `backlog` with `human_review=pending`; that pending parent is the handoff record, not authorization to execute the DAG.

## Decisions

### 1. Keep the approved contract as the only promotion boundary

All 263-node and 196-response decisions are encoded in `contracts/sdk-contract.json`; only that reviewed file may feed the existing renderer. Evidence in `.devlocal/upstream-contract/v0.7.1..v0.11.1/` remains ignored. Validator extensions SHALL enforce exact counts, unique identities, allowed dispositions, pinned source commits, and row closure before render.

Alternative: generate bindings directly from the reconciled collector manifest. Rejected because extractor evidence includes candidates and unresolved policy; direct generation would bypass human API decisions.

### 2. Preserve the public surface and defer candidate families

The 94 unchanged rows retain regression fixtures. The 102 changed rows adapt existing resources/models/adapters only. New families remain deferred because discovery proves availability, not durable Python naming, value, or compatibility. The five source-only names are closed explicitly: `multica` and `probe-runtimes` are non-surface; `doc` and `environment` are deferred; hidden `rerun` is non-surface.

Alternative: publish every new help node for CLI parity. Rejected because it would add large unreviewed public families and response contracts outside the current 196-operation registry.

### 3. Migrate existing rerun behavior without a compatibility fallback

`IssueResource.rerun(issue_id)` and its command sibling retain their Python signatures and action result, but the governed argv changes from removed `issue rerun` to supported `issue rerun-task`. Contract rows, generated bindings, canonical vectors, docs, and negative discovery assertions move atomically.

Alternative: probe the CLI and fall back to `issue rerun`. Rejected because the target removed the public command, runtime branching would weaken deterministic plans, and older compatibility is already governed by the package's version preflight.

### 4. Adapt presence-sensitive behavior through current typed seams

Changed response rows update existing private wire structs, public models, adapters, and frozen cases. Omission, null, empty, unknown-open-enum, pagination, and malformed-wire behavior stay explicit. Squad assignees, payload conditions, `run_outcome`, `daemon_id`, workspace `pinned_at`, text-channel semantics, NUL sanitization, and 400/409/413 errors use existing discriminators, presence sentinels, page abstractions, content helpers, and exception classes.

Alternative: create version-specific `v011` models/resources. Rejected because the SDK already has additive optional/open-value policies and explicit adapters; parallel models would duplicate the whole supported surface.

### 5. Preserve the compatibility floor and advance the ceiling

`min_cli_version` remains `0.6.2`; `0.11.1` becomes maximum tested and `0.11.2` the exclusive ceiling. Existing operation-level minimums remain unless exact source proves a later requirement. Documentation describes direct `0.7.1` to `0.11.1` migration without requiring intermediate SDK releases.

Alternative: raise the minimum to `0.11.1`. Rejected because the evidence establishes target changes but does not prove that every retained older operation must be dropped.

### 6. Verify at the lowest sufficient deterministic layer

`e2e_required=false`. Contract/source validation proves inventory decisions; unit and contract tables prove mappings/models/presence; fake-CLI component tests prove command/error boundaries; controlled fixtures prove pagination and atomic behavior; type/lint/package jobs prove distribution. No acceptance result requires a live backend, browser, persistent identity, or visible-output screenshot.

Alternative: add a dedicated live upgrade runner. Rejected because it would duplicate lower-level assertions while requiring private stand state and would not improve proof of deterministic contract generation.

### 7. Ponytail full scope gate

Every planned production change is tied to a changed contract row or compatibility risk and reuses an existing path: contract validator/renderer, explicit resources, wire adapters, shared errors, case tables, docs, or existing CI. Duplicate registries, wrappers, new families, speculative enum closures, and intermediate-version delivery phases are omitted.

## Risks / Trade-offs

- **Wide direct range can hide an unclassified delta** → Require exact 263-node, 31-changed-node, five-source-only, and 196-response closure with mutation/negative validation.
- **Keeping open values reduces static exhaustiveness** → Close only SDK-owned enums; preserve target-owned unknown strings and test malformed wire types separately.
- **Preserving the `0.6.2` floor increases regression breadth** → Retain existing compatibility cases and operation-level gates; do not claim behavior outside reviewed rows.
- **Issue text sanitization differs from local argv NUL rejection** → Test command-channel behavior and target persistence semantics separately so one boundary does not masquerade as the other.
- **Long complete suites can exceed the workspace limit** → Run focused checks locally and the unsplit complete suite in GitHub Actions on the published exact revision when expected to exceed ten minutes.
- **Deferred families may be valuable later** → Preserve their reviewed dispositions and source evidence, but require a separate OpenSpec public-API decision.

## Migration Plan

1. Extend the approved contract schema/validation data with exact target provenance, all command/source-only decisions, and the closed 196-row response registry.
2. Validate and render through the existing pipeline; prove double-render byte stability and no `.devlocal` dependency.
3. Adapt current bindings, wire/public models, decoders, errors, pagination, and content semantics for changed retained rows; atomically replace rerun argv.
4. Extend existing frozen cases and focused lifecycle/component tests, then update compatibility, API, migration, coverage, changelog, packaging, and release documentation.
5. Run focused local gates and publish the exact revision; run any expected-over-limit automated suite unsplit in GitHub Actions.
6. Have an independent Tester inspect row/scenario coverage from a fresh checkout, verify remote SHA and CI, and publish sanitized evidence with read-back in Multica.
7. Roll back by reverting the implementation commit set and restoring the `0.7.1` approved contract/projection; no persisted user data migration is required.

## Open Questions

None. New command families remain deferred, target-owned future values remain open, the proven compatibility floor is preserved, and implementation stops at the human approval gate.
