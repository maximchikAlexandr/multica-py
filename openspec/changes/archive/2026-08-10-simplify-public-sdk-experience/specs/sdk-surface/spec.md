## ADDED Requirements

### Requirement: Default and layered client options
`MulticaClient` SHALL accept no argument and use `ClientConfig()` defaults, while continuing to accept one explicit `ClientConfig`. The SDK SHALL expose `with_options(...)` for immutable client views and `OperationOptions` for one-call overrides. The supported override fields SHALL be `profile`, `workspace_id`, `timeout`, `cwd`, and `environment`; omission SHALL inherit the lower layer, explicit `None` SHALL clear nullable scalar/path settings, and an explicit empty environment SHALL clear inherited SDK environment entries. Effective precedence SHALL be operation options over scoped-client options over base configuration. Numeric timeouts SHALL represent nonnegative finite seconds and normalize to `datetime.timedelta`; cwd SHALL accept `str` or `os.PathLike` and normalize to `pathlib.Path`.

#### Scenario: Default client is usable
- **WHEN** a caller constructs `MulticaClient()`
- **THEN** it behaves as `MulticaClient(ClientConfig())` and exposes the complete resource tree

#### Scenario: Explicit configuration remains available
- **WHEN** a caller passes a `ClientConfig` to `MulticaClient`
- **THEN** that exact immutable configuration remains the base layer

#### Scenario: Scoped options do not mutate their source
- **WHEN** `scoped = client.with_options(profile="automation", workspace_id="ws_1", timeout=30, cwd="./repo")` is created
- **THEN** `scoped` uses the normalized overrides, `client.config` is unchanged, and both clients share only the existing process semaphore

#### Scenario: Per-operation options win
- **WHEN** a command is constructed with `OperationOptions(timeout=5, workspace_id="ws_2")` from a client scoped to timeout 30 and workspace `ws_1`
- **THEN** its preview and execution use timeout 5 and workspace `ws_2` while inheriting every non-overridden setting

#### Scenario: Invalid execution values fail before I/O
- **WHEN** a timeout is negative, non-finite, or not a supported duration/number, or a non-`None` profile/workspace is blank
- **THEN** construction raises `TypeError` or `ValueError` before command or transport I/O

### Requirement: Direct typed parameters are the sole operation input
Affected eager and `*_command()` operations SHALL expose matching explicit typed parameters and SHALL NOT accept a one-operation request DTO, a generic `request | None` positional slot, or public `**kwargs: object`. The SDK SHALL remove exactly `AgentCreateRequest`, `AgentUpdateRequest`, `ProjectCreateRequest`, `ProjectUpdateRequest`, `SkillCreateRequest`, `SkillUpdateRequest`, `LabelUpdateRequest`, `IssueCreateRequest`, `IssueUpdateRequest`, `IssueAssignmentRequest`, `IssueReorderRequest`, `ProjectResourceAddLocalDirectoryRequest`, `ProjectResourceUpdateLocalDirectoryRequest`, `CommentListFlatRequest`, `CommentListThreadRequest`, `CommentListRecentRequest`, `MetadataListRequest`, `MetadataSetRequest`, `AutopilotUpdateRequest`, `AutopilotTriggerCreate`, `AutopilotTriggerUpdate`, `RuntimeUpdate`, and `UserProfileUpdate`. Validation formerly owned by those DTOs SHALL run in the public method or command-building layer before I/O.

#### Scenario: Runtime signatures describe real inputs
- **WHEN** `inspect.signature` examines any affected eager or command method
- **THEN** it exposes the real typed operation fields plus the shared optional `options` keyword and contains no request slot or catch-all kwargs

#### Scenario: Eager and command signatures match
- **WHEN** an affected eager method and its `*_command()` sibling are normalized for their return annotation
- **THEN** their operation parameters, defaults, keyword-only boundaries, and `OperationOptions` parameter are identical

#### Scenario: Removed DTO imports fail
- **WHEN** a consumer imports any of the 23 removed names from `multica_py`, `multica_py.models`, or its former model module
- **THEN** the name is absent, while modules containing retained semantic/output models remain importable

#### Scenario: Empty request-only modules are deleted
- **WHEN** `models.projects` and `models.labels` contain no retained public model after migration
- **THEN** those files and all references to them are removed

#### Scenario: Validation survives DTO removal
- **WHEN** callers provide null non-nullable updates, blank identifiers/names, invalid pagination, multiple assignment modes, or zero/multiple reorder targets through retained low-level methods
- **THEN** equivalent typed errors occur before I/O and no invariant is weakened

#### Scenario: Semantic value objects remain
- **WHEN** public models are inspected after the cleanup
- **THEN** `IssueListFilter`, issue description variants, `MetadataPredicate`/`IssueMetadataItem`, `CommentCursor`, `LocalDirectoryResourceRef`, `ProjectResourceRecord`, `Unset`, enums, pages, entities, and output/result models remain available from their dedicated modules

### Requirement: Canonical bound Issue collections
`issues.list(...)` SHALL return `IssueListPage` whose `items`/compatibility `issues` alias contains bound `Issue` entities, and `issues.search(...)` SHALL return `Page[Issue]`. Workspace, workspace-member, project, agent, and squad issue relations SHALL yield bound `Issue` entities. Each decoder SHALL construct the canonical `Issue` from fields already present in the collection row, default unavailable fields safely, preserve optional open-string `match_source` on search-originated issues, and bind the originating client without issuing an automatic `issues.get`.

#### Scenario: List returns actionable issues
- **WHEN** a caller iterates `client.issues.list().items`
- **THEN** each value is a bound `Issue` that can immediately call entity actions and relations

#### Scenario: Search preserves match metadata
- **WHEN** search rows include a known or unknown future `match_source`
- **THEN** the returned bound `Issue.match_source` preserves that string and defaults to `None` when omitted

#### Scenario: Partial rows remain honest
- **WHEN** list, search, or relation rows omit fields only supplied by `issue get`
- **THEN** the corresponding optional/snapshot fields on `Issue` use documented defaults until explicit `refresh()`/`get()` and are not fabricated

#### Scenario: Collections avoid N plus one reads
- **WHEN** N issue rows are decoded from list, search, or a relation
- **THEN** exactly the collection command runs and zero per-row `issue get` commands run

#### Scenario: IssueSummary leaves the primary API
- **WHEN** public types, return annotations, contracts, docs, and examples are inspected
- **THEN** normal issue workflows use `Issue`; `IssueSummary` is absent or confined to a private compatibility decoder with no public export

### Requirement: Explicit issue domain actions
The canonical resource actions SHALL be `assign(issue_id, assignee)`, `unassign(issue_id)`, `move_to_top(issue_id)`, `move_to_bottom(issue_id)`, `move_before(issue_id, other_issue)`, and `move_after(issue_id, other_issue)`, each with an argument-identical `*_command()` sibling. Bound `Issue` SHALL expose the corresponding context-bound forms plus `refresh`, `update`, and `set_status`. Assignment and issue references SHALL accept a nonblank identifier or an appropriate bound entity and normalize to its ID. The low-level direct `reorder(...)` operation MAY remain for compatibility but SHALL retain its exactly-one-target validation and SHALL not be the documented default.

#### Scenario: Resource assignment reads as intent
- **WHEN** `client.issues.assign("MUL-123", agent)` is called with an agent entity or identifier
- **THEN** it emits the governed assignment argv and returns a bound `Issue`

#### Scenario: Unassignment has its own verb
- **WHEN** resource or bound-entity `unassign()` is called
- **THEN** the governed `--unassign` action runs without an `unassign=True` public mode flag

#### Scenario: Move methods encode one target
- **WHEN** any explicit top, bottom, before, or after method is called
- **THEN** it emits exactly one corresponding reorder target and cannot express an invalid mutually exclusive combination

#### Scenario: Bound issue continues a workflow
- **WHEN** an issue comes from get, list, search, or a relation
- **THEN** `refresh`, `update`, `assign`, `unassign`, `set_status`, and move methods delegate through the same root resource command plans and return newly bound immutable `Issue` values

### Requirement: Unified Python attachment upload
`attachments.upload(source, *, filename=None, task_id=None, options=None)` and `upload_command(...)` SHALL accept a filesystem path/path-like object, bytes-like content, or a binary file-like object. Path input SHALL use the existing file directly. In-memory input SHALL require a safe supplied filename unless a safe basename can be derived from the stream's `.name`; it SHALL be materialized only for command execution, cleaned after success/failure, and preserve exact bytes. `upload_bytes(...)` and `upload_bytes_command(...)` MAY remain as compatibility aliases that delegate to the unified API; documentation SHALL prefer `upload`.

#### Scenario: Path upload preserves governed behavior
- **WHEN** source is a path-like value
- **THEN** the existing `attachment upload <absolute-path> [--task <id>] --output json` plan and result contract are preserved without copying the file

#### Scenario: Bytes upload uses a safe filename
- **WHEN** source is bytes and `filename="report.txt"`
- **THEN** execution materializes those exact bytes under that basename, uploads it, and removes the temporary directory

#### Scenario: Stream upload is lazy and non-owning
- **WHEN** `upload_command` is constructed for an open binary stream
- **THEN** command construction performs no read, execution consumes the stream without closing it, and a closed/unreadable/text stream fails clearly

#### Scenario: Unsafe or missing filename fails before filesystem access
- **WHEN** in-memory input has no derivable filename or the filename is blank, absolute, contains path separators (including traversal forms such as `../report.txt`), or is exactly the dot-segment `.` or `..`
- **THEN** `ValueError` is raised before temporary filesystem or transport access

#### Scenario: Safe basename containing double dots remains valid
- **WHEN** in-memory input is uploaded with the safe basename `filename="report..txt"`
- **THEN** filename validation accepts it as a leaf name, and command construction preserves the filename without temporary filesystem or transport access

#### Scenario: Compatibility aliases are exact
- **WHEN** `upload_bytes(filename, payload, ...)` is used during the migration window
- **THEN** it delegates to `upload(payload, filename=filename, ...)` with identical preview, result, cleanup, and error behavior

### Requirement: Deliberately small package root
The `multica_py` root SHALL export only the default/configuration and operation option types, `Command`, common page/action/process contracts, primary bound entities, common workflow enums and `Unset`, and the public exception hierarchy. Relation implementations, JSON/metadata aliases, reusable filters and semantic value objects, compatibility page names, raw CLI result details, and resource-specific output models SHALL be imported from dedicated modules.

#### Scenario: Common imports remain obvious
- **WHEN** a normal user imports `MulticaClient`, `ClientConfig`, `OperationOptions`, `Issue`, `Project`, `Agent`, `IssueStatus`, or `MulticaError` from `multica_py`
- **THEN** each import succeeds

#### Scenario: Advanced names leave root autocomplete
- **WHEN** `multica_py.__all__` is inspected
- **THEN** request DTOs and advanced relation/wire/value/compatibility types are absent and documentation gives their dedicated-module locations when retained

## REMOVED Requirements

### Requirement: Issue list pagination and summary identity decoding
**Reason**: Collection rows now decode directly into the canonical bound `Issue` without N+1 reads.
**Migration**: Iterate `IssueListPage.items` as `Issue` and call entity actions directly; use `issue.refresh()` only when fields absent from the collection row are needed.

### Requirement: Attachment byte-oriented upload and download
**Reason**: Separate upload methods are replaced by one Pythonic source overload while download behavior remains unchanged.
**Migration**: Replace `upload_bytes(filename, payload)` with `upload(payload, filename=filename)`; existing download and temporary-cleanup contracts continue.

### Requirement: Dual input convention for request-bearing resource methods
**Reason**: One-operation request containers duplicate method schemas and are removed as a breaking API cleanup.
**Migration**: Replace `method(Request(field=value))` with `method(field=value)` using the migration table for every removed DTO.

### Requirement: Dual input convention documentation default
**Reason**: Documentation now presents one typed method form rather than primary and advanced equivalents.
**Migration**: Use direct typed parameters; retain reusable semantic objects only where they represent independent domain meaning.

### Requirement: Issue search preserves its API and decodes v0.4.20 results
**Reason**: Search now returns bound `Issue` values instead of summaries while retaining the same command and response compatibility.
**Migration**: Treat search results as `Page[Issue]` and read `Issue.match_source` for search metadata.

### Requirement: Unsupported surface migration
**Reason**: The previous migration contract required `IssueSummary` and request-object paths that this breaking release removes.
**Migration**: Follow the new consolidated migration table for typed parameters, bound issue collections, unified upload, domain verbs, and dedicated-module imports.
