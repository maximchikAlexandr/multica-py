# Handoff: Upstream v0.4.9 Migration Planning

## Purpose

This file preserves the maximum useful context collected during the
`/speckit-plan` research phase so a different agent session can continue without
repeating discovery.

It contains:

- current repository and feature state;
- completed research conclusions;
- exact implementation symbols and test authorities;
- target-source behavior for the 16 approved operation IDs;
- contract/generator/promotion pipeline findings;
- live-harness root causes and selected fixes;
- the exact selected design;
- remaining Speckit deliverables;
- acceptance commands and expected interpretations.

This is a research handoff, not an implementation authorization. No migration
implementation, contract update, generation, promotion, or live run was
performed in this session.

## Current Session State

- Repository:
  `/Users/alexandr/local_dev/repositories/my_projects/multica-py`
- Branch: `upstream-v0-4-9-migration`
- Branch base at research time:
  `e348d18` (`Merge pull request #4 ... 006-test-suite-consolidation`)
- Feature directory:
  `specs/007-upstream-v0-4-9-migration`
- Active Spec Kit feature pointer:
  `.specify/feature.json` points to
  `specs/007-upstream-v0-4-9-migration`
- Completed artifacts:
  - `spec.md`
  - `checklists/requirements.md`
  - `research.md`
  - this `HANDOFF.md`
- Created but not filled:
  - `plan.md` is still the copied Spec Kit template
- Not yet created:
  - `data-model.md`
  - `quickstart.md`
  - feature `contracts/`
- Agent context has not yet been updated to feature 007.
- Post-design constitution check has not yet been performed.
- Post-plan optional extension hook has not been executed.
- Goal remains active; it was intentionally not marked complete.

At the last status check, the feature directory and `.specify/feature.json`
were uncommitted. No commit or push was requested or performed.

## User Intent and Quality Bar

The user requested an implementation plan that weaker models can execute. The
finished plan must have:

- no unresolved alternatives;
- no vague requirements;
- no unselected options;
- no hidden source-of-truth choices;
- exact file/symbol responsibilities;
- exact data and interface contracts;
- exact ordering and gates;
- explicit expected outcomes.

The user then paused research and asked to preserve maximum useful context for
continuation in another agent session.

## Mandatory Scope and Guardrails

The migration target is:

- upstream tag `v0.4.9`;
- full commit `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`.

Historical live baseline:

- tag `v0.3.10`;
- full commit `be32e5af00c74cda60c2fe8c47d31402bc62b3a6`.

Mandatory compatibility boundary is the 16 unique operation IDs in
`contracts/sdk-contract.json`.

Do not automatically approve all 35 target command additions. Do not use the
help-degraded 107 `command_removed` rows as removal evidence.

During planning, do not:

- modify SDK implementation;
- modify `contracts/sdk-contract.json`;
- modify generated files;
- modify live target metadata;
- run generator;
- run `promote`, `reject`, or `apply-manifest-suggestions`;
- run live tests;
- start implementation or task generation.

## Evidence and Trust Order

Use this order when facts conflict:

1. exact target source at
   `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`;
2. `release-provenance.json`;
3. current approved `contracts/sdk-contract.json`;
4. manual `source-delta.json`;
5. live test results and diagnostics;
6. help-degraded bundle as unconfirmed suggestions only.

Exact target source worktree used during research:

`/Users/alexandr/.codex/worktrees/upstream-upgrade-evidence/multica`

Baseline source worktree:

`/Users/alexandr/.codex/worktrees/upstream-upgrade-evidence/multica-base`

Evidence package:

`.devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9`

## Completed Research Artifact

`research.md` contains 20 selected decisions:

1. migration contract boundary;
2. schema-v2 approved contract;
3. compatibility outcomes;
4. status bindings;
5. issue-list surface;
6. comment composite cursor;
7. issue/comment semantics;
8. label semantics;
9. project/resource semantics;
10. timeout/error compatibility;
11. deterministic generator;
12. candidate identity and promotion;
13. cross-artifact consistency;
14. runtime-readiness root cause;
15. categorized live outcomes;
16. fail-closed mutation gate;
17. stability repeat;
18. offline quality artifacts;
19. upstream-family disposition;
20. fixed implementation order.

The decisions in `research.md` are selected, not proposals. A continuing agent
should encode them into the plan and design contracts rather than reopen them
without contradictory exact-source evidence.

## Repository Architecture Facts

### Runtime and tooling

- Python: 3.12 and 3.13
- Runtime dependency: `msgspec>=0.19,<2`
- Package: `multica-py`, import `multica_py`
- Project type: synchronous Python SDK wrapping a controlled CLI subprocess
- Default suite: offline and excludes live/packaging
- Supported platforms: Linux and macOS
- Type gate:
  - strict mypy for `src`
  - checked test/script/tool modules
- Formatting/linting: Ruff
- Build: Hatchling through `uv`

### Test architecture after feature 006

Canonical test data and execution points:

- `tests/cases/argv_data.py`
  - canonical unit argv rows
  - adding command coverage should normally add/modify rows here
- `tests/cases/operations.py`
  - operation registry and live policy
- `tests/unit/resources/test_operations.py`
  - generic unit argv runner
- `tests/component/test_cli_roundtrip.py`
  - generic fake-CLI roundtrip runner
- `tests/contract/test_full_cli_coverage.py`
  - operation/manifest completeness guards
- `tests/behavioral-coverage.json`
  - behavior coverage manifest
- `tests/quality-baseline.json`
  - current quality baseline
- `scripts/check_test_architecture.py`
  - now present on current main
- `scripts/check_test_baseline.py`
  - staged quality-baseline checker

Binding test rules from `AGENTS.md` remain mandatory:

- table-driven rows before new test functions;
- reuse shared fixtures;
- complete expected argv, not partial assertions;
- do not add allowlist gaps when real coverage can be added;
- no third-party testing framework;
- live modules have explicit module-level marker profiles;
- offline suite must collect no live nodes.

## Current Approved Contract Facts

File:

`contracts/sdk-contract.json`

Current state:

- schema version: 1
- 22 flat parameter rows
- 16 unique operation IDs

The schema implementation is:

`src/multica_py/_internal/upstream_contract/generator/contract.py`

Exact current symbols:

- `ApprovedOperation`, lines 35-46
- `ApprovedContract`, lines 49-51
- `load_approved_contract`, lines 54-58
- `validate_approved`, lines 61-82

Current allowed fields:

- `operation_id`
- `binding_command_path`
- `python_parameter`
- `cli_argument`
- `required`
- one `presence_semantics` token
- `enum_policy`
- `approved_enum`
- generic `constraints`
- `test_refs`
- `source_refs`

Current validator only checks:

- unique `(operation_id, python_parameter)`;
- allowed presence token;
- allowed enum policy;
- allowed constraint category.

It cannot express:

- operation-level compatibility outcome;
- target identity;
- exact destination;
- multiple entrypoints;
- command sequences;
- state-by-state presence outcomes;
- response/error contract;
- commit-qualified source evidence;
- approved contract hash;
- public signature;
- generated output set.

Important: production code does not currently call this approved-contract
loader/generator. The package named `generator` is only a loader/validator. A
real production generator does not exist.

## The 16 Governed Operation IDs

1. `issues.comments.add`
2. `issues.comments.delete`
3. `issues.comments.list`
4. `issues.create`
5. `issues.labels.add`
6. `issues.labels.list`
7. `issues.labels.remove`
8. `issues.list`
9. `issues.set_status`
10. `projects.create`
11. `projects.resources.add_local_directory`
12. `projects.resources.list`
13. `projects.resources.remove`
14. `projects.resources.update_local_directory`
15. `projects.set_status`
16. `projects.update`

Selected compatibility outcomes:

- `issues.comments.list`: `intentionally_changed`
- all other 15: `compatible`
- none: `explicitly_unsupported`

Status binding corrections are metadata corrections, not public behavior
changes, because current Python already emits the target command.

## Current Public Implementation Map

### Issues

File: `src/multica_py/resources/issues.py`

- `IssueResource.list`: lines 44-58
- `IssueResource.create`: lines 70-96
- `IssueResource.set_status`: lines 124-127

Models:

`src/multica_py/models/issues.py`

- `IssueListFilter`: lines 55-59
- `IssueCreateRequest`: lines 86-105
- `IssueUpdateRequest`: lines 108-117
- description input variants:
  - `InlineDescription`
  - `FileDescription`
  - `StdinDescription`
  - `NoDescription`

Current `set_status` emits:

```text
issue status <issue_id> <status> --output json
```

and decodes `IssueWire` to `Issue`.

### Issue comments

File: `src/multica_py/resources/issue_comments.py`

- `_extract_cursor`: current scalar regex, lines 28-30
- `IssueCommentResource.list`: lines 43-49
- `list_flat`: lines 51-64
- `list_thread`: lines 66-86
- `list_recent`: lines 88-99
- `add`: lines 101-106
- `delete`: lines 125-126

Models:

`src/multica_py/models/issue_activity.py`

- `Comment`
- `CommentThread`
- `CommentListFlatRequest`
- `CommentListThreadRequest`
- `CommentListRecentRequest`

Current generic page:

`src/multica_py/models/common.py::Page`

with scalar `next_cursor: str | None`.

The current advanced comment API is not target-compatible:

- `list_flat` emits nonexistent target `--limit`;
- scalar cursor emits `--before` without required `--before-id`;
- thread/recent cursor does the same;
- scalar stderr parsing cannot retain both cursor components.

### Issue labels

File: `src/multica_py/resources/issue_labels.py`

- `IssueLabelResource.list`: lines 13-14
- `add`: lines 16-17
- `remove`: lines 19-20

All return decoded tuples of `Label`.

### Projects

File: `src/multica_py/resources/projects.py`

- `ProjectResource.create`: lines 28-32
- `update`: lines 34-44
- `set_status`: lines 49-52

Models:

`src/multica_py/models/projects.py`

- `ProjectCreateRequest`
- `ProjectUpdateRequest`

Current project status emits:

```text
project status <project_id> <status> --output json
```

Current update behavior:

- `name=Unset`: omit
- `description=Unset`: omit
- `description=None`: local `ValidationError`
- `description=""`: emit explicit empty flag
- both fields omitted: currently invokes target empty update; target rejects it

### Project resources

File: `src/multica_py/resources/project_resources.py`

- `ProjectResourceCollection.list`: lines 17-25
- `add_local_directory`: lines 27-49
- `update_local_directory`: lines 51-69
- `remove`: lines 71-72

Models:

`src/multica_py/models/project_resources.py`

- `LocalDirectoryResourceRef`
- `ProjectResourceRecord`
- `ProjectResourceAddLocalDirectoryRequest`
- `ProjectResourceUpdateLocalDirectoryRequest`

### Shared decoding and transport

Resource decoding:

`src/multica_py/resources/_base.py`

- `_run_json_decode`
- `_run_json_decode_list`

These append `--output json`, call controlled transport, and decode with
`msgspec`.

Wire adapters:

`src/multica_py/_internal/wire_models.py`

- `IssueWire`
- `IssueListPageWire`
- `ProjectWire`
- `ProjectResourceRecordWire`
- `CommentWire`
- `CommentThreadWire`
- conversion helpers for each public model

Failure classification:

`src/multica_py/_internal/transport.py`

Stable semantic exit mapping:

- exit 2 -> `NetworkError`
- exit 3 -> `AuthenticationError`
- exit 4 -> `NotFoundError`
- exit 5 -> `ValidationError`
- other non-zero -> `CommandExecutionError`

HTTP status parsing also maps:

- 401/403 -> authentication
- 404 -> not found
- 400/422 -> validation

SDK process timeout is independent of the upstream CLI HTTP timeout.

## Exact Target Status Evidence

Target issue source:

`server/cmd/multica/cmd_issue.go`

- `issueStatusCmd` declaration: lines 219-227
- registration: line 415
- status enum/validation: lines 361-404
- RunE/transport mapping: lines 1423-1454

Exact command:

```text
issue status <id> <status>
```

Target transport:

- resolves issue ID/key;
- sends PUT to `/api/issues/{resolved-id}`;
- JSON body contains `status`.

Baseline `v0.3.10` also declares `issue status`. Therefore
`issue set-status` was never a verified compatibility path.

Target project source:

`server/cmd/multica/cmd_project.go`

- `projectStatusCmd` declaration: lines 54-59
- registration: line 116
- status enum/validation: lines 94-110
- RunE/transport mapping: lines 487-520

Exact command:

```text
project status <id> <status>
```

Selected implementation:

- update both contract bindings to `status`;
- update generated compatibility projection;
- no fallback;
- no runtime command probe;
- no Python resource change solely for these bindings.

## Target Issue List Evidence and Selected Surface

Target source:

`server/cmd/multica/cmd_issue.go`

- flag registration: lines 436-448
- query construction/validation: lines 574-658
- enum validation: lines 361-404

Source-confirmed sort values:

- `position`
- `title`
- `created_at`
- `start_date`
- `due_date`
- `priority`

Direction values:

- `asc`
- `desc`

Constraint:

- direction requires a non-`position` sort.

Selected public changes:

- add strict `IssueSort`;
- add strict `SortDirection`;
- add `sort` and `direction` to `IssueListFilter`;
- do not add project/offset/metadata/date fields in this migration.

Presence:

- `None` omits optional flags;
- existing `limit` remains source-faithful;
- do not invent a stricter limit range not enforced by target source.

## Target Issue Create Evidence

Target source:

`server/cmd/multica/cmd_issue.go`

- input helpers/workdir checks: lines 20-89
- flag registration: lines 460-477
- `runIssueCreate`: lines 1052-1192

Source behavior:

- title is required and non-empty;
- status/priority are strict target enums when used;
- description inline/stdin/file are mutually exclusive;
- empty inline description acts as omitted;
- empty stdin/file content is rejected;
- stage is presence-sensitive and must be at least 1 when supplied;
- attachment IDs are omitted when absent;
- local attachment paths are prevalidated before creation;
- some post-create local attachment failures are warnings to avoid duplicate
  create retries.

Selected migration behavior:

- preserve existing public fields only;
- reject empty title locally;
- omit `--description` for `InlineDescription("")`;
- preserve discriminated description channels;
- do not add attachment upload fields;
- preserve post-create `label_ids` sequence:
  create -> repeated label add -> issue get refresh;
- record label steps in schema-v2 contract as an ordered command sequence.

## Target Comment Evidence

### List

Target source:

`server/cmd/multica/cmd_issue.go`

- flags: lines 510-519
- `runIssueCommentList`: lines 1756-1890

Rules:

- no target `--limit`;
- `--recent` must be positive;
- `--tail` must be non-negative;
- `--tail` requires `--thread`;
- `--thread` conflicts with `--recent`;
- `--roots-only` conflicts with thread/recent/tail/cursor modes;
- `--before` and `--before-id` must be supplied together;
- cursor pair is valid only with:
  - `--recent`, or
  - `--thread` plus `--tail`;
- target emits:
  - `Next thread cursor: --before VALUE --before-id ID`, or
  - `Next reply cursor: --before VALUE --before-id ID`.

Selected public model:

```text
CommentCursor(before: str, before_id: str)
CommentPage(items: tuple[Comment, ...], next_cursor: CommentCursor | None)
CommentThreadPage(
    items: tuple[CommentThread, ...],
    next_cursor: CommentCursor | None,
)
```

Both cursor fields must be non-empty.

Selected entrypoint changes:

- basic `list(issue_id)` unchanged;
- flat request keeps only issue ID and optional since;
- flat obsolete scalar cursor and limit are removed;
- thread request uses optional composite cursor;
- thread cursor requires a supplied tail/limit;
- tail zero is valid; negative is invalid;
- recent limit must be positive and defaults to 10;
- recent cursor is composite;
- malformed/partial stderr cursor is an output-shape failure.

### Add

Target source:

- command declaration/flags: `cmd_issue.go:246-269,539-545`
- execution: `cmd_issue.go:1920-1992`

Behavior:

- exactly one issue ID;
- one content channel required;
- empty inline content is treated as absent and therefore rejected;
- stdin/file empty content rejected;
- attachment paths prevalidated before upload;
- POST destination:
  `/api/issues/{id}/comments`;
- JSON body contains `content`, optional parent and attachment IDs.

Selected public behavior:

- keep current inline `body: str`;
- reject empty body locally with `ValidationError`;
- do not add file/stdin/attachment entrypoints in migration.

### Delete

Target:

- `DELETE /api/comments/{id}`;
- success 204;
- invalid UUID 400;
- missing/wrong-workspace 404;
- permission failure 403.

Selected public behavior:

- return `None`;
- preserve semantic exception mapping.

## Target Label Evidence

Target source:

`server/cmd/multica/cmd_issue_label.go:16-139`

Bindings:

- list: `issue label list <issue-id>`
- add: `issue label add <issue-id> <label-id>`
- remove: `issue label remove <issue-id> <label-id>`

Transport:

- list: GET `/api/issues/{id}/labels`
- add: POST label ID body
- remove: DELETE label relation path

Semantics:

- duplicate add is idempotent;
- removing an absent valid relation is idempotent;
- malformed IDs -> validation;
- unknown/wrong-scope IDs -> not found.

Known target edge:

The target post-mutation refresh may emit `{}` during a rare refresh failure.
Selected behavior is fail-closed decode/output-shape error. Do not reinterpret
it as an empty list and do not issue an automatic fallback list command.

## Target Project Evidence

Target source:

`server/cmd/multica/cmd_project.go`

- flags: lines 133-184
- create/update: lines 304-463

Create:

- title non-empty required;
- description/status/icon/lead/start/due are optional;
- empty optional create fields are omitted;
- POST `/api/projects`.

Selected create surface:

- keep name and description only;
- reject empty name;
- description `None` or empty means omitted;
- do not expose new fields.

Update:

- only changed fields are sent;
- title/description/icon/date empty strings are explicit clears;
- empty status invalid;
- empty lead cannot clear;
- empty update body rejected;
- PUT `/api/projects/{id}`.

Selected update surface:

- keep name and description;
- `Unset` omits;
- empty string clears;
- `description=None` remains rejected;
- both fields Unset rejected locally.

## Target Project Resource Evidence

Target source:

`server/cmd/multica/cmd_project.go`

- command declarations: lines 66-92
- flags: lines 151-172
- list: lines 527-569
- add: lines 571-650
- update: lines 652-906
- remove: lines 908-934

List:

- exact project ID;
- GET project resources;
- JSON list response.

Add local directory:

- local path and daemon ID are trimmed and required;
- resource type fixed to `local_directory`;
- label omitted when blank;
- POST body contains resource type and resource ref.

Selected SDK behavior:

- continue resolving local path to absolute;
- reject empty daemon ID;
- `label is None` or `label == ""` both omit `--ref-label`.

Update local directory:

- target fetches current resource list;
- seeds full resource ref;
- partial local-path update preserves daemon ID and label;
- changed path/daemon cannot be empty;
- empty label clears label;
- no changed fields rejected;
- PUT updated resource.

Selected SDK surface:

- retain required `local_path` only;
- do not expose label-only or daemon-only update;
- verify target list-before-put behavior through source/live acceptance while
  SDK still invokes one CLI command.

Remove:

- exact project/resource IDs;
- scope-resolved;
- DELETE;
- success returns `None`.

## Target Transport Evidence

Target source:

- `server/internal/cli/client.go:72-180,258-540`
- `server/internal/cli/errors.go:1-492`

Target CLI behavior:

- default HTTP timeout: 30 seconds;
- `MULTICA_HTTP_TIMEOUT` supports Go duration or positive integer seconds;
- invalid/non-positive override falls back to 30 seconds;
- API context adds grace;
- uploads have a larger floor;
- HTTP errors are structured across verbs;
- stable process exit categories remain 2/3/4/5 for
  network/auth/not-found/validation.

Selected SDK behavior:

- do not copy 30-second HTTP timeout into SDK;
- keep SDK outer process timeout;
- `timeout=None` remains no SDK kill deadline;
- child naturally inherits `MULTICA_HTTP_TIMEOUT`;
- do not parse it in SDK;
- generic exit 1, including rate limit/conflict/server failure, remains
  `CommandExecutionError`;
- tests distinguish SDK process timeout from CLI network classification.

## Canonical Test References for the 16 Operations

Current contract refs are stale/incomplete. Some point to removed
`tests/integration` modules or pre-consolidation resource test files.

Use these current authorities:

- argv construction:
  `tests/cases/argv_data.py`
- generic argv runner:
  `tests/unit/resources/test_operations.py`
- fake CLI roundtrip:
  `tests/component/test_cli_roundtrip.py`
- contract completeness:
  `tests/contract/test_full_cli_coverage.py`
- issue model semantics:
  `tests/unit/resources/test_issues.py`
- project-resource model/path semantics:
  - `tests/unit/test_project_resource_models.py`
  - `tests/unit/test_path_normalization.py`
- project assignment validation:
  `tests/component/test_issue_project_assignment.py`
- transport classification:
  `tests/unit/test_transport.py`
- process timeout:
  `tests/component/test_process_contract.py`
- live issue workflow:
  `tests/live/test_issue_workflow.py`
- live project presence:
  `tests/live/test_projects.py`
- live pagination/filter:
  `tests/live/extended/test_pagination.py`
- live operation ownership:
  - `tests/live/operations.py`
  - `tests/cases/operations.py`
  - `tools/live_support/oracle.py`

Add a contract validator that every `test_ref`:

- is repository-relative;
- resolves to an existing file;
- optionally resolves a named node when a `::node_id` suffix is used.

## Current Canonical Argv Facts

File:

`tests/cases/argv_data.py`

Relevant regions at research time:

- comments/labels: approximately lines 271-303
- issues/projects/resources: approximately lines 357-419
- status operations: approximately lines 468 and 484
- comment add/delete: approximately lines 520-523

The existing status rows already expect:

```text
issue status ...
project status ...
```

The comment flat row is currently wrong for target because it expects:

```text
--before scalar --limit N
```

The migration should modify table rows and add negative table cases rather than
create one-off test modules.

## Semantic Coverage and Public Scope Facts

Current:

`src/multica_py/_generated/upstream_coverage.json`

contains 108 decisions:

- 3 typed
- 98 raw
- 6 process
- 1 unsupported

The 16 approved operation IDs are not the entire public SDK. Many appear as raw
coverage decisions. Existing raw wrappers such as pull requests, reorder,
usage, attachment upload, and comment resolution may already exist in source.

Selected rule:

- do not delete or modify those unrelated wrappers;
- do not add them to schema-v2 approved contract;
- do not call them newly approved;
- do not require the whole 108-decision set to equal the 16-ID set;
- cross-artifact validation compares the 16-ID approved projection to the
  corresponding semantic coverage bindings while preserving unrelated rows.

## Selected Schema-v2 Shape

Top-level conceptual fields:

```text
schema_version = 2
target
scope
operations
```

`target` includes:

- version `0.4.9`
- tag `v0.4.9`
- full commit
- release ID `358605496`
- release provenance reference
- approved contract semantic hash when materialized

`scope` includes:

- exact ordered 16-ID set
- explicit statement that other raw/process operations are not governed
- family disposition reference

Each operation includes:

- unique operation ID
- compatibility outcome
- rationale
- one or more entrypoints
- response contract
- error contract
- commit-qualified source refs
- exact test refs

Each entrypoint includes:

- public symbol
- ordered signature parameters
- return type
- base command path
- output mode
- optional ordered execution steps
- parameter mappings
- constraints

Each mapping includes:

- dotted Python source path
- CLI argument/positional slot
- destination kind:
  - path
  - query
  - JSON body
  - header
  - multipart
  - local control
- destination name/path
- command step
- required flag
- explicit outcomes for:
  - omitted
  - null
  - empty
  - zero
  - false
- enum policy/values/aliases/deprecations

No arbitrary untyped extension dictionaries should be allowed.

## Selected Generator Design

Current generator does not generate production artifacts.

Implement under:

`src/multica_py/_internal/upstream_contract/generator/`

Selected generated outputs:

1. `src/multica_py/_generated/approved_sdk_contract.json`
2. `src/multica_py/_generated/approved_sdk_bindings.py`
3. `src/multica_py/_generated/approved_sdk_enums.py`
4. `src/multica_py/_generated/approved_sdk_validators.py`
5. `src/multica_py/_generated/approved_sdk_api.pyi`
6. `src/multica_py/_generated/approved_sdk_compatibility.json`
7. `docs/generated/approved-sdk-v0.4.9.md`
8. `tests/cases/generated/approved_sdk_cases.py`
9. `tests/fixtures/provenance/approved-sdk-v0.4.9.json`

Rules:

- only decoded+validated approved contract is a decision input;
- source-delta, candidate contracts, suggestions, and evidence bundles cannot be
  passed as generator inputs;
- stdlib deterministic rendering; no template dependency;
- render every output in memory before writing;
- write same-directory temp files;
- replace in fixed order;
- byte-stable sorted/canonical output;
- `--check` writes nothing and reports every missing/different/extra governed
  file.

Selected command:

```bash
uv run python scripts/upstream_contract.py generate \
  --approved contracts/sdk-contract.json
```

Check mode:

```bash
uv run python scripts/upstream_contract.py generate \
  --approved contracts/sdk-contract.json \
  --check
```

Runtime integration:

- handwritten resources import generated bindings and validators;
- `multica_py.enums` re-exports generated approved enums;
- complex resource sequencing/decoding stays handwritten;
- generated API stub and contract tests verify signatures;
- generated cases feed existing table-driven runners.

Do not generate entire resource modules because they contain unrelated
operations outside the 16-ID boundary.

## Candidate/State Pipeline Findings

Canonical paths:

`src/multica_py/_internal/upstream_contract/paths.py`

- state:
  `src/multica_py/_generated/upstream_state.json`
- supported contract:
  `src/multica_py/_generated/upstream_supported_contract.json`
- candidate contract:
  `src/multica_py/_generated/upstream_candidate_contract.json`
- coverage:
  `src/multica_py/_generated/upstream_coverage.json`

Collection:

`src/multica_py/_internal/upstream_contract/cli.py`

- collect flow: approximately lines 308-358
- `_collect_contract_ref`: lines 179-187
- persistence: lines 190-218

Current defect:

- collection always writes canonical candidate;
- but candidate state can record caller-supplied in-repo `--output`;
- this permits `candidate.json` versus `candidate-contract.json` drift.

State:

`src/multica_py/_internal/upstream_contract/state.py`

- `load_state`: lines 23-33
- `set_candidate`: lines 36-53
- `validate_state`: lines 56-71
- `replace_supported`: lines 74-79

Current validation checks commit shape/path containment but not:

- file existence;
- strict referenced artifact decode;
- state kind;
- artifact version/tag/commit equality;
- recomputed semantic hash equality.

Promotion:

- `src/multica_py/_internal/upstream_contract/promotion.py`
  - prepare/check decisions: lines 53-111
  - apply checks: lines 114-136
  - state/artifact writes: lines 139-168
  - candidate load: lines 171-175
- CLI adapter:
  `src/multica_py/_internal/upstream_contract/cli.py::cmd_promote`,
  lines 491-538

Current `PromotionDecision`:

`src/multica_py/_internal/upstream_contract/models.py:298-309`

It binds candidate semantic identity and previous supported state, but not
approved SDK contract hash or target release provenance.

Selected fixes:

- eliminate state use of custom collect output path;
- canonical candidate ref only;
- custom output is byte-identical convenience copy only;
- validate referenced file existence and full identity;
- supported ref must be canonical supported path;
- candidate ref must be canonical candidate path;
- recompute semantic hash;
- bind promotion decision to approved contract hash and release provenance;
- candidate is cleared after successful promotion.

## Current Provenance Conflict

`contracts/multica-live-target.toml` currently identifies:

- `v0.3.10`
- commit `be32e5...`

`src/multica_py/_generated/upstream_state.json` currently identifies:

- supported `v0.4.2`
- commit `48b8db...`
- candidate `v0.4.3`
- candidate commit is a placeholder-looking value
  `abc1234567890abcdef1234567890abcdef12345`

Target evidence identifies:

- `v0.4.9`
- commit `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`

Current candidate canonical file exists after the main update, but current
validation is still too weak.

Target release provenance:

- release ID `358605496`
- published `2026-07-23T10:25:45Z`
- CLI darwin/arm64 archive SHA256:
  `7413ada5907a7cf9e8618ca9c348160b015d5b21beb34b7d96af8705018aaaf4`
- extracted executable SHA256:
  `e92149ee958db469ac75c3d79b955f5f97c8753f740e7da0138d28431e9de4f8`
- backend manifest digest:
  `sha256:6e1527dd54c55c46e8b1f781d1ae118976a377a009b8a67f1de92e10bb6cf434`
- backend linux/amd64 digest:
  `sha256:645199276fa75927fca835a2a8cddbfa476f32cf97337fd7f2c113b650606438`

Linux/amd64 and darwin/amd64 release CLI checksums are also recorded in
`release-provenance.json` and must be copied exactly into the live target during
implementation, not re-inferred.

## Selected Cross-Artifact Validator

Add one fail-closed coherence validator called by upstream `check` and by an
offline contract test.

It must compare:

- approved schema-v2 contract target;
- approved contract hash;
- generated approved compatibility projection;
- semantic supported contract;
- generated supported state;
- corresponding semantic coverage bindings for the 16 IDs;
- CLI manifest metadata;
- live target TOML;
- exact release provenance;
- referenced files and semantic hashes.

It must assert:

- all 16 governed IDs occur exactly once in approved projection;
- all 16 corresponding bindings agree;
- unrelated coverage decisions are preserved but not schema-v2 approved;
- none of the 35 target additions was newly approved without an explicit
  contract entry;
- active candidate ref is canonical and valid or candidate is null;
- active supported ref is canonical and valid;
- version/tag/commit/checksums/digests agree.

Any mismatch is `INVALID_ARTIFACT`, never warning-only.

## Live Harness Findings

### Current runner

`scripts/run_live_tests.py`

Relevant symbols:

- `_run_pytest`
- `_assert_clean_worktree`
- `_patched_source`
- `run_mutation_check`
- `run_repeat`
- `_collect_leftover_prefixes`
- `run_smoke`
- parser/main

### False-positive mutation root cause

Current `_run_pytest` calls:

```text
[sys.executable, "-m", "pytest", ...]
```

Current `run_mutation_check` treats any non-zero exit as a killed mutation.

Evidence run:

- outer mutation command exited 0;
- all three subprocesses printed `No module named pytest`;
- wrapper incorrectly called this a successful mutation check.

Current tests only prove mutation anchors exist. They do not prove clean
control, collection, start, or expected failure reason.

Selected protocol:

1. exact interpreter pytest import preflight;
2. clean control for each exact node;
3. unique JUnit;
4. require node collected, started, completed, passed;
5. apply mutation;
6. rerun same node;
7. require node started and failed for expected mutation fingerprint;
8. exit 2/3/4/5, setup error, missing JUnit, no collection, missing dependency,
   or wrong failure -> invalid gate;
9. restore source and verify hash.

Selected gate exit:

- 0 valid killed mutations;
- 1 survivor;
- 2 invalid gate.

### Current mutation cases

The existing cases target:

- project update title flag;
- label get decoder;
- not-found exit mapping.

Before implementation, verify current mutation anchors because feature 006 may
have moved or removed an old target test. One existing target refers to a
removed pre-consolidation label test and must be redirected to the current
table-driven/live operation authority.

### Compatibility report defect

`scripts/live_compatibility_report.py::build_compatibility_report`

Current schema: 1.

Current logic:

```text
regression_signal = pytest_exit_code != 0 and not is_upstream_probe
```

This makes every pinned setup/infrastructure failure a product regression.

Selected schema-v2 categories:

- `passed`
- `product_failure`
- `environment_unready`
- `authentication_limited`
- `invalid_run`

Selected result fields:

- stage
- pytest exit
- collected count
- started count
- completed count
- failed count
- target node when applicable
- exception type
- normalized message
- target fingerprint
- JUnit/report/diagnostic paths

Candidate is a product regression only when:

- category is product failure;
- intended operation was reached;
- baseline/control does not share normalized
  category/stage/exception fingerprint.

Environment/auth/invalid outcomes are inconclusive.

### Runtime readiness root cause

`tests/live/backend/lifecycle.py::poll_runtime_online`,
lines 219-247.

Current logic:

1. calls `find_online_opencode_runtime(daemon_id)`;
2. then gathers every online runtime for the daemon regardless of provider;
3. requires total online matches to equal one.

`tools/live_support/oracle.py::DirectApiOracle.find_online_opencode_runtime`,
lines 280-291, correctly filters:

- provider == `opencode`;
- matching daemon ID;
- status online/ready/active;
- exactly one match.

Saved baseline/candidate runtime diagnostics had four online runtimes:

- codex
- cursor
- openclaw
- opencode

Therefore the second provider-agnostic count can never equal one, even though
the desired opencode runtime is ready. This explains the identical baseline and
candidate `runtime not ready` failure.

Selected fix:

- require exactly one online opencode runtime only;
- do not count other providers;
- include other providers as diagnostics;
- zero or multiple opencode matches -> typed
  `environment_unready/runtime_readiness`.

Required unit cases:

- four provider runtimes with one opencode -> success;
- zero online opencode -> categorized failure;
- two online opencode -> categorized failure.

### Backend and auth readiness

Backend readiness:

`tests/live/backend/compose.py`

- `probe_readiness`
- `is_ready`
- `ComposeLifecycle.wait_ready`

This is distinct from runtime readiness and should use stage
`backend_readiness`.

Auth bootstrap:

`tests/live/backend/client.py::_send_code_with_retry`

It retries HTTP 429 but ultimately produces a generic bootstrap error.

Selected auth stage:

`authentication_rate_limit`

Diagnostics may include attempt count and retry-after but no secret/token data.

### Repeat defect

Current `run_repeat`:

- hardcodes `tests/live/test_agent_sandbox.py`;
- does not run full smoke;
- accepts zero runs;
- does not require a prior successful smoke;
- does not write structured categorized outcomes per repetition.

Selected migration stability:

- exactly 10 repetitions;
- prerequisite smoke report must be readable, passed, and target-identical;
- each run executes `-m live_smoke tests/live`;
- unique run ID/JUnit/result/diagnostics/cleanup;
- stop at first failure;
- success only 10/10 and zero leftovers.

## Historical Live Evidence

Baseline pinned smoke:

- 31 passed
- 1 failed
- failure: runtime readiness

Candidate `v0.4.9` smoke:

- 31 passed
- 1 failed
- 48 deselected
- same runtime-readiness shape

Candidate extended:

- 74 passed
- 5 failed
- 1 deselected
- failures in runtime readiness
- additional auth rate-limit diagnostics

Scan/cleanup passed and no managed resources were left.

Interpretation:

- these runs do not prove a `v0.4.9` product regression;
- they also do not prove target compatibility;
- fix harness root cause and rerun;
- do not run repeat 10 before smoke passes.

## Current CI/Baseline Finding

Current main now contains:

- `scripts/check_test_architecture.py`
- `tests/quality-baseline.json`
- coverage generation in CI
- mutation result generation in CI

The older evidence package's “missing architecture script” blocker is stale and
resolved by feature 006.

Current `.github/workflows/ci.yml` runs:

- offline parallel coverage;
- serial coverage append;
- coverage JSON check;
- five architecture/baseline stages;
- process contract;
- hard-network check;
- mutation run.

However, the five-stage baseline command does not pass:

- coverage JSON;
- offline JUnit;
- mutation results.

`check_test_baseline` treats optional missing paths as skipped, so a green final
stage does not prove all three artifacts.

Selected fix:

- generate offline JUnit explicitly;
- pass coverage/JUnit/mutation paths to final baseline gate;
- explicitly supplied missing file exits as invalid input;
- final stage requires all mandatory artifacts.

## Upstream Family Disposition

Use these exact classifications:

| Family | Selected disposition |
| --- | --- |
| `issue-existing-changes` | required compatibility |
| `issue-new-commands` | required subset plus extension candidates |
| `project-and-root-registration` | required subset plus CLI-only |
| `attachments-and-client-transport` | required subset plus deferred extension |
| `transport-error-contract` | required compatibility |
| `chat-read` | separate extension candidate |
| `workspace-properties` | separate extension candidate |
| `workspace-repository-management` | deferred owner decision |
| `runtime-and-local-control` | CLI-only/local plus deferred extension |
| `agent-settings-and-skills` | deferred owner decision |
| `skills-squads-and-autopilots` | deferred owner decision |

Do not trust `source-delta.json` `sdk_operation_ids` as approval for repo,
runtime, skill, squad, or other out-of-scope commands.

## Fixed Implementation Sequence

The continuing plan must preserve this order:

1. schema-v2 contract models and validator;
2. exact 16-operation contract migration;
3. deterministic generator and check mode;
4. generated bindings/enums/validators/signatures/docs/cases integration;
5. operation compatibility fixes;
6. canonical candidate ref and strict state identity;
7. promotion decision binds approved contract/provenance;
8. cross-artifact coherence validator;
9. live target changes to exact `v0.4.9`;
10. runtime-readiness provider fix and categorized outcomes;
11. fail-closed mutation gate;
12. full-smoke repeat gate;
13. offline quality gates;
14. target smoke;
15. target extended;
16. valid mutation check;
17. repeat 10.

Do not update active supported/live metadata before contract, generator check,
promotion check, and coherence gate are green.

## Plan-Ready File Responsibilities

Likely implementation files, based on completed research:

### Approved contract and generator

- `contracts/sdk-contract.json`
- `src/multica_py/_internal/upstream_contract/generator/contract.py`
- new generator render/write modules under
  `src/multica_py/_internal/upstream_contract/generator/`
- `src/multica_py/_internal/upstream_contract/cli.py`
- `scripts/upstream_contract.py`
- generated outputs listed above
- unit tests:
  `tests/unit/test_upstream_contract_generator.py`

### Public compatibility

- `src/multica_py/enums.py`
- `src/multica_py/models/issues.py`
- `src/multica_py/models/issue_activity.py`
- `src/multica_py/models/projects.py`
- `src/multica_py/models/project_resources.py`
- `src/multica_py/resources/issues.py`
- `src/multica_py/resources/issue_comments.py`
- `src/multica_py/resources/projects.py`
- `src/multica_py/resources/project_resources.py`
- `src/multica_py/resources/issue_labels.py`
- `tests/cases/argv_data.py`
- existing generic runners and focused model/transport tests

### State/promotion/provenance

- `src/multica_py/_internal/upstream_contract/paths.py`
- `state.py`
- `provenance.py`
- `promotion.py`
- `models.py`
- `coverage.py`
- related unit tests:
  - `test_upstream_contract_state.py`
  - `test_upstream_contract_promotion.py`
  - `test_upstream_contract_provenance.py`
- contract CLI tests under `tests/contract/upstream/`

### Cross-artifact/live target

- `contracts/multica-live-target.toml`
- `src/multica_py/_generated/upstream_state.json`
- `src/multica_py/_generated/upstream_supported_contract.json`
- `src/multica_py/_generated/upstream_coverage.json`
- `src/multica_py/_generated/cli_manifest.json`
- `src/multica_py/_internal/manifest.py`
- `tests/contract/test_cli_manifest.py`
- `tests/contract/test_full_cli_coverage.py`
- `tests/contract/test_live_target_workflows.py`
- new focused supported-target coherence test under `tests/contract/upstream/`

### Live harness

- `scripts/run_live_tests.py`
- `scripts/live_compatibility_report.py`
- `tools/live_support/environment.py`
- optionally one focused typed outcome/JUnit parser module under
  `tools/live_support/` or `scripts/`; the final plan must choose exactly one
  path
- `tests/live/backend/lifecycle.py`
- `tests/live/backend/client.py`
- `tools/live_support/oracle.py`
- `tests/unit/test_live_compatibility_report.py`
- `tests/unit/test_live_support_tools.py`
- `tests/unit/test_live_bootstrap.py`
- focused runtime lifecycle tests
- `.github/workflows/ci.yml`
- `.github/workflows/live-extended.yml`

Important remaining planning decision already selected in principle but not yet
encoded as a file path: put the shared live result/JUnit parser in
`tools/live_support/outcomes.py`. This is the preferred exact path because both
scripts and live tests can import it without making production SDK code depend
on test code. A continuing agent should use this path and remove “optional
path” wording from the final plan.

## Acceptance Command Sequence

These commands are plan targets. Do not run mutating commands during planning.

### Generator and contract

```bash
uv run python scripts/upstream_contract.py generate \
  --approved contracts/sdk-contract.json \
  --check
```

Expected:

- zero byte differences;
- all nine governed outputs present;
- no write.

### Upstream state check

```bash
uv run python scripts/upstream_contract.py check --with-candidate
```

Expected:

- canonical refs;
- referenced artifacts exist;
- version/tag/commit/hash agree;
- no unresolved reviewed candidate items.

### Promotion dry check

```bash
uv run python scripts/upstream_contract.py promote \
  --decision <reviewed-decision.json> \
  --check
```

Expected:

- decision binds candidate semantic hash;
- decision binds approved contract hash;
- decision binds target provenance;
- previous supported identity matches;
- no write.

### Focused offline tests

```bash
uv run pytest \
  tests/unit/test_upstream_contract_generator.py \
  tests/unit/test_upstream_contract_state.py \
  tests/unit/test_upstream_contract_promotion.py \
  tests/unit/test_upstream_contract_provenance.py \
  tests/unit/resources/test_operations.py \
  tests/unit/resources/test_issues.py \
  tests/unit/test_project_resource_models.py \
  tests/unit/test_transport.py \
  tests/component/test_cli_roundtrip.py \
  tests/component/test_process_contract.py \
  tests/contract/upstream \
  tests/contract/test_cli_manifest.py \
  tests/contract/test_full_cli_coverage.py \
  tests/contract/test_live_target_workflows.py
```

### Full offline quality

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run mypy tests scripts tools
uv run pytest -m "not live"
uv run pytest -m "not live" --collect-only
```

Collection expectation:

- no `tests/live/*` node in non-live selection.

### Five-stage architecture gate

```bash
for stage in pr1 pr2 pr3 pr4 final; do
  uv run python -m scripts.check_test_architecture --stage "$stage"
  uv run python -m scripts.check_test_baseline \
    --baseline tests/quality-baseline.json \
    --stage "$stage"
done
```

The final implementation must extend the final baseline invocation with the
required coverage/JUnit/mutation inputs.

### Live smoke

After exact target/coherence and harness fixes:

```bash
uv run python scripts/run_live_tests.py \
  --resolve-cli \
  --mode smoke \
  --compatibility-report <artifact-dir>/smoke-report.json \
  -- \
  --junitxml=<artifact-dir>/smoke-junit.xml \
  -q
```

Expected:

- category `passed`;
- full smoke profile reached;
- target fingerprint exact `v0.4.9`;
- no infrastructure false positive;
- cleanup/secret scan green.

### Live extended

```bash
uv run python scripts/run_live_tests.py \
  --resolve-cli \
  --mode extended \
  --compatibility-report <artifact-dir>/extended-report.json \
  -- \
  --junitxml=<artifact-dir>/extended-junit.xml \
  -q
```

Expected:

- interpretable categorized result;
- for migration acceptance: passed;
- cleanup/secret scan green.

### Valid mutation gate

```bash
uv run python scripts/run_live_tests.py \
  --resolve-cli \
  --mutation-check
```

Expected:

- clean controls collected/started/passed;
- each mutation target collected/started/failed for expected fingerprint;
- no dependency/setup error accepted;
- exit 0 only for valid killed cases;
- clean worktree restored.

### Stability repeat

Only after smoke report category is passed:

```bash
uv run python scripts/run_live_tests.py \
  --resolve-cli \
  --repeat 10 \
  --prerequisite-report <artifact-dir>/smoke-report.json
```

Expected:

- 10/10 full smoke;
- same target fingerprint;
- separate artifacts for every run;
- no leftovers.

## Known Stale Statements to Correct

The current `spec.md` still says:

- feature branch is `binta/upstream-v0-4-9-migration`;
- `scripts/check_test_architecture.py` is absent;
- baseline expected coverage artifact is absent as a current blocker.

Current repository state proves:

- branch is `upstream-v0-4-9-migration`;
- architecture script is present;
- `tests/quality-baseline.json` contains coverage/mutation information;
- the remaining issue is that CI baseline invocation does not require/pass all
  produced artifacts.

Before final plan completion, update `spec.md` and checklist notes to distinguish
historical evidence-package blockers from current unresolved blockers.

## Remaining Speckit Plan Work

The continuing session should:

1. update stale spec branch/current blocker statements;
2. fill `plan.md`;
3. create `data-model.md`;
4. create feature contracts:
   - `contracts/approved-sdk-contract-v2.md`
   - `contracts/operation-decisions.md`
   - `contracts/generation-and-provenance.md`
   - `contracts/live-acceptance.md`
   - `contracts/upstream-family-disposition.md`
5. create `quickstart.md`;
6. update `AGENTS.md` Spec Kit plan pointer to feature 007;
7. re-run constitution check after design;
8. validate all referenced paths/symbols;
9. search for placeholders, `NEEDS CLARIFICATION`, “TBD”, “either/or”,
   “as needed”, and unresolved alternatives;
10. verify all 16 operations and 11 families appear exactly once in the proper
    matrices;
11. verify no out-of-scope implementation changes were made;
12. process the optional `after_plan` hook according to the skill contract;
13. report branch, plan path, generated design artifacts, and readiness for
    `/speckit.tasks`.

Do not mark the goal complete until these artifacts exist and the
requirement-by-requirement audit passes.

## Context Preservation Notes

Four read-only research streams completed:

- public SDK operations/models/tests;
- approved contract/generator/promotion pipeline;
- live/mutation/readiness/CI gates;
- exact target source behavior and family classification.

All useful conclusions from those streams are consolidated in this file and
`research.md`. The subagents made no file edits and ran no live tests.

The codebase knowledge graph was refreshed in fast mode before research. Project
identifier:

`Users-alexandr-local_dev-repositories-my_projects-multica-py`

Graph state at refresh:

- 5,473 nodes
- 17,277 edges

The refresh wrote the persistent graph artifact if configured; check git status
before committing and keep unrelated/ignored graph changes out of the feature
commit.
