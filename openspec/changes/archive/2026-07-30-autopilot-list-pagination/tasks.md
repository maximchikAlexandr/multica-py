## 1. Models

- [x] 1.1 In `src/multica_py/models/autopilots.py`, replace the `Autopilot`
  struct (line 8-11) with a widened frozen `msgspec.Struct`: fields
  `id: str`, `workspace_id: str`, `title: str`,
  `description: str | None = None`, `project_id: str | None = None`,
  `assignee_type: str`, `assignee_id: str`, `status: str`,
  `execution_mode: str`, `issue_title_template: str | None = None`,
  `created_by_type: str`, `created_by_id: str`,
  `last_run_at: datetime.datetime | None = None`,
  `created_at: datetime.datetime | None = None`,
  `updated_at: datetime.datetime | None = None`,
  `trigger_kinds: tuple[str, ...] = ()`,
  `next_run_at: datetime.datetime | None = None`,
  `last_run_status: str | None = None`,
  `subscribers: tuple[AutopilotSubscriber, ...] = ()`,
  `can_write: bool | None = None`, `can_manage_access: bool | None = None`.
  Drop `name` and `enabled`. `kw_only=True`, `frozen=True`.
- [x] 1.2 In `src/multica_py/models/autopilots.py`, add a new
  `AutopilotSubscriber(msgspec.Struct, frozen=True, kw_only=True)` with
  fields `user_type: str`, `user_id: str`,
  `created_at: datetime.datetime | None = None` (matching
  `AutopilotSubscriberEntry` at server/internal/handler/autopilot.go:62-66).
  Place it before `Autopilot`.
- [x] 1.3 In `src/multica_py/models/autopilots.py`, replace the `AutopilotRun`
  struct (line 14-18) with: `id: str`, `autopilot_id: str`,
  `trigger_id: str | None = None`, `source: str`, `status: str`,
  `issue_id: str | None = None`, `task_id: str | None = None`,
  `triggered_at: datetime.datetime | None = None`,
  `completed_at: datetime.datetime | None = None`,
  `failure_reason: str | None = None`, `reason_code: str | None = None`,
  `trigger_payload: object | None = None`,
  `result: object | None = None`,
  `created_at: datetime.datetime | None = None`. Drop `started_at` (no
  upstream backing). `kw_only=True`, `frozen=True`.
- [x] 1.4 In `src/multica_py/models/autopilots.py`, add
  `AutopilotListPage(msgspec.Struct, frozen=True, kw_only=True)` with
  `autopilots: tuple[Autopilot, ...] = ()` and `total: int = 0`.
- [x] 1.5 In `src/multica_py/models/autopilots.py`, add
  `AutopilotRunListPage(msgspec.Struct, frozen=True, kw_only=True)` with
  `runs: tuple[AutopilotRun, ...] = ()`, `total: int = 0`,
  `limit: int | None = None`, `offset: int | None = None`,
  `has_more: bool = False`.
- [x] 1.6 In `src/multica_py/enums.py`, add `AutopilotExecutionMode` enum
  with members `create_issue = "create_issue"` and `run_only = "run_only"`
  (matching the upstream validation at cmd_autopilot.go:253-258 and
  cmd_autopilot.go:388-392).

## 2. Wire

- [x] 2.1 In `src/multica_py/_internal/wire_models.py`, add an
  `AutopilotSubscriberWire(msgspec.Struct, frozen=True, kw_only=True)` with
  `user_type: str`, `user_id: str`,
  `created_at: datetime.datetime | None = None`. Place it near the existing
  `AutopilotListWire` (line 156).
- [x] 2.2 In `src/multica_py/_internal/wire_models.py`, add an
  `AutopilotWire(msgspec.Struct, frozen=True, kw_only=True)` carrying the
  upstream `AutopilotResponse` JSON names: `id: str`,
  `workspace_id: str`, `title: str`, `description: str | None = None`,
  `project_id: str | None = None`, `assignee_type: str`,
  `assignee_id: str`, `status: str`, `execution_mode: str`,
  `issue_title_template: str | None = None`, `created_by_type: str`,
  `created_by_id: str`, `last_run_at: datetime.datetime | None = None`,
  `created_at: datetime.datetime | None = None`,
  `updated_at: datetime.datetime | None = None`,
  `trigger_kinds: tuple[str, ...] = ()`,
  `next_run_at: datetime.datetime | None = None`,
  `last_run_status: str | None = None`,
  `subscribers: tuple[AutopilotSubscriberWire, ...] = ()`,
  `can_write: bool | None = None`, `can_manage_access: bool | None = None`.
  Import `AutopilotSubscriberWire` is local; the public `Autopilot` import
  is already present (line 10).
- [x] 2.3 In `src/multica_py/_internal/wire_models.py`, add
  `autopilot_from_wire(wire: AutopilotWire) -> Autopilot` returning an
  `Autopilot` with `subscribers` mapped via
  `tuple(AutopilotSubscriber(user_type=s.user_type, user_id=s.user_id,
  created_at=s.created_at) for s in wire.subscribers)`. Import
  `AutopilotSubscriber` from `multica_py.models.autopilots` (extend line 10).
- [x] 2.4 In `src/multica_py/_internal/wire_models.py`, add an
  `AutopilotRunWire(msgspec.Struct, frozen=True, kw_only=True)` with the
  upstream `AutopilotRunResponse` JSON names: `id: str`, `autopilot_id: str`,
  `trigger_id: str | None = None`, `source: str`, `status: str`,
  `issue_id: str | None = None`, `task_id: str | None = None`,
  `triggered_at: datetime.datetime | None = None`,
  `completed_at: datetime.datetime | None = None`,
  `failure_reason: str | None = None`, `reason_code: str | None = None`,
  `trigger_payload: object | None = None`, `result: object | None = None`,
  `created_at: datetime.datetime | None = None`.
- [x] 2.5 In `src/multica_py/_internal/wire_models.py`, add
  `autopilot_run_from_wire(wire: AutopilotRunWire) -> AutopilotRun`.
  Import `AutopilotRun` is already present (line 10).
- [x] 2.6 In `src/multica_py/_internal/wire_models.py`, widen
  `AutopilotListWire` (line 156-158) — it already has
  `autopilots: tuple[Autopilot, ...] = ()` and `total: int = 0`; change the
  `autopilots` element type to `AutopilotWire` and add
  `autopilot_list_page_from_wire(wire: AutopilotListWire) -> AutopilotListPage`
  returning `AutopilotListPage(autopilots=tuple(autopilot_from_wire(a) for a
  in wire.autopilots), total=wire.total)`. Import `AutopilotListPage` from
  `multica_py.models.autopilots` (extend line 10).
- [x] 2.7 In `src/multica_py/_internal/wire_models.py`, add an
  `AutopilotRunListPageWire(msgspec.Struct, frozen=True, kw_only=True)` with
  `runs: tuple[AutopilotRunWire, ...] = ()` and `total: int = 0`, and
  `autopilot_run_list_page_from_wire(wire: AutopilotRunListPageWire, limit:
  int | None, offset: int | None) -> AutopilotRunListPage` computing
  `has_more = (offset or 0) + len(runs) < wire.total`. Import
  `AutopilotRunListPage`.

## 3. Resource

- [x] 3.1 In `src/multica_py/resources/autopilots.py`, replace the `list`
  method (line 18-27) body to return
  `autopilot_list_page_from_wire(self._run_json_decode(("autopilot", "list",
  "--output", "json"), AutopilotListWire))`. Add a bare-array fallback:
  on `OutputShapeError`, decode `list[AutopilotWire]` and return
  `AutopilotListPage(autopilots=tuple(autopilot_from_wire(a) for a in items),
  total=len(items))`. Update imports: add `AutopilotListWire`,
  `autopilot_list_page_from_wire`, `autopilot_from_wire`, `AutopilotWire`
  from `wire_models`; `AutopilotListPage` from `models.autopilots`. Return
  type annotation `-> AutopilotListPage`.
- [x] 3.2 In `src/multica_py/resources/autopilots.py`, change `get`
  (line 29-30) to decode via wire: `return autopilot_from_wire(
  self._run_json_decode(("autopilot", "get", autopilot_id), AutopilotWire))`.
- [x] 3.3 In `src/multica_py/resources/autopilots.py`, change `create`
  (line 32-33) signature to
  `create(self, title: str, *, description: str | None = None,
  agent: str, execution_mode: AutopilotExecutionMode, priority: str = "none",
  project_id: str | None = None, issue_title_template: str | None = None,
  subscribers: tuple[str, ...] = ()) -> Autopilot`. Build argv
  `["autopilot", "create", "--title", title, "--agent", agent, "--mode",
  execution_mode.value, "--priority", priority]`, then conditionally append
  `--description`/`--project`/`--issue-title-template` when not None, and
  `--subscriber <ref>` repeated for each subscriber. Append
  `["--output", "json"]`. Decode via `autopilot_from_wire(... AutopilotWire)`.
  Import `AutopilotExecutionMode` from `multica_py.enums`.
- [x] 3.4 In `src/multica_py/resources/autopilots.py`, change `update`
  (line 35-43) signature to
  `update(self, autopilot_id: str, *, title: str | None = None,
  description: str | None = None, agent: str | None = None,
  project_id: str | None = None, priority: str | None = None,
  status: str | None = None,
  execution_mode: AutopilotExecutionMode | None = None,
  issue_title_template: str | None = None,
  subscribers: tuple[str, ...] | None = None,
  clear_subscribers: bool = False) -> Autopilot`. Emit only `Flags().Changed`
  semantics: append `--title/--description/--agent/--project/--priority/
  --status/--mode/--issue-title-template` when the field is not None
  (`execution_mode.value` for mode). For `project_id`, `None` omits the flag
  and `""` appends `--project ""` (clear). `clear_subscribers=True` appends
  `--clear-subscribers`; if both `clear_subscribers` and
  `subscribers is not None`, raise `ValueError("...clear_subscribers and
  subscribers are mutually exclusive")` before any transport call. When
  `subscribers is not None` (and not clear), append `--subscriber <ref>`
  repeated. Append `["--output", "json"]`. Decode via
  `autopilot_from_wire(... AutopilotWire)`.
- [x] 3.5 In `src/multica_py/resources/autopilots.py`, change `run`
  (line 48-49) to decode via wire: `return autopilot_run_from_wire(
  self._run_json_decode(("autopilot", "run", autopilot_id, "--output",
  "json"), AutopilotRunWire))`. Note upstream `autopilot trigger <id>` is
  emitted as `("autopilot", "run", autopilot_id)` by the current SDK; keep
  the existing argv (it is the SDK convention; verify against
  cmd_autopilot.go:56-60 which uses `autopilot trigger <id>` — if the SDK
  argv diverges, this is a pre-existing defect NOT in scope for this change;
  leave argv as-is and file a follow-up).
- [x] 3.6 In `src/multica_py/resources/autopilots.py`, replace `history`
  (line 51-52) signature with `history(self, autopilot_id: str, *,
  limit: int | None = None, offset: int | None = None) ->
  AutopilotRunListPage`. Add a nonnegative guard at the top:
  `if limit is not None and limit < 0: raise ValueError("...limit
  nonnegative")` and `if offset is not None and offset < 0: raise
  ValueError("...offset nonnegative")`. Build argv
  `["autopilot", "runs", autopilot_id]` (NOT `"history"` — upstream has no
  `autopilot history` subcommand, only `autopilot runs <id>`
  (cmd_autopilot.go:64,105); this fixes the pre-existing `history` argv
  defect, see design D9), append `--limit <n>` / `--offset <n>` when provided,
  append `["--output", "json"]`. Decode via `AutopilotRunListPageWire` and
  return `autopilot_run_list_page_from_wire(page, limit=limit, offset=offset)`.
- [x] 3.7 In `src/multica_py/resources/autopilots.py`, leave `get_run`
  (line 54-55) UNCHANGED: it stays an ungoverned hand-written method emitting
  `("autopilot","run","get",run_id,"--output","json")` against a non-existent
  upstream command (design D10). Do NOT add a contract binding for it; do NOT
  widen its decode path (it continues to use `AutopilotRun` directly via
  `_run_json_decode`). A follow-up will fix or remove this defect.
- [x] 3.8 In `src/multica_py/resources/autopilots.py`, `delete` (line 45-46)
  is unchanged (no body, `run_text`).

## 4. Approved contract

- [x] 4.1 In `contracts/sdk-contract.json`, add a source ref `S-AUTO` to the
  `source_refs` catalog covering `server/cmd/multica/cmd_autopilot.go`.
- [x] 4.2 In `contracts/sdk-contract.json`, add the following types to the
  `types` catalog: `autopilot`, `autopilot_wire`, `autopilot_subscriber`,
  `autopilot_subscriber_wire`, `autopilot_run`, `autopilot_run_wire`,
  `autopilot_list_page`, `autopilot_list_page_wire`,
  `autopilot_run_list_page`, `autopilot_run_list_page_wire`. Values are the
  public/wire class names (e.g. `"autopilot": "Autopilot"`,
  `"autopilot_wire": "AutopilotWire"`, etc.).
- [x] 4.3 In `contracts/sdk-contract.json`, add signatures to the
  `signatures` catalog: `autopilot_list` `(-> AutopilotListPage)`,
  `autopilot_get` `((autopilot_id: str) -> Autopilot)`,
  `autopilot_create` `((title: str, *, description: str | None, agent: str,
  execution_mode: AutopilotExecutionMode, priority: str, project_id: str |
  None, issue_title_template: str | None, subscribers: tuple[str, ...]) ->
  Autopilot)`, `autopilot_update` `((autopilot_id: str, *, title: str |
  None, ..., clear_subscribers: bool) -> Autopilot)`,
  `autopilot_delete` `((autopilot_id: str) -> None)`,
  `autopilot_run` `((autopilot_id: str) -> AutopilotRun)`,
  `autopilot_history` `((autopilot_id: str, *, limit: int | None,
  offset: int | None) -> AutopilotRunListPage)`. Do NOT add an
  `autopilot_get_run` signature (D10: `get_run` is not governed).
- [x] 4.4 In `contracts/sdk-contract.json`, add responses to the `responses`
  catalog: `autopilot` (`public_type_id autopilot`, `wire_type_id
  autopilot_wire`, `decoder_id decode_autopilot`, `success_exit_codes [0]`,
  `malformed_output raise_output_shape_or_decode_error`), `autopilot_run`
  (similarly), `autopilot_list_page` (`wire_type_id autopilot_list_page_wire`,
  `decoder_id decode_autopilot_list_page`), `autopilot_run_list_page`
  (`wire_type_id autopilot_run_list_page_wire`, `decoder_id
  decode_autopilot_run_list_page`), `none` for delete (reuse existing `none`
  if present).
- [x] 4.5 In `contracts/sdk-contract.json`, add decoders to the `decoders`
  map: `decode_autopilot` ->
  `multica_py._internal.wire_models.autopilot_from_wire`,
  `decode_autopilot_run` -> `autopilot_run_from_wire`,
  `decode_autopilot_list_page` -> `autopilot_list_page_from_wire`,
  `decode_autopilot_run_list_page` -> `autopilot_run_list_page_from_wire`.
- [x] 4.6 In `contracts/sdk-contract.json`, add binding descriptors to the
  `binding_descriptors` array for `autopilot_list`, `autopilot_get`,
  `autopilot_create`, `autopilot_update`, `autopilot_delete`,
  `autopilot_run`, `autopilot_history` (7 descriptors — NO
  `autopilot_get_run`, see D10). Each carries `command`, `mappings`
  (path/flag/header/body), `constraints`. The `autopilot_history` binding's
  `command` is `"autopilot runs"` (the upstream subcommand, NOT `autopilot
  history` — see D9). For `autopilot_create`: mappings `title -> --title ->
  body:title`, `description -> --description -> body:description`, `agent ->
  --agent -> body:assignee_id` (resolved), `execution_mode -> --mode ->
  body:execution_mode`, `priority -> --priority -> body:priority`,
  `project_id -> --project -> body:project_id`, `issue_title_template ->
  --issue-title-template -> body:issue_title_template`, `subscribers ->
  --subscriber -> body:subscribers` (repeatable). For `autopilot_history`:
  `autopilot_id -> <positional> -> path:autopilot_id`, `limit -> --limit ->
  query:limit`, `offset -> --offset -> query:offset`. For `autopilot_update`:
  presence-sensitive mappings with `project_id` clear-on-empty. For
  `autopilot_run`: the `command` stays `"autopilot run"` (the pre-existing
  argv defect vs upstream `autopilot trigger <id>` is deferred, D11); mark
  the operation `intentionally_changed` with that rationale.
- [x] 4.7 In `contracts/sdk-contract.json`, add `mapping_presence` entries
  for each new binding: `autopilot_create` (required: title/agent/
  execution_mode; optional_omit: description/project_id/priority/
  issue_title_template/subscribers), `autopilot_update` (optional_omit for
  all fields; `project_id` uses `optional_omit` — the `presence` enum has no
  `empty` value; `optional_omit` means `null/omitted -> omit flag`, `""` (empty)
  `-> emit flag`, which is exactly the "`None` omits, `\"\"` clears" policy),
  `autopilot_history` (optional_omit: limit/offset). The `presence` catalog
  values are `required_nonblank`, `required_value`, `optional_omit`,
  `optional_blank_omit`, `update_text`, `literal` (catalogs.presence in
  sdk-contract.json); `optional_omit` has `"empty": "emit"` matching the
  clear-on-empty semantics, so `project_id` -> `optional_omit` (NOT `empty`).
- [x] 4.8 In `contracts/sdk-contract.json`, add operation entries to the
  `operations` array: `autopilots.list`, `autopilots.get`,
  `autopilots.create`, `autopilots.update`, `autopilots.delete`,
  `autopilots.run`, `autopilots.history` (7 operations — NO
  `autopilots.get_run`, see D10). Each with `operation_id`, `compatibility:
  "intentionally_changed"`, `rationale` naming the model widening and/or
  pagination return-type change (for `autopilots.history` also name the argv
  fix to `autopilot runs <id>`; for `autopilots.run` name the deferred
  `autopilot trigger <id>` argv divergence), `source_ref_ids: ["S-AUTO"]`,
  `entrypoints` (binding + response), and `test_ref_ids` pointing to the
  relevant `manual:autopilots.*` / `generated:autopilots.*` test vectors.
- [x] 4.9 In `contracts/sdk-contract.json`, split the
  `skills-squads-and-autopilots` family entry (disposition
  `deferred_owner_decision`, `required_operation_ids: []`, `source_ref_ids:
  ["F-AUTOPILOT","F-SKILL","F-SKILL-RUN","F-SQUAD"]`) into two
  `scope.family_dispositions` entries (design D12):
  - `autopilot`: `disposition: "required_compatibility"`,
    `required_operation_ids: ["autopilots.list","autopilots.get",
    "autopilots.create","autopilots.update","autopilots.delete",
    "autopilots.run","autopilots.history"]`, `source_ref_ids:
    ["F-AUTOPILOT"]`, `rationale: "Governed autopilot resource operations."`
    (`required_compatibility` is the established disposition for a governed
    family, used by `issue-existing-changes` and `transport-error-contract`;
    per-operation `compatibility` is independent and stays
    `intentionally_changed`).
  - `skills-squads`: `disposition: "deferred_owner_decision"`,
    `required_operation_ids: []`, `source_ref_ids: ["F-SKILL","F-SKILL-RUN",
    "F-SQUAD"]`, `rationale: "No governed skill or squad operation."` (this
    preserves the exact prior status of skills/squads, isolated).
  Remove the old `skills-squads-and-autopilots` entry. Add the 7 autopilot
  operation ids to the top-level `scope.operation_ids` array (alphabetically
  grouped under `autopilots.*`).
- [x] 4.10 In `tools/upstream_contract/contract.py`, add the new auxiliary
  catalog keys to `_AUXILIARY_CATALOG_KEYS`: extend `types` frozenset
  (line 84) with `autopilot`, `autopilot_wire`, `autopilot_subscriber`,
  `autopilot_subscriber_wire`, `autopilot_run`, `autopilot_run_wire`,
  `autopilot_list_page`, `autopilot_list_page_wire`,
  `autopilot_run_list_page`, `autopilot_run_list_page_wire`; extend
  `signatures` frozenset (line 108) with `autopilot_list`, `autopilot_get`,
  `autopilot_create`, `autopilot_update`, `autopilot_delete`,
  `autopilot_run`, `autopilot_history` (NOT `autopilot_get_run` — it is not
  governed); extend `decoders` frozenset (line 131) with `decode_autopilot`,
  `decode_autopilot_run`, `decode_autopilot_list_page`,
  `decode_autopilot_run_list_page`. Add `AutopilotExecutionMode` to
  `_ENUM_TYPES` (line 45) and `_VALIDATOR_ENUM_IDS` (line 71) if the enum is
  used in validators.
- [x] 4.11 In `tools/upstream_contract/contract.py`, add any request field
  order entries needed for the autopilot request structs in
  `_REQUEST_FIELD_ORDER` (line 49) if new request types are introduced (the
  create/update use kwargs directly; add only if the contract introduces
  typed request structs).
- [x] 4.12 Update the `generated:autopilots.list:default:canonical` (and
  other generated autopilot) test vectors in `contracts/sdk-contract.json`
  `test_vectors` to reflect the new envelope stdout
  (`{"autopilots":[],"total":0}` for list; `{"runs":[],"total":0}` for
  history) and the new decoded types (`AutopilotListPage`,
  `AutopilotRunListPage`). Recompute `stdout_base64`.

## 5. Generator output

- [x] 5.1 Run
  `uv run python scripts/upstream_contract.py validate --approved
  contracts/sdk-contract.json --source-checkout /Users/alexandr/local_dev/repositories/gen_dev/multica`
  (the `S-AUTO` source ref needs the upstream checkout). Must pass.
- [x] 5.2 Run
  `uv run python scripts/upstream_contract.py render --approved
  contracts/sdk-contract.json --runtime-output
  src/multica_py/_generated/approved_sdk.py --transient-output
  /tmp/multica-transient`. The transient path MUST be outside tracked dirs.
- [x] 5.3 Re-run the render and confirm
  `git diff --stat src/multica_py/_generated/approved_sdk.py` is empty
  (idempotent). Remove `/tmp/multica-transient`.

## 6. Tests

- [x] 6.1 In `tests/cases/operations.py`, update the autopilot rows
  (lines 730-800) to reflect the new signatures and envelopes:
  - `manual:autopilots.list:canonical` — `stdout` changes from `b"[]"` to
    `b'{"autopilots":[],"total":0}'` and the result is decoded as
    `AutopilotListPage` (add `assert_result` or rely on the generated
    `decoded_type` assertion).
  - `manual:autopilots.get:canonical` — `_AP` fixture widens to a full
    `AutopilotResponse` JSON (id, workspace_id, title, status,
    execution_mode, assignee_type, assignee_id, created_by_type,
    created_by_id, created_at, updated_at, subscribers []).
  - `manual:autopilots.create:canonical` — argv changes from
    `("autopilot","create","--name","my-ap",...)` to
    `("autopilot","create","--title","my-ap","--agent","ag1","--mode","create_issue","--priority","none","--output","json")`;
    `args=("my-ap",)` becomes
    `args=("my-ap",)` with `kwargs=(("agent","ag1"),("execution_mode",AutopilotExecutionMode.create_issue))`.
  - `manual:autopilots.update:canonical` and variants — argv/kwargs change
    from `--name`/`--enabled` to `--title`/`--status`; `kwargs` use the new
    keyword-only form.
  - `manual:autopilots.run:canonical` — `_APRUN` fixture widens to a full
    `AutopilotRunResponse` JSON; argv stays `("autopilot","run","a1",
    "--output","json")` (pre-existing `autopilot trigger <id>` argv defect
    deferred, D11).
  - `manual:autopilots.get_run:canonical` — `_APRUN` fixture widens to a full
    `AutopilotRunResponse` JSON; argv stays `("autopilot","run","get","r1",
    "--output","json")` (NOT governed, D10; the method is unchanged). This row
    stays `manual:` and does NOT get a `contract_operation_id`.
  - `manual:autopilots.history:canonical` — `stdout` changes from `b"[]"`
    to `b'{"runs":[],"total":0}'`; argv changes from
    `("autopilot","history","a1","--output","json")` to
    `("autopilot","runs","a1","--output","json")` (the upstream subcommand is
    `autopilot runs <id>`, NOT `autopilot history`, see D9); add
    `kwargs=(("limit",None),("offset",None))`
    or omit (defaults); result decoded as `AutopilotRunListPage`.
  - Add new variant rows (all `manual:`, noncanonical):
    `manual:autopilots.history:variant:01` with `limit=10` → argv
    `("autopilot","runs","a1","--limit","10","--output","json")`,
    `manual:autopilots.history:variant:02` with `offset=20` → argv
    `("autopilot","runs","a1","--offset","20","--output","json")`,
    `manual:autopilots.history:variant:03` with `limit=10, offset=20` → argv
    `("autopilot","runs","a1","--limit","10","--offset","20","--output","json")`,
    `manual:autopilots.update:variant:03` with `project_id=""` (clear) → argv
    contains `--project ""`,
    `manual:autopilots.create:variant:01` with optional fields set
    (`description`, `project_id`, `issue_title_template`, `subscribers`).
  Update imports in the `_build_operation_cases` local imports block
  (lines ~441-465): add `AutopilotListPage, AutopilotRunListPage,
  AutopilotSubscriber` from `multica_py.models.autopilots` and
  `AutopilotExecutionMode` from `multica_py.enums`.
- [x] 6.2 In `tests/cases/operations.py`, add the 5 new variant rows to
  `LEGACY_ARGV_MIGRATION` continuing after the current max `legacy:138`
  (this branch is off `main`, where `LEGACY_ARGV_MIGRATION` max is 138):
  `"legacy:139": "manual:autopilots.history:variant:01"`,
  `"legacy:140": "manual:autopilots.history:variant:02"`,
  `"legacy:141": "manual:autopilots.history:variant:03"`,
  `"legacy:142": "manual:autopilots.update:variant:03"`,
  `"legacy:143": "manual:autopilots.create:variant:01"`. Reconcile indices
  with the issue-list-pagination branch at merge time (that branch adds
  legacy:139-141; renumber this branch's new entries to start after the
  merged max — the final absolute indices may shift, but the count is +5).
- [x] 6.3 In `tests/cases/legacy_payloads.py`, append 5 fingerprints for
  `legacy:139`–`legacy:143` computed with the existing helper formula
  `hashlib.sha256(repr(payload(case)).encode()).hexdigest()` where `payload`
  is the tuple from
  `tests/unit/resources/test_operations.py::test_legacy_payload_bijection`
  (lines 103-114). The fingerprint list grows 138 → 143.
- [x] 6.4 In `tests/unit/resources/test_operations.py::test_discovered_public_methods`
  (lines 79-95), recompute the counter assertions against the actual edited
  `OPERATION_CASES`. Exact final invariants (see design §Migration):
  - `len(discovered) == 117` (canonical public method set unchanged; `get_run`
    stays a public method, just ungoverned).
  - `len(OPERATION_CASES) == 146` (141 + 5 new variant rows).
  - `sum(... if c.is_canonical) == 117` (canonical unchanged).
  - `sum(... if not c.is_canonical) == 29` (24 + 5 new variants).
  - `len(generated) == 37` (30 + 7 autopilot canonical rows flip `manual:` →
    `generated:`: list/get/create/update/delete/run/history; `get_run` stays
    `manual:`).
  - `len(manual) == 109` (111 − 7 flipped + 5 new variants).
  These are exact invariants — recompute against the actual edited
  `OPERATION_CASES` before committing; no allowlist.
- [x] 6.5 In `tests/unit/resources/test_operations.py::test_legacy_payload_bijection`
  (lines 116-119), update `range(1, 139)` to `range(1, 144)` (5 new legacy
  entries: legacy:139-143), `len(LEGACY_PAYLOAD_FINGERPRINTS) == 143` (was
  138), and the bijection length `== 143` (was 138). `LEGACY_ARGV_MIGRATION`
  max becomes `legacy:143`. Reconcile the absolute indices with the
  issue-list-pagination branch at merge time (that branch also adds legacy
  entries; the +5 count is fixed).
- [x] 6.6 Create `tests/contract/test_autopilot_models.py` with
  table-driven decode tests:
  - `test_autopilot_decoding` `@pytest.mark.parametrize` over: full
    `AutopilotResponse` JSON → all fields; minimal JSON → optional fields
    `None`; `subscribers` array → typed `tuple[AutopilotSubscriber, ...]`;
    list-derived optional fields (`trigger_kinds`/`next_run_at`/
    `last_run_status`/`can_write`/`can_manage_access`) absent → defaults.
  - `test_autopilot_run_decoding` `@pytest.mark.parametrize` over: full
    `AutopilotRunResponse` JSON; nullable `completed_at`/`issue_id` → None;
    `started_at` absent (assert `AttributeError` on `.started_at`).
  - `test_autopilot_list_page_decoding`: envelope `{"autopilots":[...],
    "total":N}` → `AutopilotListPage`; empty; bare-array fallback.
  - `test_autopilot_run_list_page_decoding`: envelope with `total`; `has_more`
    computed for offset=None and offset set; last page `has_more False`;
    default limit/offset echo.
  - `test_autopilot_list_rejects_legacy_fields`: construct `Autopilot(...)`
    and assert `hasattr(ap, "name") is False`, `hasattr(ap, "enabled") is False`.
  Use `decode_json` from `multica_py._internal.decoders` and the wire
  converters. Use `mock_transport`/`ClientConfig()` fixtures for the
  resource-level tests.
- [x] 6.7 In `tests/contract/test_autopilot_models.py`, add
  `@pytest.mark.parametrize` rejection tests:
  - `test_history_rejects_negative_limit` over `(-1, -5)` — call
    `AutopilotResource(mock_transport, ClientConfig()).history("a1", limit=v)`,
    assert `ValueError` and `"limit"` in message, assert
    `mock_transport.run_bytes.assert_not_called()`. Add a `limit=0` valid row
    asserting argv equals
    `("autopilot","runs","a1","--limit","0","--output","json")` (the `runs`
    subcommand; `--limit 0` is emitted but upstream ignores it via `if v > 0`,
    see design D13 — this is an SDK pass-through assertion, not a page-content
    guarantee).
  - `test_history_rejects_negative_offset` over `(-1, -5)` — same for
    `offset`. Add an `offset=0` valid row asserting argv equals
    `("autopilot","runs","a1","--offset","0","--output","json")`.
  - `test_update_rejects_clear_subscribers_with_subscribers` —
    `.update("a1", clear_subscribers=True, subscribers=("u1",))` raises
    `ValueError` and transport not called.
  - `test_create_emits_repeatable_subscribers` —
    `.create("T", agent="ag1", execution_mode=..., subscribers=("u1","u2"))`
    argv contains `--subscriber u1 --subscriber u2`.
  - `test_update_clears_project_id_with_empty_string` —
    `.update("a1", project_id="")` argv contains `--project ""`.
  - `test_update_omits_project_id_when_none` — `.update("a1", title="x")`
    argv does NOT contain `--project`.

## 7. Verification

- [x] 7.1 `uv run pytest -m "not live"` green.
- [x] 7.2 `uv run mypy src` and `uv run mypy tests` green.
- [x] 7.3 `uv run ruff check` and `uv run ruff format --check` green.
- [x] 7.4 `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods`
  asserts the canonical method set is unchanged (117 methods) and the exact
  counters: `len(OPERATION_CASES) == 146`, canonical `== 117`, noncanonical
  `== 29`, `len(generated) == 37`, `len(manual) == 109` — no allowlist.
- [x] 7.5 `uv run pytest tests/unit/resources/test_operations.py::test_legacy_payload_bijection`
  green with 143 legacy fingerprints (`range(1, 144)`,
  `len(LEGACY_PAYLOAD_FINGERPRINTS) == 143`).
- [x] 7.6 `uv run openspec change validate autopilot-list-pagination --strict`
  green.