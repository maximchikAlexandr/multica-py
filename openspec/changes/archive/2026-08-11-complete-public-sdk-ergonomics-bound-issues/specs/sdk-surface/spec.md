## ADDED Requirements

### Requirement: Natural issue and project operation inputs
Project and issue creation SHALL accept ordinary Python text, path, identifier, and appropriate entity-reference values without restoring one-operation request DTOs. `ProjectResource.create` and `create_command` SHALL expose matching `description: str | None` and `description_file: str | os.PathLike[str] | None` keywords. `IssueResource.create` and `create_command` SHALL expose matching ordinary `description`, `description_file`, and `project: str | Project | None` keywords while retaining `description_input: IssueDescriptionInput | None` for the semantically distinct `InlineDescription`, `FileDescription`, `StdinDescription`, and `NoDescription` variants. The existing `project_id` keyword MAY remain as a compatibility spelling, but documentation SHALL use `project`; callers SHALL NOT provide both. Project-scoped issue creation SHALL expose the same description forms while continuing to supply its bound project implicitly. Normalization SHALL preserve the approved argv, `OperationOptions`, eager/command parity, result decoding, and client binding.

#### Scenario: Project file description is passive and inspectable
- **WHEN** a caller builds `client.projects.create_command(name="Backend", description_file=path)` with a string or `os.PathLike[str]`
- **THEN** the plan contains `project create --title Backend --description-file <lexically-absolute-path> --output json`, construction does not open, stat, or require the path to exist, and the eager method exposes the same operation parameters

#### Scenario: Issue inline description uses the governed flag
- **WHEN** a caller creates an issue with `description="Investigate the login failure"`
- **THEN** normalization emits the existing `--description` argv mapping and does not construct an `IssueDescriptionInput` request DTO

#### Scenario: Issue file description preserves semantic alternatives
- **WHEN** a caller supplies a path through `description_file` or a `FileDescription`, inline text through `description` or `InlineDescription`, or explicit stdin through `StdinDescription`
- **THEN** exactly the existing approved `--description-file`, `--description`, or `--description-stdin` mapping is emitted and `NoDescription`/omission emits none of those flags

#### Scenario: Project entity normalizes to its identifier
- **WHEN** `client.issues.create(title="Fix authentication", project=project)` receives a `Project` entity
- **THEN** it emits the same `--project <project.id>` mapping as an identifier string and performs no lookup or other implicit I/O

#### Scenario: Invalid or conflicting natural forms fail locally
- **WHEN** a caller supplies more than one description form, both `project` and `project_id`, a bytes path, a blank file path or identifier, an incompatible entity type, or another unsupported natural value
- **THEN** construction raises `TypeError` or `ValueError` before filesystem or transport I/O and never leaks an implementation `AttributeError`

### Requirement: Public status inputs normalize exact enum values
Issue status inputs on direct list fields, `IssueListFilter`, issue resource `set_status`, and bound `Issue.set_status`, plus `ProjectResource.set_status`, SHALL accept either the corresponding `IssueStatus`/`ProjectStatus` member or its exact case-sensitive string value. `Project` has no `set_status[_command]` bound-entity surface, and this change SHALL NOT add one. Normalization SHALL occur before `.value` access or command construction. Unknown strings SHALL not be aliased to a different upstream status; documentation SHALL use real values such as `"todo"`, `"in_progress"`, and `"done"`, and SHALL not use the unsupported `"open"` spelling.

#### Scenario: Exact issue status string is accepted
- **WHEN** a caller uses `issues.list(status="todo")` or `issue.set_status("done")`
- **THEN** the command contains the same governed status value as the corresponding `IssueStatus` member

#### Scenario: Exact project resource status string is accepted
- **WHEN** a caller uses `client.projects.set_status(project_id, "in_progress")`
- **THEN** the command contains the same governed status value as `ProjectStatus.in_progress`

#### Scenario: Unknown status fails with a typed local error
- **WHEN** a caller passes `"open"`, a differently cased spelling, or a non-string/non-enum value to a public status input
- **THEN** construction raises `ValueError` for an unknown string or `TypeError` for an incompatible type before transport and does not raise `AttributeError`
