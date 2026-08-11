## 1. Approved contract and test inventory

- [x] 1.1 Update `contracts/sdk-contract.json` signature, mapping, rationale, and canonical/variant rows for project `description_file`, issue ordinary descriptions/project references, exact issue status string unions, and `ProjectResource` status string unions without changing upstream command or response evidence; do not add bound `Project.set_status[_command]` operations.
- [x] 1.2 Deterministically render `src/multica_py/_generated/approved_sdk.py`, update computed operation/case constants and source-link expectations where required, and prove `scripts/upstream_contract.py check` reports no drift.
- [x] 1.3 Extend structural public-surface tests to require eager/`*_command()` parameter parity for every changed root, bound, and project-scoped method and to reject request DTOs, catch-all kwargs, or missing `OperationOptions`.

## 2. Natural project description inputs

- [x] 2.1 Add frozen operation and invalid-input cases for omitted/inline/file project descriptions, string and `os.PathLike[str]` paths, exact passive preview argv, description conflicts, blank/bytes paths, and zero filesystem/transport I/O on failure.
- [x] 2.2 Implement `description_file` on `ProjectResource.create` and `create_command` with shared lexical absolute-path normalization, mutual exclusion from `description`, matching signatures, and the governed `--description-file` plan/result binding.

## 3. Natural issue creation inputs and references

- [x] 3.1 Add table-driven cases covering omission, ordinary inline text, ordinary string/path-like files, every retained `IssueDescriptionInput` variant, all pairwise conflicts, invalid types/paths, and exact eager/command plans with no preview-time file access.
- [x] 3.2 Implement one issue-description normalizer and expose matching `description`, `description_file`, and optional semantic `description_input` parameters on root and project-scoped create pairs while preserving ordered label steps, `OperationOptions`, decoding, and binding.
- [x] 3.3 Add type/behavior cases for `project` as a nonblank ID or `Project`, retained `project_id` compatibility, simultaneous-form rejection, incompatible entities, project-scoped implicit IDs, and zero implicit project reads.
- [x] 3.4 Implement a type-specific project-reference normalizer, wire canonical `project` and compatibility `project_id` to the same approved `--project` mapping, and update project-scoped forwarding/cache invalidation without accepting arbitrary bound entities.

## 4. Exact status-string normalization

- [x] 4.1 Add frozen matrices for enum and exact-string status values across direct issue list fields, `IssueListFilter`, root/bound issue status actions, and `ProjectResource.set_status[_command]`; preserve eager/command parity and identical argv, and keep bound `Project` status actions out of the discovered public-method set.
- [x] 4.2 Add negative cases for `"open"`, wrong case, blank values, and non-string/non-enum inputs, asserting `ValueError`/`TypeError` before transport and explicitly preventing `AttributeError` regressions.
- [x] 4.3 Implement narrow issue/`ProjectResource` status normalizers, apply issue normalization after filter resolution and before `.value` access, update public annotations consistently, and leave decoded status models and unrelated enum-like inputs unchanged.

## 5. Raw CLI execution-mode boundary

- [x] 5.1 Define a frozen auth execution-form matrix for both `command` and `command_command`: allow `auth login --token <token>` with trailing arguments/options; reject bare/no-token forms and `--token` missing or option-like operands; assert identical actionable errors, zero transport/spawn calls on rejection, and no token/raw-argv leakage.
- [x] 5.2 Add allowed cases proving bounded token login, `workspace watch`, and unknown future command paths preserve structured argv, redaction, scoped/operation options, timeout/error classification, and `CliResult` behavior; retain rejected cases for `setup cloud`, `setup self-host`, `daemon start`, `daemon logs`, and top-level `update` with trailing arguments.
- [x] 5.3 Implement the explicit immutable execution-mode registry and shared post-shape/pre-plan validator in `resources/cli.py`, with a narrow `auth login` branch that permits only the governed `--token <token>` bounded form and rejects no-token/malformed forms without echoing argv or token values; keep other prefixes strict without family-wide or keyword heuristics.
- [x] 5.4 Add a contract regression check that every public operation returning `ManagedProcess` is either represented by the raw rejection registry or has an explicit reviewed exception, and that overloaded `auth.login` token/non-token forms plus bounded `WorkspaceResource.watch[_command]` remain explicit reviewed paths outside any blanket deny rule.

## 6. Direct issue-children binding

- [x] 6.1 Add parameterized empty, children-only, unstaged-only, and mixed `_IssueChildrenResultWire` cases that assert complete envelope preservation, originating-client binding, actionable entity command construction, and exactly one `issue children` call with zero `issue get` calls.
- [x] 6.2 Add `IssueResource._bind_issue_children_result`, map it after wire decoding in `children_command`, bind both `items`/`children` and `unstaged`, copy all metadata unchanged, and tighten the runtime `unstaged` type without coupling wire models to a client.
- [x] 6.3 Verify bound `Issue.children` lazy loading, command inspection, refresh/cache behavior, and origin scope remain unchanged when consuming the newly bound direct envelope.

## 7. Canonical documentation and migration guidance

- [x] 7.1 Rewrite the README opening so `MulticaClient()` → `issues.get(...)` → `issue.set_status("done")` appears before listing with a real status such as `"todo"`, followed by `get_command` inspection.
- [x] 7.2 Update API, service-usage, migration, examples, and typed documentation fixtures to use ordinary project/issue descriptions, canonical `project`, exact status strings, retained semantic variants only for distinct behavior, and no removed request DTOs.
- [x] 7.3 Document every rejected raw form with its typed SDK/`ManagedProcess` replacement, the allowed bounded `auth login --token <token>` and `workspace watch` forms, and the rule that unknown bounded non-interactive argv remains supported; add scans/order assertions preventing `"open"`, token leakage, and stale raw-boundary claims from returning to active docs.

## 8. Integrated offline verification

- [x] 8.1 Run focused unit, contract, and component suites for project/issue operations, direct keyword validation, issue/project relations, CLI raw commands, public signatures, docs, generated runtime, and upstream contract; resolve every regression before the full gate.
- [x] 8.2 Run `uv run pytest -m "not live" --collect-only`, prove no `tests/live/*` node is collected, then run the complete `uv run pytest -m "not live"` suite with exact subprocess-count and no-network assertions green.
- [x] 8.3 Run `uv run mypy src` and `uv run mypy tests`; fix all issues without broad `Any`, public `object` kwargs, new `type: ignore`, or weakened entity/status/reference annotations.
- [x] 8.4 Run `uv run ruff check` and `uv run ruff format --check`, approved contract source validation/render/check, source-link audit, canonical discovery/count tests, and generated-runtime/package validation.
- [x] 8.5 Build and test wheel and sdist for clean import, `py.typed`, curated exports, and documentation examples without requiring a Multica executable, backend, or network.
- [x] 8.6 Before archive, run `openspec validate complete-public-sdk-ergonomics-bound-issues --type change --strict --json` and strict main-spec validation; preserve the successful proof in `verification-proof.md`. On archived tips, use `openspec validate --specs --strict --json` because the archived change has no active deltas.
