## 1. Approved contract (issue_create only)

- [x] 1.1 Add `request.parent_id -> --parent -> json_body:parent_issue_id` as a new entry in the `issue_create` mappings array of the `bindings` section in `contracts/sdk-contract.json` (after the existing `request.project_id` mapping at line ~237-239). No new binding descriptor; append to the existing `issue_create` mappings list.
- [x] 1.2 Add the same mapping object `{"source": "request.parent_id", "binding": "--parent", "destination": "json_body:parent_issue_id"}` to the `issue_create` operation entry's `mappings` array in `contracts/sdk-contract.json` (after the existing `request.project_id` mapping at line ~1410-1413). The operation `source_ref_ids` stays `["S-ISSUE"]` — `S-ISSUE` already covers `cmd_issue.go:20-2010` including `runIssueCreate`.
- [x] 1.3 Insert one `"optional_omit"` entry into `mapping_presence.issue_create` in `contracts/sdk-contract.json` (line ~709-716) after the existing `project_id` presence entry (index 4, the 5th element), before the `label_ids` entry — matching the position of the new mapping inserted in 1.1/1.2. Do NOT add a `mapping_presence.issue_update` — `issue_update` is ungoverned.
- [x] 1.4 Run `uv run python scripts/upstream_contract.py validate --approved contracts/sdk-contract.json` (without `--source-checkout`: no new `source_ref` is added, so source-existence validation is not needed for this contract edit). Must pass.

## 2. Models and wire

- [x] 2.1 Add `parent_id: str | None = None` to `IssueCreateRequest` in `src/multica_py/models/issues.py` (after `project_id` at line 98) and extend `__post_init__` with a nonblank guard: `if self.parent_id is not None and not self.parent_id.strip(): raise ValueError("parent_id must be non-empty when set")` — mirror the existing `project_id` guard at lines 106-107.
- [x] 2.2 Add `parent_id: str | None = None` to `IssueUpdateRequest` in `src/multica_py/models/issues.py` (after `project_id` at line 115) and extend `__post_init__` with the same nonblank guard (mirror lines 117-119).
- [x] 2.3 Add `parent_id`, `project_id`, `creator_id`, `creator_type` (all `str | None = None`) to `Issue` in `src/multica_py/models/issues.py` (after `updated_at` at line 52).
- [x] 2.4 Add `parent_issue_id`, `project_id`, `creator_id`, `creator_type` (all `str | None = None`) to `IssueWire` in `src/multica_py/_internal/wire_models.py` (after `updated_at` at line 58). Transfer all four in `issue_from_wire` (lines 61-77): `parent_id=wire.parent_issue_id` (rename), `project_id=wire.project_id`, `creator_id=wire.creator_id`, `creator_type=wire.creator_type`.

## 3. Resource

- [x] 3.1 In `IssueResource.create` (`src/multica_py/resources/issues.py:85`), after the `--project` block at line 106-107, add: `if request.parent_id is not None: args.extend(["--parent", request.parent_id])`.
- [x] 3.2 In `IssueResource.update` (`src/multica_py/resources/issues.py:115`), after the `--project` block at line 125-126, add: `if request.parent_id is not None: args.extend(["--parent", request.parent_id])`. No contract binding for `issue_update`.

## 4. Generator output

- [x] 4.1 Run `uv run python scripts/upstream_contract.py render --approved contracts/sdk-contract.json --runtime-output src/multica_py/_generated/approved_sdk.py --transient-output /tmp/multica-transient`. The transient path MUST be outside tracked dirs per AGENTS.md.
- [x] 4.2 Re-run the same render command and confirm `git diff --stat src/multica_py/_generated/approved_sdk.py` is empty (idempotent). Remove `/tmp/multica-transient` after.

## 5. Tests

- [x] 5.1 Add three table rows in `tests/cases/operations.py` using `_c(...)` with `manual:` ID prefixes (noncanonical variants so the canonical method set stays at 116 per AGENTS.md):
  - `manual:issues.create:variant:05` — `IssueCreateRequest(title="Test", parent_id="iss_parent")`, `expected_argv=("issue","create","--title","Test","--parent","iss_parent","--output","json")`, `stdout=b'{"id":"iss_1","title":"Test","status":"todo"}'`.
  - `manual:issues.create:variant:06` — `IssueCreateRequest(title="Test", parent_id="iss_parent", project_id="pr_001")`, `expected_argv=("issue","create","--title","Test","--project","pr_001","--parent","iss_parent","--output","json")`, `stdout=b'{"id":"iss_1","title":"Test","status":"todo"}'`.
  - `manual:issues.update:variant:02` — `args=("iss_1", IssueUpdateRequest(parent_id="iss_parent"))`, `expected_argv=("issue","update","iss_1","--parent","iss_parent","--output","json")`, `stdout=b'{"id":"iss_1","title":"Test","status":"todo"}'`.
  Insert near the existing `issues.create` rows (line ~1082-1131) and `issues.update` rows (line ~1486-1497). No changes to `tests/unit/resources/`.
- [x] 5.2 Add `test_issue_scalar_relation_fields_decoding` in `tests/contract/test_issue_models.py`: build the JSON `{"id":"iss_1","title":"t","status":"todo","parent_issue_id":"p_1","project_id":"pr_1","creator_id":"u_1","creator_type":"member"}`, decode via `decode_json(json.dumps(data).encode(), IssueWire)` then `issue_from_wire(...)`, assert `issue.parent_id == "p_1"`, `issue.project_id == "pr_1"`, `issue.creator_id == "u_1"`, `issue.creator_type == "member"`. Also add one assertion that a JSON omitting all four keys (e.g. `{"id":"iss_1","title":"t","status":"todo"}`) decodes to `issue.parent_id is None`, `issue.project_id is None`, `issue.creator_id is None`, `issue.creator_type is None`.
- [x] 5.3 Replace `test_issue_create_request_rejects_empty_project_id` and `test_issue_update_request_rejects_empty_project_id` in `tests/contract/test_issue_models.py` with one `@pytest.mark.parametrize` test `test_request_rejects_empty_id_field` over rows `(factory, field_name, bad_value)`:
  - `(lambda **kw: IssueCreateRequest(title="t", **kw), "project_id", "")`
  - `(lambda **kw: IssueCreateRequest(title="t", **kw), "parent_id", "")`
  - `(lambda **kw: IssueCreateRequest(title="t", **kw), "parent_id", "  ")`
  - `(lambda **kw: IssueUpdateRequest(**kw), "project_id", "")`
  - `(lambda **kw: IssueUpdateRequest(**kw), "parent_id", "")`
  - `(lambda **kw: IssueUpdateRequest(**kw), "parent_id", "  ")`
  Each row asserts `ValueError` is raised and `field_name` appears in the message.

## 6. Verification

- [x] 6.1 `uv run pytest -m "not live"` green.
- [x] 6.2 `uv run mypy src` and `uv run mypy tests` green.
- [x] 6.3 `uv run ruff check` and `uv run ruff format --check` green.
- [x] 6.4 `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods` still asserts the canonical method set is unchanged (116 methods); new rows use `:variant:` IDs (noncanonical).