## 1. Agent model: typed skills and archived_at

- [x] 1.1 Add `AgentSkill(msgspec.Struct, frozen=True, kw_only=True)` with fields `id: str`, `name: str`, `enabled: bool` to `src/multica_py/models/agents.py` (before `class Agent`).
- [x] 1.2 In `src/multica_py/models/agents.py`, change `Agent.skills` from `tuple[str, ...] = ()` to `tuple[AgentSkill, ...] = ()`.
- [x] 1.3 In `src/multica_py/models/agents.py`, add `archived_at: datetime.datetime | None = None` to `Agent` (after `skills`). `import datetime` is already present.

## 2. Squad model: leader_id and archived_at

- [x] 2.1 In `src/multica_py/models/system.py`, add `import datetime` at the top (currently only `import msgspec`).
- [x] 2.2 In `src/multica_py/models/system.py`, add `leader_id: str | None = None` and `archived_at: datetime.datetime | None = None` to `Squad` (after `member_count: int = 0`). Add a `ponytail:` comment on `Squad` noting `member_type`/`role` enums are deferred until upstream values stabilise (applies to `SquadMember` in task 3).

## 3. SquadMember model and members resource

- [x] 3.1 Add `SquadMember(msgspec.Struct, frozen=True, kw_only=True)` with `member_id: str`, `member_type: str`, `role: str` to `src/multica_py/models/system.py` (after `Squad`). Add a `# ponytail: member_type/role are free str, no enum — upstream values not stabilised; add enums when they are` comment.
- [x] 3.2 Create `src/multica_py/resources/squad_members.py` with `SquadMemberResource(BaseResource)` whose `list(self, squad_id: str) -> tuple[SquadMember, ...]` calls `self._run_json_decode_list(("squad", "member", "list", squad_id), SquadMember)`. Import `SquadMember` from `multica_py.models.system`.
- [x] 3.3 In `src/multica_py/resources/squads.py`, import `SquadMemberResource` and set `self.members = SquadMemberResource(transport, config)` in `SquadResource.__init__` (mirror `AgentResource.skills` at `src/multica_py/resources/agents.py:15`).

## 4. AgentSkillResource returns typed AgentSkill

- [x] 4.1 In `src/multica_py/resources/agent_skills.py`, change the `list` return type from `tuple[Skill, ...]` to `tuple[AgentSkill, ...]` and change the `_run_json_decode_list` item type from `Skill` to `AgentSkill`. Import `AgentSkill` from `multica_py.models.agents` (replace the `Skill` import). The `set` method is unchanged.

## 5. Operation cases

- [x] 5.1 In `tests/cases/operations.py`:
  - Add `from multica_py.resources.squad_members import SquadMemberResource` to the imports inside `_build_operation_cases()`.
  - Add `("squads", "members"): "squads_members"` to `_NESTED_RESOURCE_ATTRS` (after the existing `("skills", "files"): "skill_files"` entry at line ~95). This mirrors how `("agents", "skills"): "agent_skills"` wires the nested resource. NOTE: do NOT add a literal `("squads.members", ...)` flat key — the wiring is by flat key `squads_members`, derived from this dict. Without this entry `_resource_attr("squads.members.list")` returns `"squads"` (wrong: `SquadResource.list()` takes no args), and `test_operation` raises `TypeError`.
  - Add `("squads_members", SquadMemberResource)` to `RESOURCE_SPECS` (after the `("squads", SquadResource)` entry around line 82), using the **flat key** `squads_members` — same flat-key convention as `("agent_skills", AgentSkillResource)`, `("issue_comments", IssueCommentResource)`, `("skill_files", SkillFileResource)`. Do NOT use a dotted `"squads.members"` key here; `_resource_attr` resolves `"squads.members.list"` → `"squads_members"` via `_NESTED_RESOURCE_ATTRS`, and `_RESOURCE_MAP["squads_members"]` → `SquadMemberResource`.
  - Add a pre-encoded `_SQ_MEMBERS = msgspec.json.encode([SquadMember(member_id="a1", member_type="agent", role="architecture-reviewer")])` near `_SQ` (line ~503) and import `SquadMember` from `multica_py.models.system`.
  - Add one canonical row after `manual:squads.get:canonical` (line ~1405):
    `_c("squads.members.list", ("squad", "member", "list", "s1", "--output", "json"), args=("s1",), stdout=_SQ_MEMBERS, id="manual:squads.members.list:canonical")`.
  - With the wiring in place: `discover_public_methods` produces `"squads.members.list"` (flat_key `squads_members` → `_NESTED_DOTTED_PREFIXES["squads_members"]` = `"squads.members"`); `_resource_attr("squads.members.list")` → `"squads_members"` → `_RESOURCE_MAP["squads_members"]` → `SquadMemberResource`; `SquadMemberResource.list("s1")` calls `_run_json_decode_list(("squad","member","list","s1"), SquadMember)`. Matches the existing `agents.skills`/`agent_skills` path exactly.
- [x] 5.2 Update `test_discovered_public_methods` in `tests/unit/resources/test_operations.py`:
  - `assert len(discovered) == 116` → `== 117`.
  - `assert len(OPERATION_CASES) == 140` → `== 141`.
  - `assert sum(1 for c in OPERATION_CASES if c.is_canonical) == 116` → `== 117`.
  - `assert sum(1 for c in OPERATION_CASES if not c.is_canonical) == 24` (unchanged — new row is canonical).
  - `assert len(manual) == 110` → `== 111`.
  - `assert len(generated) == 30` (unchanged).
- [x] 5.3 Run `uv run python -c "import msgspec; from multica_py.models.agents import Agent; from multica_py.models.system import Squad; print(msgspec.json.encode(Agent(id='a1', name='n'))); print(msgspec.json.encode(Squad(id='s1', name='S')))"` to capture the new `_AG` / `_SQ` bytes after the model edits. Confirm `_AG` now ends with `,"archived_at":null}` and `_SQ` now ends with `,"leader_id":null,"archived_at":null}`.

## 6. Legacy fingerprint regeneration

- [x] 6.1 After tasks 1–3 land, run this one-off to regenerate the 8 affected fingerprints and overwrite `tests/cases/legacy_payloads.py`:
  ```bash
  uv run python - <<'PY'
  import hashlib, importlib
  from tests.cases.operations import OPERATION_CASES, LEGACY_ARGV_MIGRATION
  final_by_id = {c.id: c for c in OPERATION_CASES}
  def payload(case):
      return (case.resource_attr, case.method, case.args,
              tuple(sorted(dict(case.kwargs).items())), case.transport_method,
              case.expected_argv, case.stdin, case.timeout, case.stdout)
  # Load existing fingerprints
  from tests.cases.legacy_payloads import LEGACY_PAYLOAD_FINGERPRINTS
  fps = list(LEGACY_PAYLOAD_FINGERPRINTS)
  affected_legacy = {"002","004","005","006","007","008","009","082"}
  for legacy_id, final_id in LEGACY_ARGV_MIGRATION.items():
      idx = int(legacy_id.split(":")[1])
      if f"{idx:03d}" in affected_legacy:
          fps[idx-1] = hashlib.sha256(repr(payload(final_by_id[final_id])).encode()).hexdigest()
  # Write back
  ...
  PY
  ```
  Concretely: edit `tests/cases/legacy_payloads.py` `LEGACY_PAYLOAD_FINGERPRINTS` entries at indices 1, 3, 4, 5, 6, 7, 8 (legacy 002, 004–009) and index 81 (legacy 082) to the freshly computed hashes. Keep the other 130 entries unchanged. The tuple length MUST stay 138.
- [x] 6.2 Run `uv run pytest tests/unit/resources/test_operations.py::test_legacy_payload_bijection -v` and confirm it passes. If any other legacy row fails, its fingerprint also drifted — regenerate it too and note which row in the run.

## 7. Decoder contract tests

- [x] 7.1 Create `tests/contract/test_executor_models.py` with `pytestmark = [pytest.mark.contract]` (or rely on the `tests/contract/` path marker auto-applied by `tests/conftest.py`). Add two `@pytest.mark.parametrize` tests:
  - `test_executor_field_decoding`: rows as `(model_type, json_bytes, expected_field, expected_value)` covering:
    - Agent with skill object: `{"id":"a1","name":"n","skills":[{"id":"sk_1","name":"openspec-propose","enabled":true}]}` → `Agent.skills[0] == AgentSkill(id="sk_1", name="openspec-propose", enabled=True)`.
    - Agent with `archived_at: null` → `Agent.archived_at is None`.
    - Agent with `archived_at: "2026-07-28T11:47:17Z"` → `Agent.archived_at == datetime.datetime(2026,7,28,11,47,17,tzinfo=datetime.timezone.utc)`.
    - Agent missing `skills`/`archived_at` → `Agent.skills == ()` and `Agent.archived_at is None`.
    - Squad with `leader_id: "leader-1"` → `Squad.leader_id == "leader-1"`.
    - Squad with `leader_id: null` / missing → `Squad.leader_id is None`.
    - Squad with `archived_at: null` → `Squad.archived_at is None`.
    - Squad with `archived_at: "2026-07-28T11:47:17Z"` → `Squad.archived_at == datetime.datetime(2026,7,28,11,47,17,tzinfo=datetime.timezone.utc)`.
    - Existing minimal Squad `{"id":"s1","name":"S","member_count":0}` → `Squad.leader_id is None`, `Squad.archived_at is None`, `Squad.member_count == 0`.
    Decode via `decode_json(json_bytes, model_type, command="test")`.
  - `test_squad_member_decoding`: decode `[{"member_id":"a1","member_type":"agent","role":"architecture-reviewer"},{"member_id":"u1","member_type":"member","role":"reviewer"}]` via `decode_json(bytes, list[SquadMember], command="test")` and assert the two `SquadMember` objects preserve `member_id`, `member_type`, `role` in order.
  Reuse `decode_json` from `multica_py._internal.decoders` and `AgentSkill`/`Agent`/`Squad`/`SquadMember` from their model modules. No new fixtures, no new factories — inline JSON bytes in the parametrize rows per AGENTS.md "Table-driven first".

## 8. Verification

- [x] 8.1 `uv run pytest -m "not live"` green.
- [x] 8.2 `uv run mypy src` and `uv run mypy tests` green (no `Any` leaks; `AgentSkill`/`SquadMember` are typed structs).
- [x] 8.3 `uv run ruff check .` and `uv run ruff format --check .` green.
- [x] 8.4 `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods -v` asserts 117 canonical methods and 141 total cases.
- [x] 8.5 `uv run pytest tests/unit/resources/test_operations.py::test_legacy_payload_bijection -v` passes with the 8 regenerated fingerprints.
- [x] 8.6 `uv run pytest tests/contract/test_executor_models.py -v` passes all decoder rows.