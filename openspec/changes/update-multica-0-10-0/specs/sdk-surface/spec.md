## ADDED Requirements

### Requirement: Backward-compatible retained response adaptations
Retained SDK operations SHALL expose only proven `0.10.0` task, attachment, comment-resolution, project, runtime, user-profile, workspace, issue-requester, subscriber, activity/archive, and pagination fields through existing public model and entity seams.

#### Scenario: Legacy omission remains decodable
- **WHEN** a supported older CLI omits a target-added optional or nullable field
- **THEN** the existing operation SHALL decode successfully using the documented legacy default without fabricating a target value

#### Scenario: Present, null, and malformed values stay distinct
- **WHEN** a target response contains a valid present value, an explicitly nullable value, or an invalid wire type
- **THEN** the SDK SHALL respectively preserve the value, preserve documented null semantics, or raise the existing typed output-shape error

#### Scenario: Upstream-owned values remain open
- **WHEN** a retained response contains a syntactically valid future status, delivery, visibility, or result token
- **THEN** the SDK SHALL preserve the token instead of failing a closed enum that this change did not approve

### Requirement: Project privacy, activity, and subscriber semantics
Project and issue operations SHALL represent target project activity/archive/list pagination, membership-only private access, and inherited subscriber coverage/delivery without broadening caller access.

#### Scenario: Private non-member remains undiscoverable
- **WHEN** a privileged but non-member caller gets or lists a private project
- **THEN** the SDK SHALL preserve the proven not-found or omission behavior and SHALL NOT synthesize a redacted project

#### Scenario: Project list pagination is complete
- **WHEN** the target project list returns activity/archive fields and `has_more`
- **THEN** the existing page/result seam SHALL preserve those fields, cursor/limit behavior, omission/null rules, and malformed-value rejection

#### Scenario: Subscriber delivery is explicit
- **WHEN** issue subscribers include project-inherited coverage
- **THEN** `project_covered` and delivery classification SHALL decode with positive, omitted, null, malformed, and older-server fixtures

### Requirement: Run-targeted rerun migration
The SDK SHALL remove the target-invalid `issue rerun` mapping and SHALL expose the proven `issue rerun-task` operation using explicit run/task identity, resume-versus-fresh semantics, and its typed result.

#### Scenario: Resume an existing task run
- **WHEN** the caller invokes rerun-task with the required identity and resume mode
- **THEN** the SDK SHALL build the exact target argv and decode the returned run/task result

#### Scenario: Start fresh
- **WHEN** the caller selects fresh mode
- **THEN** the SDK SHALL emit only the proven fresh selector and preserve the target result and error contract

#### Scenario: Legacy issue rerun is not silently aliased
- **WHEN** a caller looks for the removed issue-targeted operation
- **THEN** the public surface and migration documentation SHALL direct the caller to explicit run-targeted rerun and SHALL NOT infer a run from an issue

### Requirement: New command families remain deferred
Every target-added command family without a separately approved Python contract SHALL remain inventoried but unavailable from the public SDK.

#### Scenario: Deferred operations create no public symbols
- **WHEN** generated and handwritten public surfaces are inspected
- **THEN** issue batch/delete/status, workflow, project workflow/member/archive/restore, saved-view, runtime-concurrency, PR-link/unlink, hidden/source-only commands, and other deferred nodes SHALL have no method, binding, model, export, or usage example

#### Scenario: Retained operations remain complete
- **WHEN** public-operation completeness is checked
- **THEN** deferral SHALL NOT remove or weaken any retained/adapted operation required by this change
