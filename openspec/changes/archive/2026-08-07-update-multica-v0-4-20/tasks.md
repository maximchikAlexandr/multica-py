## 1. Collect and Review the v0.4.20 Authority

- [x] 1.1 Create a clean, read-only upstream checkout at tag `v0.4.20`; verify both `git describe --tags --exact-match` and `git rev-parse HEAD` resolve to `v0.4.20` / `93342d04a7a9f788fec921e5aa736f86c7f22d8f`, and record the absolute checkout path for later validation.
- [x] 1.2 Download the platform-matching CLI asset from GitHub release `366120041` into ignored `.devlocal` storage, verify its SHA-256 against `checksums.txt` (darwin-arm64: `2ff226b0d8c086736ad3e7ab223bf53d6cbce7e6961deadf6922e13dce4f6f08`), extract it, and capture the exact `multica version --output json` bytes beside the binary.
- [x] 1.3 Run `scripts/upstream_contract.py collect` with tag `v0.4.20`, version `0.4.20`, commit `93342d04a7a9f788fec921e5aa736f86c7f22d8f`, release ID `366120041`, and the verified asset/checksum/OS/architecture; confirm evidence and every review item remain under ignored `.devlocal` output and create no tracked files.
- [x] 1.4 Review the collected command tree plus the pinned source diff from `v0.4.9` through `v0.4.20`; classify only issue #30's SDK-affecting deltas, and record every unknown/dynamic pattern as a fail-closed review item rather than importing behavior from upstream `main`.

## 2. Reconcile the Approved SDK Contract

- [x] 2.1 Update `contracts/sdk-contract.json.target` to version/tag/commit/release `0.4.20` / `v0.4.20` / `93342d04a7a9f788fec921e5aa736f86c7f22d8f` / `366120041` and point `release_provenance_ref` at the ignored `v0.4.9..v0.4.20` evidence location.
- [x] 2.2 Re-resolve every retained `source_refs` entry against the pinned checkout: update its commit, path, symbol, and line range individually, remove only refs proven obsolete, and add a contract test that no current target/source ref retains `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`.
- [x] 2.3 Add source refs for `agentCopyCmd`, `registerAgentCopyFlags`, `runAgentCopy`, `applyAgentPermissionFlags`, and max-concurrency validation; trace source ID and every exposed SDK flag through the CLI's source GET and create JSON body/local-control behavior.
- [x] 2.4 Add source refs for `issueSearchCmd` / `runIssueSearch` and the handler's `SearchIssueResponse` / `match_source` query logic; record the CLI query, envelope, optional fields, number-query fallback, and open-string response policy.
- [x] 2.5 Refresh runtime-delete source refs/rationale to cover conflict discovery and `/unbind-agents-and-delete`, and explicitly record task cancellation plus preserved agent configuration/chats/history instead of legacy archive/destruction semantics.
- [x] 2.6 Refresh `S-ERRORS` (or split focused refs if required) to cover HTTP kind classification, the English/Chinese conflict and validation prefixes/fallbacks, and the reviewed local max-concurrency message at the pinned commit.
- [x] 2.7 Add complete contract catalogs for `agents.copy`: public signature, binding descriptor, mappings, five-state presence decisions, validators/imperative constraints, existing `Agent` response adapter, canonical/variant vectors, source refs, and positive/negative test refs; mark secret/machine-local flags as intentionally unsupported by the SDK entrypoint.
- [x] 2.8 Promote `issues.search` from a manual ungoverned convenience row to a governed operation with public signature, exact binding, query destination, private envelope/legacy adapter policy, response/test refs, and one canonical transport vector.
- [x] 2.9 Revalidate `autopilots.trigger` at `v0.4.20`: retain the public symbol/signature and `("autopilot", "trigger")` binding, update source refs, and add a contract mutation test proving `("autopilot", "run")` fails validation or canonical-vector agreement.
- [x] 2.10 Update provenance command fixtures and contract/catalog counts from computed data; verify `agent copy` and `issue search` are present, `autopilot trigger` remains present, and no unreleased tag-external command becomes approved.
- [x] 2.11 Run `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json --source-checkout <absolute-v0.4.20-checkout>` and resolve every schema, symbol, signature, source-range, presence, validator, response, and canonical-vector failure before generation.

## 3. Implement the Agent Copy Surface

- [x] 3.1 In `src/multica_py/resources/agents.py`, add `copy_command` and `copy` with the exact Decision 2 keyword-only signature using `Unset` / `UnsetType`; keep `source_agent_id` positional and make `copy()` delegate only through `copy_command().run()`.
- [x] 3.2 Validate a nonblank source ID, a nonblank present name, `1..50` present max concurrency, nonblank present member IDs, a present string-only `custom_args: tuple[str, ...]`, and a nonempty present member tuple; prove each rejection occurs before transport.
- [x] 3.3 Build deterministic argv in signature order: preserve present empty strings, compact-JSON encode the present `custom_args: tuple[str, ...]`, emit repeatable permission members in caller order, encode present `public_to_workspace=False` as a changed false boolean flag, and map `copy_skills=False` only to `--no-skills`.
- [x] 3.4 Implement cross-runtime model policy: when `runtime_id` is present and `model is Unset`, emit `--model ""` as the sole automatic runtime-specific default; when `thinking_level` or `service_tier` is omitted, leave its flag absent; when runtime is omitted, keep all omitted runtime-specific values absent; emit each present value verbatim for upstream validation.
- [x] 3.5 Decode the JSON result through the existing `Agent` model and bind it to the originating client in the command finalizer; confirm construction performs no subprocess I/O and preview/run share the same one-step plan.
- [x] 3.6 Add canonical and variant rows to `tests/cases/operations.py` for basic same-runtime copy, cross-runtime default model with omitted thinking/service flags, explicit future model/thinking/service strings, empty description/instructions, compact string custom args, max concurrency, permission flags/member order, and `copy_skills=False`; assert complete preview and executed argv plus bound result type.
- [x] 3.7 Add table-driven zero-I/O invalid-input tests and a public-signature test proving `custom_env`, `mcp_config`, `runtime_config`, and legacy `visibility` are absent from both copy methods and their preview/executed argv.

## 4. Adapt Issue Search Without Changing Its Return Type

- [x] 4.1 Add `match_source: str | None = None` to `IssueSummary` and `_IssueSummaryWire`, and transfer it in `issue_summary_from_wire` without introducing an enum or changing issue-list defaults.
- [x] 4.2 Add private `_IssueSearchResultWire` for the `v0.4.20` `{"issues": [...], "total": ...}` shape and a search-local decoder that accepts only this object envelope or the legacy top-level array, routing both through `_IssueSummaryWire` and `issue_summary_from_wire`.
- [x] 4.3 Change `IssueResource.search_command` to use the dual-shape decoder while keeping exact `issue search <query> --output json`, `Command[tuple[IssueSummary, ...]]`, and eager tuple behavior; malformed/other top-level shapes must raise the existing decode/shape exception.
- [x] 4.4 Replace the canonical search fixture's bare array with a `v0.4.20` envelope and add frozen decode cases for title, description, comment, number-only/comment fallback, omitted source, unknown future source, legacy array, empty envelope, and malformed top-level shape.
- [x] 4.5 Extend issue-list/relationship decoding assertions to prove the new optional field defaults to `None` outside search and does not trigger per-item gets, bound-entity construction, or a new public search-result model.

## 5. Preserve Conflict and Validation Details

- [x] 5.1 Import `ConflictError` in `src/multica_py/_internal/transport.py` and extend raw HTTP classification so `409` maps to `ConflictError` with the actual CLI exit code, while existing `400`/`422` mapping remains `ValidationError` with reported semantic code `5`.
- [x] 5.2 Add narrowly reviewed marker tables for the pinned English/Chinese actionable and generic conflict/validation messages plus `--max-concurrent-tasks must be between 1 and 50`; classify these before network/generic fallbacks without adding broad substring heuristics.
- [x] 5.3 Update `_raise_command_error` to redact both streams first, choose nonempty stripped stderr then stdout as the exception message, and use the current redacted generic command-failed text only when both are empty; retain redacted stream attributes and redacted argv, while passing the actual argv only to subprocess execution.
- [x] 5.4 Expand the frozen failure matrix in `tests/unit/test_transport.py` for raw `409`, English/Chinese actionable conflict prefixes, both generic conflict fallbacks, exit `5`, raw `400`/`422`, English/Chinese validation prefixes, local max-concurrency validation, and unrelated exit `1`; assert class and reported exit code exactly.
- [x] 5.5 Add detail-selection/redaction cases proving `str(exc)` contains useful stderr (or stdout fallback), empty streams use the generic message, upstream retry boilerplate does not replace a server conflict reason, and secrets are absent from message/attributes/redacted argv while subprocess execution received the original secret in its actual argv.
- [x] 5.6 Add a fake-CLI component case that exits nonzero with a pinned conflict message and another with a pinned validation message, proving the public command path raises `ConflictError` / `ValidationError` with preserved detail rather than only unit-testing the classifier helper.

## 6. Align Runtime, Autopilot, and Open-String Guarantees

- [x] 6.1 Add `RuntimeResource.delete` / `delete_command` docstrings and public documentation that define `cascade=True` as unbind agents, cancel queued/running tasks, delete runtime, and preserve agent configuration/chats/history; remove any current wording that says dependent agents are deleted or archived.
- [x] 6.2 Extend runtime resource operation variants for cascade omitted/present, exact command preview, and a conflict fixture; assert the non-cascade failure becomes `ConflictError` and retains upstream guidance without pretending the offline test observes server persistence.
- [x] 6.3 Keep `AutopilotResource.trigger` code unchanged unless source reconciliation finds real `v0.4.20` drift; retain its canonical preview/execution row and add the negative source-contract regression from task 2.9 instead of adding a public `run` alias.
- [x] 6.4 Add focused typed decoding tests with unknown future `RuntimeUsage.provider` / `model` values and command tests with unknown copy model/thinking/service strings; assert no closed SDK enum rejects them before upstream validation.

## 7. Generate Compatibility Output and Update Documentation

- [x] 7.1 Render `contracts/sdk-contract.json` to `src/multica_py/_generated/approved_sdk.py` with ignored transient output, verify generated target/min/max constants are `0.4.20` / `0.4.20` / `0.4.21`, and confirm generated copy/search descriptors match the approved contract exactly.
- [x] 7.2 Render a second time from the unchanged approved contract and compare hashes/git diff to prove deterministic bytes; run `uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json` after the second render.
- [x] 7.3 Update compatibility/provenance unit expectations and current non-archive docs from `v0.4.9` to `v0.4.20` / `[0.4.20, 0.4.21)`; leave historical archived OpenSpec evidence at its historical target.
- [x] 7.4 Update `docs/api.md` and `docs/service-usage.md` with `agents.copy`/`copy_command`, cross-runtime default-model behavior, unchanged tuple-returning search plus optional `match_source`, and typed actionable conflict/validation examples.
- [x] 7.5 Update `docs/migration.md`, `docs/compatibility.md`, and maintainer/release text as needed to state runtime cascade preservation, retain `autopilots.trigger` as the only supported spelling, describe secret/machine-local copy exclusions, and show the exact reviewed upstream workflow.
- [x] 7.6 Recompute the canonical discovered-method, unique-case, noncanonical-variant, and legacy-migration counts from the final tables; update stored constants/mappings in the same change and run the exact-equality completeness assertion with no allowlist.

## 8. Verification and Delivery Gates

- [x] 8.1 Run focused tests for agent resources/operations, issue models/resources/relations, transport classification, compatibility policy, upstream contract, baseline specs, and command preview; fix discovery/count/type failures before the full suite.
- [x] 8.2 Re-run the complete `collect → validate --source-checkout → render → check` chain from clean ignored evidence paths and verify tracked output is limited to the reviewed contract/runtime/code/tests/docs change.
- [x] 8.3 Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy --namespace-packages --explicit-package-bases -p multica_py`, `uv run mypy tests scripts tools --ignore-missing-imports --follow-imports=silent --check-untyped-defs`, and the repository's separate tools mypy invocation; resolve every failure without suppressing new errors.
- [x] 8.4 Run `uv run pytest -m "not live" --collect-only` and verify no `tests/live/*` node is collected, then run the complete `uv run pytest -m "not live"` suite including exact canonical discovery and contract mutation tests.
- [x] 8.5 Run `uv build`, verify exactly one wheel and one sdist, run `uv run pytest tests/packaging/ -v -o addopts="" -m packaging`, and import `multica_py` from a clean isolated wheel environment with no repository path on `PYTHONPATH`.
- [x] 8.6 Run `openspec validate update-multica-v0-4-20 --json`, inspect `git diff --check` and `git status`, and confirm there are no tracked release binaries, collected evidence, transient projections, secrets, or unrelated code changes before handoff.
