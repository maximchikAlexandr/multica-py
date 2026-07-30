## Context

`IssueResource.list` (src/multica_py/resources/issues.py:50) is hand-written
on top of the governed `issue_list` binding: it builds the `issue list` argv
from `IssueListFilter`, calls
`self._run_json_decode(tuple(args), IssueListPageWire)` (which appends
`--output json` via BaseResource, src/multica_py/resources/_base.py:20), then
maps `.issues` through `issue_summary_from_wire` and returns
`tuple[IssueSummary, ...]`. The pagination metadata that
`IssueListPageWire` already decodes (`issues` only, per
src/multica_py/_internal/wire_models.py:42) is discarded — and the wire model
itself does not yet declare `has_more`/`limit`/`offset`/`total`.

The installed upstream binary confirms the surface (verified
`multica issue list --help` and `multica issue list --output json --limit 1`):
`--offset int` ("Number of issues to skip (for pagination)") and
`--project string` ("Filter by project ID") are real flags, and the JSON
top-level keys are exactly `["has_more","issues","limit","offset","total"]`;
each issue object carries `created_at`, `parent_issue_id`, `project_id`,
`creator_id`, `creator_type` alongside `id`/`title`/`status`/`priority`.

Contract state today (contracts/sdk-contract.json):
- `issue_list` binding descriptor (lines 323-365) maps `filter.status`,
  `filter.priority`, `filter.assignee_id`, `filter.limit`, `filter.sort`,
  `filter.direction` to `--<flag>` → `query:<field>`; constraints are
  `direction_requires_sort` and `position_forbids_direction`.
- `mapping_presence.issue_list` (lines 734-741) is six `optional_omit`
  entries, one per mapping.
- The `types` catalog already declares `issue_list_page_wire` →
  `IssueListPageWire` (line 22) and `issue_summaries` →
  `tuple[IssueSummary, ...]` (line 21).
- The `issue_summaries` response (lines 825-833) uses
  `wire_type_id: issue_list_page_wire` and `decoder_id: decode_issue_summaries`
  (→ `multica_py._internal.wire_models.issue_summary_from_wire`, line 886).
- The `issues.list` operation (lines 3684-3703) is `compatibility: compatible`,
  `response_id: issue_summaries`; it belongs to the
  `issue-existing-changes` family with
  `disposition: required_compatibility` (lines 3380-3395).
- The `issue_list` signature (line 44) is
  `(filter: IssueListFilter | None = None) -> tuple[IssueSummary, ...]`.
- The canonical test vector `generated:issues.list:default:canonical`
  (lines 2247-2274) has `stdout_base64` `eyJpc3N1ZXMiOltdfQ==`
  (`{"issues":[]}`) and assertion `decoded_type -> builtins.tuple`.

`IssueSummary` (src/multica_py/models/issues.py:11) and `IssueSummaryWire`
(src/multica_py/_internal/wire_models.py:26) expose only `id`, `title`,
`status`, `priority`. The richer `IssueWire`/`Issue` already decode
`created_at`, `parent_issue_id`→`parent_id`, `project_id`, `creator_id`,
`creator_type` (added by the archived `issue-parent-decoding` change), so the
list endpoint needs the same five fields on the summary shape.

The repo has precedent for a typed page return: `IssueCommentResource.list_flat/list_thread/list_recent` return `Page[Comment]`/`Page[CommentThread]`
(src/multica_py/resources/issue_comments.py:60,72,96), and
`issues.comments.list` is sanctioned as `compatibility: intentionally_changed`
(contracts/sdk-contract.json:3552) with the rationale "Cursor pair replaces the
obsolete scalar cursor contract." That is the precedent for marking an
`issues.*` operation breaking.

Constraints carried from AGENTS.md and the existing specs:
- The approved contract is the only generator input; `approved_sdk.py` is
  regenerated only via `scripts/upstream_contract.py render`.
- Tests are table-driven first, reuse shared cases, no new test files.
- All new public fields are additive optional (`None` defaults) so existing
  fixtures and older CLI responses keep decoding.
- `tests/unit/resources/test_operations.py::test_discovered_public_methods`
  pins counters (117 canonical / 141 total / 30 generated / 111 manual as of
  the `decode-executor-fields-and-squad-members` merge); new `manual:` variant
  rows keep the canonical method set unchanged, and updating the one
  `generated:issues.list:default:canonical` vector keeps the generated count
  at 30. Counter deltas are computed precisely in tasks.md.

## Goals / Non-Goals

**Goals:**
- Let consumers page (`offset`) and scope (`project_id`) an issue list without
  a CLI fallback.
- Expose the pagination metadata the upstream response already returns.
- Expose the per-issue identity/hierarchy scalars on `IssueSummary` so a
  consumer can locally filter root issues from one decoded page.
- Sanction the `IssueResource.list` return-type widening as an intentional,
  reviewed break in the approved contract, mirroring the
  `issues.comments.list` precedent.

**Non-Goals:**
- Auto-pagination / iterator helpers over `IssueListPage`. Consumers drive
  paging by passing `offset`; the SDK does not loop.
- A `next_cursor`/cursor model. Upstream `issue list` is offset-paged
  (`has_more` + `offset` + `limit`), not cursor-paged; reusing `Page[T]`
  (which carries `next_cursor`) would mis-model the wire. A dedicated
  `IssueListPage` mirrors upstream exactly.
- A `CreatorType` enum. `creator_type` stays `str | None`, consistent with the
  archived `issue-parent-decoding` decision (free string until upstream
  stabilises).
- Clearing semantics for `project_id` on the filter. `None`/omitted omits the
  flag (filter not applied); there is no "all projects" sentinel.
- Governing `--offset` with a contract validator. `--offset` is a local CLI
  control flag like `--limit` (already `optional_omit` only); the nonnegative
  guard is Python-only in `IssueResource.list`, mirroring the existing
  Python-only `direction_requires_sort` guard at line 56.

## Decisions

**1. New `IssueListPage` model; do not reuse `Page[T]`.**
`Page[T]` (src/multica_py/models/common.py:10) has `items` + `next_cursor`,
which does not match the upstream `issue list` envelope (`issues` + `has_more`
+ `limit` + `offset` + `total`). A dedicated frozen `msgspec.Struct`
`IssueListPage(issues, has_more, limit, offset, total)` models the wire
exactly and keeps `Page[T]` reserved for cursor-paged operations. The field is
named `issues` (not `items`) to match the upstream JSON key and the existing
`IssueListPageWire.issues` field, avoiding a rename in the wire layer.

**2. Widen `IssueListPageWire`, not replace it.**
`IssueListPageWire` (src/multica_py/_internal/wire_models.py:42) already
exists with `issues: tuple[IssueSummaryWire, ...]`. Add the four metadata
fields (`has_more: bool = False`, `limit: int | None = None`,
`offset: int | None = None`, `total: int | None = None`) with defaults so
older responses omitting them still decode. Add a new
`issue_list_page_from_wire(IssueListPageWire) -> IssueListPage` decoder that
maps `issues` through `issue_summary_from_wire` and copies the four metadata
fields.

**3. `IssueSummary` mirrors `Issue` for the five scalar fields.**
Add `created_at: datetime.datetime | None = None`, `parent_id: str | None`,
`project_id: str | None`, `creator_id: str | None`, `creator_type: str | None`
to `IssueSummary` and `IssueSummaryWire`, and transfer all five in
`issue_summary_from_wire`. `parent_issue_id` is renamed to `parent_id` on the
public model, matching the established `Issue.parent_id` rename from the
archived `issue-parent-decoding` change (consistency across the issue
surface). The wire field stays `parent_issue_id` (upstream JSON name).

**4. `IssueListFilter` gains `offset` and `project_id`; `--offset`/`--project`
   are Python-only emissions, contract-mapped as `optional_omit`.**
Add `offset: int | None = None` and `project_id: str | None = None` to
`IssueListFilter`. Emit them in `IssueResource.list` inside the existing
`if filter is not None:` block: `--offset` after `--limit`, `--project` after
`--offset` (matching the contract mapping order). Add two `optional_omit`
entries to `mapping_presence.issue_list` and the two mappings to both the
binding descriptor and the operation entry, mirroring the existing six. The
nonnegative `offset` guard is Python-only in `IssueResource.list`
(`if filter.offset is not None and filter.offset < 0: raise ValueError(...)`),
matching the Python-only `direction_requires_sort` guard; no new contract
validator id is added (offset is local CLI control, like `--limit`).

**5. Contract: new `issue_list_page` public type + `decode_issue_list_page`
   decoder; repoint the `issues.list` entrypoint; flip compatibility.**
- Add `issue_list_page` → `IssueListPage` to the `types` catalog (after
  `issue_summaries`, line 21).
- Add a new `issue_list_page` response block (after `issue_summaries`, line
  833) with `public_type_id: issue_list_page`, `wire_type_id:
  issue_list_page_wire` (already in the catalog), `decoder_id:
  decode_issue_list_page`.
- Register `decode_issue_list_page` →
  `multica_py._internal.wire_models.issue_list_page_from_wire` in the
  `decoders` map (line 886), and add `issue_list_page` to the
  `_AUXILIARY_CATALOG_KEYS` `types` set and `decode_issue_list_page` to the
  `decoders` set in tools/upstream_contract/contract.py (lines 84-138) so the
  contract validator accepts the new keys.
- Repoint the `issues.list` entrypoint `response_id` from `issue_summaries`
  to `issue_list_page` (line 3700).
- Update the `issue_list` signature (line 44) to
  `(filter: IssueListFilter | None = None) -> IssueListPage`.
- Flip `issues.list` operation `compatibility` from `"compatible"` to
  `"intentionally_changed"` (line 3686) with rationale
  `"Return type widens from tuple[IssueSummary, ...] to IssueListPage, exposing
  pagination metadata; offset and project_id filters added."`. This sanctions
  the break against the `issue-existing-changes`
  `required_compatibility` family, following the `issues.comments.list`
  precedent at line 3552.
- The old `issue_summaries` response block and `decode_issue_summaries`
  decoder are left in place (still referenced by no entrypoint after the
  repoint; kept to avoid touching unrelated catalog keys). The
  `tuple[IssueSummary, ...` `issue_summaries` type stays because
  `IssueResource.search` (src/multica_py/resources/issues.py:166) still
  returns `tuple[IssueSummary, ...]` and is ungoverned; leaving the catalog
  key avoids a cascade of unrelated edits.

**6. Regenerate `approved_sdk.py` and update the one canonical vector.**
Run `scripts/upstream_contract.py render` to regenerate
`src/multica_py/_generated/approved_sdk.py` (the `ISSUE_LIST_BINDING` gains the
two new mappings; line 88). Update the
`generated:issues.list:default:canonical` test vector
(contracts/sdk-contract.json:2247-2274): change `stdout_base64` to a page
payload carrying metadata
(`{"issues":[],"has_more":false,"limit":50,"offset":0,"total":0}` → base64)
and change the assertion from `decoded_type -> builtins.tuple` to
`decoded_type -> multica_py.models.issues.IssueListPage`. The generated count
stays 30; only one vector changes shape.

**7. Tests: rows, not files; parametrize for the rejection.**
- Extend the `issues.list` row set in `tests/cases/operations.py`: update the
  canonical `generated:issues.list:default:canonical` row's `stdout` to the
  metadata payload and add an `assert_result` that asserts the result is an
  `IssueListPage`; add three `manual:` variant rows (`:variant:01` offset,
  `:variant:02` project, `:variant:03` offset+project). New `manual:` IDs are
  noncanonical, so the canonical method set stays at 117. The total case
  count rises 141 → 144; manual rises 111 → 114; generated stays 30;
  noncanonical rises 24 → 27 (the three new variants are noncanonical, joining
  the 24 existing `:variant:` rows). Counter assertions in
  `test_discovered_public_methods` are updated accordingly.
- Add a legacy fingerprint for each new `manual:` row in
  `tests/cases/legacy_payloads.py` and a `LEGACY_ARGV_MIGRATION` entry
  (`legacy:139/140/141`), growing the legacy set 138 → 141, matching the
  bijection test's `range(1, 139)` → `range(1, 142)` and fingerprint count
  138 → 141.
- Contract decode tests in `tests/contract/test_issue_models.py` (existing
  file): add `IssueListPageWire`/`IssueListPage` import; add
  `test_issue_list_page_decoding` (full metadata round-trip + omitted-
  metadata backward-compatible decode + empty page) and
  `test_issue_summary_scalar_fields_decoding` (per-issue
  `created_at`/`parent_id`/`project_id`/`creator_id`/`creator_type` present
  and absent). One `@pytest.mark.parametrize`
  `test_issue_list_filter_rejects_negative_offset` over `(-1,)` and `(0,)`
  rows — wait: `0` is valid (nonnegative), so the parametrize covers only
  negative values; `0` is asserted valid in the round-trip test instead.
  Reuse `decode_json` from `multica_py._internal.decoders`. No new fixtures.

## Risks / Trade-offs

- [Breaking `IssueResource.list` return type] → sanctioned as
  `intentionally_changed` in the contract, mirroring `issues.comments.list`.
  Consumers iterating the result (e.g. examples/fastapi_adapter.py:23 returns
  `client.issues.list(filter)` directly) must read `.issues`; this is the
  requested behavior. The change is documented in the proposal and spec.
- [Older CLI responses without pagination metadata] → `IssueListPageWire`
  defaults (`has_more=False`, `limit/offset/total=None`) make this additive;
  existing fixtures with only `{"issues":[...]}` keep decoding.
- [`creator_type` as free string] → accepted, consistent with the
  `issue-parent-decoding` decision; a follow-up enum can be added when
  upstream stabilises (already tracked by a `ponytail:` comment in
  wire_models.py:63 for `IssueWire`).
- [`issue_summaries` catalog key retained but unreferenced] → intentional,
  to avoid cascading edits to `IssueResource.search` (ungoverned) and the
  `tools/upstream_contract/contract.py` auxiliary keys; leaving an unused
  catalog key is harmless and the `issue_list_page` key is the one the
  validator checks for the repointed entrypoint.
- [Generator determinism] → render is idempotent; verify by running twice
  and diffing `approved_sdk.py`.
- [`offset` nonnegative guard is Python-only, not a contract validator] →
  mirrors `--limit` (also `optional_omit` only) and the Python-only
  `direction_requires_sort` guard; adding a contract validator only for
  `offset` would be inconsistent and would require a new validator id with
  positive/negative tests beyond scope.