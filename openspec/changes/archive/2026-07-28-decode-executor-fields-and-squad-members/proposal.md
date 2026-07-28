## Why

The Multica CLI already returns executor fields that AI Factory must verify
before activation (agent archive state, assigned skill objects, squad leader
and archive state, squad member roster), but `multica-py` drops them:

- `Agent.skills` is typed as `tuple[str, ...]` while the CLI returns skill
  objects with `id`, `name`, `enabled`;
- `Agent` has no `archived_at` field;
- `Squad` has no `leader_id` or `archived_at` fields;
- there is no `squad member list` operation, so the SDK cannot read a squad's
  member roster.

This blocks downstream consumers (e.g. AI Factory activation checks) from
validating configured agents and Review/Fix squads through the typed SDK.

## What Changes

- **BREAKING**: `Agent.skills` changes from `tuple[str, ...]` to
  `tuple[AgentSkill, ...]`, where `AgentSkill` is a new typed model
  (`id`, `name`, `enabled`). Existing fixtures that supplied string skill ids
  must be updated to the typed shape.
- Add `Agent.archived_at: datetime.datetime | None = None` (RFC3339 decoded,
  `null` → `None`).
- Add `Squad.leader_id: str | None = None` and
  `Squad.archived_at: datetime.datetime | None = None`.
- Add `AgentSkill` model (`id`, `name`, `enabled`) in
  `multica_py.models.agents`.
- Add `SquadMember` model (`member_id`, `member_type`, `role`) in
  `multica_py.models.system`.
- Add `SquadMemberResource` with `list(squad_id) -> tuple[SquadMember, ...]`
  running `multica squad member list <squad-id> --output json`.
- Wire `SquadResource.members = SquadMemberResource(...)` (same nested-resource
  pattern as `AgentResource.skills` and `IssueResource.comments`).
- Ensure the assigned-skills read path (`AgentSkillResource.list`) returns the
  same typed `AgentSkill` (currently it decodes the generic `Skill` model).
- Add table-driven tests (decoder fixtures + argv operation cases) and keep
  existing minimal fixtures decoding by virtue of additive optional fields.

The `Agent.skills` type change is the only breaking edit; every other field is
additive with `None` defaults, so older CLI responses without the new keys keep
decoding.

## Capabilities

### New Capabilities
<!-- None: this change widens existing resource/model surfaces, it does not
     introduce a new capability boundary. -->

### Modified Capabilities
- `sdk-surface`: adds the requirement "Executor fields and squad member
  decoding" covering typed `AgentSkill`, `Agent.archived_at`, `Squad.leader_id`,
  `Squad.archived_at`, the `SquadMember` model, and the
  `client.squads.members.list` operation.

## Impact

- Public models: `multica_py.models.agents.Agent` and `AgentSkill` (new);
  `multica_py.models.system.Squad` and `SquadMember` (new).
- Public resources: `multica_py.resources.squads.SquadResource` gains a nested
  `members` resource; `AgentSkillResource.list` return type moves to
  `tuple[AgentSkill, ...]`.
- Contract: the `skills-squads-and-autopilots` family is
  `deferred_owner_decision` with `required_operation_ids: []`, so the new
  `squad member list` operation is ungoverned (Python-only, like the existing
  `squads.list` / `squads.get` and `agent skill list` operations). No
  `contracts/sdk-contract.json` binding is added for it; the operation is
  hand-written in `SquadMemberResource`.
- Tests: new rows in `tests/cases/operations.py` and decoder fixtures in a
  table-driven contract test; the canonical public-method count in
  `test_discovered_public_methods` rises by one (`squads.members.list`).
- No new dependencies; `msgspec` decodes RFC3339 timestamps into
  `datetime.datetime` natively.