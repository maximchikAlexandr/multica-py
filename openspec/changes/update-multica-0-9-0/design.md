## Context

The planning base is `b268e3bec0436fe51727fda50583344f57663284`, whose reviewed `contracts/sdk-contract.json` targets Multica `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` and records `0.7.1` as the maximum tested CLI. The target is stable Multica `0.9.0`, release `444052572`, commit `8cd8a2db978d532d8627c78cd29f05deab6c6f17`. The verified Darwin/arm64 target archive has SHA-256 `107cfffef0ff871388d9ec7110f664f6e90392cf9bba92b0bdea672d7fa9f343`; its extracted executable has SHA-256 `2c11ee05872013453fab87872188ccaea3af4f81d3f6cb5848c57726ae4eaa10` and reports Go `1.27.4`.

The direct range changes the verified CLI inventory from 209 to 236 nodes: 28 added, one removed, and 18 changed. The reviewed response dossier contains 196 unique baseline entrypoint verdicts (88 changed and 108 unchanged) with no pending row. Evidence, verified binaries, collector output, and review JSON are untracked; only the reviewed approved contract can affect generation.

The existing implementation already supplies the required seams: contract validation/render/check in `scripts/upstream_contract.py`, the generated projection in `src/multica_py/_generated/approved_sdk.py`, explicit resources/models and shared wire decoders, subprocess classification, table-driven `ArgvCase`/`DecodeCase`/`CommandCase` coverage, and repository CI/package/live-smoke gates. These seams are reused rather than replaced.

## Goals / Non-Goals

**Goals:**

- Encode the complete reviewed `0.7.1` to `0.9.0` provenance, command dispositions, response verdicts, mappings, compatibility policy, and test references in one approved contract.
- Adapt retained public operations and typed projections for every mandatory response and error-semantic change while preserving older-server omission compatibility.
- Replace the removed issue-targeted rerun mapping with the proven run-targeted resume/fresh operation and an explicit migration path.
- Prove exact argv, destination, presence, malformed-shape, authorization, cancellation, generation, documentation, packaging, and release behavior through existing test and CI layers.
- Publish implementation and verification only on an exact reviewed revision; planning itself changes no production code or main spec.

**Non-Goals:**

- Public SDK methods for issue-status administration, workflows, project workflows/members, saved views, runtime concurrency, issue deletion, hidden `probe-runtimes`/`rerun`, unattached `environment`, daemon watchdog/force, UI, Desktop, themes, or messaging-only changes.
- Automatic promotion from extractor output, command similarity, release notes, or response evidence.
- A new generator, model framework, transport layer, test framework, runtime dependency, or separate intermediate-release delivery.
- Implementation, live verification, merge, or release during planning.

## Decisions

### 1. Keep one reviewed contract as the promotion boundary

The implementation SHALL update `contracts/sdk-contract.json`, validate every changed command mapping through `RunE` and helpers, render the existing generated module, and compare a second render byte-for-byte. Each command row records positional arity, local/inherited flags, defaults, aliases/deprecation, required/conflict/presence rules, destination, disposition, source, and tests. Each of the 196 response rows records model/error/fixture/doc action and pinned source.

Alternative: generate directly from the verified inventory and response review. Rejected because those artifacts prove facts but do not approve public naming, enum policy, destructive behavior, compatibility, or migration.

### 2. Adapt retained surfaces and defer all optional command families

The public surface grows only where a retained operation needs a proven field or the removed `issue rerun` command needs its reviewed replacement. New command families remain `defer`, destructive issue deletion remains `defer`, and source-only commands remain `not_sdk_surface` or `defer` as recorded. No optional family is left for the implementer to decide.

The existing explicit resource/model architecture is sufficient for retained operations. It is insufficient without edits because current issue rerun emits `issue rerun <issue-id>`, existing wire structs do not represent all 0.9.0 fields/presence states, and current compatibility/source links stop at 0.7.1.

Alternative: expose every public 0.9.0 CLI node for parity. Rejected because public naming, presence, error, pagination, destructive, and lifecycle contracts for those families are not approved by this change.

### 3. Preserve presence and open-value behavior at wire boundaries

Additive fields use optional/nullable wire members and stable public projections. Fixtures cover present, omitted, explicit null where upstream permits it, and malformed type. Open server vocabularies remain strings or existing open-value wrappers; no closed enum is introduced from observed examples. Private-project reads preserve proven 404/omission/redaction behavior, and relationship create/update validation completes before transport.

Alternative: decode new payloads into untyped mappings. Rejected because it bypasses the SDK's typed contract and moves malformed data into callers.

### 4. Make rerun migration explicit and run-targeted

Remove the false issue-targeted CLI mapping and add explicit typed command/eager methods that emit `issue rerun-task <run-id>` with reviewed resume/fresh mode inputs and decode the typed result. Migration documentation maps the old call to the run identifier already available from issue runs/task projections. No alias may silently reinterpret an issue id as a run id.

Alternative: retain `issues.rerun(issue_id)` as a compatibility alias. Rejected because upstream removed the command and the identifier and lifecycle semantics differ.

### 5. Reuse shared transport and decoder seams for cancellation and runtime failures

The common transport/error path recognizes the proven 499 cancellation/no-body outcome without attempting JSON decoding and keeps normal non-zero runtime-update failures observable. Literal argv, file/stdin, prevalidation, atomic attachment binding, and cleanup behavior stay in existing command/resource helpers.

Alternative: special-case cancellation and runtime update inside each resource. Rejected because it duplicates classification and risks inconsistent eager/preview behavior.

### 6. Verify with lower layers plus focused protected live smoke

Contract, unit, component, packaging, and CI checks prove deterministic mappings, wire shapes, authorization semantics, 499/no-body cancellation, and failures. Pinned `0.9.0` has no safe deterministic public action that forces the server-side 499 path, so that path remains a required exact fake-CLI/process fixture and is not claimed as live evidence. A focused protected exact-SHA live smoke is required only for the reproducible real CLI/backend boundaries: `rerun-task` lifecycle, private-project behavior, project-inherited subscriber provenance, safe update of the reserved nonexistent runtime identifier, and exact usage window. It reuses `.github/workflows/live-smoke.yml`, `scripts/e2e/verify_multica_test.py`, and the project test stand; it does not add a second E2E framework, add project visibility mutation to the candidate SDK, or mutate the prepared runtime.

Run-created resources use an administrator-owned fixture helper around the pinned CLI. Private project creation and all permanent issue deletion stay outside the candidate SDK. Before any CLI or SDK create mutation, the helper durably `fsync`s a globally unique intent title/marker to a protected persistent journal. A post-commit interruption is recovered by exhaustive exact title/marker/parent reconciliation; returned IDs move intents to registered normally. Fixture `finally` and workflow `if: always()` cleanup cancel active tasks, delete issues before projects, verify issue/run/project absence, and retain only unresolved evidence. The private project explicitly includes the verified primary user and excludes the denied user. Project deletion alone is insufficient because the server detaches issues rather than deleting them.

Alternative: declare all behavior lower-level-only. Rejected because the remaining gaps depend on authorization filtering and server-owned lifecycle state. Conversely, forcing 499 live coverage was rejected because no public deterministic trigger exists; inventing a backend fault hook would expand product scope.

## Risks / Trade-offs

- [Large reviewed contract delta introduces transcription drift] → require 236/236 command accounting, 196/196 response verdict uniqueness, exact source-link audit, canonical vectors, and repeated byte-stable rendering.
- [Additive fields differ between 0.7.1 and 0.9.0 servers] → model omission separately from null and retain fixtures for both versions.
- [Rerun migration breaks callers] → make removal and replacement explicit, retain no misleading alias, and provide compiling migration examples.
- [Private-project tests leak identity or private URLs] → use isolated disposable test data, sanitize evidence, and publish raw outputs only as access-controlled Multica attachments.
- [Live checks consume mutable state or exceed the local test limit] → use the isolated `multica-py-e2e-062` stand, readiness gate, bounded focused cases, persistent intent journal with normal/pending recovery probes, issue-before-project cleanup plus absence checks, and GitHub Actions for automated suites expected to exceed or reaching ten minutes.
- [Concurrent package work conflicts in shared contract/generated files] → topology places those files in one foundation predecessor and reserves shared integration/docs/CI repairs for a final package.

## Migration Plan

1. Update and validate the approved contract at the exact pinned target; render and review the generated projection.
2. Adapt retained resources/models/decoders/transport and table-driven fixtures without exposing deferred families.
3. Replace issue rerun with run-targeted rerun-task and update exports, examples, migration, compatibility, and API documentation.
4. Run focused checks, then the repository gates under the ten-minute local-suite rule; publish the exact revision normally.
5. Run independent exact-SHA verification and the authorized protected live cases; publish commands, exits, links, assertions, and images in Multica and clean only run-owned stand data.

Rollback is a normal revert of the implementation commit set and generated projection together. The approved contract and generated file SHALL never be rolled back independently.

## Open Questions

None. Optional new command families and destructive issue deletion are explicitly deferred and require a separate approved OpenSpec change.
