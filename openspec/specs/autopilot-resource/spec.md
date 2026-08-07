# autopilot-resource Specification

## Purpose
TBD - created by archiving change autopilot-list-pagination. Update Purpose after archive.
## Requirements
### Requirement: Governed autopilot resource

The SDK MUST expose governed `autopilots.list/get/create/update/delete/trigger/history`
operations in the approved contract. Legacy `autopilots.run` MUST remain
renamed to `autopilots.trigger` and emit `autopilot trigger <autopilot-id>`.
`autopilots.get_run` MUST remain absent because pinned CLI `0.4.20` has no
single-run fetch; callers MUST use `history()` and select from its page.
Trigger reads MUST come from the governed autopilot get envelope; mutations
MUST use `trigger_add`, `trigger_update`, and `trigger_delete` methods backed
by upstream `trigger-add`, `trigger-update`, and `trigger-delete` commands.
All bindings and source references SHALL be revalidated at pinned commit
`93342d04a7a9f788fec921e5aa736f86c7f22d8f`.

#### Scenario: Autopilot operations are governed
- **WHEN** `contracts/sdk-contract.json` is inspected
- **THEN** it governs list, get, create, update, delete, trigger, history, trigger-add, trigger-update, and trigger-delete with `v0.4.20` bindings, signatures, responses, source refs, and migration compatibility

#### Scenario: Unsupported get-run is absent
- **WHEN** canonical public methods are discovered
- **THEN** `autopilots.get_run` is absent, while `autopilots.trigger` and `autopilots.history` are present

#### Scenario: Legacy autopilot run is absent
- **WHEN** canonical public methods are discovered
- **THEN** legacy `autopilots.run` is absent, while `autopilots.trigger` is present

#### Scenario: Manual trigger emits the supported command
- **WHEN** `client.autopilots.trigger("a1")` or its command form is used
- **THEN** exact argv contains `autopilot trigger a1 --output json` and never `autopilot run`

#### Scenario: Autopilot operations decode via wire converters
- **WHEN** `client.autopilots.get("a1")` receives the upstream get envelope
- **THEN** it adapts the `autopilot` member to a bound `Autopilot` and seeds explicitly present complete triggers/subscribers

### Requirement: Autopilot model reflects upstream response

Public `Autopilot` MUST be a bound entity over immutable `AutopilotData`.
`AutopilotData` MUST contain the upstream scalar fields `id`, `workspace_id`,
`title`, `description`, `project_id`, `assignee_type`, `assignee_id`, `status`,
`execution_mode`, `issue_title_template`, `created_by_type`, `created_by_id`,
`last_run_at`, `created_at`, `updated_at`, `trigger_kinds`, `next_run_at`,
`last_run_status`, `subscriber_snapshot`, `can_write`, and
`can_manage_access`. Legacy `name`, `enabled`, and eager `subscribers` MUST NOT
exist. `Autopilot.triggers` and `Autopilot.subscribers` MUST be read-only lazy
relations seeded from complete get-envelope fields when present.

#### Scenario: Full autopilot decode
- **WHEN** the get envelope provides all scalar fields and subscribers
- **THEN** `Autopilot.to_data()` preserves them, subscribers are stored as `subscriber_snapshot`, and relation access performs no I/O

#### Scenario: Optional fields default to None
- **WHEN** the get envelope omits optional scalar fields
- **THEN** `AutopilotData` preserves their documented `None` or empty-tuple defaults without loading an omitted relation

#### Scenario: Legacy name and enabled are absent
- **WHEN** a bound `Autopilot` or its immutable data snapshot is inspected
- **THEN** legacy `name` and `enabled` attributes are absent

#### Scenario: Missing embedded field remains unloaded
- **WHEN** a compact payload omits triggers or subscribers
- **THEN** the corresponding relation remains unloaded rather than becoming an empty relation

#### Scenario: Explicit empty embedded field seeds relation
- **WHEN** the get envelope explicitly contains an empty complete triggers or subscribers field
- **THEN** the corresponding relation is loaded as empty and `all()` performs no subprocess call

### Requirement: AutopilotRun model reflects upstream run response

Public `AutopilotRun` MUST be a bound entity over immutable
`AutopilotRunData` containing `id`, `autopilot_id`, `trigger_id`, `source`,
`status`, `issue_id`, `task_id`, `triggered_at`, `completed_at`,
`failure_reason`, `reason_code`, `trigger_payload`, `result`, and `created_at`.
Legacy `started_at` MUST NOT exist. `AutopilotRun.messages` MUST be a relation
available only when `task_id` is non-null and MUST call
`issues.run_messages(task_id, issue_id=issue_id)`.

#### Scenario: Full run decode
- **WHEN** an autopilot run response is decoded
- **THEN** `to_data()` exposes the upstream fields and no `started_at` attribute

#### Scenario: Nullable run fields decode to None
- **WHEN** an autopilot run response contains null optional identifiers, completion, failure, payload, or result fields
- **THEN** `AutopilotRunData` preserves those values as `None`

#### Scenario: Run messages require task ID
- **WHEN** `task_id` is null and messages are consumed
- **THEN** `MissingRelationContextError` is raised before transport access

### Requirement: Autopilot list returns a page with total

`AutopilotResource.list` MUST return `AutopilotListPage` containing bound
`Autopilot` entities and `total`. `Workspace.autopilots` MUST be an unpaged
`LazyCollection[Autopilot]` loaded by exactly one `autopilots.list` call and
MUST expose the page total as `relation.metadata.total`.

#### Scenario: List returns total
- **WHEN** direct list receives `autopilots` and `total`
- **THEN** the page contains bound entities and preserves total

#### Scenario: Empty list page
- **WHEN** direct list receives no autopilots and a zero total
- **THEN** it returns an empty bound page with `total == 0`

#### Scenario: Workspace relation uses one list page
- **WHEN** `workspace.autopilots.all()` loads
- **THEN** exactly one workspace-scoped list call runs, the relation caches all returned autopilots, and `metadata.total` equals the envelope total

### Requirement: Autopilot history supports limit/offset and returns a page

`AutopilotResource.history(autopilot_id, *, limit=None, offset=None)` MUST emit
`autopilot runs <id>` with optional nonnegative limit/offset and return
`AutopilotRunListPage`. `Autopilot.runs` MUST be
`OffsetLazyCollection[AutopilotRun]`, use a default page limit of 20, advance
the next offset by `len(page.runs)`, and stop when `has_more` is false.

#### Scenario: History emits the upstream runs subcommand with limit and offset
- **WHEN** history is called with limit 10 and offset 20
- **THEN** argv is `("autopilot", "runs", <id>, "--limit", "10", "--offset", "20", "--output", "json")`

#### Scenario: History returns a page with has_more
- **WHEN** history pages report more data then completion
- **THEN** `Autopilot.runs.all()` returns bound runs in page order and `metadata.total` preserves the last consistent total

#### Scenario: History last page has_more false
- **WHEN** the final history page reports no continuation
- **THEN** `Autopilot.runs.all()` stops without another subprocess call

#### Scenario: History default limit and offset
- **WHEN** `Autopilot.runs` requests its first page
- **THEN** it uses limit 20 and offset 0

#### Scenario: History rejects negative limit
- **WHEN** direct history or relation page receives a negative limit
- **THEN** `ValueError` names `limit` and transport is not called

#### Scenario: History rejects negative offset
- **WHEN** direct history or relation page receives a negative offset
- **THEN** `ValueError` names `offset` and transport is not called

### Requirement: Autopilot create aligns to upstream flags

`AutopilotResource.create` MUST accept `title`, `description`, `agent`,
`execution_mode`, `priority`, `project_id`, `issue_title_template`, and
`subscribers`, emitting the corresponding upstream flags. `agent` and
`execution_mode` MUST be required (no default). `execution_mode` MUST be the
`AutopilotExecutionMode` enum.

#### Scenario: Create emits required and optional flags

- **WHEN** `client.autopilots.create("My AP", description="d", agent="ag1", execution_mode=AutopilotExecutionMode.create_issue, priority="high", project_id="p1", issue_title_template="{{date}}", subscribers=("u1","u2"))` is called
- **THEN** the transport receives the argv
  `("autopilot", "create", "--title", "My AP", "--description", "d", "--agent", "ag1", "--mode", "create_issue", "--priority", "high", "--project", "p1", "--issue-title-template", "{{date}}", "--subscriber", "u1", "--subscriber", "u2", "--output", "json")`.

#### Scenario: Create minimal

- **WHEN** `client.autopilots.create("My AP", agent="ag1", execution_mode=AutopilotExecutionMode.run_only)` is called
- **THEN** the transport receives the argv
  `("autopilot", "create", "--title", "My AP", "--agent", "ag1", "--mode", "run_only", "--priority", "none", "--output", "json")` and no `--description`/`--project`/`--issue-title-template`/`--subscriber` flags.

### Requirement: Autopilot update uses presence semantics

`AutopilotResource.update` MUST emit only the flags for fields that are not
`None`, using the `--<flag>` form. `project_id` MUST use the presence policy:
`None` omits the flag, `""` emits `--project ""` to clear.
`clear_subscribers=True` MUST emit `--clear-subscribers` and MUST conflict with
`subscribers is not None`.

#### Scenario: Update emits changed flags only

- **WHEN** `client.autopilots.update("a1", title="New", status="paused")` is called
- **THEN** the transport receives the argv
  `("autopilot", "update", "a1", "--title", "New", "--status", "paused", "--output", "json")` and no other update flags.

#### Scenario: Update clears project_id with empty string

- **WHEN** `client.autopilots.update("a1", project_id="")` is called
- **THEN** the transport receives the argv
  `("autopilot", "update", "a1", "--project", "", "--output", "json")`.

#### Scenario: Update omits project_id when None

- **WHEN** `client.autopilots.update("a1", title="New")` is called
- **THEN** the transport argv does NOT contain `--project`.

#### Scenario: Update rejects clear_subscribers with subscribers

- **WHEN** `client.autopilots.update("a1", clear_subscribers=True, subscribers=("u1",))` is called
- **THEN** `ValueError` is raised and the transport is not called.

#### Scenario: Update emits repeatable subscribers

- **WHEN** `client.autopilots.update("a1", subscribers=("u1","u2"))` is called
- **THEN** the transport argv contains `--subscriber`, `u1`, `--subscriber`, `u2` in order.

