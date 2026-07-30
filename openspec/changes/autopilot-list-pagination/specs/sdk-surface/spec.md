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
  `autopilots.update`, `autopilots.delete`, `autopilots.run`,
  `autopilots.history`, and `autopilots.get_run` are present with
  `compatibility` set to `intentionally_changed` and a rationale naming the
  model widening and pagination return-type change.