## Why

Resource methods that mutate state currently force callers to construct a
`*Request` msgspec.Struct even for one-off operations with two or three
ordinary fields (`projects.create(ProjectCreateRequest(name=...))` instead of
`projects.create(name=...)`). This is ceremony without benefit for the common
case, hides the real fields behind an extra import and indirection, and is
inconsistent with mainstream Python SDK conventions. Issue #22 asks the SDK to
accept the fields directly as keyword-only arguments while keeping the
request-object form for reuse, validation, and cross-layer assembly.

## What Changes

- Add a dual-input public calling convention to qualifying resource methods:
  either pass a single positional request object, or pass the request's fields
  directly as keyword-only arguments. Exactly one style per call.
- Mixed input (request object plus keyword fields) raises `TypeError` with the
  message `Pass either a request object or keyword arguments, not both.` before
  any CLI invocation.
- Direct keyword fields are keyword-only (the request object stays the only
  positional argument) and mirror the request model's own field names, types,
  defaults, optional-ness, and `__post_init__` validation.
- Expose `@overload` signatures so static type checkers and IDEs understand
  both forms and offer autocomplete for the direct fields.
- Keep the existing request classes, request-object signatures, and transport
  behavior unchanged. No public method is renamed, split, or removed.
- Apply the dual-input pattern per method, only where the request object groups
  a small set of ordinary fields. Skip request objects that represent a
  meaningful standalone contract (mutually-exclusive variants, nested
  configuration, complex validation, multi-input shapes) unless a direct form
  stays clear and unambiguous.
- Documentation presents the direct keyword form as the default and the
  request-object form as the advanced/reusable alternative.

### Methods in scope (direct form added)

- `projects.create` — `ProjectCreateRequest` (name, description).
- `projects.update` — `ProjectUpdateRequest` (name, description with
  `Unset`/`None` presence semantics).
- `agents.create` — `AgentCreateRequest` (name, description, runtime_id, model).
- `agents.update` — `AgentUpdateRequest` (name, description).
- `skills.create` — `SkillCreateRequest` (name, description).
- `skills.update` — `SkillUpdateRequest` (name, description).
- `issues.create` — `IssueCreateRequest` (title, description_input, priority,
  assignee_id, label_ids, project_id, parent_id).
- `issues.update` — `IssueUpdateRequest` (title, description, priority,
  assignee_id, project_id, parent_id).
- `issues.assign` — `IssueAssignmentRequest` (issue_id, member_id, agent_id,
  squad_id, unassign) — exactly-one-target validation preserved.
- `issues.reorder` — `IssueReorderRequest` (issue_id, before_id, after_id, top,
  bottom) — exactly-one-target validation preserved.
- `runtimes.update` — `RuntimeUpdate` (target_version, wait).
- `project_resources.add_local_directory` —
  `ProjectResourceAddLocalDirectoryRequest` (local_path, daemon_id, label).
- `project_resources.update_local_directory` —
  `ProjectResourceUpdateLocalDirectoryRequest` (local_path).
- `users.profile_update` — `UserProfileUpdate` (description with
  `Unset`/present semantics).

### Methods reviewed and intentionally left request-object-only

- `issue_comments` list overloads (`CommentListFlatRequest`,
  `CommentListThreadRequest`, `CommentListRecentRequest`) — multi-variant
  dispatch with cursor/since/limit combinations; a flat keyword surface would
  blur which list mode is selected.
- `issue_metadata.query` (`MetadataListRequest`) — nested predicate tuple and
  cursor/limit pagination; the request object is the clear boundary.
- `issue_metadata.set_typed` (`MetadataSetRequest`) — already has a
  `set(issue_id, key, value)` direct sibling; `set_typed` keeps its
  value-type-bearing request form.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdk-surface`: Add the dual-input calling convention requirement
  (request-object or keyword-only direct fields, exactly-one-style rule,
  `TypeError` on mixed input, `@overload` type surface, per-method scope, and
  documentation default) to the public synchronous resource surface.

## Impact

- `src/multica_py/resources/` — every in-scope method gains an
  overload-decorated dual-input signature and a small normalize-or-reject
  dispatcher at the top of its body. No transport, argv, or wire-model change.
- `src/multica_py/models/` — request classes unchanged; they remain the source
  of truth for field names, types, defaults, and `__post_init__` validation.
- `tests/cases/operations.py` and `tests/unit/resources/` — new
  `OperationCase` rows added to `OPERATION_CASES` for the direct keyword
  form and for request-object parity per in-scope method; dedicated
  `mock_transport`-based tests for mixed-input/neither-input `TypeError`
  and `__post_init__` `ValueError` paths.
- `docs/` — resource method examples flip to the direct keyword form first,
  request-object form shown as the advanced/reusable alternative.
- No CLI, wire, transport, dependency, packaging, or public-method-name
  changes. No request class is removed or renamed.