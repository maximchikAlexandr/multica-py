## ADDED Requirements

### Requirement: Issue list pagination and summary identity decoding
The SDK SHALL accept `offset` and `project_id` on `IssueListFilter`, SHALL forward them as the upstream `--offset` and `--project` flags only when non-`None` (and `offset` nonnegative), SHALL return a typed `IssueListPage` from `IssueResource.list` carrying the listed issues and the pagination metadata (`has_more`, `limit`, `offset`, `total`) that the upstream `issue list --output json` response returns, and SHALL expose the per-issue identity and hierarchy scalar fields (`created_at`, `parent_id` renamed from `parent_issue_id`, `project_id`, `creator_id`, `creator_type`) on `IssueSummary`.

#### Scenario: List with offset emits --offset
- **WHEN** `IssueResource.list` is called with `IssueListFilter(offset=20)`
- **THEN** the CLI argv includes `--offset 20`.

#### Scenario: List without offset omits --offset
- **WHEN** `IssueResource.list` is called with `IssueListFilter()` (offset is `None`)
- **THEN** the CLI argv does not include `--offset`.

#### Scenario: List with project emits --project
- **WHEN** `IssueResource.list` is called with `IssueListFilter(project_id="pr_001")`
- **THEN** the CLI argv includes `--project pr_001`.

#### Scenario: List without project omits --project
- **WHEN** `IssueResource.list` is called with `IssueListFilter()` (project_id is `None`)
- **THEN** the CLI argv does not include `--project`.

#### Scenario: Negative offset is rejected before invocation
- **WHEN** `IssueResource.list` is called with `IssueListFilter(offset=-1)`
- **THEN** a `ValueError` is raised before any CLI invocation, naming `offset`.

#### Scenario: Pagination metadata round-trips into IssueListPage
- **WHEN** the upstream `issue list --output json` response contains `{"issues":[...],"has_more":true,"limit":50,"offset":20,"total":137}`
- **THEN** the decoded `IssueListPage` exposes `has_more == True`, `limit == 50`, `offset == 20`, `total == 137`, and `issues` is the decoded `tuple[IssueSummary, ...]`.

#### Scenario: Omitted pagination metadata decodes backward-compatibly
- **WHEN** an older CLI response omits `has_more`, `limit`, `offset`, and `total` (only `issues` present)
- **THEN** the decoded `IssueListPage` exposes `has_more == False`, `limit is None`, `offset is None`, `total is None`, and `issues` is decoded from the present array.

#### Scenario: Empty page decodes
- **WHEN** the upstream response is `{"issues":[],"has_more":false,"limit":50,"offset":0,"total":0}`
- **THEN** the decoded `IssueListPage.issues` is `()` and `has_more == False`.

#### Scenario: Summary scalar fields round-trip
- **WHEN** an issue in the `issues` array contains `created_at`, `parent_issue_id`, `project_id`, `creator_id`, `creator_type`
- **THEN** the decoded `IssueSummary` exposes `created_at` as `datetime.datetime | None`, `parent_id` (renamed from `parent_issue_id`), `project_id`, `creator_id`, and `creator_type`, each defaulting to `None` when absent.

#### Scenario: Summary without scalar fields decodes backward-compatibly
- **WHEN** an issue in the `issues` array omits `created_at`, `parent_issue_id`, `project_id`, `creator_id`, `creator_type`
- **THEN** the decoded `IssueSummary` exposes `created_at is None`, `parent_id is None`, `project_id is None`, `creator_id is None`, `creator_type is None`.

#### Scenario: IssueListPage is the public return type
- **WHEN** `IssueResource.list` is called
- **THEN** the returned object is an instance of `multica_py.models.issues.IssueListPage`.

## MODIFIED Requirements

### Requirement: Public resource surface
The SDK MUST retain every public resource method present in the canonical operation table.
#### Scenario: Public methods have canonical rows
- **WHEN** a public resource method exists
- **THEN** one canonical operation row covers it.
<!-- Source IDs: 001:FR-018–FR-031,005:FR-019–FR-025 -->
<!-- Modified by issue-list-pagination: `IssueResource.list` return type widens from
     `tuple[IssueSummary, ...]` to `IssueListPage`; the `issues.list` operation is
     re-marked `intentionally_changed` in the approved contract. The method name,
     resource, and entrypoint are unchanged. -->

### Requirement: Closed public types
The SDK MUST use immutable `msgspec` models and closed public enums or primitive unions without public `Any`.
#### Scenario: Structured output stays closed and typed
- **WHEN** structured output is decoded
- **THEN** it is a typed model or documented closed primitive.
<!-- Source IDs: 001:FR-033–FR-039 -->
<!-- Modified by issue-list-pagination: `IssueListPage` is a frozen `msgspec.Struct`
     with typed `issues: tuple[IssueSummary, ...]` and closed-scalar pagination
     fields; no public `Any`. -->