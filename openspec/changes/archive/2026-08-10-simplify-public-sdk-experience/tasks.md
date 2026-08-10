## 1. Approved contract and fail-closed inventory

- [x] 1.1 Update `contracts/schema/upstream-contract-v2.schema.json` and `tools/upstream_contract/contract.py` so direct-only operation entries can carry the final explicit signatures, `typed_input_id: null`, `input_mode: direct`, `OperationOptions`, new domain aliases, and bound `Issue` collection responses without weakening existing validation.
- [x] 1.2 Change the 23 DTO-backed operation entries in `contracts/sdk-contract.json` from `request.*` bindings/typed inputs to the exact direct parameter names, presence policies, validators, command symbols, and response contracts required by the specs; preserve pinned v0.4.20 argv/source semantics.
- [x] 1.3 Add approved operation/signature/response entries for `with_options`-affected command methods, explicit issue assign/unassign/move verbs, bound continuation aliases, project-scoped issue create, unified upload forms, and `client.cli.command`; mark local-only permalink methods outside canonical CLI discovery.
- [x] 1.4 Change issue list/search response catalogs and relation declarations from `IssueSummary` to partial bound `Issue`, retaining list/search wire fields, pagination, optional open `match_source`, and zero-extra-read policy.
- [x] 1.5 Update deterministic generation in `tools/upstream_contract/` and `src/multica_py/_generated/approved_sdk.py` for the revised catalogs, then prove render/check is byte-stable and no evidence/heuristic file can promote behavior.
- [x] 1.6 Rewrite canonical `OperationCase` rows/count fingerprints for all added/removed/changed methods, keeping exactly one canonical row per discovered CLI-backed eager method and exact preview/argv/mode/stdin/timeout/result assertions.
- [x] 1.7 Add contract/schema negative cases for stale request DTO IDs, `request.*` mappings, summary responses, missing `options` parity, duplicate/unapproved domain aliases, and invalid raw-command categories; run focused contract tests and approved source validation before runtime edits.

## 2. Default client and layered execution options

- [x] 2.1 Add frozen keyword-only `OperationOptions` in `config.py` with `Unset` defaults for profile, workspace, timeout, cwd, and environment, plus shared normalizers for finite nonnegative numeric/timedelta timeouts, path-like cwd, stable environment tuples, and nonblank nullable identifiers.
- [x] 2.2 Extend `ClientConfig` with validated `app_url` and `workspace_slug` fields without changing existing execution defaults; factor URL validation so API and app origins share HTTPS/loopback safety but remain independent settings.
- [x] 2.3 Change `MulticaClient.__init__` to accept `ClientConfig | None = None`, instantiate `ClientConfig()` for the default path, and add unit/type tests proving explicit config and clean import remain unchanged.
- [x] 2.4 Implement `MulticaClient.with_options(...)` using the shared normalizers and config replacement, preserving the original client and sharing only its `ProcessSemaphore`; rewrite `with_profile`, `with_workspace`, `with_timeout`, `with_cwd`, and `with_environment` as exact delegators.
- [x] 2.5 Add `BaseResource._effective_config(options)` and thread `options` through `_plan`, decoded/list/page/text/action/raw/spawn helpers so `_CommandPlan.config_snapshot` and transport snapshot are created once from the effective configuration.
- [x] 2.6 Ensure composite plans, runtime result/temp references, pagination continuations, bound/nested resource delegators, and no-step cached commands retain one effective config/semaphore and cannot redispatch under a different scope.
- [x] 2.7 Add a table-driven precedence/normalization matrix covering every field at base/scoped/operation layers, omission, explicit nullable clears, empty-environment clear, invalid values, source-client immutability, config snapshot stability, preview/execution parity, and unchanged behavior when options are omitted.

## 3. Remove one-operation DTO inputs

- [x] 3.1 Add focused domain validators/normalizers in resource modules for nonblank values, nullability, update presence, assignment references, exactly-one reorder target, pagination, metadata, trigger, and local-directory invariants currently implemented by DTO `__post_init__`; assert zero I/O on failure.
- [x] 3.2 Remove `AgentCreateRequest` and `AgentUpdateRequest`; convert agent create/update eager and command methods to one explicit signature, preserve no-op/nullable update behavior and exact plans, then rewrite agent operation/type tests.
- [x] 3.3 Remove `ProjectCreateRequest` and `ProjectUpdateRequest`; convert project/root and bound forwarding methods to explicit signatures, preserve `Unset` no-op/clear semantics, delete `models/projects.py`, and rewrite project tests/imports.
- [x] 3.4 Remove `SkillCreateRequest` and `SkillUpdateRequest`; convert skill create/update eager and command methods to one explicit signature, preserve validation/presence/results, and rewrite skill tests/imports.
- [x] 3.5 Remove `LabelUpdateRequest`; convert label update methods to explicit fields with existing no-op validation, delete `models/labels.py`, and rewrite label tests/imports.
- [x] 3.6 Remove `IssueCreateRequest`, `IssueUpdateRequest`, `IssueAssignmentRequest`, and `IssueReorderRequest`; convert issue methods to concrete typed signatures while preserving description variants, ordered label attachment, update clear/no-op plans, assignment validation, low-level reorder validation, and exact return binding.
- [x] 3.7 Remove `ProjectResourceAddLocalDirectoryRequest` and `ProjectResourceUpdateLocalDirectoryRequest`; convert root collection and bound Project local-directory methods to explicit path/daemon/label fields with the same path normalization, required-value behavior, cache invalidation, and command parity.
- [x] 3.8 Remove `CommentListFlatRequest`, `CommentListThreadRequest`, `CommentListRecentRequest`, `MetadataListRequest`, and `MetadataSetRequest`; convert comment/metadata eager-command methods and every Issue/CommentThread lazy loader to direct fields while preserving cursors, limits, predicates, JSON values, and result types.
- [x] 3.9 Remove `AutopilotUpdateRequest`, `AutopilotTriggerCreate`, and `AutopilotTriggerUpdate`; convert top-level and bound autopilot update/trigger methods to explicit fields while preserving `Unset`, subscriber clear/no-op behavior, trigger validation, and targeted cache invalidation.
- [x] 3.10 Remove `RuntimeUpdate` and `UserProfileUpdate`; convert runtime update and profile update methods to explicit fields, preserving required target version/wait behavior and omitted/string/`None` profile-description semantics.
- [x] 3.11 Delete removed DTO exports/imports from `models/__init__.py`, root `__init__.py`, internal resources, examples, docs, tests, generated/contract tables, and packaging expectations; add a scan asserting all 23 names and DTO-flow `_resolve_request` calls are absent.
- [x] 3.12 Replace generic `_resolve_request` with an issue-filter-specific normalization path for retained `IssueListFilter`, preserve object/direct filter reuse and validation, and prove no generic operation-bag abstraction or public catch-all kwargs remains.

## 4. Propagate OperationOptions across the public command surface

- [x] 4.1 Add the final keyword-only `options: OperationOptions | None = None` to agent, skill, label, project, project-resource, runtime, user, and autopilot eager-command pairs migrated in section 3; pass it to the final plan rather than CLI operation argv.
- [x] 4.2 Add matching options to IssueResource and nested comments, labels, metadata, subscribers, runs/messages, children, pull-request, search/list, usage, rerun/cancel, and bound Issue action pairs; preserve relation loaders' captured origin scopes.
- [x] 4.3 Add matching options to workspace, squad/member, repository, configuration, auth, setup, daemon, maintenance, attachment, agent-skill/task, skill-file, and remaining direct-resource eager-command pairs, including spawn/text/bytes modes.
- [x] 4.4 Update composite/no-op/paginated command constructors so every internal helper and continuation forwards the same options exactly once; verify options never appear as operation-specific argv or alter response finalizers.
- [x] 4.5 Extend structural discovery/type tests to require normalized eager-command parameter parity and a consistent final options keyword for every CLI-backed public resource/entity method, with explicit documented exceptions only for local-only and lazy relation load points.
- [x] 4.6 Run focused command-preview, client-isolation, transport, resource operation, and mypy tests; resolve all signature drift without `Any`, public `object` kwargs, broad ignores, or duplicate overload paths.

## 5. Canonical bound Issue values everywhere

- [x] 5.1 Refactor issue wire models so list/search/get-compatible rows share identity/status and optional fields, add open `match_source`, and decode absent get-only values to documented `Issue` defaults without fabricating relation completeness.
- [x] 5.2 Remove public `IssueSummary`, change `IssueListPage` to contain `Issue` while retaining its warning-free `issues is items` compatibility alias, and change search to `Page[Issue]` with envelope and legacy-array decoding.
- [x] 5.3 Bind list/search issues to the originating client in the finalizer and add exact tests for complete/partial rows, labels, metadata, identity/hierarchy fields, optional match sources including unknown strings, and immutable serialization/equality.
- [x] 5.4 Replace `_issue_summary_offset_page` helpers with bound-Issue page helpers and migrate `Workspace.issues` and `WorkspaceMember.issues` annotations/loaders/command adapters without changing workspace or assignee filters.
- [x] 5.5 Migrate `Agent.issues`, `Squad.issues`, and `Project.issues` read/page/all paths to bound `Issue`, preserving offset guards, metadata, cache/coalescing, command previews, and parent filters.
- [x] 5.6 Update approved-contract/public-surface/type fixtures and consumer flow tests so get/list/search/five relations/children all expose `Issue`; assert N rows never cause an implicit per-row `issue get` and partial entities can construct actions immediately.
- [x] 5.7 Remove remaining `IssueSummary` exports/docs/tests or confine any unavoidable legacy decoder detail to private names; add a source/package scan preventing its return to the primary public API.

## 6. Entity continuation actions and project-scoped creation

- [x] 6.1 Add a typed internal entity/ID normalization helper and public assignment/reference unions that accept nonblank identifiers plus appropriate Agent/Squad/WorkspaceMember/Issue entities without circular runtime imports or overbroad structural acceptance.
- [x] 6.2 Refactor root issue assignment to canonical `assign(issue_id, assignee)` and add `unassign[_command]`; preserve governed `--to-id`/`--unassign` argv, validation, decoding, operation options, and exact error behavior.
- [x] 6.3 Add root `move_to_top`, `move_to_bottom`, `move_before`, and `move_after` eager-command pairs as one-target delegators; keep low-level direct `reorder` as an advanced compatibility surface with exactly-one validation.
- [x] 6.4 Add bound `Issue.refresh`, `update`, `assign`, `unassign`, `set_status`, and four move eager-command pairs; require client context, forward the fixed ID/options to root plans, and return new immutable bound Issue values.
- [x] 6.5 Add bound `Project.refresh` and `update` eager-command pairs with identical root fields/options and immutable replacement behavior.
- [x] 6.6 Introduce `ProjectIssueCollection(OffsetLazyCollection[Issue])`, keep existing read/page/all/refresh semantics, and add create/create_command with root issue-create fields except public `project_id`, automatically supplying `project.id`.
- [x] 6.7 Map successful project-scoped create to invalidate only that memoized relation; prove failure preserves loaded/unloaded state, subsequent read reloads, and issues later updated/moved are not silently rebound to the source project.
- [x] 6.8 Add focused root/bound parity, detached-entity, ID/entity normalization, command preview, result binding, immutable-original, relation-cache, and no-generic-bind tests; update the normative 33-row relation matrix assertions.

## 7. Unified attachment source API

- [x] 7.1 Define typed upload source overloads for path/path-like, bytes-like, and binary streams on eager and command methods, including filename derivation/override, task ID, and operation options with exact parity.
- [x] 7.2 Reuse/factor `_safe_leaf` semantics to reject blank, absolute, or separator-containing path/traversal filenames and exact dot-segments (`.`/`..`) before filesystem access, while allowing ordinary basenames containing `..` (for example, `report..txt`); validate closed/unreadable/text streams clearly while leaving caller-owned binary streams open.
- [x] 7.3 Generalize the existing temp provider so bytes/stream content is read/materialized only during `Command.run`, exact content is written once at `${temp.path}`, and cleanup runs on success, transport/decode failure, timeout, and cancellation; path sources install no provider.
- [x] 7.4 Rewrite `upload_bytes` and `upload_bytes_command` as compatibility aliases to `upload(payload, filename=...)`, keep download/download-bytes unchanged, and assert alias preview/result/error/cleanup identity.
- [x] 7.5 Add table-driven tests for path/path-like, empty/binary bytes, named/unnamed streams, current stream position, closed/text streams, unsafe names (including exact `.`/`..` dot-segments and separator-containing traversal forms), the accepted `report..txt` basename, preview-only no-I/O, success/failure cleanup, task/options propagation, and exact governed argv.

## 8. Safe raw CLI escape hatch

- [x] 8.1 Add immutable public `CliResult` in a dedicated module with stdout/stderr bytes and duration but no actual argv or collected secrets; update transport/raw finalization without changing nonzero exception behavior.
- [x] 8.2 Add `CliResource` and attach it as `MulticaClient.cli`, with `command(*argv, options=None) -> Command[CliResult]` using `BaseResource._raw_command` and the same plan/config/transport snapshot path.
- [x] 8.3 Validate nonempty string argv, blank/duplicated executable first component, non-string components, and NUL before I/O while permitting literal later empty values needed by upstream flags; never accept/execute a shell string.
- [x] 8.4 Document and test the bounded non-interactive contract: no TTY/login prompting, indefinite streaming, spawn, or async promise; direct users to existing typed `ManagedProcess` operations for those workflows.
- [x] 8.5 Add safety tests for quoting/metacharacters, full global argv, scoped/operation options, preview no-I/O, redaction, result fields, nonzero classification, timeout, and proof that only controlled `CliTransport` receives the original argv.

## 9. Explicit entity permalinks

- [x] 9.1 Complete `app_url`/`workspace_slug` normalization tests for hosted `https://multica.ai`, self-hosted HTTPS, loopback HTTP, trailing slashes, credentials, query/fragment, blank/slashed slug, and independence from `server_url`.
- [x] 9.2 Add typed `MissingPermalinkContextError` to the public exception hierarchy and a pure internal builder that URL-encodes path segments and requires a bound client plus both configuration values.
- [x] 9.3 Add local-only `Issue.permalink()` using `/{workspace_slug}/issues/{id}` with no command sibling or I/O; test UUID/identifier/encoded segments, detached entities, missing context, and repeated access.
- [x] 9.4 Add local-only `Project.permalink()` using `/{workspace_slug}/projects/{id}` with the same context/error/passivity behavior.
- [x] 9.5 Add hosted/self-hosted documentation examples and contract tests proving app URL is never inferred from API URL and workspace slug is never inferred from ID/name.

## 10. Curated namespace and migration documentation

- [x] 10.1 Define one expected root export table covering client/config/options, Command/Page/ActionResult/ManagedProcess, primary entities, common enums/Unset, and public exceptions; rewrite `multica_py.__init__` to match it exactly.
- [x] 10.2 Move/document retained filters, description variants, metadata/cursor/value types, lazy relation/page implementations, compatibility page names, `CliResult`, and resource-specific outputs under dedicated modules; update all internal and test imports.
- [x] 10.3 Rewrite README usage to start with `MulticaClient()`, retrieve/iterate bound Issue values, and invoke an entity action before introducing explicit config, filters, command inspection, or advanced modules.
- [x] 10.4 Rewrite `docs/api.md`, `docs/service-usage.md`, and runnable examples for `with_options`, `OperationOptions`, direct-only inputs, explicit domain verbs, project-scoped create, unified upload, raw argv, and permalinks; remove every request-object/default-summary claim.
- [x] 10.5 Add a complete breaking table to `docs/migration.md` and `CHANGELOG.md` with compiling before/after examples for all 23 DTOs, IssueSummary/list/search/relation types, assignment/reorder modes, upload aliases, project-scoped create, options, raw CLI, permalink config, and every root import moved to a dedicated module.
- [x] 10.6 Extend typed documentation/public-surface/packaging tests so every common import and migration example resolves, every advanced import uses its documented module, and no deleted name or stale request/summary wording remains outside historical OpenSpec/archive material.

## 11. Integrated verification and release readiness

- [x] 11.1 Run focused unit/contract/component suites for config/options, direct inputs/presence, issue decoding/relations/actions, attachments, raw CLI, permalinks, public exports, and command preview; fix all failures before the full suite.
- [x] 11.2 Run `uv run pytest -m "not live" --collect-only` and prove no `tests/live/*` node is collected, then run `uv run pytest -m "not live"` with exact subprocess-count/no-network assertions green.
- [x] 11.3 Run `uv run mypy src` and `uv run mypy tests`; fix every issue without new broad `Any`, `object` kwargs, `type: ignore`, or weakened overload/signature types.
- [x] 11.4 Run `uv run ruff check` and `uv run ruff format --check`; keep generated and handwritten code deterministic and clean.
- [x] 11.5 Run approved contract source validation, `scripts/upstream_contract.py check`, deterministic render freshness, source-link audit, canonical discovery/count tests, and generated-runtime/package tests; confirm only reviewed v0.4.20 behavior is represented.
- [x] 11.6 Build wheel and sdist and run packaging tests against both, verifying the curated root, dedicated advanced modules, `py.typed`, and clean import without an installed Multica executable.
- [x] 11.7 Run `openspec validate simplify-public-sdk-experience --type change --strict --json` and `openspec validate --specs --strict --json`; reconcile any overlap with the merged operation-contract and command-preview baselines without weakening this change.
- [x] 11.8 Complete the breaking release checklist after the required offline gates are green; live smoke and `MULTICA_LIVE_*` validation remain upstream-owned release validation and are excluded from this change.
