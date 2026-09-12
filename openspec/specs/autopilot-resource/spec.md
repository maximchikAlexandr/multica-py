# autopilot-resource Specification

## Purpose
TBD - created by archiving change autopilot-list-pagination. Update Purpose after archive.
## Requirements
### Requirement: Governed autopilot resource

The SDK MUST expose governed `autopilots.list/get/create/update/delete/trigger/history`
operations in the approved contract. Legacy `autopilots.run` MUST remain
renamed to `autopilots.trigger` and emit `autopilot trigger <autopilot-id>`.
`autopilots.get_run` MUST remain absent because pinned CLI `0.4.28` has no
single-run fetch; callers MUST use `history()` and select from its page.
Trigger reads MUST come from the governed autopilot get envelope; mutations
MUST use `trigger_add`, `trigger_update`, and `trigger_delete` methods backed
by upstream `trigger-add`, `trigger-update`, and `trigger-delete` commands.
All bindings and source references SHALL be revalidated at pinned commit
`38c992ad0a757434fb51584fa34e3bc57d1b78e1`.

#### Scenario: Autopilot operations are governed
- **WHEN** `contracts/sdk-contract.json` is inspected
- **THEN** it governs list, get, create, update, delete, trigger, history, trigger-add, trigger-update, and trigger-delete with `v0.4.28` bindings, signatures, responses, source refs, and migration compatibility

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
`execution_mode`, `project_id`, `issue_title_template`, and `subscribers`,
emitting the corresponding target flags. It MUST NOT accept or emit
`priority`. `agent` and `execution_mode` MUST be required (no default).
`execution_mode` MUST be the `AutopilotExecutionMode` enum.

#### Scenario: Create emits supported flags
- **WHEN** create receives all supported optional fields
- **THEN** exact argv contains description, agent, mode, project, issue-title-template, subscriber, and JSON-output flags and contains no `--priority`

#### Scenario: Create minimal has no legacy priority
- **WHEN** create receives only title, agent, and execution mode
- **THEN** exact argv contains those values plus `--output json` and does not emit `--priority none`

#### Scenario: Legacy create priority is absent
- **WHEN** the create signature, type-check fixtures, docs, and canonical cases are inspected
- **THEN** no `priority` parameter or `--priority` mapping remains

#### Scenario: Create emits required and optional flags
- **WHEN** create receives every supported optional field
- **THEN** exact argv contains description, agent, mode, project, issue-title-template, subscribers, and JSON output, with no `--priority` flag

#### Scenario: Create minimal
- **WHEN** create receives only title, agent, and execution mode
- **THEN** exact argv contains those values and JSON output, with no description, project, issue-title-template, subscriber, or priority flag

### Requirement: Autopilot update uses presence semantics

`AutopilotResource.update` MUST emit only flags for supported fields that are
not `Unset`; it MUST NOT accept or emit `priority`. Omitted, `None`, empty
string, zero, and false SHALL follow each target field's reviewed
`Flags().Changed` and request encoding. `project_id` SHALL distinguish omission
from the target's explicit clear form. `clear_subscribers=True` SHALL emit
`--clear-subscribers` and SHALL conflict with present subscribers.

#### Scenario: Update emits changed flags only
- **WHEN** update receives title and status only
- **THEN** exact argv contains only those changed flags plus JSON output and no priority flag

#### Scenario: Update preserves explicit clear and omission
- **WHEN** project ID is omitted versus supplied as the reviewed empty clear value
- **THEN** omission emits no project flag and clear emits `--project ""`

#### Scenario: Update preserves false and empty presence
- **WHEN** a supported boolean is explicitly false or a supported string is explicitly empty
- **THEN** target `Flags().Changed` semantics are preserved and neither value is collapsed into omission

#### Scenario: Subscriber channels remain exclusive
- **WHEN** clear-subscribers and subscribers are both present
- **THEN** construction raises `ValueError` before transport

#### Scenario: Legacy update priority is absent
- **WHEN** update signatures, generated bindings, docs, and cases are inspected
- **THEN** no priority parameter, mapping, or compatibility alias remains

#### Scenario: Update clears project_id with empty string
- **WHEN** update receives `project_id=""`
- **THEN** exact argv contains `--project ""`

#### Scenario: Update omits project_id when None
- **WHEN** update receives another changed field while `project_id` is omitted
- **THEN** exact argv contains no `--project` flag

#### Scenario: Update rejects clear_subscribers with subscribers
- **WHEN** `clear_subscribers=True` and subscribers are both present
- **THEN** `ValueError` is raised before transport

#### Scenario: Update emits repeatable subscribers
- **WHEN** update receives multiple subscribers
- **THEN** exact argv emits one `--subscriber` flag per value in input order

### Requirement: Trigger add exposes the pinned schedule inputs

`AutopilotResource` SHALL expose these exact public add signatures:

```python
def trigger_add(
    self,
    autopilot_id: str,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_add_command(
    self,
    autopilot_id: str,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...
```

They SHALL emit `autopilot trigger-add <autopilot-id>` followed in declaration order by present `--kind`, `--cron`, `--timezone`, and `--label` flags and structured JSON output. `kind` SHALL be `schedule` or `webhook`; an empty kind SHALL normalize to `schedule`. A schedule SHALL require a nonempty cron expression. A webhook SHALL reject a nonempty cron expression or timezone. Omitted, `None`, and empty timezone/label SHALL emit no flag; nonempty values SHALL pass through unchanged. All locally decidable failures SHALL occur before transport I/O.

#### Scenario: Schedule trigger is created with cron and timezone
- **WHEN** `client.autopilots.trigger_add("a1", cron_expression="*/30 * * * *", timezone="Europe/Minsk", label="half-hour")` is called
- **THEN** exact argv is `("autopilot", "trigger-add", "a1", "--kind", "schedule", "--cron", "*/30 * * * *", "--timezone", "Europe/Minsk", "--label", "half-hour", "--output", "json")`

#### Scenario: Omitted add optionals remain absent
- **WHEN** a schedule add omits timezone and label or supplies either as `None` or `""`
- **THEN** the corresponding flag is absent and no literal `None` or empty flag value reaches transport

#### Scenario: Schedule requires cron
- **WHEN** kind is omitted, empty, or `schedule` and cron expression is omitted, `None`, or empty
- **THEN** `ValueError` names `cron_expression` and transport is not called

#### Scenario: Webhook rejects schedule-only values
- **WHEN** kind is `webhook` and cron expression or timezone is nonempty
- **THEN** `ValueError` names the incompatible field and transport is not called

#### Scenario: Invalid kind fails locally
- **WHEN** kind is `None` or any nonempty value other than `schedule` or `webhook`
- **THEN** `TypeError` or `ValueError` is raised before transport I/O

### Requirement: Trigger update uses explicit patch presence

`AutopilotResource` SHALL expose these exact public update signatures:

```python
def trigger_update(
    self,
    autopilot_id: str,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_update_command(
    self,
    autopilot_id: str,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...
```

They SHALL NOT accept `title` or `kind`. `Unset` SHALL omit a field; `None` SHALL raise `TypeError`; empty string SHALL be emitted for each string field; and `False` and `True` SHALL emit `--enabled=false` and `--enabled=true` respectively. At least one update field SHALL be supplied. Flags SHALL appear in signature order as `--cron`, `--timezone`, `--label`, and `--enabled=<lowercase-bool>`. The SDK SHALL leave target-kind validation of cron/timezone to the governed CLI/server because the direct call has no persisted trigger-kind context.

#### Scenario: Schedule cadence and timezone are updated
- **WHEN** `client.autopilots.trigger_update("a1", "t1", cron_expression="0 */3 * * *", timezone="Europe/Minsk")` is called
- **THEN** exact argv is `("autopilot", "trigger-update", "a1", "t1", "--cron", "0 */3 * * *", "--timezone", "Europe/Minsk", "--output", "json")`

#### Scenario: Both enabled values are presence-sensitive
- **WHEN** otherwise identical updates pass `enabled=False` and `enabled=True`
- **THEN** their argv contain exactly `--enabled=false` and `--enabled=true`, and neither value is mistaken for omission

#### Scenario: Empty strings are explicit updates
- **WHEN** cron expression, timezone, or label is supplied as `""`
- **THEN** the corresponding flag and empty argv token are emitted so the pinned CLI's `Flags().Changed` PATCH semantics are preserved

#### Scenario: Unset fields are omitted
- **WHEN** one update field is supplied and the other three remain `Unset`
- **THEN** only the supplied update flag is present

#### Scenario: Null update field is rejected
- **WHEN** any update field is explicitly `None`
- **THEN** `TypeError` names that field and transport is not called

#### Scenario: Empty update is rejected
- **WHEN** all four update fields are `Unset`
- **THEN** `ValueError` is raised before I/O and no fallback `autopilot get` command is constructed

### Requirement: Autopilot trigger reflects the pinned response

The immutable public `AutopilotTrigger` and its private wire converter SHALL decode the pinned common and schedule trigger response using `id`, `autopilot_id`, `kind`, `enabled`, nullable `cron_expression`, `timezone`, `next_run_at`, `label`, and `last_fired_at`, plus `created_at` and `updated_at`. Timestamp fields SHALL use timezone-aware `datetime` values. Legacy `type` and tuple `config` SHALL be absent because the pinned response does not emit them. Webhook-only secret, provider, signing, and event-filter fields SHALL remain outside this schedule-focused projection and SHALL be ignored when present.

#### Scenario: Schedule trigger response decodes
- **WHEN** add, update, or get returns a schedule trigger with `kind="schedule"`, enabled state, cron, timezone, label, next-run, and audit timestamps
- **THEN** the returned `AutopilotTrigger` preserves those values and decodes every present timestamp as a timezone-aware `datetime`

#### Scenario: Nullable trigger fields remain None
- **WHEN** a schedule response contains null webhook fields, last-fired time, or optional label
- **THEN** the corresponding model attributes are `None` without fabricated `type` or `config` data

#### Scenario: Governed mutations share one response decoder
- **WHEN** trigger add, trigger update, and autopilot get-envelope trigger seeding receive the same trigger object
- **THEN** all three paths produce equal `AutopilotTrigger` values through the same private wire conversion

