## Context

`main` at `f55dc1d` already has the foundations this change should preserve: immutable `ClientConfig`, derived clients sharing one `ProcessSemaphore`, one controlled `CliTransport`, immutable `Command` plans with preview/execution parity, common `Page`/`ActionResult` contracts, frozen bound entities, and lazy relation caching. The recently merged `unify-sdk-operation-contracts` change intentionally expanded dual request-object/direct-keyword overloads; GitHub issue #42 now supersedes that input decision and requires the request containers to be removed.

The current public friction is structural:

- `MulticaClient` requires an explicit `ClientConfig` even for defaults, and five separate `with_*` helpers do not scale to multi-setting or one-operation overrides.
- 23 one-operation DTOs drive overloads, `_resolve_request`, casts, public `**kwargs: object`, duplicate tests/exports, and mixed-input validation.
- issue list/search and five issue relations decode `_IssueSummaryWire` into detached `IssueSummary`, while get/children decode `_IssueWire` into actionable `Issue`.
- bound `Issue` lacks refresh/update/assignment/status/reorder continuation methods; `Project.issues` is a plain `OffsetLazyCollection` with no scoped create action.
- attachment paths and bytes have separate public methods; bytes already use the command-plan temp-provider mechanism that can support all in-memory sources.
- `BaseResource._raw_command` exists privately, but there is no governed public raw-argv resource/result.
- `server_url` is an API setting and cannot safely supply web permalinks. Reviewed Multica web routes are `/{workspaceSlug}/issues/{id}` and `/{workspaceSlug}/projects/{id}`; the SDK currently has neither app origin nor workspace slug context.
- the package root exports request DTOs, relation implementations, JSON/value aliases, compatibility page types, and resource-specific outputs alongside the ordinary entry points.

This is a coordinated breaking public API release. It changes SDK code, the approved operation contract, generated projections, type fixtures, docs, and tests, but not the Multica CLI/server, wire protocol, subprocess mechanism, or persistence.

## Goals / Non-Goals

**Goals:**

- Establish one canonical public form for ordinary operations: explicit typed method parameters with argument-identical eager and command methods.
- Make configuration scale from default client, to immutable scope, to one operation with deterministic precedence and snapshot behavior.
- Make every public issue collection return the same bound `Issue` without automatic per-row reads.
- Complete common entity workflows and the project-to-issues domain path while preserving immutable wrappers and targeted lazy-cache invalidation.
- Use normal Python path/bytes/binary-stream values for upload, structured argv for the raw escape hatch, and explicit web context for permalinks.
- Reduce root autocomplete and provide complete, type-checked breaking migration guidance.
- Preserve the approved-contract boundary, command plans, exact governed argv, validation, presence/nullability, decoding, exceptions, and offline quality gates.

**Non-Goals:**

- No HTTP client, async client, `Command.run_async`, shell command strings, interactive/TTY raw commands, generic workflow/DAG, or generic relation `bind` API.
- No new Multica CLI/server flags, endpoints, response fields, or frontend routes.
- No automatic `issue get` hydration, eager relation loading, identity map, mutable entity refresh, or global reverse-index cache invalidation.
- No inference of app URL from API `server_url`, workspace slug from ID/name, or public behavior from unapproved upstream evidence.
- No elimination of reusable query specifications, semantic field variants, sentinels, enums, output/result models, `Page`, `ActionResult`, lazy relations, or the low-level direct `reorder` compatibility method.

## Decisions

### Decision 1: Remove operation bags and make method signatures the schema

Delete the 23 named input containers from `models/agents.py`, `projects.py`, `skills.py`, `labels.py`, `issues.py`, `project_resources.py`, `issue_activity.py`, `autopilots.py`, and `system.py`. Delete `models/projects.py` and `models/labels.py` when empty. Affected resources and bound entities receive one concrete signature; eager methods call their command sibling directly with named parameters.

Move DTO `__post_init__` checks into small domain-specific validators/normalizers near the command builder. Update validation and no-op branching continue using explicit local variables and `Unset`; they are not replaced by dictionaries or catch-all kwargs. Remove generic `_resolve_request` when its operation-bag consumers disappear. `IssueListFilter` remains the sole reusable filter object/direct-field exception and uses an issue-filter-specific resolver so its independent query semantics are visible.

In `contracts/sdk-contract.json`, affected entries set `typed_input_id: null` and `input_mode: direct`; signature and binding catalogs name direct fields rather than `request.*`. Contract/generator changes happen before runtime rewrites so discovery and table cases fail closed throughout the migration.

Alternative: retain private request DTOs and construct them internally. Rejected because runtime signatures would still not be the schema, validation would remain split, and dead argument-bag abstractions would continue to shape implementation and tests.

### Decision 2: Represent layered execution settings with one partial options model

Add frozen keyword-only `OperationOptions` beside `ClientConfig` in `config.py`. Each field defaults to `Unset`:

```python
profile: str | None | UnsetType
workspace_id: str | None | UnsetType
timeout: datetime.timedelta | float | int | None | UnsetType
cwd: str | os.PathLike[str] | None | UnsetType
environment: Mapping[str, str] | tuple[tuple[str, str], ...] | UnsetType
```

Central normalization converts numeric timeouts to `timedelta`, path-like cwd to `Path`, and environment to a stable sorted tuple; it validates finite/nonnegative durations and nonblank non-null profile/workspace values. `environment=()` is the explicit clear. `MulticaClient.__init__(config: ClientConfig | None = None)` substitutes `ClientConfig()` for `None`. `with_options(...)` builds an `OperationOptions`, applies present values to a copied config, and creates a new client sharing the semaphore. Existing single-option helpers delegate to it.

Every CLI-backed resource/entity eager-command pair adds one final keyword-only `options: OperationOptions | None = None`. Relation load methods retain their captured origin scope; callers needing a different relation scope derive the client/entity first. `BaseResource` gains `_effective_config(options)` and `_plan(..., options=...)`; all decoded/text/action/raw/spawn helper constructors accept and forward options. `_plan` snapshots the effective config and snapshots transport from it exactly once, so composite/paged continuations cannot mix scopes.

Alternative: implement operation options by creating an ephemeral client and dynamically redispatching the method. Rejected because it invites recursion/signature drift, makes bound/nested resources difficult, and obscures the command-plan snapshot that tests already govern.

### Decision 3: Decode collection rows directly into partial bound Issue values

Remove public `IssueSummary`. Consolidate collection/get wire fields by extending a shared issue row wire model (or a narrow shared base) with optional get-only fields and `match_source`. List/search decoders construct `Issue` with safe defaults for absent fields and immediately call `_with_client(self._client)`. `IssueListPage` becomes `Page[Issue]` while retaining its `issues` alias during page compatibility; search becomes `Page[Issue]` for a consistent collection contract.

Replace `_issue_summary_offset_page*` with `_issue_offset_page*`, and change workspace, workspace-member, project, agent, and squad relation annotations/loaders to `Issue`. The loader maps only the response already received. `Issue.match_source: str | None` preserves open upstream values for search-originated entities and defaults elsewhere. Missing description, assignee, timestamps, snapshots, and other get-only fields retain documented defaults until explicit `Issue.refresh()`; a partial bound entity means actionable, not fully hydrated.

Alternative: call `issues.get` for every row. Rejected because it adds N+1 latency/failure behavior, changes command preview, defeats paging, and violates the source issues. Alternative: keep `IssueSummary` as a public subclass. Rejected because users would still face two entity types and inconsistent autocomplete.

### Decision 4: Add entity actions as thin immutable forwarding methods

Add `Issue.refresh[_command]`, `update[_command]`, `assign[_command]`, `unassign[_command]`, `set_status[_command]`, and `move_{to_top,to_bottom,before,after}[_command]`. Add `Project.refresh[_command]` and `update[_command]`. Each requires the bound client, forwards the fixed entity ID and all explicit typed fields/options to the root resource, and returns the newly decoded bound entity. The original frozen entity and its snapshots remain unchanged.

Normalize entity/ID inputs with typed public unions and one internal ID extractor. Canonical assignment is `assign(issue_id, assignee)` where `assignee` is a nonblank ID or bound Agent/Squad/WorkspaceMember; upstream already accepts the unified target ID. Unassignment is separate. Add the four move verbs at root and entity levels, each delegating to one governed reorder target. Keep direct `reorder(issue_id, *, before_id, after_id, top, bottom)` only as an advanced compatibility surface with exactly-one validation; docs use verbs.

Alternative: mutate frozen entities in place after an action. Rejected because it violates the existing immutable replacement boundary and complicates equality, caches, and concurrency.

### Decision 5: Specialize only the Project-to-Issues relation

Introduce `ProjectIssueCollection(OffsetLazyCollection[Issue])` in the project/issues resource boundary. It receives the parent `Project`, root `IssueResource`, and existing page loaders. `create[_command]` mirrors root issue-create fields except `project_id`; it forwards `project.id`, maps the result to invalidate this exact relation after success, and leaves state untouched on failure. Read/page/all/refresh behavior remains inherited.

Do not add mutation methods to generic lazy collection classes and do not add a generic `bind(**context)` API. `project_id` is create context, not an invariant attached to issues later returned from the relation, so future issue update/move calls remain explicit.

Alternative: expose `Project.create_issue`. Rejected because the existing discoverable graph is `project.issues`, and the source issue specifically requires the relation to be the domain action surface.

### Decision 6: Unify uploads with source adapters backed by the existing temp provider

Give `AttachmentResource.upload[_command]` overloads for `os.PathLike`, bytes-like values, and `BinaryIO`, with `filename` optional only when a safe stream basename can be derived. Reuse the existing `_safe_leaf` validator and `_TempProvider`/`${temp.path}` plan reference: a safe leaf is nonblank, does not denote an absolute or separator-containing path/traversal, and is not the exact dot-segment `.` or `..`; ordinary basenames containing `..`, such as `report..txt`, remain valid. Path input resolves directly and installs no provider. Bytes/stream providers create a private temp directory only in `run()`, write exact content once, and clean in `_CommandPlan.run`'s existing `finally` block. Streams are caller-owned, read from their current position, and must remain open until command execution; construction performs no read.

Keep `upload_bytes[_command]` as a thin compatibility alias for one migration window. Keep download/download-bytes behavior unchanged.

Alternative: materialize in-memory sources during command construction. Rejected because command preview is contractually I/O-free and a preview-only command would leak temporary artifacts.

### Decision 7: Expose raw argv through a dedicated resource and safe result

Add `CliResource` to `MulticaClient` as `.cli`. `command(*argv, options=None)` validates a nonempty string sequence, rejects a duplicated executable/blank first element/NUL, and builds one `_raw_command` plan. Arguments are subcommand argv; full executable/global args remain owned by `CliTransport`.

Move or adapt private raw output into public dedicated-module `CliResult(stdout: bytes, stderr: bytes, duration: timedelta)`. Do not expose actual argv or collected secret values. Nonzero exits continue raising existing exceptions, so a public result represents success. The resource supports ordinary non-interactive bounded commands only and uses the current synchronous `Command.run` contract.

Alternative: return `subprocess.CompletedProcess` or accept a shell string. Rejected because both leak transport details, weaken redaction/typing, and make quoting/injection ambiguous.

### Decision 8: Configure permalinks independently from API execution

Extend `ClientConfig` with `app_url: str | None` and `workspace_slug: str | None`. Validate `app_url` with the same HTTPS/loopback policy as `server_url`, plus no credentials/query/fragment and normalized trailing slash. Validate slug as one nonblank path segment. Do not default `app_url` to `multica.ai`: that would make self-hosted/default-profile clients silently produce wrong hosted links.

Add a small pure URL builder and typed `MissingPermalinkContextError`. `Issue.permalink()` and `Project.permalink()` require a bound client and complete routing config, URL-encode slug/ID segments, and build the reviewed paths. They perform no I/O and do not receive command siblings because they are local-only.

Alternative: derive app origin by stripping `/api` from `server_url`, or fetch workspace/app config. Rejected because API/frontend deployments can differ and permalink access must remain passive/predictable.

### Decision 9: Make root exports a curated convenience layer

Rewrite `multica_py.__init__` around categories ordinary users need: client/config/options; `Command`, `Page`, `ActionResult`, `ManagedProcess`; primary bound entities; common workflow enums and `Unset`; public exceptions. Remove request objects entirely. Keep filters, description variants, metadata/cursor types, lazy relation classes/pages, resource-specific outputs, raw CLI result, and compatibility types in documented dedicated modules.

Tests compare `__all__`, importability, packaging contents, and typed README/migration examples to one declared expected set. This avoids using mere underscore naming or accidental imports as the namespace policy.

Alternative: leave all retained symbols at root to minimize migration. Rejected because issue #33 explicitly requires root autocomplete to answer the normal-user question, and the DTO cleanup is already a coordinated breaking release.

### Decision 10: Land contract, runtime, docs, and tests as one fail-closed migration

Update the approved contract schema/catalogs, generated projection, canonical operation cases, discovery/count invariants, and presence matrices together. Rewrite parity tests around direct signatures and command equivalence; delete request-object/mixed-input tests; retain/expand exact argv, no-op, nullability, validation, decoder, and command-plan coverage. Add type fixtures for every entity origin and every migration example. Preserve full offline gates and no-network tests.

The implementation sequence below keeps intermediate commits coherent, but the feature branch is not releaseable until the complete breaking surface and docs are green. No runtime compatibility shim is added for deleted DTO calls; only upload aliases and low-level reorder receive an explicit migration window.

## Risks / Trade-offs

- **[Risk] Wide signature churn across the canonical operation inventory** → Update contract/schema/cases first, use structural eager-command parity tests, and migrate resources in bounded families so missing `options` or DTO paths fail immediately.
- **[Risk] Partial `Issue` values may be mistaken for hydrated get results** → Document field provenance/defaults, keep refresh explicit, test every row shape, and do not seed unavailable lazy relations as complete.
- **[Risk] Circular imports from typed entity references and `IssueListPage[Issue]`** → Use `TYPE_CHECKING`, narrow protocols/helpers, local runtime imports already established by `_issue_from_wire`, and contract type tests.
- **[Risk] Operation options accidentally change process concurrency or client lifecycle** → Only copy config fields; preserve the same semaphore; snapshot a distinct transport/config per command; add isolation and composite-plan tests.
- **[Risk] Stream upload command outlives its caller-owned stream** → Make lifetime explicit, validate at execution, never close the stream, and recommend eager `upload` or running the command inside the stream context.
- **[Risk] Raw commands expand user power and secret exposure** → Keep argv-only/shell-free execution, reuse transport/redaction/classification, omit actual argv from `CliResult`, and scope documentation to bounded non-interactive commands.
- **[Risk] Explicit permalink settings add configuration ceremony** → Keep the method pure and errors precise; do not trade ceremony for incorrect URLs. Provide hosted and self-hosted examples.
- **[Risk] Removing root exports and DTOs breaks alpha consumers immediately** → Ship a complete typed migration table/changelog and keep only the narrowly justified upload/reorder compatibility paths.
- **[Risk] Existing unarchived OpenSpec changes describe dual input or summaries** → This delta explicitly removes/supersedes the conflicting main requirements; validation and later sync must apply this change after the already-merged baseline.

## Migration Plan

1. Update the approved contract/schema, generated projection, operation counts, and canonical direct signatures/response types; add failing completeness tests for the final surface.
2. Add default construction, `OperationOptions`, normalization, `with_options`, effective-plan snapshotting, and the shared `options` keyword across resource/entity command pairs; verify isolation and unchanged omitted-options behavior.
3. Remove DTOs family-by-family, move validation/presence logic to command builders, delete empty modules/exports and generic request plumbing, and rewrite exact operation tests.
4. Replace summary decoders/types with partial bound `Issue`, migrate all five issue-list relations/search/list pages, and add entity continuation/domain actions with no-N+1 proof.
5. Introduce `ProjectIssueCollection` and scoped create invalidation; then add unified upload adapters/temp providers, `CliResource`/`CliResult`, and configured permalinks.
6. Curate root exports and rewrite README, API, migration, examples, changelog, typed docs fixtures, and packaging expectations.
7. Run OpenSpec and approved-contract validation/render/check, Ruff check/format, `mypy src`, `mypy tests`, package validation, and the complete non-live test suite. Release only when every breaking migration example compiles.

Rollback is a branch/commit revert before release. After publishing the breaking version, consumers roll back by pinning the previous SDK version; the SDK does not maintain a runtime dual-input fallback that could mask incomplete migration.

## Open Questions

None. The source issues and reviewed current code resolve the input precedence, retained semantic objects, issue hydration policy, relation scope, upload lifetime, raw-command boundary, permalink routes/context, and compatibility windows needed for implementation.
