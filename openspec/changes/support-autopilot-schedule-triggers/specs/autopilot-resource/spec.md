## MODIFIED Requirements

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

## ADDED Requirements

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
