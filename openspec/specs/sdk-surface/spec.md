## Purpose

Define the public synchronous SDK surface, its type guarantees, and its
distribution boundary.
## Requirements
### Requirement: Synchronous resource client
The SDK MUST expose one synchronous `MulticaClient` with stateless domain resources and immutable typed models.
#### Scenario: Resource calls remain stateless
- **WHEN** a consumer calls a resource method
- **THEN** no model performs hidden I/O or Active Record persistence.
<!-- Source IDs: 001:FR-001,FR-002,FR-003,FR-004,FR-005 -->

### Requirement: Public resource surface
The SDK MUST retain every public resource method present in the canonical operation table.
#### Scenario: Public methods have canonical rows
- **WHEN** a public resource method exists
- **THEN** one canonical operation row covers it.
<!-- Source IDs: 001:FR-018–FR-031,005:FR-019–FR-025 -->

### Requirement: Closed public types
The SDK MUST use immutable `msgspec` models and closed public enums or primitive unions without public `Any`.
#### Scenario: Structured output stays closed and typed
- **WHEN** structured output is decoded
- **THEN** it is a typed model or documented closed primitive.
<!-- Source IDs: 001:FR-033–FR-039 -->

### Requirement: Distribution boundary
The distribution MUST remain `multica-py`, import as `multica_py`, include `py.typed`, and import without a CLI.
#### Scenario: Clean installation imports without a CLI
- **WHEN** installed cleanly
- **THEN** `import multica_py` succeeds before a CLI invocation.
<!-- Source IDs: 001:FR-006A–FR-006D,FR-047–FR-050B -->

### Requirement: Executor fields and squad member decoding
The SDK SHALL decode the executor fields the Multica CLI already returns on `agent get`, `agent list`, and `squad get`, and SHALL expose a typed `squad member list` operation.
#### Scenario: Agent skills decode as typed AgentSkill objects
- **WHEN** the CLI response for `agent get` / `agent list` contains `"skills": [{"id":"sk_1","name":"openspec-propose","enabled":true}]`
- **THEN** the decoded `Agent.skills` is `tuple[AgentSkill, ...]` with `AgentSkill(id="sk_1", name="openspec-propose", enabled=True)`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Agent with no skills decodes to empty tuple
- **WHEN** the CLI response omits `skills` or returns `"skills": []`
- **THEN** the decoded `Agent.skills` is `()`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Agent archived_at null decodes to None
- **WHEN** the CLI response contains `"archived_at": null` or omits the key
- **THEN** the decoded `Agent.archived_at` is `None`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Agent archived_at RFC3339 decodes to datetime
- **WHEN** the CLI response contains `"archived_at": "2026-07-28T11:47:17Z"`
- **THEN** the decoded `Agent.archived_at` is a `datetime.datetime` equal to `datetime.datetime(2026, 7, 28, 11, 47, 17, tzinfo=datetime.timezone.utc)`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Assigned skills read returns typed AgentSkill
- **WHEN** `client.agents.skills.list("a1")` is called and the CLI returns `{"id":"sk_1","name":"openspec-propose","enabled":true}`
- **THEN** the result is `tuple[AgentSkill, ...]` with `AgentSkill(id="sk_1", name="openspec-propose", enabled=True)`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad leader_id decodes
- **WHEN** the CLI response for `squad get` / `squad list` contains `"leader_id": "leader-agent-id"`
- **THEN** the decoded `Squad.leader_id` is `"leader-agent-id"`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad leader_id absent decodes to None
- **WHEN** the CLI response omits `leader_id` or returns `"leader_id": null`
- **THEN** the decoded `Squad.leader_id` is `None`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad archived_at null decodes to None
- **WHEN** the CLI response contains `"archived_at": null` or omits the key
- **THEN** the decoded `Squad.archived_at` is `None`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad archived_at RFC3339 decodes to datetime
- **WHEN** the CLI response contains `"archived_at": "2026-07-28T11:47:17Z"`
- **THEN** the decoded `Squad.archived_at` is a `datetime.datetime` equal to `datetime.datetime(2026, 7, 28, 11, 47, 17, tzinfo=datetime.timezone.utc)`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Existing minimal squad fixture still decodes
- **WHEN** a fixture encodes `Squad(id="s1", name="S")` with no `leader_id` or `archived_at`
- **THEN** it decodes back to a `Squad` with `leader_id is None` and `archived_at is None` and `member_count == 0`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad member list emits exact argv
- **WHEN** `client.squads.members.list("sq_1")` is called
- **THEN** the transport receives the argv `("squad", "member", "list", "sq_1", "--output", "json")` via `run_bytes`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad member list returns typed members
- **WHEN** `client.squads.members.list("sq_1")` is called and the CLI returns `[{"member_id":"a1","member_type":"agent","role":"architecture-reviewer"}]`
- **THEN** the result is `tuple[SquadMember, ...]` with `SquadMember(member_id="a1", member_type="agent", role="architecture-reviewer")`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad member list with multiple roles preserves each
- **WHEN** the CLI returns multiple members with distinct roles
- **THEN** each `SquadMember` preserves its `member_id`, `member_type`, and `role` verbatim, in response order.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

Specifically:

- `Agent.skills` SHALL be `tuple[AgentSkill, ...]` where `AgentSkill` is a frozen `msgspec.Struct` with `id: str`, `name: str`, `enabled: bool`.
- `Agent` SHALL decode `archived_at` as `datetime.datetime | None`, where JSON `null` decodes to `None` and an RFC3339 timestamp decodes to a `datetime.datetime`.
- `Squad` SHALL decode `leader_id: str | None = None` and `archived_at: datetime.datetime | None = None`.
- A `SquadMember` model (frozen `msgspec.Struct`, `member_id: str`, `member_type: str`, `role: str`) SHALL decode the `multica squad member list <squad-id> --output json` response.
- `SquadResource` SHALL expose a nested `members` resource whose `list(squad_id)` method returns `tuple[SquadMember, ...]` and emits the argv `("squad", "member", "list", <squad-id>, "--output", "json")`.
- `AgentSkillResource.list` SHALL return `tuple[AgentSkill, ...]` (same typed shape as `Agent.skills`), replacing the previous generic `Skill` decode.

All new scalar fields are additive with `None` defaults so that fixtures and older CLI responses omitting them continue to decode.
