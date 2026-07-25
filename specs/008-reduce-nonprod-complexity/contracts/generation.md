# Contract: Approved Generation and Upstream Review

## Authority

`contracts/sdk-contract.json` is the only file whose reviewed semantic content
may change generated public SDK behavior. Evidence, help output, diffs,
reports, temporary projections, and Git metadata cannot be generator inputs.

## Tool Ownership

`scripts/upstream_contract.py` imports only
`tools.upstream_contract.cli.main`. The package has exactly:

- `contract.py`: closed schema decode and validation;
- `evidence.py`: declarative extraction, checksum/provenance checks, and review
  item serialization;
- `generation.py`: render, write, and check;
- `cli.py`: argument parsing and four commands;
- `__init__.py`: no public exports.

Delete `src/multica_py/_internal/upstream_contract/` after these commands and
their focused tests pass.

## Commands

### validate

```bash
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json
```

Exit `0` only when the closed schema and every semantic/source/test reference
validate. Exit `2` for invalid contract or unresolved review markers. It writes
nothing.

### collect

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout /absolute/pinned/source \
  --binary /absolute/verified/multica \
  --tag vX.Y.Z \
  --version X.Y.Z \
  --commit <40-hex> \
  --release-id <id> \
  --asset-name <name> \
  --sha256 <64-hex> \
  --os <os> \
  --arch <arch> \
  --version-output /absolute/version.json \
  --output-dir /absolute/ignored/directory
```

It writes exactly `evidence.json` and `review-items.json` below `--output-dir`.
It refuses an output directory equal to or inside `contracts/`, `src/`,
`tests/`, `docs/`, or `openspec/`. It never loads a current approved contract
to infer facts and never modifies tracked files.

Automatically recorded facts are limited to the declarative patterns in
`AGENTS.md`. Every unknown helper, dynamic enum, imperative validation,
presence-sensitive branch, or unclassified mapping creates a review item.

### render

```bash
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /absolute/ignored/directory
```

`--runtime-output` accepts only the exact repository path above.
`--transient-output` is required and obeys the same tracked-directory refusal
as `collect`.

### check

```bash
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
```

It writes nothing and performs, in order:

1. closed contract validation;
2. two renders into separate temporary directories;
3. identical relative-path and byte comparison;
4. exact comparison of rendered runtime bytes to committed
   `approved_sdk.py`, failing if missing;
5. Python compilation of runtime and transient Python;
6. JSON decoding and semantic ID checks for transient JSON;
7. Markdown non-empty/operation-ID checks;
8. import of generated runtime symbols from the source checkout.

Any failure exits `1`; contract invalidity exits `2`; success exits `0`.

`check` is a source-checkout generator gate only. The isolated wheel build,
install, and generated-symbol import gate is owned exclusively by
`tests/packaging/test_generated_runtime.py` as specified in `verification.md`.

## Runtime Projection

The file is rendered in this exact section order:

1. future import;
2. required stdlib imports;
3. compatibility constants;
4. generated enum classes sorted by public name;
5. immutable `GeneratedMapping` and `GeneratedBinding` types;
6. `OPERATION_BINDINGS` sorted by `(operation_id, entrypoint_id)`;
7. validator functions sorted by function name;
8. `__all__` in public symbol order.

It contains no copied approved-contract JSON, compatibility JSON, provenance
JSON, timestamp, source path, review metadata, or test rows.

`MIN_CLI_VERSION = TARGET_VERSION`.
`MAX_CLI_VERSION` is the next patch version, computed during render and emitted
as a literal.

## Transient Projection Paths

When requested, render exactly:

- `docs/approved-sdk.md`;
- `reports/compatibility.json`;
- `reports/provenance.json`.

`check` materializes these in two private temporary directories. No production
or test module imports a transient path.

## Removed Artifacts and Commands

Delete tracked:

- `src/multica_py/_generated/upstream_state.json`;
- `src/multica_py/_generated/upstream_supported_contract.json`;
- `src/multica_py/_generated/upstream_coverage.json`;
- `src/multica_py/_generated/cli_manifest.json`;
- old `approved_sdk_enums.py`;
- every `tests/fixtures/upstream_contract/v2/*.golden`;
- candidate/supported/state goldens under
  `tests/fixtures/upstream_contract/golden/`.

Remove commands `observe`, `diff`, `prepare-upgrade`,
`apply-manifest-suggestions`, `stage-reviewed-candidate`, `promote`, `reject`,
`upgrade`, and `compat`. Delete `scripts/upstream_upgrade.sh` and
`scripts/check_upstream_drift.py`.

Compatibility reporting remains a runtime SDK concern in
`multica_py._internal.compat`, using generated constants; it is not a
maintainer CLI subcommand.

## Tests

`tests/unit/test_upstream_contract.py` contains table-driven invalid-contract
rows plus distinct tests for:

- `collect` tracked-directory refusal and fail-closed review items;
- deterministic two-render equality;
- runtime drift/missing failure;
- compilation and semantic validation;
- the sole-input invariant: changing evidence with a fixed approved contract
  cannot change any rendered byte.

Consolidate the current assertions from
`tests/contract/upstream/test_requirement_traceability.py`,
`test_family_dispositions.py`, and `test_source_authority.py` into
`tests/contract/test_sdk_contract.py`, preserving their approved-contract
semantic coverage. Delete the three source modules after the consolidated
module passes. All state/diff/promotion/observer/upgrade/suggestion/report
schema tests are deleted.

## Closed implementation additions

Schema v3 adds closed `enum_definitions`, `validator_definitions`, `binding_descriptors`, and `test_vectors` catalogs. An entrypoint references one descriptor; its executable rows are in `test_vectors`. Enum entries contain ordered members. Each validator is `{"name":str,"parameter_name":str,"body_kind":BodyKind}` where `parameter_name` is a nonempty valid Python identifier and `BodyKind` is exactly one of `nonblank`, `nonnegative_int`, `positive_int`, `one_of:<enum-id>`, `project_update`, or `resource_update`; no literal placeholder parameter name is permitted.

`test_vectors` is the single test-data authority for all 30 generated rows. Each vector object has exactly `vector_id`, `operation_id`, `entrypoint_id`, `is_canonical`, `args`, `kwargs`, `stdout_base64`, `stderr`, `exit_code`, `transport_method`, `expected_argv`, `stdin_base64`, `timeout`, and `assertion`; the map key equals `vector_id`, and unknown fields are rejected. `entrypoint_id` is a nonempty lowercase ASCII identifier matching `[a-z][a-z0-9_]*`. A vector ID is exactly `generated:<operation-id>:<entrypoint-id>:canonical` or `generated:<operation-id>:<entrypoint-id>:variant:<nn>`, where `<nn>` is a two-digit local ordinal from `01` through `99`. Each entrypoint has exactly one `:canonical` vector. This suffix denotes its entrypoint base vector; it does not set `OperationCase.is_canonical`. A `TaggedValue` is exactly one of `{"kind":"primitive","value":null|bool|int|float|str}`, `{"kind":"datetime","value":str}`, `{"kind":"enum","type":"IssueStatus|ProjectStatus|IssueSort|SortDirection","member":str}`, `{"kind":"path","value":str}`, `{"kind":"unset"}`, `{"kind":"inline_description","text":str}`, `{"kind":"file_description","path":str}`, `{"kind":"stdin_description"}`, `{"kind":"comment_cursor","before":str,"before_id":str}`, `{"kind":"list","items":[TaggedValue,...]}`, or `{"kind":"request","type":"CommentListFlatRequest|CommentListThreadRequest|CommentListRecentRequest|IssueCreateRequest|IssueListFilter|ProjectCreateRequest|ProjectUpdateRequest|ProjectResourceAddLocalDirectoryRequest|ProjectResourceUpdateLocalDirectoryRequest","fields":[[str,TaggedValue],...]}`. A `datetime.value` is ISO-8601 with an explicit `Z` or numeric UTC offset; the loader calls `datetime.fromisoformat(value.replace("Z", "+00:00"))`, rejects a naive result, and preserves its parsed offset. A request accepts only its declared dataclass fields; `Unset`, `datetime`, `Path`, file/stdin descriptions, enums, primitives, lists, and cursors therefore have no inference path. `assertion` is exactly `{"id":"assert:<vector_id>","kind":"none|decoded_type|page_items","expected":TaggedValue}`; its ID is unique and must match the vector ID. `args`, `kwargs`, `expected_argv`, `stdout_base64`, `stderr`, `exit_code`, `stdin_base64`, `timeout`, and assertion expected value are each complete expected values for that vector, not values merged from a local dictionary.

The fixed constructor catalog is: `CommentListFlatRequest(issue_id,since)`; `CommentListThreadRequest(issue_id,thread_id,cursor,limit,since)`; `CommentListRecentRequest(issue_id,limit,cursor,since)`; `IssueCreateRequest(title,description_input,priority,assignee_id,project_id,label_ids)`; `IssueListFilter(status,priority,assignee_id,limit,sort,direction)`; `ProjectCreateRequest(name,description)`; `ProjectUpdateRequest(name,description)`; `ProjectResourceAddLocalDirectoryRequest(local_path,daemon_id,label)`; and `ProjectResourceUpdateLocalDirectoryRequest(local_path)`. `fields` must be in that listed field order, omit an optional field only to use its constructor default, and may not contain another field. The closed `decoded_type` model-name set is the exact set of fully-qualified names appearing as `decoded_type.expected.value` in the 30 vectors; loader validation rejects a name outside that set. `assert_result` is executable: `none` requires primitive null and passes only when `result is None`; `decoded_type` requires one of those primitive strings and passes only when `f"{type(result).__module__}.{type(result).__qualname__}" == expected.value`; `page_items` requires a list whose every item is a primitive string and passes only when `type(result) is multica_py.models.common.Page` and `tuple(item.id for item in result.items)` equals the ordered expected string tuple. Assertion tests construct `multica_py.models.common.Page` directly for the positive page case, reject `multica_py.models.issue_activity.Page`, and reject a `decoded_type` expected name not present in the 30-vector set. A missing `items`, a non-string item ID, a different concrete type, or any other expected tag fails. Thus every constructor and expected result is declarative and closed.

`approved_sdk.py` exports only typed version constants, `IssueSort`, `SortDirection`, `GeneratedMapping`, `GeneratedBinding`, `OPERATION_BINDINGS`, generated validators, and `__all__`. `enums.py` re-exports the two enums; `compat.py` imports the three version constants; `issue_comments.py`, `issues.py`, `issue_labels.py`, `projects.py`, and `project_resources.py` import their binding/validator symbols. Resource method bodies, request construction, CLI invocation, multi-step issue creation, decoding, and error conversion stay handwritten.

## Exact generated operation rows

`tests/cases/operations.py` defines the sole registry as `tuple(sorted((*MANUAL_OPERATION_CASES, *generated_operation_cases(catalog)), key=lambda c: c.id))`. It has exactly 137 rows: 116 canonical public-method rows and 21 noncanonical argv variants, preserving every current argv row. `MANUAL_OPERATION_CASES` contains exactly 107 ungoverned rows (97 canonical public-method rows and 10 variants). `generated_operation_cases(catalog)` produces exactly 30 governed rows (19 entrypoint-base vectors and 11 entrypoint variants; 16 canonical public-method rows and 14 noncanonical rows). There are exactly 116 distinct supported `sdk_method` values. The unit executor is the only success consumer; no generated test file exists.

### Closed legacy-row mapping

`legacy:<nnn>` is the one-based, three-digit position in the current
`ARGV_CASES` tuple in `tests/cases/argv_data.py`; it is the legacy-row ID even
when `ArgvSpec.id` is empty. The implementation writes exactly one
`legacy_argv_migration` object in the approved contract with keys
`legacy:001` through `legacy:135`. It must equal this total mapping: the 30
explicit generated entries below, plus every other row mapped by the closed
manual rule immediately after the table. No other legacy row ID is accepted.

| Legacy row | Final ID |
| --- | --- |
| 030 | `generated:issues.comments.list:direct:canonical` |
| 031 | `generated:issues.comments.list:flat:canonical` |
| 032 | `generated:issues.comments.list:thread:canonical` |
| 033 | `generated:issues.comments.list:thread:variant:01` |
| 034 | `generated:issues.comments.list:recent:canonical` |
| 035 | `generated:issues.comments.list:recent:variant:01` |
| 036 | `generated:issues.labels.add:default:canonical` |
| 037 | `generated:issues.labels.remove:default:canonical` |
| 038 | `generated:issues.labels.list:default:canonical` |
| 047 | `generated:issues.list:default:canonical` |
| 049–053 | `generated:issues.create:default:canonical`, then `variant:01`–`variant:04` |
| 056–057 | `generated:projects.create:default:canonical`, then `variant:01` |
| 058–061 | `generated:projects.update:default:canonical`, then `variant:01`–`variant:03` |
| 063 | `generated:projects.resources.list:default:canonical` |
| 064–065 | `generated:projects.resources.add_local_directory:default:canonical`, then `variant:01` |
| 066 | `generated:projects.resources.update_local_directory:default:canonical` |
| 067 | `generated:projects.resources.remove:default:canonical` |
| 090 | `generated:issues.set_status:default:canonical` |
| 096 | `generated:projects.set_status:default:canonical` |
| 108 | `generated:issues.comments.add:default:canonical` |
| 109 | `generated:issues.comments.delete:default:canonical` |

The four `issues.comments.list` entrypoint bases are internal binding vectors;
only row 030 has `is_canonical=True` for the public method
`issues.comments.list`. Rows 031, 032, and 034 have `is_canonical=False` even
though their IDs end in `:canonical`.

For every row not named in the table, the mapping value is
`manual:<sdk_method>:canonical` for the first remaining row with that exact
`sdk_method` in source order, otherwise
`manual:<sdk_method>:variant:<nn>` where `<nn>` is its two-digit ordinal among
subsequent remaining rows of that `sdk_method`. This rule and the bounded
source set make all 105 migrated manual mappings exact. The only ten manual variants
proved by the current tuple are: `legacy:005` →
`manual:agents.create:variant:01`, `legacy:006` →
`manual:agents.create:variant:02`, `legacy:007` →
`manual:agents.create:variant:03`, `legacy:009` →
`manual:agents.update:variant:01`, `legacy:021` →
`manual:autopilots.update:variant:01`, `legacy:022` →
`manual:autopilots.update:variant:02`, `legacy:040` →
`manual:issues.metadata.set:variant:01`, `legacy:076` →
`manual:skills.create:variant:01`, `legacy:078` →
`manual:skills.update:variant:01`, and `legacy:100` →
`manual:issues.update:variant:01`.

The migration test reads the untouched legacy tuple and the final registry,
computes each row's complete transport payload as `(resource_attr, method,
args, sorted(kwargs.items()), transport_method, expected_argv, stdin, timeout,
stdout)`, and asserts: (1) all 135 legacy row IDs are present exactly once in
`legacy_argv_migration`; (2) each mapped final row has the identical payload;
and (3) the 135 final IDs are distinct and consumed exactly once. It rejects a
missing, extra, duplicated, or payload-mismatched mapping.

The 30-vector typed-literal audit is closed: `legacy:031` is the only vector
requiring `datetime` (`2026-07-12T10:00:00+00:00`); `legacy:090` and `096`
require the existing `IssueStatus` and `ProjectStatus` enum tags; rows
`050`–`052` require inline/file/stdin description tags; row `033` requires
`comment_cursor`; rows `031`–`035`, `049`–`053`, `056`–`061`, and `064`–`066`
require the listed request tags; all remaining arguments and kwargs are
primitive tags. No governed vector requires another tag kind. `unset` remains
the representation for an explicitly serialized unset value, although row 058
omits both optional request fields and therefore uses constructor defaults.

Each listed resource imports its exact binding constant and uses it in the stated
method. The SDK's existing handwritten validation remains authoritative; this
table does not invent validators. 

| Governed method signature | binding key | exact current fields used to form argv |
| --- | --- | --- |
| `comments.add(issue_id: str, body: str)` | `comment_add` | `issue_id`, `body` as `--content body` |
| `comments.delete(comment_id: str)` | `comment_delete` | `comment_id` |
| `comments.list(issue_id: str)` | `comment_list` | `issue_id` |
| `comments.list_flat(request: CommentListFlatRequest)` | `comment_list_flat` | `request.issue_id`, `request.since` |
| `comments.list_thread(request: CommentListThreadRequest)` | `comment_list_thread` | `request.issue_id`, `request.thread_id`, `request.cursor.before`, `request.cursor.before_id`, `request.limit`, `request.since` |
| `comments.list_recent(request: CommentListRecentRequest)` | `comment_list_recent` | `request.issue_id`, `request.limit`, `request.cursor.before`, `request.cursor.before_id`, `request.since` |
| `issues.create(request: IssueCreateRequest)` | `issue_create` | `request.title`, `request.description_input`, `request.priority`, `request.assignee_id`, `request.project_id`, `request.label_ids` |
| `issues.list(filter: IssueListFilter | None = None)` | `issue_list` | `filter.status`, `filter.priority`, `filter.assignee_id`, `filter.limit`, `filter.sort`, `filter.direction` |
| `issues.set_status(issue_id: str, status: IssueStatus)` | `issue_status` | `issue_id`, `status.value` |
| `issues.labels.add(issue_id: str, label_id: str)` | `issue_labels_add` | `issue_id`, `label_id` |
| `issues.labels.list(issue_id: str)` | `issue_labels_list` | `issue_id` |
| `issues.labels.remove(issue_id: str, label_id: str)` | `issue_labels_remove` | `issue_id`, `label_id` |
| `projects.create(request: ProjectCreateRequest)` | `project_create` | `request.name`, `request.description` |
| `projects.update(project_id: str, request: ProjectUpdateRequest)` | `project_update` | `project_id`, `request.name is not Unset`, `request.description is Unset/None/string` |
| `projects.set_status(project_id: str, status: ProjectStatus)` | `project_status` | `project_id`, `status.value` |
| `projects.resources.add_local_directory(project_id: str, request: ProjectResourceAddLocalDirectoryRequest)` | `project_resource_add` | `project_id`, `request.local_path`, `request.daemon_id`, `request.label` |
| `projects.resources.list(project_id: str)` | `project_resource_list` | `project_id` |
| `projects.resources.remove(project_id: str, resource_id: str)` | `project_resource_remove` | `project_id`, `resource_id` |
| `projects.resources.update_local_directory(project_id: str, resource_id: str, request: ProjectResourceUpdateLocalDirectoryRequest)` | `project_resource_update` | `project_id`, `resource_id`, `request.local_path` |

Each vector has exactly the v3 object shape above. Its `assertion.id` is `assert:<vector_id>` and unique. There are no `factory_id` or `response_fixture_id` fields, and no parallel fixture/projection file.
`generated_operation_cases(catalog: ContractCatalog) -> tuple[OperationCase, ...]` materializes 30 vector objects into one `OperationCase` each. `materialize_arguments(args: tuple[TaggedValue, ...], kwargs: tuple[tuple[str, TaggedValue], ...]) -> tuple[tuple[object, ...], dict[str, object]]` is the only value factory. `assert_result(assertion: ResultAssertion, result: object) -> None` uses the assertion object carried by that same vector. No parallel factory, response-fixture, argv, or assertion dictionary exists. The loader rejects a missing field, nonmatching key/vector ID, duplicate assertion ID, totals other than 19 entrypoint-base vectors plus 11 entrypoint variants, or generated public-method totals other than 16 canonical plus 14 noncanonical rows.

## Evidence schema and source verification

`evidence.json` has sorted keys `schema_version`, `target`, `binary`, `facts`. `target` contains tag/version/commit/release_id; `binary` contains asset_name, sha256, os, arch, version_output_sha256; every fact has kind, command_path, value, and source `{path,symbol,line_start,line_end}`. Facts sort by kind, command path, source path, line start, and canonical value JSON. `review-items.json` has `schema_version` and sorted items with code, message, and source. Codes are exactly `UNKNOWN_PATTERN`, `UNRESOLVED_HELPER`, `DYNAMIC_ENUM`, `IMPERATIVE_VALIDATION`, `PRESENCE_SENSITIVE`, and `UNRESOLVED_MAPPING`.

Only closed Cobra literals, closed `AddCommand` identifier lists, known flag
registrations, known declarative validators, and source locations create facts.
Any other relevant syntax creates a review item. Collection and
`validate --source-checkout ROOT` read source text only as Git blobs from the
pinned target commit; they never trust worktree files. Validation requires every
contract ref path under ROOT, the checkout HEAD and every source-ref commit to
equal the target commit, and symbol text inside its inclusive blob line range.

## Command modes and retired-flow migration

`validate --approved PATH` is offline mode: it validates JSON schema, catalog cross-references, test-vector IDs, and source-ref field syntax. `validate --approved PATH --source-checkout ROOT` additionally verifies source paths, exact HEAD commit, symbols, lines, and evidence. Promotion review runs source mode, then `render --approved PATH --runtime-output src/multica_py/_generated/approved_sdk.py --transient-output /absolute/ignored/output`, then `check --approved PATH`; the fixed flow is collect → source-validate → render → check.

Delete every `upgrade`, `prepare-upgrade`, `stage-reviewed-candidate`, `observe`, `diff`, `promote`, `reject`, and `apply-manifest-suggestions` entrypoint from AGENTS.md, docs/contributing.md, docs/cli-coverage.md, docs/releasing.md, docs/compatibility.md, scripts, workflows, and active specs/007. Verify with `git grep -nE 'prepare-upgrade|stage-reviewed-candidate|upstream_contract\.py (upgrade|observe|diff|promote|reject)|upstream_upgrade\.sh' -- ':!specs/008-reduce-nonprod-complexity/**'`; success is no output.

`tests/cases/operations.py::generated_operation_cases` is the sole runtime case factory and consumes `catalogs.test_vectors` directly; no generated-case file is materialized.
