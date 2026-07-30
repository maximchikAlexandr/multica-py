## ADDED Requirements

### Requirement: Autopilot resource governance and pagination

The SDK MUST govern the autopilot resource operations in the approved contract
and MUST expose pagination metadata on `autopilots.list` and
`autopilots.history`, consistent with the issue-list pagination surface.

#### Scenario: Autopilot list returns AutopilotListPage

- **WHEN** `client.autopilots.list()` is called and the CLI returns
  `{"autopilots":[...],"total":N}`
- **THEN** the result is an `AutopilotListPage` with `total == N` and an
  `autopilots: tuple[Autopilot, ...]` field, not a bare `tuple[Autopilot, ...]`.

#### Scenario: Autopilot history returns AutopilotRunListPage

- **WHEN** `client.autopilots.history("a1", limit=10, offset=20)` is called and
  the CLI returns `{"runs":[...],"total":N}`
- **THEN** the result is an `AutopilotRunListPage` with `total`, `limit`,
  `offset`, and a Python-computed `has_more`.

#### Scenario: Autopilot operations are in the approved contract

- **WHEN** the approved contract operation list is inspected
- **THEN** `autopilots.list`, `autopilots.get`, `autopilots.create`,
  `autopilots.update`, `autopilots.delete`, `autopilots.run`, and
  `autopilots.history` are present with `compatibility` set to
  `intentionally_changed` and a rationale naming the model widening and
  pagination return-type change (and, for `history`, the argv fix to the
  upstream `autopilot runs <id>` subcommand; for `run`, the deferred
  `autopilot trigger <id>` argv divergence).
- **AND** `autopilots.get_run` is NOT present (it stays ungoverned; upstream
  has no single-run fetch subcommand).