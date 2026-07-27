## Why

`IssueResource.create` cannot build the parent/child relationship that the
upstream CLI exposes via `--parent`, and the decoded `Issue` drops four scalar
fields (`parent_issue_id`, `project_id`, `creator_id`, `creator_type`) that the
`GET /api/issues/{id}` and `POST /api/issues` responses already return. Both
gaps were surfaced by the upstream-contract investigation recorded on Multica
issue UNI-11 (comment `0b2bd9d6-ac5c-4486-8709-4d14415b07cd`) against pinned
upstream `v0.4.9` / current `v0.4.11`, where the relevant CLI/handler/service
files are unchanged.

## What Changes

- Add `IssueCreateRequest.parent_id: str | None = None` and
  `IssueUpdateRequest.parent_id: str | None = None` with `__post_init__`
  guards rejecting empty/whitespace strings; `None`/omitted omits `--parent`.
- Add the reviewed mapping `request.parent_id -> --parent -> json_body:parent_issue_id`
  to the `issue_create` binding in `contracts/sdk-contract.json` (descriptor and
  operation entry) with `optional_omit` presence in `mapping_presence.issue_create`.
  The existing `source_ref` `S-ISSUE` (covering `cmd_issue.go:20-2010`, including
  `runIssueCreate`) already covers this mapping; the UNI-11 comment is the
  review note, not a contract field.
- `IssueResource.update` is a hand-written ungoverned operation (no contract
  binding exists; `scope.ungoverned_policy = "existing_unrelated_operations_unchanged"`).
  Its `--parent` emission is added in Python only, mirroring the existing
  `--project` block; no contract change for `issue_update`.
- Emit `--parent <id>` in `IssueResource.create` and `IssueResource.update`.
- Add flat scalar fields to `IssueWire` and `Issue`:
  `parent_issue_id`/`parent_id`, `project_id`, `creator_id`, `creator_type`
  (all `str | None = None`); `issue_from_wire` transfers them. No nested
  objects, no new enum for `creator_type` in this scope.
- Regenerate `src/multica_py/_generated/approved_sdk.py` via the
  `upstream_contract render` command from the approved contract only.
- Add table rows in `tests/cases/operations.py` for `issues.create` with `parent`
  alone and `parent`+`project` together, and for `issues.update` with `parent`;
  extend `tests/contract/test_issue_models.py` with a flat-JSON decode asserting
  all four new fields and replace the two existing non-parametrized empty-field
  rejection tests with one `@pytest.mark.parametrize` covering `project_id` and
  `parent_id` emptiness for both create and update requests.

Queue (`IssueSort.queue`) is explicitly out of scope; upstream CLI rejects it
today.

## Capabilities

### New Capabilities
<!-- None: this change widens existing resource/contract surfaces, it does not
     introduce a new capability boundary. -->

### Modified Capabilities
- `sdk-surface`: adds the requirement "Issue parent linkage and scalar relation
  decoding" covering the new `parent_id` request field and the four decoded
  scalar relation fields.