## Context

`AutopilotResource` (src/multica_py/resources/autopilots.py) is an ungoverned
SDK surface: it is absent from `contracts/sdk-contract.json` (the
`skills-squads-and-autopilots` family is `deferred_owner_decision`), and its
public models diverge sharply from the upstream `multica` CLI. The upstream
`AutopilotResponse` (server/internal/handler/autopilot.go:31-79) returns ~20
fields; the SDK `Autopilot` (src/multica_py/models/autopilots.py:8) models three
(`id, name, enabled`), and two of those (`name`, `enabled`) have no upstream
backing — the upstream fields are `title` and `status`. The upstream
`autopilot list` and `autopilot runs` commands return pagination envelopes
(`{"autopilots":[...],"total":N}` and `{"runs":[...],"total":N}`) that the SDK
discards, and `autopilot runs` exposes `--limit`/`--offset` flags
(server/cmd/multica/cmd_autopilot.go:152-153) that the SDK does not surface. The
upstream `autopilot create`/`update` commands register a rich flag set
(`--title`, `--description`, `--agent`, `--mode`, `--priority`, `--project`,
`--issue-title-template`, `--subscriber`, `--clear-subscribers`) that the SDK
does not emit.

This change promotes autopilot to a governed contract resource, widens the
models to the upstream surface, and adds pagination. The precedent is the
`issue-list-pagination` change: expose a `*ListPage` return type, dropped
metadata, and `--limit`/`--offset` filter flags.

The contract pipeline split (AGENTS.md) applies: `sdk-contract.json` is the
human/agent-approved contract; `generator/` deterministically renders the
approved SDK. Evidence files do not drive generation. Autopilot has existing
`manual:autopilots.*` test vectors and `legacy_argv_migration` entries but no
binding descriptors, signatures, responses, decoders, or operations — this
change creates all of them.

## Goals / Non-Goals

**Goals:**
- Govern autopilot: add 7 operations (`autopilots.list/get/create/update/
  delete/run/history`) to the approved contract with full binding descriptors,
  signatures, responses, decoders, types, and mappings. (`autopilots.get_run`
  is NOT governed — see D10.)
- Widen `Autopilot` and `AutopilotRun` to the upstream `AutopilotResponse` and
  `AutopilotRunResponse` fields, via wire decoders (`*_from_wire`).
- Add `AutopilotListPage(autopilots, total)` and
  `AutopilotRunListPage(runs, total, limit, offset, has_more)` return types;
  expose `--limit`/`--offset` on `history`, and fix the `history` argv to the
  upstream-correct `autopilot runs <id>` subcommand (D9).
- Align `create`/`update` signatures to upstream flags, including the
  `project_id=""` clears / `project_id=None` omits presence policy.
- Regenerate `approved_sdk.py` and update the test-counter invariants.

**Non-Goals:**
- Autopilot triggers (`autopilot trigger-add/update/delete/rotate-url`,
  `autopilot triggers list`) remain ungoverned — they are a separate
  `autopilot_triggers` resource already partly covered by test vectors; this
  change does not promote them. The `AutopilotTriggerResource` is left
  unchanged.
- Autopilot collaborators (`/api/autopilots/:id/collaborators`) are not in the
  upstream CLI surface and are out of scope.
- `AutopilotResource.run` (manual trigger) keeps its existing argv
  `("autopilot","run",autopilot_id)`: upstream `autopilot trigger <id>` is a
  pre-existing argv defect NOT in scope to fix (D11). Only its model is
  widened, not its argv. The operation is still governed (with the wrong
  argv) and marked `intentionally_changed` with a deferral rationale.
- `AutopilotResource.get_run` is NOT governed and NOT altered by this change:
  upstream has no single-run fetch subcommand, so the current
  `("autopilot","run","get",run_id)` argv is a pre-existing defect. It stays
  an ungoverned hand-written method (D10). Fixing/removing it is a follow-up.
- The list-only derived fields (`trigger_kinds`, `next_run_at`,
  `last_run_status`) and permission fields (`can_write`, `can_manage_access`)
  are modelled as optional `None` defaults — this change does not add SDK
  helpers around them, only typed decode.

## Decisions

### D1: Widen models via wire decoders, not direct `decode_json(..., Autopilot)`

The current `AutopilotResource.get/create/update` call
`self._run_json_decode((...), Autopilot)` directly. The upstream
`AutopilotResponse` has nullable pointer fields (`*string`) and nested
`subscribers []AutopilotSubscriberEntry`; a direct decode into a public
`msgspec.Struct` would force every optional field onto the public model with
upstream JSON names. Instead, add `AutopilotWire` / `AutopilotRunWire` wire
structs in `wire_models.py` (carrying upstream JSON names incl. nested
`AutopilotSubscriberWire`) and `autopilot_from_wire` / `autopilot_run_from_wire`
converters, mirroring the existing `issue_from_wire` / `project_from_wire`
pattern. The resource methods decode to the wire struct then convert. This
keeps the public model free of upstream naming quirks and centralizes decode
logic.

**Alternative considered**: widen `Autopilot` directly with all upstream
fields and decode into it. Rejected because the existing `issue`/`project`
precedent uses wire converters for nullable/rename cases, and `subscribers`
needs a typed nested model that the public surface should expose as
`tuple[AutopilotSubscriber, ...]`, not a raw dict.

### D2: `name`/`enabled` are dropped, not aliased

The SDK `Autopilot.name` and `.enabled` have no upstream backing. Upstream
returns `title` and `status`. Adding aliases (`name = title`) would silently
return `None` for `name` on real responses and mislead callers. Dropping them
is a clean break; the contract marks these operations
`intentionally_changed`. Consumers migrate `ap.name` → `ap.title`,
`ap.enabled` → `ap.status`.

### D3: `AutopilotRun.started_at`/`completed_at` → `triggered_at`/`completed_at`

Upstream `AutopilotRunResponse` (autopilot.go:137-162) has `triggered_at`
(string, always present) and `completed_at` (*string, nullable). The SDK
`started_at` does not exist upstream. Drop `started_at`, keep `completed_at`
with the same nullable semantics, add `triggered_at`.

### D4: `has_more` is computed Python-side for `history`

Upstream `autopilot runs --output json` returns `{"runs":[...],"total":N}`
with no `has_more` (cmd_autopilot.go:484-492). To give callers a usable
page-end signal, `AutopilotResource.history` computes
`has_more = offset is not None and (offset + len(runs)) < total` (or
`len(runs) < total` when `offset is None`), mirroring the `issue list`
precedent where the CLI itself derives `has_more`. `limit`/`offset` on the
returned page echo the request values (or the upstream defaults 20/0 when
omitted) so callers can resume.

### D5: `create` makes `agent` and `execution_mode` required positional-or-keyword

Upstream `autopilot create` requires `--title`, `--agent`, `--mode`
(cmd_autopilot.go:248-258) and validates `--mode` is `create_issue` or
`run_only`. The SDK signature `create(title: str, *, description=None,
agent: str, execution_mode: AutopilotExecutionMode, priority="none",
project_id=None, issue_title_template=None, subscribers=()) -> Autopilot`
makes `title` positional and the rest keyword-only, with `agent` and
`execution_mode` keyword-required (no default). A new
`AutopilotExecutionMode` enum (`"create_issue"`, `"run_only"`) is added to
`src/multica_py/enums.py`. `--subscriber` is repeatable so `subscribers:
tuple[str, ...] = ()` emits one `--subscriber` per element.

### D6: `update` presence policy — `project_id=""` clears, `None` omits

Upstream `autopilot update` uses `Flags().Changed("project")`: empty string
`--project ""` sets `body["project_id"] = nil` (clear), and an unchanged flag
leaves the field untouched (cmd_autopilot.go:368-376). The SDK represents this
with `project_id: str | None = None` where `None` means "omit the flag" and
`""` means "emit `--project ""` to clear". This matches the existing
`IssueCreateRequest.project_id` presence policy and needs no sentinel. All
other `update` fields use `None`-omits-flag. `clear_subscribers: bool = False`
emits `--clear-subscribers` when true and conflicts with `subscribers`
(cmd_autopilot.go:388-396) — a Python-side guard raises `ValueError` when both
are set.

### D7: `status` filter on `list` is deferred

Upstream `autopilot list` has `--status` (active/paused) (cmd_autopilot.go:112)
but no `--limit`/`--offset`. The upstream `total` is the full count, not a
filtered count, and `--status` filters server-side. This change does not add a
`status` filter to `list` to keep scope tight; it only exposes `total`. A
follow-up can add `AutopilotListFilter(status)`.

### D8: Contract source ref

A new source ref `S-AUTO` (cmd_autopilot.go) is added to
`contracts/sdk-contract.json` `source_refs` catalog covering the autopilot
command file. The handler file (autopilot.go) is referenced in rationale but
does not need a separate source ref — the contract governs CLI behavior, and
the command file is the CLI surface.

### D9: `history` argv fixed to the upstream `autopilot runs <id>` subcommand

The current `AutopilotResource.history` emits
`("autopilot","history",autopilot_id)`, but upstream has no `autopilot
history` subcommand — only `autopilot runs <id>` (cmd_autopilot.go:64
`Use: "runs <id>"`, line 105 `AddCommand(autopilotRunsCmd)`). The full
upstream subcommand list is `list, get, create, update, delete, trigger,
runs, trigger-add, trigger-update, trigger-delete, trigger-rotate-url`. The
`history` argv is therefore a pre-existing defect: upstream CLI rejects it as
an unknown command. Because pagination of autopilot runs is impossible against
a non-working argv, this change fixes it: `history` SHALL emit
`("autopilot","runs",autopilot_id,"--limit",n?,"--offset",n?,"--output",
"json")`. The public Python method name stays `history` (no API rename) —
only the emitted argv changes, and the operation is marked
`intentionally_changed` with rationale naming the argv fix.

**Alternative considered**: defer the argv fix like `run` (D11) and keep
`history`. Rejected — unlike `run` (whose upstream command exists under a
different name and could be fixed by a rename), `history` has NO upstream
equivalent at all; the governed `autopilots.history` operation would describe
non-working behavior. The spec scenario MUST assert the upstream-correct
`runs` argv, not the broken `history` argv.

### D10: `get_run` is NOT governed — no upstream single-run fetch exists

Upstream has no subcommand to fetch a single autopilot run by id: only
`autopilot runs <id>` (list runs of an autopilot) and `autopilot trigger <id>`
(manual trigger). The current `AutopilotResource.get_run` emits
`("autopilot","run","get",run_id)` against a non-existent command — a
pre-existing defect. This change does NOT add `autopilots.get_run` to the
governed contract (no binding/signature/response) and does NOT alter its argv
or signature; it stays an ungoverned hand-written method like the autopilot
triggers. The `manual:autopilots.get_run:canonical` test row stays `manual:`
(does NOT flip to `generated:`), so it contributes to the canonical public
method set but not to the governed operation count. Fixing the argv or
removing the method is deferred to a follow-up.

**Alternative considered**: govern `get_run` as `cli_only`/`deferred`.
Rejected — the contract must not describe behavior upstream does not provide;
governing a non-existent command invites the generator to emit binding code
that can never succeed against a real CLI. Leaving it ungoverned (option a) is
cleaner and matches how triggers are handled.

### D11: `run` argv defect deferred (governed with wrong argv)

`AutopilotResource.run` emits `("autopilot","run",autopilot_id)`; the
upstream subcommand is `autopilot trigger <id>` (cmd_autopilot.go:56-60). This
is a pre-existing argv defect. Unlike `history` (D9), the upstream command
exists under a different name, so the defect is a rename, not a missing
command. Renaming the emitted argv is out of scope for this change: the
operation IS governed (it flips `manual:` → `generated:`) but keeps the
existing argv, and is marked `intentionally_changed` with rationale "argv
divergence pre-existing (autopilot trigger <id> vs autopilot run), deferred".
A follow-up can rename the argv (and possibly the method) once the impact on
the trigger resource is assessed.

### D12: Family split — `autopilot` (governed) + `skills-squads` (deferred)

The `skills-squads-and-autopilots` family (disposition
`deferred_owner_decision`, `required_operation_ids: []`,
`source_ref_ids: ["F-AUTOPILOT","F-SKILL","F-SKILL-RUN","F-SQUAD"]`) has a
single `disposition` field covering skills, squads, AND autopilot. Narrowing
the whole family to a "covered" disposition would implicitly promote
skills/squads, which must stay ungoverned. There is no `covered` disposition
value in the contract (used dispositions are `required_compatibility`,
`deferred_owner_decision`, `required_subset_plus_*`, `cli_only_*`,
`separate_extension_candidate`); the contract validator
(tools/upstream_contract/contract.py:986-990) only requires `disposition` to
be a string, so a new value is technically allowed, but reusing an existing
value is safer.

This change SPLITS the family into two `scope.family_dispositions` entries:
- `autopilot`: `disposition: "required_compatibility"`,
  `required_operation_ids` = the 7 governed autopilot ops (`autopilots.list`,
  `autopilots.get`, `autopilots.create`, `autopilots.update`,
  `autopilots.delete`, `autopilots.run`, `autopilots.history`),
  `source_ref_ids: ["F-AUTOPILOT"]`, rationale "Governed autopilot resource
  operations." `required_compatibility` is the established disposition for a
  family whose operations are governed (used by `issue-existing-changes` and
  `transport-error-contract`); per-operation `compatibility` is independent
  (our ops are `intentionally_changed`).
- `skills-squads`: `disposition: "deferred_owner_decision"`,
  `required_operation_ids: []`, `source_ref_ids: ["F-SKILL","F-SKILL-RUN",
  "F-SQUAD"]`, rationale "No governed skill or squad operation." This is the
  exact prior status of skills/squads, isolated.

**Alternative considered**: keep one family, leave `disposition` as
`deferred_owner_decision`, add the 7 autopilot ops to
`required_operation_ids`. Rejected — `deferred_owner_decision` semantically
means "owner decides later", contradicting "these ops are now required";
the split keeps the semantics honest and prevents any future reader from
inferring skills/squads are governed.

### D13: `limit=0` / `offset=0` are SDK pass-through with no upstream effect

`--limit`/`--offset` on `autopilot runs` use `if v > 0` upstream
(cmd_autopilot.go:498-503), so `--limit 0` / `--offset 0` are accepted by the
SDK (the nonnegative guard permits 0) and emitted on argv, but upstream
ignores them and returns the default page (limit default 20, offset 0). The
SDK-level argv assertion is correct (the flags ARE emitted); the returned
page simply reflects upstream defaults. This is documented here so the
`limit=0`/`offset=0` valid-row tests (tasks 6.7) are understood as
pass-through assertions, not behavioral guarantees about the page contents.

## Risks / Trade-offs

- **[BREAKING model change]** → Mitigation: the contract marks the seven
  governed operations `intentionally_changed` with rationale naming the field
  renames; no alias shim is added because `name`/`enabled`/`started_at` would
  return `None` on real data and mask migration. The change is documented in
  the proposal Impact section.
- **[List-derived optional fields may be absent on older servers]**
  (trigger_kinds/next_run_at/last_run_status, can_write/can_manage_access are
  documented as list-endpoint-only or caller-context-dependent in
  autopilot.go:55-79) → Mitigation: all are `None` defaults on the wire and
  public model; decode is additive and backward-compatible.
- **[`has_more` is a heuristic, not server-provided]** → Mitigation: document
  it on `AutopilotRunListPage.has_more` and compute it deterministically from
  `total`; the same approach is accepted for `issue list`.
- **[Large contract-surface diff]** (8 new operations + bindings +
  signatures + responses + decoders + types) → Mitigation: the change is
  structured into model/wire/resource/contract/generator/test tasks so each
  layer is reviewable independently; the `issue-list-pagination` change is the
  reference for the pagination layer.
- **[`subscribers` nested model adds surface area]** → Mitigation: only
  `AutopilotSubscriber(user_type, user_id, created_at)` is modelled; the richer
  collaborator entry is out of scope.

## Migration Plan

1. Implement models, wire, resource (tasks 1-3) on this branch.
2. Update contract (task 4) and regenerate (task 5).
3. Update tests and counters (task 6).
4. Verify offline suite + mypy + ruff (task 7).
5. The breaking model change ships in the same release as the contract
   promotion; consumers migrate `name`→`title`, `enabled`→`status`,
   `started_at`→`triggered_at` in one step.

### Exact counter deltas (baseline on `main`)

Baseline (current `main`, `tests/unit/resources/test_operations.py`):
`len(discovered) == 117`, `len(OPERATION_CASES) == 141`, canonical `== 117`,
noncanonical `== 24`, `len(generated) == 30`, `len(manual) == 111`;
`LEGACY_ARGV_MIGRATION` max `legacy:138`, `len(LEGACY_PAYLOAD_FINGERPRINTS)
== 138`, `range(1, 139)`.

This change:
- Adds 5 new `manual:` variant rows (`autopilots.history:variant:01/02/03`,
  `autopilots.update:variant:03`, `autopilots.create:variant:01`) → total
  `+5`, noncanonical `+5`.
- Flips 7 canonical autopilot rows `manual:` → `generated:` (they gain a
  `contract_operation_id`): `autopilots.list/get/create/update/delete/run/
  history`. `autopilots.get_run` stays `manual:` (NOT governed, D10).
  → generated `+7`, manual `-7` (then `+5` from the new variants).

Final invariants (exact):
- `len(discovered) == 117` (canonical public method set unchanged — `get_run`
  remains a public method, just ungoverned).
- `len(OPERATION_CASES) == 146` (`141 + 5`).
- canonical `== 117`.
- noncanonical `== 29` (`24 + 5`).
- `len(generated) == 37` (`30 + 7`).
- `len(manual) == 109` (`111 - 7 + 5`).
- `LEGACY_ARGV_MIGRATION` max `legacy:143` (`138 + 5`),
  `len(LEGACY_PAYLOAD_FINGERPRINTS) == 143`, `range(1, 144)`.

## Open Questions

- Should `autopilot list` gain a `--status` filter now or in a follow-up?
  Decision (D7): follow-up, to keep this change to pagination + governance.