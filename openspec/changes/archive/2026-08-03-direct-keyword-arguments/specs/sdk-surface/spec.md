## ADDED Requirements

### Requirement: Dual input convention for request-bearing resource methods

The SDK SHALL support two equivalent public calling conventions on every
in-scope request-bearing resource method: (1) a single positional request
object argument, and (2) the request object's fields passed directly as
keyword-only arguments. The two conventions SHALL be mutually exclusive within a
single call.

The direct keyword form SHALL be the primary form presented in documentation.
The request-object form SHALL remain available for reuse, validation, storage,
and cross-layer assembly. No public method SHALL be renamed, split, or added to
distinguish the two forms — both SHALL use the same domain method.

In-scope methods are exactly:
`projects.create`, `projects.update`, `agents.create`, `agents.update`,
`skills.create`, `skills.update`, `issues.create`, `issues.update`,
`issues.assign`, `issues.reorder`, `runtimes.update`,
`project_resources.add_local_directory`,
`project_resources.update_local_directory`, and `users.profile_update`.

Request-bearing methods not listed above are intentionally out of scope and
SHALL retain their existing request-object-only signature unchanged.

#### Scenario: Direct keyword arguments build the request and invoke the CLI

- **WHEN** an in-scope method is called with keyword-only fields matching the
  request model's field names, types, defaults, and optional-ness
- **THEN** the SDK constructs the equivalent request object internally and
  emits the exact same argv, transport method, stdin, and timeout as the
  equivalent request-object call.

#### Scenario: Request object call remains supported and unchanged

- **WHEN** an in-scope method is called with a single positional request
  object
- **THEN** the SDK emits the exact same argv, transport method, stdin, and
  timeout it emits today, with no behavioral change.

#### Scenario: Both forms return the same type

- **WHEN** the same in-scope operation is invoked via the direct keyword form
  and via the request-object form with equivalent inputs
- **THEN** both calls return values of the same public type (e.g. `Project`,
  `IssueEntity`, `AgentEntity`, `SkillEntity`, `RuntimeUpdateResult`,
  `ProjectResourceRecord`, `UserProfile`).

#### Scenario: Direct fields are keyword-only

- **WHEN** an in-scope method is called with positional arguments beyond the
  accepted single request-object positional slot
- **THEN** the call raises `TypeError` at call time, before any CLI
  invocation, because the direct fields are keyword-only.

#### Scenario: Mixed input is rejected before invocation

- **WHEN** an in-scope method is called with both a positional request object
  and one or more keyword fields
- **THEN** the SDK raises `TypeError` with the message
  `Pass either a request object or keyword arguments, not both.` before any
  CLI invocation.

#### Scenario: Neither request object nor direct fields raises TypeError

- **WHEN** an in-scope method is called with no positional request object and
  no keyword fields (beyond any required positional identifiers the method
  already takes, such as `project_id` on `projects.update`)
- **THEN** the SDK raises `TypeError` indicating the missing required
  request input, before any CLI invocation.

#### Scenario: Direct keyword form preserves request validation

- **WHEN** the direct keyword form supplies values that would violate the
  request model's `__post_init__` validation (e.g. blank `project_id` on
  `IssueCreateRequest`, non-exactly-one target on `IssueAssignmentRequest` or
  `IssueReorderRequest`, blank `daemon_id` on
  `ProjectResourceAddLocalDirectoryRequest`, blank `local_path` on
  `ProjectResourceUpdateLocalDirectoryRequest`)
- **THEN** the same `ValueError` the request object raises is raised from the
  direct form too, before any CLI invocation. A relative `local_path` on
  `ProjectResourceAddLocalDirectoryRequest` is NOT such a case: that
  request's `__post_init__` only validates `daemon_id`, and the call site
  normalizes `local_path` via `os.path.abspath` in both forms identically.

#### Scenario: Update-style presence semantics are identical in both forms

- **WHEN** an update-style in-scope method (`projects.update`,
  `users.profile_update`) is called via the direct keyword form with an
  omitted field, an explicit `None`, or an explicit `Unset` where the request
  model distinguishes them
- **THEN** the resulting argv matches the equivalent request-object call bit
  for bit, including the omission-vs-null-vs-unset distinction.

#### Scenario: Static type checkers understand both forms

- **WHEN** `uv run mypy src` and `uv run mypy tests` are run against the
  dual-input method signatures
- **THEN** both pass and a direct keyword call type-checks with the field
  names and types advertised by the request model.

#### Scenario: IDE autocomplete surfaces direct fields

- **WHEN** a caller starts a direct keyword call on an in-scope method
- **THEN** the `@overload` signatures expose the request model's field names
  as keyword-only parameters with their declared types and defaults.

#### Scenario: Request-object methods out of scope are unchanged

- **WHEN** an out-of-scope request-bearing method
  (`issue_comments` list overloads, `issue_metadata.query`,
  `issue_metadata.set_typed`) is inspected
- **THEN** its signature, argv, and behavior are unchanged and no direct
  keyword overload is added.

### Requirement: Dual input convention documentation default

The SDK documentation SHALL present the direct keyword form as the default
example for every in-scope method and SHALL document the request-object form as
the advanced/reusable alternative, explaining when request objects are useful
(reuse, validation, cross-layer assembly, complex/mutually-exclusive inputs).

#### Scenario: Docs show direct keyword form first

- **WHEN** the resource method documentation for an in-scope method is
  reviewed
- **THEN** the primary example uses the direct keyword form and a secondary
  example shows the request-object form labeled as the reusable/advanced
  alternative.

#### Scenario: Docs explain when request objects remain valuable

- **WHEN** the documentation is reviewed
- **THEN** it states that request objects are useful for reuse, validation,
  storage, and cross-layer assembly, and that out-of-scope request objects
  remain the only form for their methods.