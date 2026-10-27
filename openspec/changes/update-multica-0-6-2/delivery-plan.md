## Delivery contract

- Planning issue: `MYL-474`
- Change: `update-multica-0-6-2`
- Graph revision: `3`; supersedes graph revision 2 only for verification routing.
- Approved product base: `6ef02a4b0f879cd4d5726433a803745fe57be547`
- Revision-2 planning authority: `e51f2090ead255b9cc854aaf5101a2837f75aa09`
- Accepted `WP-1` result: `386bc365cfbe55f0c82636d58120a2c6768d359b`
- Revision-3 parent and reviewed product head: `63ad61fadc8d9f4aadabe8e2df39ea8f7dcef6e6`
- Existing pull request: `https://github.com/maximchikAlexandr/multica-py/pull/101`
- Target branch: `feat/MYL-474-update-multica-0.6.2`
- Implementation gate: the recorded human approval remains applicable. Revision 3 changes no product API or daemon-autostart decision. The completed `WP-1`, existing PR, accepted implementation, and review findings/fixes remain valid and SHALL NOT be replaced, restarted, or replayed. The detailed review ledger remains authoritative in Multica rather than being copied into Git.
- Estimate source: the authoritative `Estimate, hours`, `Estimate min, hours`, and `Estimate max, hours` custom properties on the planning issue. Numeric totals are intentionally not duplicated here.
- Estimate basis: remaining work from the reviewed product head to the revised acceptance criteria, including the CI/live-fixture adjustment, the local artifact script, execution evidence, and likely delta review/fixes. Completed product implementation and accepted review work are not re-estimated.
- Confidence: medium. The affected workflow, fixture, SDK configuration, and test stand are inspectable, but protected-environment approval and the wrapper-owned local execution context are external gates.
- Calibration: uncalibrated for one experienced developer familiar with the repository; unattended GitHub queue time, environment approval delay, and human response time are excluded.
- Non-authoritative candidate: `adc56e3cb9a7c057f5b71efa1e120a073941df77` remains rejected diagnostic evidence only. It SHALL NOT be merged, treated as a base, or credited as completed work.

## Ponytail-full decision

No new subsystem is required. Reuse the existing `tests/live` suite, its protected GitHub workflow, the public SDK, the `multica-test` wrapper, pytest/stdlib conventions, and Multica attachments. Add only the smallest missing pieces: an exact-head authorization/check-out path, the target-version fixture update, and one repository-native local walkthrough script. Do not add a second live suite, generic E2E framework, credential broker, target-discovery service, container controller, screenshot harness, or new dependency.

## E2E decision

`e2e_required=true` for the owner-required local manual/scripted artifact walkthrough. This does not move V-12 out of GitHub CI and does not make the local stand a credential source for CI.

### V-12 — exact-head GitHub CI live smoke

- Extend `.github/workflows/live-smoke.yml`, `tests/live/conftest.py`, and `tests/live/README.md`; reuse `tests/live/test_smoke.py` unless a missing `0.6.2` public-path assertion is demonstrated.
- The dispatch accepts a PR number and full candidate SHA. An uncredentialed authorization job resolves the open PR through GitHub, requires a same-repository/non-fork head, and requires `candidate_sha == pull_request.head.sha` before the protected job can start.
- The protected `multica-live` job checks out the authorized full SHA with persisted Git credentials disabled, records `git rev-parse HEAD`, verifies the prepared CLI reports `0.6.2`, then runs the existing `live_smoke` marker under strict compatibility.
- The workflow definition may be loaded from the repository's trusted default branch, but a default-branch checkout or the dispatch event's default-branch SHA is not product-head evidence. Acceptance requires the resolved PR head, approved input, checkout HEAD, and tested product revision to be identical.
- GitHub environment variables/secrets remain in the protected job. The workflow SHALL NOT print, artifact, commit, or transfer tokens, profile contents, server settings, workspace credentials, or other reusable credentials.
- Required evidence: workflow/run URL, PR URL, exact SHA comparison, CLI version result, test command and exit status, cleanup result, and sanitized failure diagnostics. No live credential value is evidence.

### V-13 — isolated `multica-test` artifact walkthrough

- Repository script: `scripts/e2e/verify_multica_test.py`.
- Entry command: `uv run python scripts/e2e/verify_multica_test.py --output <run-owned-directory-outside-git>` from the tested checkout. The script fixes the executable to `multica-test` and offers no profile, server, workspace, token, or primary-CLI override.
- Execution context: a fresh independent Tester process authorized for the isolated project test stand. It SHALL NOT run through the primary Multica agent context, invoke the primary `multica` executable, alter primary profiles, or inspect/copy credential files.
- Initial state: wrapper-prepared test profile/workspace plus unique run prefix. The script performs a sanitized `0.6.2` preflight; reads daemon status; creates uniquely named disposable project/issue/property resources; exercises direct and create-time `multi_text`/`multi_url` assignment, canonical decoded tuples, exact-element filtering, and project update presence; then deletes all test-owned resources in failure-safe cleanup.
- Generated evidence outside Git: `manifest.json` with tested Git SHA, CLI version, scenario results, resource IDs, commands, exit codes, cleanup state, and artifact hashes; `stdout.txt`; `stderr.txt`; and `cleanup.json`. Artifacts SHALL be sanitized before attachment and SHALL contain no environment dump, profile contents, server URL, token, password, or reusable credential.
- Independent check: the Tester inspects the created/read-back values through separate public SDK reads, verifies the exact tested checkout, confirms cleanup with a not-found/read-back check, and does not treat a second invocation of the script as the manual inspection.
- Images: none. Human-facing terminal tables, logs, progress, and browser UI are unchanged, so PNG capture would be decorative. Actual source-language JSON/text output is retained instead.

### Publication and cleanup

- The test repository is `https://github.com/maximchikAlexandr/multica-py`, as supplied by the project description.
- Tester publishes PR, exact commit, workflow-run, workflow-file, live-fixture, and local-script links plus the sanitized local files as attachments in the final Multica comment, then reads back the comment/attachments.
- Commands, exit codes, assertions, actual output/logs, hashes, diagnostic JSON, provenance, and cleanup results live only in Multica. Only the reusable workflow/fixture/script and ordinary tests belong in Git.
- Cleanup removes run-owned local output and disposable test resources but preserves PR #101, its branch/commits, workflow run, and attached evidence. Closing, merging, or deleting the PR/branch is outside this plan.

## Verification matrix

| Case | Requirement / scenario | Verification gap and decision | OpenAPI operation/schema | Local script | Independent steps | CI disposition | Assertions | Artifacts / images |
|---|---|---|---|---|---|---|---|---|
| V-01 | `0.6.2` source authority; provenance mismatch | Existing lower-level contract checks are sufficient | N/A: CLI/SDK contract | None | Inspect exact target and compatibility interval | Existing contract checks/source-link audit | Full immutable provenance; deterministic bytes | Commands/exits in Multica; no images |
| V-02 | Complete command/response reconciliation | Existing manifest audit is sufficient | N/A: CLI inventory/responses | None | Inspect dynamic `checkin`, hidden `probe-runtimes`, autostart disposition | Existing inventory/registry tests | 209 nodes and 196 entrypoints reconcile | Audit result in Multica; no images |
| V-03 | Deferred daemon autostart | Existing public-surface audit is sufficient | N/A: local CLI control | None | Inspect client surface, exports, bindings, operation cases | Existing public-invariant tests | Three deferred rows; zero public methods/models/examples | Assertion summary; no images |
| V-04 | List-property definitions/discriminator/values | Existing unit/component coverage plus V-13 live read-back | N/A: CLI resource boundary | V-13 property lifecycle | Independently read direct/create-time values and invalid-input behavior | Existing tables; no duplicate CI E2E | Canonical tuples, bounds, dedupe, HTTP(S), null/unset, zero I/O | Sanitized manifest/text; no images |
| V-05 | List-property filtering/display | Existing component coverage plus V-13 exact-element query | N/A: CLI resource boundary | V-13 property lifecycle | Query exact element and inspect literal member-shaped value | Existing issue/property fixtures | No splitting or actor resolution | Sanitized manifest/text; no images |
| V-06 | Daemon `cli_commit` | Existing decoder coverage plus isolated live read | N/A: daemon status CLI | V-13 daemon read | Compare typed field with sanitized live response state | Existing system/daemon cases | Full/empty/omitted semantics; no version fallback | Sanitized manifest; no images |
| V-07 | Wakeup `last_error` recovery | Deterministic fixture lifecycle remains sufficient | N/A: wakeup CLI | None | Inspect pending-to-healthy fixture assertions | Existing wakeup tables | Diagnostics round-trip and clear without cache | Test link/result; no images |
| V-08 | Interrupted upload response | Transport fault injection remains sufficient | N/A: upload CLI transport | None | Inspect exception and absence of result | Existing transport/attachment cases | `NetworkError`, redaction/chaining, no partial result | Test link/result; no images |
| V-09 | Search, project presence/concurrency, redacted 500 | Existing fixtures plus V-13 project presence read-back | N/A: CLI resources | V-13 project lifecycle | Compare omitted and explicit update result | Existing resource/transport cases | Exact argv; typed errors; safe detail | Sanitized manifest/text; no images |
| V-10 | Offline and packaging gates | Existing CI checks are sufficient | N/A | None | Inspect collection and package contents | Existing CI/package jobs | No live collection; wheel/sdist/public typing valid | Existing run links; no images |
| V-11 | Direct migration documentation | Existing documentation contract checks are sufficient | N/A | None | Compare docs with actual signatures/contract | Existing docs/public-surface tests | Direct upgrade, ceiling, fields/types/errors, autostart defer | File/test links; no images |
| V-12 | Credential-gated live smoke at reviewed head | Current workflow tests only default branch and fixture pins an old CLI; exact-head CI is required | N/A: public SDK over CLI | None | Verify PR/head/input/checkout identity and sanitized cleanup | Extend protected `live-smoke` workflow/fixture for `0.6.2` | Same-repo open PR; all full SHAs equal; strict preflight; suite passes | Run/PR/SHA/exit/cleanup links; no credentials or images |
| V-13 | Owner-required isolated SDK walkthrough | Real wrapper/SDK/CLI/backend interaction and retained artifacts are not covered by lower-level tests | N/A: public SDK over CLI | `scripts/e2e/verify_multica_test.py` | Separate SDK reads and cleanup inspection in test context | Local-only; CI V-12 is not duplicated | Only `multica-test`; `0.6.2`; representative results; primary Multica untouched; cleanup complete | Attached sanitized JSON/text/hash files; no images |

## Evidence ownership and review impact

The existing `WP-1` implementation and review ledger remain accepted evidence for unchanged product code. Manager owns the bounded implementation-parent continuation on PR #101: route only the workflow, fixture/readme, local script, and directly coupled test/documentation delta for review. Security review focuses on exact-SHA authorization, protected-environment ordering, fork rejection, log/artifact redaction, and target isolation. Test review focuses on fixture `0.6.2`, script cleanup, deterministic assertions, and non-duplication. Existing findings/fixes and approvals remain valid for untouched files; do not replay the completed four-profile ledger solely because the verification route changed.

Implementer owns repository changes to CI, fixtures, scripts, and their tests. Tester SHALL NOT edit them: Tester runs the approved exact-head workflow and isolated walkthrough, performs independent reads, publishes links/files with read-back, and reports findings. Any finding that changes product API or stable requirements returns to planning; a defect confined to the verification delta returns to Manager's existing PR review/fix loop.

## Work package topology

- Delivery mode: `single_wp_no_dag`.
- `WP-1` — Implement and verify the complete `update-multica-0-6-2` change.
  - Task coverage: tasks `1.1` through `5.5`, including `2.6`, exactly once.
  - Lifecycle preservation: the existing child and its accepted implementation remain complete. Revision 3 SHALL NOT create, replace, restage, or restart a WP child. Tasks `5.4` and `5.5` are the remaining acceptance delta and are routed through the existing implementation parent/PR review-fix and Tester continuation.
  - Deliverable: the already accepted product implementation plus an exact-head protected live run and an isolated local artifact walkthrough, with no product-API change.
  - `depends_on`: none.
  - Owned responsibility scope: approved contract/schema/generator projection; affected models/resources/transport; directly related tests, fixtures, docs, packaging metadata, workflow, local verification script, and repository service files. This is not an exhaustive allowlist.
  - Contract surface: existing product APIs and compatibility policy; `.github/workflows/live-smoke.yml`; `tests/live`; `scripts/e2e/verify_multica_test.py`; evidence-publication and cleanup rules.
  - Definition of done: tasks `1.1` through `5.3` retain accepted evidence; V-01 through V-11 retain valid reviewed evidence; V-12 proves the exact reviewed PR head in protected GitHub CI; V-13 proves isolated `multica-test` operation with attached sanitized artifacts and cleanup; daemon autostart remains deferred.
  - Parallel safety: one WP continues to own the cross-cutting contract. No stage, dependency edge, frontier, sibling write zone, or managed DAG is created.

## Assumptions and risks

- The protected GitHub environment can approve the exact same-repository PR head without exposing credentials to the authorization job. If repository policy cannot support this, V-12 is blocked; a default-branch run is not a substitute.
- The prepared CI runner can supply or build CLI `0.6.2` and the prepared target accepts the existing live suite. Environment approval/queue delay is external waiting, not developer effort.
- A Tester process can run in the isolated `multica-test` context described by the project. If the wrapper still rejects that test-context process, V-13 is blocked; bypassing the wrapper or using primary credentials is forbidden.
- The local stand may contain shared test data. Every mutation uses unique names and failure-safe cleanup; the script does not reset containers, databases, profiles, or other users' resources.
- No changed visible output requires images. If implementation changes a human-facing table, log, progress state, or browser UI, this decision is invalid and the plan must add genuine before/after capture.
