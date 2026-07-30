# autopilot-resource Specification

## Purpose
TBD - created by archiving change autopilot-list-pagination. Update Purpose after archive.
## Requirements
### Requirement: Governed autopilot resource

The SDK MUST expose a governed `AutopilotResource` whose operations
(`autopilots.list/get/create/update/delete/run/history`) are defined in the
approved contract with binding descriptors, signatures, responses, decoders,
and types. `autopilots.get_run` is NOT governed (no upstream single-run fetch
subcommand exists) and stays an ungoverned hand-written method.

#### Scenario: Autopilot operations are governed

- **WHEN** the approved contract `contracts/sdk-contract.json` is inspected
- **THEN** it contains operation entries for `autopilots.list`,
  `autopilots.get`, `autopilots.create`, `autopilots.update`,
  `autopilots.delete`, `autopilots.run`, and `autopilots.history`, each with a
  binding descriptor, signature, response, and source ref.
- **AND** it does NOT contain an `autopilots.get_run` operation entry (the
  `get_run` method stays ungoverned, no binding/response).

#### Scenario: Autopilot operations decode via wire converters

- **WHEN** `client.autopilots.get("a1")` is called and the CLI returns an
  `AutopilotResponse` JSON object
- **THEN** the result is an `Autopilot` decoded through `AutopilotWire` and
  `autopilot_from_wire`, not a direct `decode_json(..., Autopilot)`.

### Requirement: Autopilot model reflects upstream response

The SDK MUST model `Autopilot` with the fields the upstream
`AutopilotResponse` returns: `id`, `workspace_id`, `title`, `description`,
`project_id`, `assignee_type`, `assignee_id`, `status`, `execution_mode`,
`issue_title_template`, `created_by_type`, `created_by_id`, `last_run_at`,
`created_at`, `updated_at`, `trigger_kinds`, `next_run_at`, `last_run_status`,
`subscribers`, `can_write`, `can_manage_access`. The legacy fields `name` and
`enabled` MUST NOT be present.

#### Scenario: Full autopilot decode

- **WHEN** the CLI returns `{"id":"a1","workspace_id":"w1","title":"My AP","description":"d","project_id":"p1","assignee_type":"agent","assignee_id":"ag1","status":"active","execution_mode":"create_issue","issue_title_template":"{{date}}","created_by_type":"member","created_by_id":"u1","last_run_at":"2026-01-01T00:00:00Z","created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-02T00:00:00Z","trigger_kinds":["schedule"],"next_run_at":"2026-01-03T00:00:00Z","last_run_status":"succeeded","subscribers":[{"user_type":"member","user_id":"u2","created_at":"2026-01-01T00:00:00Z"}],"can_write":true,"can_manage_access":false}`
- **THEN** the decoded `Autopilot` has `title == "My AP"`, `status == "active"`,
  `execution_mode == "create_issue"`, `project_id == "p1"`,
  `len(subscribers) == 1`, `subscribers[0].user_id == "u2"`,
  `can_write is True`, `can_manage_access is False`, and no `name` or `enabled`
  attribute.

#### Scenario: Optional fields default to None

- **WHEN** the CLI returns `{"id":"a1","workspace_id":"w1","title":"T","assignee_type":"agent","assignee_id":"ag1","status":"active","execution_mode":"create_issue","created_by_type":"member","created_by_id":"u1","created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-02T00:00:00Z","subscribers":[]}`
- **THEN** the decoded `Autopilot` has `description is None`,
  `project_id is None`, `issue_title_template is None`, `last_run_at is None`,
  `trigger_kinds == ()`, `next_run_at is None`, `last_run_status is None`,
  `can_write is None`, `can_manage_access is None`, `subscribers == ()`.

#### Scenario: Legacy name and enabled are absent

- **WHEN** an `Autopilot` instance is constructed
- **THEN** accessing `.name` raises `AttributeError` and accessing `.enabled`
  raises `AttributeError`.

### Requirement: AutopilotRun model reflects upstream run response

The SDK MUST model `AutopilotRun` with the fields the upstream
`AutopilotRunResponse` returns: `id`, `autopilot_id`, `trigger_id`, `source`,
`status`, `issue_id`, `task_id`, `triggered_at`, `completed_at`,
`failure_reason`, `reason_code`, `trigger_payload`, `result`, `created_at`.
The legacy fields `started_at` MUST NOT be present; `completed_at` remains.

#### Scenario: Full run decode

- **WHEN** the CLI returns `{"id":"r1","autopilot_id":"a1","trigger_id":"t1","source":"manual","status":"succeeded","issue_id":"i1","task_id":"tk1","triggered_at":"2026-01-01T00:00:00Z","completed_at":"2026-01-01T00:05:00Z","failure_reason":null,"reason_code":null,"trigger_payload":null,"result":null,"created_at":"2026-01-01T00:00:00Z"}`
- **THEN** the decoded `AutopilotRun` has `source == "manual"`,
  `triggered_at == datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc)`,
  `completed_at == datetime.datetime(2026,1,1,0,5,tzinfo=datetime.timezone.utc)`,
  `issue_id == "i1"`, and no `started_at` attribute.

#### Scenario: Nullable run fields decode to None

- **WHEN** the CLI returns a run with `"completed_at": null` and
  `"issue_id": null`
- **THEN** the decoded `AutopilotRun` has `completed_at is None` and
  `issue_id is None`.

### Requirement: Autopilot list returns a page with total

`AutopilotResource.list` MUST return an `AutopilotListPage` carrying the
`autopilots` tuple and the `total` envelope key, instead of a bare
`tuple[Autopilot, ...]`.

#### Scenario: List returns total

- **WHEN** `client.autopilots.list()` is called and the CLI returns
  `{"autopilots":[{"id":"a1","title":"T","status":"active","execution_mode":"create_issue","assignee_type":"agent","assignee_id":"ag1","workspace_id":"w1","created_by_type":"member","created_by_id":"u1","created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-02T00:00:00Z","subscribers":[]}],"total":42}`
- **THEN** the result is an `AutopilotListPage` with `total == 42`,
  `len(autopilots) == 1`, and `autopilots[0].title == "T"`.

#### Scenario: Empty list page

- **WHEN** the CLI returns `{"autopilots":[],"total":0}`
- **THEN** the result is an `AutopilotListPage` with `autopilots == ()` and
  `total == 0`.

### Requirement: Autopilot history supports limit/offset and returns a page

`AutopilotResource.history` MUST accept `limit: int | None` and
`offset: int | None`, emit the upstream-correct `autopilot runs <id>`
subcommand (NOT the non-existent `autopilot history`), emit `--limit`/`--offset`
when provided, and return an `AutopilotRunListPage(runs, total, limit, offset,
has_more)`. `has_more` MUST be computed Python-side as `len(runs) < total` when
`offset is None`, or `offset + len(runs) < total` when `offset` is set.

#### Scenario: History emits the upstream runs subcommand with limit and offset

- **WHEN** `client.autopilots.history("a1", limit=10, offset=20)` is called
- **THEN** the transport receives the argv
  `("autopilot", "runs", "a1", "--limit", "10", "--offset", "20", "--output", "json")`
  via `run_bytes` (the upstream subcommand is `autopilot runs <id>`, not
  `autopilot history`).

#### Scenario: History returns a page with has_more

- **WHEN** `client.autopilots.history("a1", limit=10, offset=20)` is called and
  the CLI returns `{"runs":[...10 items...],"total":42}`
- **THEN** the result is an `AutopilotRunListPage` with `total == 42`,
  `len(runs) == 10`, `limit == 10`, `offset == 20`, and
  `has_more is True` (20 + 10 < 42).

#### Scenario: History last page has_more false

- **WHEN** `client.autopilots.history("a1", limit=10, offset=40)` is called and
  the CLI returns `{"runs":[...2 items...],"total":42}`
- **THEN** the result has `has_more is False` (40 + 2 == 42).

#### Scenario: History default limit and offset

- **WHEN** `client.autopilots.history("a1")` is called and the CLI returns
  `{"runs":[...20 items...],"total":42}`
- **THEN** the result has `limit == 20` (upstream default), `offset == 0`,
  and `has_more is True` (len(runs)=20 < total=42).

#### Scenario: History rejects negative limit

- **WHEN** `client.autopilots.history("a1", limit=-1)` is called
- **THEN** `ValueError` is raised and `"limit"` appears in the message, and
  the transport is not called.

#### Scenario: History rejects negative offset

- **WHEN** `client.autopilots.history("a1", offset=-5)` is called
- **THEN** `ValueError` is raised and `"offset"` appears in the message, and
  the transport is not called.

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

