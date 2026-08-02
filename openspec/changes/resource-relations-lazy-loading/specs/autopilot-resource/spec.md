## MODIFIED Requirements

### Requirement: Governed autopilot resource

The SDK MUST expose governed `autopilots.list/get/create/update/delete/trigger/history`
operations in the approved contract. Legacy `autopilots.run` MUST be renamed
to `autopilots.trigger` and emit `autopilot trigger <autopilot-id>`.
`autopilots.get_run` MUST be removed because pinned CLI `0.4.9` has no
single-run fetch; callers MUST use `history()` and select from its page.
Trigger reads MUST come from the governed autopilot get envelope; mutations
MUST use `trigger_add`, `trigger_update`, and `trigger_delete` methods backed
by upstream `trigger-add`, `trigger-update`, and `trigger-delete` commands.

#### Scenario: Supported operations are governed
- **WHEN** `contracts/sdk-contract.json` is inspected
- **THEN** it governs list, get, create, update, delete, trigger, history, trigger-add, trigger-update, and trigger-delete with bindings, signatures, responses, source refs, and migration compatibility

#### Scenario: Unsupported get-run is absent
- **WHEN** canonical public methods are discovered
- **THEN** `autopilots.get_run` and legacy `autopilots.run` are absent, while `autopilots.trigger` and `autopilots.history` are present

#### Scenario: Get decodes aggregate envelope
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

#### Scenario: Full autopilot data decodes
- **WHEN** the get envelope provides all scalar fields and subscribers
- **THEN** `Autopilot.to_data()` preserves them, subscribers are stored as `subscriber_snapshot`, and relation access performs no I/O

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

#### Scenario: Run data remains typed
- **WHEN** an autopilot run response is decoded
- **THEN** `to_data()` exposes the upstream fields and no `started_at` attribute

#### Scenario: Run messages require task ID
- **WHEN** `task_id` is null and messages are consumed
- **THEN** `MissingRelationContextError` is raised before transport access

### Requirement: Autopilot list returns a page with total

`AutopilotResource.list` MUST return `AutopilotListPage` containing bound
`Autopilot` entities and `total`. `Workspace.autopilots` MUST be an unpaged
`LazyCollection[Autopilot]` loaded by exactly one `autopilots.list` call and
MUST expose the page total as `relation.metadata.total`.

#### Scenario: Direct list returns bound page
- **WHEN** direct list receives `autopilots` and `total`
- **THEN** the page contains bound entities and preserves total

#### Scenario: Workspace relation uses one list page
- **WHEN** `workspace.autopilots.all()` loads
- **THEN** exactly one workspace-scoped list call runs, the relation caches all returned autopilots, and `metadata.total` equals the envelope total

### Requirement: Autopilot history supports limit/offset and returns a page

`AutopilotResource.history(autopilot_id, *, limit=None, offset=None)` MUST emit
`autopilot runs <id>` with optional nonnegative limit/offset and return
`AutopilotRunListPage`. `Autopilot.runs` MUST be
`OffsetLazyCollection[AutopilotRun]`, use a default page limit of 20, advance
the next offset by `len(page.runs)`, and stop when `has_more` is false.

#### Scenario: Direct history emits exact runs command
- **WHEN** history is called with limit 10 and offset 20
- **THEN** argv is `("autopilot", "runs", <id>, "--limit", "10", "--offset", "20", "--output", "json")`

#### Scenario: Runs relation traverses pages
- **WHEN** history pages report more data then completion
- **THEN** `Autopilot.runs.all()` returns bound runs in page order and `metadata.total` preserves the last consistent total

#### Scenario: Negative pagination is rejected
- **WHEN** direct history or relation page receives a negative limit or offset
- **THEN** `ValueError` names the invalid parameter and transport is not called
