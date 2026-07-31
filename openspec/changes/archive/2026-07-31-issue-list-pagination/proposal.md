## Why

`IssueResource.list` (src/multica_py/resources/issues.py:50) returns
`tuple[IssueSummary, ...]` and discards the pagination metadata that
`multica issue list --output json` already returns at the top level
(`has_more`, `limit`, `offset`, `total`), verified against the installed
upstream binary (`multica issue list --help` exposes `--offset int` and
`--project string`; `--output json` returns all four metadata keys). The SDK
filter model `IssueListFilter` (src/multica_py/models/issues.py:59) does not
support `offset` or `project_id`, so a consumer cannot page past the first
window or filter to one project without a CLI fallback, and the listed-issue
summary drops the identity and hierarchy fields (`created_at`,
`parent_issue_id`, `project_id`, `creator_id`, `creator_type`) that the list
endpoint already returns per issue. This blocks SDK consumers from reading
every backlog page once and locally filtering root issues, as reported in
GitHub issue maximchikAlexandr/multica-py#12.

## What Changes

- Add `offset: int | None = None` and `project_id: str | None = None` to
  `IssueListFilter` (src/multica_py/models/issues.py:59). `offset` is forwarded
  as `--offset <int>` (nonnegative); `project_id` is forwarded as
  `--project <ref>` with the same presence policy as the existing
  `IssueCreateRequest.project_id` (None/omitted omits the flag).
- Emit `--offset` and `--project` in `IssueResource.list`
  (src/multica_py/resources/issues.py:50) in filter-iteration order, after the
  existing `--limit` and before `--sort`/`--direction`.
- Widen `IssueSummary` (src/multica_py/models/issues.py:11) and
  `IssueSummaryWire` (src/multica_py/_internal/wire_models.py:26) with the
  scalar fields the list endpoint already returns: `created_at`
  (`datetime.datetime | None`), `parent_id` (renamed from upstream
  `parent_issue_id`), `project_id`, `creator_id`, `creator_type` (all
  `str | None = None`); `issue_summary_from_wire` transfers all five. All
  additive with `None` defaults so existing fixtures and older CLI responses
  keep decoding.
- Decode and expose the pagination metadata. Introduce a new public
  `IssueListPage` frozen `msgspec.Struct`
  (`issues: tuple[IssueSummary, ...]`, `has_more: bool = False`,
  `limit: int | None = None`, `offset: int | None = None`,
  `total: int | None = None`) in src/multica_py/models/issues.py and a matching
  `IssueListPageWire` (extending the existing
  `IssueListPageWire` at src/multica_py/_internal/wire_models.py:42 with the
  four metadata fields). `IssueResource.list` SHALL return `IssueListPage`
  instead of `tuple[IssueSummary, ...]`.
- Update the approved contract `contracts/sdk-contract.json` for the
  `issues.list` operation:
  - add `filter.offset -> --offset -> query:offset` and
    `filter.project_id -> --project -> query:project_id` mappings to the
    `issue_list` binding descriptor (lines ~329-360) and the `issues.list`
    operation entry's `mappings` array (lines ~1517-1548); add two
    `optional_omit` entries to `mapping_presence.issue_list` (lines ~734-741);
  - widen the `issue_list` signature (line 44) to
    `(filter: IssueListFilter | None = None) -> IssueListPage` and add
    `issue_list_page` to the `types` catalog as `IssueListPage`;
  - change the `issue_summaries` response entry (lines 825-833) to a new
    `issue_list_page` response (`public_type_id` `issue_list_page`,
    `wire_type_id` `issue_list_page_wire`, `decoder_id`
    `decode_issue_list_page`) and repoint the `issues.list` entrypoint
    `response_id` from `issue_summaries` to `issue_list_page` (line 3700);
  - register `decode_issue_list_page` in the `decoders` map (line ~880) as
    `multica_py._internal.wire_models.issue_list_page_from_wire`;
  - flip the `issues.list` operation `compatibility` from `"compatible"` to
    `"intentionally_changed"` (line 3686) with a rationale naming the return-
  type widening; the `issue-existing-changes` family
  `disposition` is `required_compatibility`, so the change is documented as an
  intentional, reviewed break (same precedent as `issues.comments.list` at
  line 3552).
- Regenerate `src/multica_py/_generated/approved_sdk.py` via
  `scripts/upstream_contract.py render` from the approved contract only; update
  the `generated:issues.list:default:canonical` test vector assertion from
  `decoded_type -> builtins.tuple` to `decoded_type ->
  multica_py.models.issues.IssueListPage` and its `stdout_base64` to a payload
  carrying the pagination metadata.
- Add `offset` nonnegative validation: register `offset_nonnegative` as a
  named contract validator in `catalogs.validators` (reusing
  `validate_nonnegative_limit`), `validator_definitions`, `validator_evidence`,
  `issue_list` binding descriptor constraints, and `issues.list` entrypoint
  `validator_ids`. The runtime guard in `IssueResource.list`
  (`if filter.offset is not None and filter.offset < 0: raise ValueError(...)`)
  remains the enforcement point. The contract validator id satisfies
  AGENTS.md's requirement that imperative constraints be normalized by review
  as named custom validators with positive/negative tests.
- Tests: extend the existing `tests/cases/operations.py` `issues.list` row
  set and `tests/contract/test_issue_models.py`, no new test files.
  - New `manual:` variant rows for `issues.list` with `--offset`, `--project`,
    and `--offset`+`--project`; update the canonical
    `generated:issues.list:default:canonical` row's `stdout` to a page payload
    with metadata and add an `assert_result` that asserts the result is an
    `IssueListPage`.
  - Contract decode tests for `IssueListPageWire`/`IssueListPage` covering:
    full metadata round-trip; omitted-metadata backward-compatible decode
    (only `issues` present); per-issue scalar relation fields
    (`created_at`/`parent_id`/`project_id`/`creator_id`/`creator_type`) on
    `IssueSummary`; empty and multi-issue pages.
  - One `@pytest.mark.parametrize` rejection test for negative `offset` on
    `IssueListFilter` (mirrors the existing
    `test_request_rejects_empty_id_field` parametrize pattern).

## Capabilities

### New Capabilities
<!-- None: this change widens the existing issue list surface; it does not
     introduce a new capability boundary. -->

### Modified Capabilities
- `sdk-surface`: adds the requirement "Issue list pagination and summary
  identity decoding" covering the new `IssueListPage` return type, the
  `offset`/`project_id` filter fields, and the five decoded summary scalar
  fields.