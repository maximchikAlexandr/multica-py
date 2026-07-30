## Why

`AutopilotResource` is ungoverned (absent from `contracts/sdk-contract.json`
operations, bindings, signatures, responses, decoders) and its public surface
is both stale and lossy relative to the upstream `multica` CLI:

- `AutopilotResource.list` (src/multica_py/resources/autopilots.py:18) returns
  `tuple[Autopilot, ...]` and discards the `total` envelope key that
  `multica autopilot list --output json` already returns
  (`{"autopilots":[...],"total":N}`, verified in
  `server/cmd/multica/cmd_autopilot.go:185-189`).
- `AutopilotResource.history` (src/multica_py/resources/autopilots.py:51)
  returns `tuple[AutopilotRun, ...]`, discards `total`, and does not expose the
  upstream `--limit`/`--offset` flags the CLI registers on the `autopilot runs
  <id>` subcommand (`server/cmd/multica/cmd_autopilot.go:150-153`). The current
  SDK emits the non-existent argv `("autopilot","history",autopilot_id)` — a
  pre-existing defect: upstream has no `autopilot history` subcommand, only
  `autopilot runs <id>` (cmd_autopilot.go:64,105). This change fixes the argv
  to `("autopilot","runs",autopilot_id,...)` (the public method name `history`
  is preserved) and adds `--limit`/`--offset`.
- The public `Autopilot` model (src/multica_py/models/autopilots.py:8) carries
  only `id, name, enabled`, while the upstream `AutopilotResponse`
  (`server/internal/handler/autopilot.go:31-79`) returns
  `id, workspace_id, title, description, project_id, assignee_type,
  assignee_id, status, execution_mode, issue_title_template,
  created_by_type, created_by_id, last_run_at, created_at, updated_at,
  trigger_kinds, next_run_at, last_run_status, subscribers, can_write,
  can_manage_access`. The SDK field `name` does not exist upstream (the
  upstream field is `title`); `enabled` does not exist (the upstream field is
  `status`). `AutopilotResource.create` (src/multica_py/resources/autopilots.py:32)
  emits `--name`, but the upstream `autopilot create` command
  (`server/cmd/multica/cmd_autopilot.go:120-127`) registers `--title`,
  `--description`, `--agent`, `--mode`, `--priority`, `--project`,
  `--issue-title-template`, `--subscriber` — no `--name`.

This blocks SDK consumers from listing autopilots with paging metadata,
filtering runs by limit/offset, or reading any autopilot field beyond the three
the SDK happens to model. This was confirmed in the threaded discussion on issue
MYL-4: the only real "list-style" candidate beyond `issue list` is autopilot, and
the user approved adding it as a governed resource ("Да. Добавь также новый
ресурс автопилот").

## What Changes

### BREAKING: widen the `Autopilot` model to the upstream `AutopilotResponse` surface

- **BREAKING**: replace `Autopilot(id, name, enabled)` with
  `Autopilot(id, workspace_id, title, description, project_id, assignee_type,
  assignee_id, status, execution_mode, issue_title_template,
  created_by_type, created_by_id, last_run_at, created_at, updated_at,
  trigger_kinds, next_run_at, last_run_status, subscribers, can_write,
  can_manage_access)` in src/multica_py/models/autopilots.py. Drop `name` and
  `enabled` (no upstream backing). Add `AutopilotSubscriber` and
  `AutopilotSubscriberList` typed models for the `subscribers` array
  (`AutopilotSubscriberEntry` at
  server/internal/handler/autopilot.go:62-66).
- Add an `AutopilotWire` decoder struct in
  src/multica_py/_internal/wire_models.py and an `autopilot_from_wire` function;
  replace direct `decode_json(..., Autopilot)` decodes in
  `AutopilotResource.get/create/update` with the wire decoder path so all
  optional fields default to `None`.

### BREAKING: widen `AutopilotRun` to the upstream `AutopilotRunResponse` surface

- **BREAKING**: replace `AutopilotRun(id, status, started_at, completed_at)`
  with `AutopilotRun(id, autopilot_id, trigger_id, source, status, issue_id,
  task_id, triggered_at, completed_at, failure_reason, reason_code,
  trigger_payload, result, created_at)` matching
  `AutopilotRunResponse` (server/internal/handler/autopilot.go:137-162). Drop
  `started_at`/`completed_at` (no upstream backing; upstream uses
  `triggered_at`/`completed_at`). Add an `AutopilotRunWire` decoder and
  `autopilot_run_from_wire`.

### Pagination for `list` and `history`

- **BREAKING**: `AutopilotResource.list` SHALL return
  `AutopilotListPage(autopilots, total)` instead of `tuple[Autopilot, ...]`,
  exposing the dropped `total`. Introduce `AutopilotListPage` and
  `AutopilotListPageWire(autopilots, total)` in
  src/multica_py/models/autopilots.py and
  src/multica_py/_internal/wire_models.py.
- **BREAKING**: `AutopilotResource.history` SHALL accept
  `limit: int | None = None` and `offset: int | None = None` (emit
  `--limit`/`--offset`), emit the upstream-correct subcommand `autopilot runs
  <id>` (fixing the pre-existing `autopilot history` argv defect), and return
  `AutopilotRunListPage(runs, total, limit, offset, has_more)` instead of
  `tuple[AutopilotRun, ...]`. `has_more` is computed Python-side as
  `offset + len(runs) < total` because upstream returns only `total` (no
  `has_more`), mirroring the `issue list` precedent. Introduce
  `AutopilotRunListPage` and `AutopilotRunListPageWire(runs, total)`.
- Add a nonnegative guard on `limit`/`offset` in `AutopilotResource.history`
  raising `ValueError`.

### Governed autopilot contract

- Promote autopilot to governed: add 7 operation entries — `autopilots.list`,
  `autopilots.get`, `autopilots.create`, `autopilots.update`,
  `autopilots.delete`, `autopilots.run`, `autopilots.history` — to
  `contracts/sdk-contract.json` with binding descriptors, signatures,
  responses, decoders, types, mappings, and source refs. `autopilots.history`
  binds to the upstream-correct `autopilot runs <id>` subcommand; the public
  method name stays `history`.
- Split the `skills-squads-and-autopilots` family into two: a new `autopilot`
  family (disposition `required_compatibility`, `required_operation_ids` = the
  7 governed autopilot ops, `source_ref_ids: ["F-AUTOPILOT"]`) and a
  `skills-squads` family (disposition stays `deferred_owner_decision`,
  `required_operation_ids: []`, `source_ref_ids: ["F-SKILL","F-SKILL-RUN",
  "F-SQUAD"]`). This keeps skills/squads ungoverned and avoids any implicit
  promotion caused by a single shared disposition field.

### Out-of-scope autopilot methods (ungoverned, unchanged)

- `AutopilotResource.get_run` (src/multica_py/resources/autopilots.py:54)
  emits `("autopilot","run","get",run_id)` against an upstream subcommand that
  does not exist (upstream has no single-run fetch; only `autopilot runs <id>`
  for listing and `autopilot trigger <id>` for manual trigger). This is a
  pre-existing defect. This change does NOT add `autopilots.get_run` to the
  governed contract and does NOT alter its argv or signature; it remains an
  ungoverned hand-written method (like the autopilot triggers). Fixing the
  `get_run` argv or removing the method is deferred to a follow-up.
- `AutopilotResource.run` (manual trigger) stays governed but keeps its
  existing argv `("autopilot","run",autopilot_id)`: the upstream subcommand is
  `autopilot trigger <id>`, so this is a pre-existing argv defect NOT in scope
  to fix; the operation is marked `intentionally_changed` with a deferral
  rationale. Only its model is widened, not its argv.

### Upstream-aligned create/update signatures

- **BREAKING**: `AutopilotResource.create` signature changes from
  `create(name: str) -> Autopilot` to
  `create(title: str, *, description: str | None = None, agent: str,
  execution_mode: AutopilotExecutionMode, priority: str = "none",
  project_id: str | None = None, issue_title_template: str | None = None,
  subscribers: tuple[str, ...] = ()) -> Autopilot`, emitting
  `--title`/`--description`/`--agent`/`--mode`/`--priority`/`--project`/
  `--issue-title-template`/`--subscriber` (repeatable) per
  server/cmd/multica/cmd_autopilot.go:120-127. `--agent` and `--mode` are
  required upstream (cmd_autopilot.go:248-258).
- **BREAKING**: `AutopilotResource.update` signature changes from
  `update(autopilot_id, name=None, enabled=None) -> Autopilot` to
  `update(autopilot_id, *, title: str | None = None, description: str | None = None,
  agent: str | None = None, project_id: str | None = None, priority: str | None = None,
  status: str | None = None, execution_mode: AutopilotExecutionMode | None = None,
  issue_title_template: str | None = None, subscribers: tuple[str, ...] | None = None,
  clear_subscribers: bool = False) -> Autopilot`, emitting only changed flags
  (`Flags().Changed` semantics, cmd_autopilot.go:350-414). `project_id=None`
  omits the flag; empty-string `--project ""` clears it upstream
  (cmd_autopilot.go:368-376), so an explicit sentinel is needed: a new
  `AutopilotProjectRef` sentinel OR the convention `project_id=""` emits
  `--project ""` (clear) and `project_id=None` omits.

### Tests and generator

- Regenerate `src/multica_py/_generated/approved_sdk.py` from the approved
  contract.
- Update `OPERATION_CASES`/`LEGACY_ARGV_MIGRATION`/
  `test_discovered_public_methods` counter assertions for the new/changed
  autopilot rows.
- Table-driven decode tests for the widened models and pagination pages;
  nonnegative-limit/offset rejection tests.

## Capabilities

### New Capabilities
- `autopilot-resource`: governed autopilot SDK surface — the `Autopilot` and
  `AutopilotRun` models, the governed `AutopilotResource` methods
  (list/get/create/update/delete/run/history), pagination pages,
  upstream-aligned create/update signatures, and contract governance for the
  seven autopilot operations. `get_run` stays ungoverned (out-of-scope defect).

### Modified Capabilities
- `sdk-surface`: adds the requirement "Autopilot resource governance and
  pagination" covering the widened `Autopilot`/`AutopilotRun` models, the
  `AutopilotListPage`/`AutopilotRunListPage` return types, the
  `limit`/`offset` history filters, and the governed autopilot operations.

## Impact

- **Public API (BREAKING)**: `Autopilot`, `AutopilotRun`, `AutopilotResource`
  signatures and return types change. Consumers using `Autopilot.name` or
  `.enabled`, or `AutopilotRun.started_at`, break and must migrate to
  `title`/`status`/`triggered_at`.
- **Contract**: `contracts/sdk-contract.json` gains 7 operations, 7 binding
  descriptors, signatures, responses, decoders, types; the
  `skills-squads-and-autopilots` family is split into a governed `autopilot`
  family (`required_compatibility`) and an unchanged `skills-squads` family
  (`deferred_owner_decision`).
- **Code**: src/multica_py/models/autopilots.py,
  src/multica_py/_internal/wire_models.py,
  src/multica_py/resources/autopilots.py,
  src/multica_py/_generated/approved_sdk.py,
  contracts/sdk-contract.json, tools/upstream_contract/contract.py,
  tests/cases/operations.py, tests/contract/test_autopilot_models.py (new),
  tests/unit/resources/test_operations.py.
- **Upstream evidence**: server/cmd/multica/cmd_autopilot.go,
  server/internal/handler/autopilot.go. No new source_ref is needed beyond
  the existing autopilot command source ref added by this change.