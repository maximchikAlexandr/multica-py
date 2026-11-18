## Context

The repository at planning base `b268e3bec0436fe51727fda50583344f57663284` approves Multica `0.7.1` in contract blob `41a551bca2f5e2d63bd6b7404c5fa1e6dc647ecf`, source commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, with `max_tested_cli_version=0.7.1`. The target is stable Multica `0.10.0`, release `446890529`, source/tag commit `2fcb424b72b024f65161809081009063846ea44d`, published `2026-11-16T10:30:22Z`.

The reviewed direct range contains `209` baseline and `246` target CLI nodes (`38` added, `1` removed, `26` changed) and closes all `196` supported response entrypoints (`94` changed, `102` unchanged, zero pending). Verified Darwin/arm64 archives have SHA-256 `a1f78965984fa0eacff331d67360da2cfc8298e9e97d5f136000b3e8682b1c9b` and `ddf7a6f7f59f90bf844edff92428e45affa0a80a40b93bed86ab9218d297c9f7`; extracted executables have SHA-256 `f167df5161555d8696a996be8fedfde8ab1cbad27c419c9a7905b23492ad9350` and `459eeca0af331b137155370651e944269dfa5a99fbe248d67c32616a03826905`.

Evidence is review-only. The existing approved contract, deterministic generator, resource/entity/wire adapters, shared transport/errors, and frozen operation tables are the implementation seams. This planning change edits no production code, approved contract, generated projection, tests, or main specs.

## Goals / Non-Goals

**Goals:**

- Define one direct `0.7.1` to `0.10.0` upgrade with exact release, source, archive, executable, command, and response provenance.
- Adapt every proven retained public operation with backward-compatible omission/null handling, open upstream values, malformed-payload rejection, and typed errors.
- Replace the removed issue-targeted rerun mapping with the proven run-targeted command and explicit migration guidance.
- Keep generation deterministic and make every contract decision traceable to pinned source and table-driven tests.
- Provide reproducible offline, CI, and isolated-stand verification without committing evidence artifacts.

**Non-Goals:**

- Automatically exposing all commands added between `0.7.1` and `0.10.0`.
- Publishing issue batch/delete/status, workflow, project workflow/member/archive/restore, saved-view, runtime-concurrency, PR-link, or other deferred families without a separate approved API contract.
- Generating from collectors, release notes, source diffs, binaries, or response-review JSON.
- Adding another generator, transport layer, compatibility registry, E2E framework, runtime dependency, or implementation work during planning.

## Decisions

### 1. Advance one approved contract across the direct range

Update the existing contract lineage from exact `0.7.1` to exact `0.10.0`, append release/binary provenance, set maximum tested to `0.10.0`, and derive the exclusive upper compatibility boundary from the repository's existing policy. Every changed operation SHALL retain baseline and target full-SHA source URLs, normalized argument/flag constraints, RunE/helper destinations, response/error actions, and test references. The existing validate/render/check commands remain the only promotion path.

Alternative considered: merge intermediate release contracts or generate from the gap audit. Rejected because the issue authorizes one direct range and evidence cannot approve Python names, presence semantics, or public coverage.

### 2. Adapt retained models at existing wire boundaries

Use existing frozen public models, wire structs, entity binders, page types, and decoders. Add only proven fields and semantics: task/attachment/comment-resolution additions; project activity/archive/list pagination; issue requester; inherited subscriber coverage/delivery; runtime/user/workspace additions; private-project omission/redaction; and changed cancellation/error behavior. Legacy omissions SHALL decode compatibly, explicit null SHALL remain distinct where source proves it, malformed present values SHALL fail typed decoding, and upstream-owned enums SHALL remain open.

Alternative considered: versioned model subclasses or a `0.10` response layer. Rejected because it duplicates current adapters and would force callers to branch by CLI version.

### 3. Migrate rerun to the real run-targeted command

Remove the `issues.rerun(issue_id)` command mapping because target CLI no longer exposes `issue rerun`. Add a run-targeted `rerun_task` operation using the existing issue/task-run resource seam, with required task/run identity, resume-versus-fresh input, typed result, standard error decoding, and positive/negative command cases. Documentation SHALL identify the replacement and SHALL NOT retain a compatibility alias that silently changes identity semantics.

Alternative considered: keep `rerun` as an alias or infer the latest run from an issue. Rejected because either invokes a nonexistent command or introduces an unproven lookup/race policy.

### 4. Fail closed on unapproved new command families

Record every added/source-only name in the approved inventory, but mark issue batch/delete, issue-status, workflows, project workflows/members/archive/restore, views, runtime concurrency, PR link/unlink, and other unapproved families `defer`. Hidden `rerun` and `probe-runtimes` remain non-public; attached-but-omitted `environment` remains deferred. No deferred node receives a public symbol, binding, fixture that implies support, or documentation example.

Alternative considered: expose read-only subsets immediately. Rejected because naming, pagination, membership visibility, confirmation, partial success, and error policy are contract decisions rather than mechanical mappings.

### 5. Preserve target text, metadata, webhook, and destructive safety semantics

At existing command builders and transport/error boundaries, inline text SHALL remain literal, file/stdin channels SHALL preserve content except one trailing LF, explicit empty SHALL differ from omission, and explicitly false stdin selectors SHALL omit the field. Metadata paths SHALL be escaped as one segment. Webhook trigger filters SHALL enforce target requires/conflicts rules before I/O. Cancellation status `499` with no body, private membership not-found/omission, archived-project `409`, and bounded runtime-delete conflicts SHALL map through existing typed errors without destructive retry or follow-up.

Alternative considered: normalize these behaviors in a generic string or HTTP wrapper. Rejected because their presence and safety rules are operation-specific and existing builders already own them.

### 6. Ponytail full gate

Each material addition has a requirement or unique risk and an existing seam: approved facts use `contracts/sdk-contract.json` and `scripts/upstream_contract.py`; model changes use `src/multica_py/models`, `entities`, and `_internal/*_wires.py`; command behavior uses `resources`; process/error behavior uses `_internal/transport.py` and `exceptions.py`; tests use existing `ArgvCase`, `CommandCase`, decode tables, and live-smoke facilities. A second registry, API version layer, wrapper hierarchy, test DSL, or dependency has no separate risk to solve and is excluded.

### 7. Isolated E2E closes real process/auth boundaries

`e2e_required=true`. Lower-level tests prove deterministic argv, decoding, and validation, but cannot prove the combined `multica-test` process, isolated profile/daemon, membership-only private visibility, no-body cancellation, literal file/stdin handling, and bounded destructive failures against the target stand. Implement one repository-native script, `scripts/e2e_multica_010.py`, using only public SDK calls and disposable resources. It SHALL accept stand/profile inputs without embedding private URLs or credentials, record tested product and test-code revisions, sanitize output, and clean up failure-safely.

The independent Tester SHALL use the project test repository context and dedicated `multica-test` profile/daemon, never the primary Multica profile or daemon. CI SHALL extend the existing exact-PR-head live workflow to require observed `0.10.0`; CI tests/fixtures are implemented with product work, while the Tester only verifies coverage and reports findings. No before/after PNG is required because public terminal tables, logs, progress, summaries, and browser UI are unchanged; machine-readable outputs and manual observations are sufficient.

## Risks / Trade-offs

- **Wide multi-release diff can hide SDK-relevant behavior** → Require exhaustive `209→246` inventory and `196/196` response closure with full-SHA source links.
- **Additive fields can break strict decoders or erase absence meaning** → Use explicit wire presence, legacy fixtures, null/omitted/present/malformed cases, and open enums.
- **Rerun migration can target the wrong identity** → Remove issue-targeted inference and require the exact task/run identifier accepted by `rerun-task`.
- **Private-project evidence can leak identities or endpoints** → Use disposable stand data, sanitize artifacts, and publish evidence only in access-controlled Multica comments.
- **Text and metadata normalization can corrupt user input** → Assert inline/file/stdin/empty/omitted cases and path escaping at the command boundary.
- **Destructive errors can invite unsafe retries** → Fail closed before transport where possible and treat proven `409`/bounded conflicts as terminal typed errors.
- **Full automated verification may exceed ten minutes locally** → Stop only the owned automated test process at ten minutes and run the unsplit suite in GitHub Actions on the published exact revision.

## Migration Plan

1. Update and validate the approved contract with exact provenance, complete command/response reconciliation, reviewed dispositions, compatibility bounds, and source/test references.
2. Render the existing generated projection and prove byte-stable check mode from the approved contract alone.
3. Adapt existing model/resource/transport seams, replace rerun mapping, and add table-driven positive/negative fixtures without publishing deferred families.
4. Update compatibility, API, migration, coverage, changelog, contribution, packaging, and release documentation.
5. Run focused offline gates locally; run any automated suite expected to exceed ten minutes in GitHub Actions at the exact published revision.
6. Execute the isolated target-stand script and independent manual walkthrough, publish sanitized evidence in Multica with read-back, and preserve the evidence branch/MR/commits while cleaning stand data.
7. Roll back by reverting the implementation commits and restoring the `0.7.1` contract/projection; no persisted SDK data migration is introduced.

## Open Questions

None. New command families remain deferred rather than leaving API design choices to the implementer.
