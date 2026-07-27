## ADDED Requirements

### Requirement: Issue parent linkage and scalar relation decoding
The SDK SHALL accept `parent_id` on `IssueCreateRequest` and `IssueUpdateRequest` and SHALL emit the upstream `--parent` flag only when the value is non-`None` and non-empty. The decoded `Issue` SHALL expose the flat scalar relation fields (`parent_id`, `project_id`, `creator_id`, `creator_type`) that the upstream `GET /api/issues/{id}` and `POST /api/issues` responses return.

#### Scenario: Create with parent emits --parent
- **WHEN** `IssueResource.create` is called with `IssueCreateRequest(title="t", parent_id="iss_parent")`
- **THEN** the CLI argv includes `--parent iss_parent`.

#### Scenario: Create without parent omits --parent
- **WHEN** `IssueResource.create` is called with `IssueCreateRequest(title="t")` (parent_id is `None`)
- **THEN** the CLI argv does not include `--parent`.

#### Scenario: Update with parent emits --parent
- **WHEN** `IssueResource.update` is called with `IssueUpdateRequest(parent_id="iss_parent")`
- **THEN** the CLI argv includes `--parent iss_parent`.

#### Scenario: Update without parent omits --parent
- **WHEN** `IssueResource.update` is called with `IssueUpdateRequest()` (parent_id is `None`)
- **THEN** the CLI argv does not include `--parent` (meaning "do not touch the parent").

#### Scenario: Empty parent id on create is rejected
- **WHEN** `IssueCreateRequest(title="t", parent_id="")` or `IssueCreateRequest(title="t", parent_id="  ")` is constructed
- **THEN** a `ValueError` is raised before any CLI invocation.

#### Scenario: Empty parent id on update is rejected
- **WHEN** `IssueUpdateRequest(parent_id="")` or `IssueUpdateRequest(parent_id="  ")` is constructed
- **THEN** a `ValueError` is raised before any CLI invocation.

#### Scenario: Response scalar fields round-trip
- **WHEN** the upstream response JSON contains flat `parent_issue_id`, `project_id`, `creator_id`, `creator_type` scalars
- **THEN** the decoded `Issue` exposes `parent_id` (renamed from `parent_issue_id`), `project_id`, `creator_id`, and `creator_type`, each defaulting to `None` when absent.