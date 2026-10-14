## Delivery contract

- Planning issue: `MYL-474`
- Change: `update-multica-0-6-2`
- Graph revision: `2`; supersedes graph revision 1 without replacing or restarting `WP-1`.
- Approved base: `6ef02a4b0f879cd4d5726433a803745fe57be547`
- Revision parent: `c16423beb6cba18c5d824967b429dc4db8d592fa`
- Target branch: `feat/MYL-474-update-multica-0.6.2`
- Implementation gate: the recorded human approval for the `0.6.2` upgrade remains applicable because revision 2 makes the already-approved pre-I/O validation contract implementable through one additive optional discriminator. WP-1 SHALL remain paused until revision 2 receives independent planning verification and Manager records the revised SHA; no new child or restart is authorized.
- Estimate source: the authoritative `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours` custom properties on the planning issue. Numeric totals are intentionally not duplicated here.
- Confidence: medium. The public delta is bounded and evidence is already reconciled, while the large approved contract and exhaustive registry checks make mechanical-edit and integration variance material.
- Calibration: estimate includes implementation, table-driven tests, deterministic regeneration, docs, packaging, full offline gates, and review fixes; it excludes planning already completed, CI queue time, and deferred daemon autostart.
- Non-authoritative candidate: `adc56e3cb9a7c057f5b71efa1e120a073941df77` is rejected diagnostic evidence only. It SHALL NOT be merged, treated as the implementation base, or credited as completed OpenSpec work; useful inspected code/tests can be re-authored only against the approved revision SHA.

## E2E decision

`e2e_required=false`.

All changed product behavior is structured CLI JSON decoded by the SDK or typed transport failure behavior. Existing contract validation, unit decoder/validator tests, fake-CLI component tests, packaging checks, documentation assertions, and separately gated live smoke fully observe it. There is no changed CLI table, log, progress display, browser UI, or real lifecycle interaction that requires a new local stand. Consequently:

- Local E2E scripts: none.
- Independent Tester stand: none; Tester independently inspects planned automated evidence and performs the public SDK walkthroughs below against disposable fixtures when the normal verification workflow reaches that gate.
- Before/after images: none; visible terminal output is unchanged and decorative captures are prohibited.
- Generated evidence files: none committed. Commands, exit codes, tested revision, logs, hashes, assertions, and any diagnostic JSON belong only in the final Multica verification comment.
- Test repository URL: use the project description resource at execution time; do not copy private repository or host details into public artifacts.
- Cleanup: dispose of temporary CLI profiles/resources while preserving the evidence branch/MR/commits; do not merge, close, or delete them without separate authorization.

## Verification matrix

| Case | OpenSpec requirement / scenario | Gap and decision | Public action / independent check | CI disposition | Assertions and evidence |
|---|---|---|---|---|---|
| V-01 | 0.6.2 source authority; provenance mismatch | Lower-level contract checks are sufficient | Run approved validate/render/check against pinned source; inspect exact target and interval | Extend existing contract tests and source-link audit | Full commits, release/archive/executable/version identities, deterministic bytes, exit codes |
| V-02 | Complete command/response reconciliation; dynamic and hidden nodes | Lower-level manifest audit is sufficient | Compare approved 209-node and 196-entrypoint manifests; inspect `checkin`, `probe-runtimes`, and autostart disposition | Extend existing inventory/response registry tests | Bijective totals, semantic dimensions, changed/unchanged reconciliation, full-SHA links |
| V-03 | Deferred autostart | Public-surface audit is sufficient | Inspect `client.daemon`, exports, generated bindings, and operation cases | Extend public-invariant tests | Three inventory rows exist; zero SDK methods/bindings/models/examples |
| V-04 | List-property definitions, discriminator, and values | Unit + fake CLI close the parsing/typing gap | Create/list definitions; exercise both direct set and create-time assignment with omitted/valid/invalid discriminator, JSON/comma/sequence values; independently inspect exact argv, pre-I/O failure, and immutable decoded tuples | Extend property resource/operation case tables | Options rejection, discriminator policy, 1–20, stable de-dup, text/URL bounds, HTTP(S), null/unset, malformed rows, zero transport on invalid input |
| V-05 | List-property filtering/display | Component fixture is sufficient | Search/list issues with exact element predicate; inspect literal member-shaped display string | Extend issue list/property fixtures | No assignment splitting, no actor resolution, raw and resolved projections remain separate |
| V-06 | Daemon `cli_commit` | Decoder cases are sufficient | Decode full, empty, and omitted fixtures through eager/command paths | Extend system model/daemon cases | Exact SHA, empty string, `None`, no version fallback |
| V-07 | Wakeup `last_error` and recovery | Decoder/component lifecycle fixtures are sufficient | Exercise create/get/list/update/disable fixtures and independent pending→healthy inspection | Extend wakeup resource and response cases | Three diagnostic strings, null/omission, clearing with no stale cache |
| V-08 | Interrupted upload response | Transport fault injection is sufficient | Inject reviewed body-read interruption; inspect exception and absence of result | Extend transport and attachment cases | `NetworkError`, safe redaction/chaining, no partial `AttachmentResult` |
| V-09 | Search, project presence/concurrency, redacted 500 | Existing public boundaries plus fixtures are sufficient | Search digit key/cancel; preview omitted/null project update; simulate revision conflict and redacted 500 | Extend resource/transport component cases | Exact argv, typed cancellation/conflict/error, no raw backend text |
| V-10 | Offline and packaging gates | Existing CI jobs are sufficient | Run non-live suite/collect-only, Ruff, mypy, contract checks, docs, build and artifact imports | Extend current repository jobs; no new framework/job unless current job cannot host a required command | Commands, exit codes, no live collection, wheel/sdist contents, import before CLI |
| V-11 | Direct migration documentation | Documentation contract tests are sufficient | Independently compare docs examples/claims to actual signatures and contract | Extend docs/public-surface tests | `0.6.1→0.6.2`, `0.6.3` ceiling, new fields/types/errors, autostart defer |
| V-12 | Existing gated live smoke | Existing live suite only; no new local E2E | In configured disposable environment, call representative property, daemon-status, wakeup, search, project, and upload paths without editing tests | Existing separately gated live-smoke job | Tested product SHA, actual command outcomes, cleanup result; findings published only in Multica |

## Evidence and ownership

The Implementer owns all tasks in `tasks.md`, including contract/test fixtures, documentation assertions, packaging changes, and any required extension to existing GitHub CI coverage. Tester does not edit implementation tests or fixtures; Tester verifies their coverage, performs independent public-path inspections, and reports findings with MR/commit/file links and command/exit-code evidence in Multica. No diagnostic output, evidence JSON, screenshots, provenance bundle, or logs are committed unless their generation is itself the product behavior under test, which is not the case here. Revision 2 resumes the existing `WP-1` only after its revised planning SHA is independently approved and handed to Manager; no new WP child or restart is permitted.

The implementation shall keep functional changes and test changes reviewable in ordinary commits. If a verified Git utility creates a functional-result commit, preserve that commit and link it as produced; do not rename it for evidence conventions. There is no Mac terminal before/after capture because user-visible output does not change.

## Work package topology

- Delivery mode: `single_wp_no_dag`.
- `WP-1` — Implement and verify the complete `update-multica-0-6-2` change.
  - Task coverage: tasks `1.1` through `5.4`, including new task `2.6`, exactly once.
  - Deliverable: one reviewable implementation that advances the approved SDK contract to `0.6.2`, adapts typed behavior, extends all required tests/docs, and passes the specified release gates while leaving daemon autostart absent.
  - `depends_on`: none.
  - Owned responsibility scope: approved contract/schema/generator projection; affected models/resources/transport; directly related tests, fixtures, docs, packaging metadata, snapshots, and repository service files. No exhaustive file allowlist is imposed.
  - Contract surface: `contracts/sdk-contract.json`; generated approved SDK module; public property/daemon/wakeup/issue/project/attachment/error APIs; the shared list-property discriminator and pre-I/O normalizer contract; compatibility/version policy; offline and packaging verification commands.
  - Definition of done: every task checkbox has implementation evidence; V-01 through V-12 have their planned assertions; strict OpenSpec and repository gates pass; Git contains no review-only evidence; autostart remains deferred.
  - Parallel safety: one WP intentionally owns the cross-cutting contract and generated projection, avoiding conflicting writes and synchronization overhead. No stages or managed DAG are created.

## Assumptions and risks

- The reviewed upstream dossier and exact pinned source remain available to the implementer outside tracked directories.
- Existing repository case-table and fake-CLI infrastructure can express all new cases without a new dependency.
- The live environment may be unavailable; that blocks only the separately gated live result, not substitution with invented evidence or weakening of offline acceptance.
- The dominant uncertainty is exhaustive contract/registry reconciliation and resulting fixture updates, not new architecture.
