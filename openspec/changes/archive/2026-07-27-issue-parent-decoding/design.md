## Context

`IssueResource.create` (src/multica_py/resources/issues.py:85) already builds
`--project` from `IssueCreateRequest.project_id` and the contract maps
`request.project_id -> --project -> json_body:project_id`
(contracts/sdk-contract.json:237-239 and 1410-1413). The upstream CLI accepts a
symmetric `--parent <issue-ref>` that resolves to a canonical UUID and is sent
as `parent_issue_id` in the `POST /api/issues` JSON body (UNI-11 evidence,
sections 2 and 3). `IssueWire`/`Issue` today decode only `id` and `created_at`
of the scalar response fields; the handler returns `parent_issue_id`,
`project_id`, `creator_id`, `creator_type` as flat scalars, not nested
objects.

`IssueResource.update` (src/multica_py/resources/issues.py:115) is hand-written
and ungoverned: there is no `issue_update` binding descriptor, no
`issues.update` operation entry, and `scope.ungoverned_policy` is
`"existing_unrelated_operations_unchanged"`. The existing `--project`,
`--title`, `--priority`, `--assignee-id` emissions in `update` are all Python-
only. Parent follows the same pattern.

Constraints carried over from AGENTS.md and the existing specs:

- The approved contract is the only generator input; `approved_sdk.py` is
  regenerated only via `upstream_contract render`.
- Tests are table-driven first, reuse shared cases, no new test files.
- All new public fields are additive optional `str | None = None` to preserve
  compatibility with existing fixtures and older CLI output.

## Goals / Non-Goals

**Goals:**
- Expose `parent_id` on `IssueCreateRequest` and `IssueUpdateRequest` with the
  same presence policy as the existing `project_id` (None/omitted omits the
  flag; empty/whitespace string rejected by SDK `__post_init__` guard).
- Decode the four flat scalar fields the upstream response already returns.
- Add the reviewed parent mapping to the `issue_create` contract binding and
  regenerate the runtime module from it; keep `IssueResource.update`
  hand-written and ungoverned, adding `--parent` in Python only.

**Non-Goals:**
- `IssueSort.queue`: upstream CLI rejects it; deferred until upstream support
  lands.
- Nested parent/project/creator objects: upstream returns scalars, so we mirror
  that.
- A dedicated `CreatorType` enum: minimal scope keeps it as `str | None`.
- A contract binding for `issue_update`: introducing one only to emit `--parent`
  is scope creep against `ungoverned_policy`. Update stays Python-only.
- Clearing a parent via `--parent ""` on update: no `IssueUpdateRequest` field
  supports clearing today (`None` = "do not touch" for every field); this is a
  repo-wide concern owned by a separate change, not parent-specific.

## Decisions

**1. Mirror `project_id` for `parent_id` mapping shape and guard.**
The project mapping is already reviewed and tested; parent is structurally
identical (`--<flag> <ref>` then `json_body:<field>`). Reusing the same presence
policy (`optional_omit`) and the same `__post_init__` nonblank guard avoids a
new validator and a new presence kind. The `parent_id` nonblank guard is
Python-only in `IssueCreateRequest.__post_init__` / `IssueUpdateRequest.__post_init__`,
mirroring the existing `project_id` guard; no `nonblank:request.parent_id`
contract constraint is added (the existing `project_id` guard is also
Python-only — the contract `issue_create` constraints are only
`nonblank:request.title` and `description_exactly_one`).

**2. Wire field names match upstream JSON, public field renames only where
already established.**
`IssueWire` uses upstream names (`parent_issue_id`, `project_id`, `creator_id`,
`creator_type`); `Issue` exposes `parent_id` (matching the request field) for
`parent_issue_id` and keeps the other three verbatim. Renaming
`parent_issue_id -> parent_id` matches the request side and the existing
`parent_id` naming on `CommentWire` (src/multica_py/_internal/wire_models.py:113).

**3. No unset sentinel for create or update.**
`None` and "omitted" are equivalent for `create` — both omit `--parent` and the
JSON body key. For `update`, `None` = omit = "do not touch the parent", matching
every existing `IssueUpdateRequest` field. A sentinel is only needed where
`None` and "omitted" diverge from "clear the value" (e.g. `update --parent ""`
clearing), which is out of scope and applies to all update fields, not just
parent.

**4. Regenerate `approved_sdk.py` from the contract, never hand-edited.**
Per `upstream-contract` spec "Deterministic generation" and AGENTS.md, the
runtime module is the render output. The new mapping flows through the existing
generator; we run `upstream_contract render` and commit the result.

**5. `issue_update` stays ungoverned.**
`IssueResource.update` is hand-written and has no contract binding
(`scope.ungoverned_policy = "existing_unrelated_operations_unchanged"`).
Introducing a full contract surface (signature + descriptor + operation entry +
source_refs + test_refs) only to emit `--parent` would be scope creep and would
change the ungoverned policy. The `--parent` emission for update is added in
Python in `IssueResource.update`, mirroring the existing `--project` block.
The contract is touched only for `issue_create`.

**6. Tests: rows, not files; parametrize replaces existing non-parametrized
rejection tests.**
New coverage goes into the existing `tests/cases/operations.py` (new `_c(...)`
rows for create-with-parent, create-with-parent-and-project, and
update-with-parent) and `tests/contract/test_issue_models.py`. Per AGENTS.md
"Table-driven first", the two existing non-parametrized rejection functions
(`test_issue_create_request_rejects_empty_project_id` and
`test_issue_update_request_rejects_empty_project_id`) are replaced by one
`@pytest.mark.parametrize` over `(request_factory, field_name, bad_value)`
rows covering `project_id=""`, `parent_id=""`, `parent_id="  "` for both create
and update. No new test module, no new fixtures, no duplicate coverage.

## Risks / Trade-offs

- [Older CLI responses without the four new fields] → `msgspec` Struct
  defaults (`str | None = None`) make this additive; existing fixtures keep
  decoding. No migration.
- [`creator_type` as free string drifts if upstream adds values] → accepted
  for minimal scope; a follow-up enum can be added when upstream stabilises.
  Tracked as a deliberate simplification (`ponytail:` comment in wire_models).
- [Generator must stay deterministic] → render is idempotent; we verify by
  running it twice and diffing `approved_sdk.py`.
- [`IssueUpdateRequest` clearing semantics diverge from set semantics] →
  accepted: `None` = "do not touch" is the existing contract for every update
  field; clearing (`--parent ""` / `--project ""`) is a repo-wide concern owned
  by a separate change. Parent follows the existing update pattern.
- [`issue_update` contract left ungoverned] → intentional; introducing it only
  for `--parent` is scope creep. The Python-only emission mirrors the existing
  `--project` block in `IssueResource.update`.