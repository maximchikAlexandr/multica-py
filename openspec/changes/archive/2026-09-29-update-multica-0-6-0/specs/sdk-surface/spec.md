## ADDED Requirements

### Requirement: Agent task history exposes target cursor without response leakage
`AgentResource.tasks[_command]` SHALL accept `limit: int = 200` in `1..200` and
optional opaque `before`, always emit `--limit`, emit `--before` only when present,
decode stdout only as the target bare array, and set `Page.next_cursor` only from
the exact successful-stderr cursor hint. Missing hint SHALL yield `None`; unrelated
stderr SHALL remain diagnostics. `IssueResource.runs` SHALL share additive task
fields but SHALL retain its existing non-cursor pagination behavior.

#### Scenario: Successful cursor is captured narrowly
- **WHEN** agent tasks returns a valid bare array and exact cursor hint
- **THEN** items come only from stdout and the opaque cursor is preserved once

#### Scenario: Cursor does not leak to issue runs
- **WHEN** issue runs uses the shared task model or agent-task stderr lacks the exact hint
- **THEN** no cursor is fabricated and existing issue-runs pagination remains unchanged

### Requirement: Issue update delegates target attachment workflow
`IssueResource.update[_command]` SHALL accept ordered repeatable local attachment
paths and `allow_external_file: bool = False`. It SHALL validate container, path
type/existence and boolean before I/O, emit each attachment once, emit external
opt-in only when true, execute attach-only updates, and use an effective timeout of
at least 60 seconds without reducing a larger caller timeout. Target CLI SHALL own
upload, description merge and attachment-ID update. URL paths SHALL not be treated
as local uploads; post-upload failure diagnostics SHALL preserve redacted uploaded
IDs and the SDK SHALL not retry.

#### Scenario: Attachment update maps exactly
- **WHEN** valid in-root attachments are supplied with or without other update fields
- **THEN** their order and flags are exact and target CLI performs the composite workflow once

#### Scenario: Invalid attachment fails before I/O
- **WHEN** the container, element type, existence or external-file permission is invalid
- **THEN** SDK rejects before upload or issue update

#### Scenario: Partial side effect remains observable
- **WHEN** target update fails after uploads succeed
- **THEN** the typed error retains redacted uploaded IDs and no automatic retry occurs

### Requirement: Task wakeup fields are additive and presence-aware
The shared task-run wire/public model SHALL expose optional
`wakeup_system_rule` and `wakeup_joined` according to approved omission/null/type
rules on agent tasks and issue runs. Existing task fields SHALL remain independent;
missing additive fields SHALL not synthesize defaults and malformed present values
SHALL fail typed decoding.

#### Scenario: Task entrypoints preserve additive fields independently
- **WHEN** either changed task entrypoint returns omitted, null or valid wakeup fields
- **THEN** the approved presence state is preserved without changing the envelope or legacy fields

### Requirement: Comment supplements coexist with legacy projection
All seven changed comment entrypoints SHALL decode optional `supplements` in their
existing envelopes. Every supplement SHALL require task ID and status and SHALL
apply the approved optionality to agent ID, failure reason and delivered-at.
Omitted supplements SHALL normalize to an empty immutable collection; explicit
null or malformed items SHALL fail. Legacy scalar supplement fields SHALL decode
independently and SHALL NOT be synthesized from the collection or overwrite it.

#### Scenario: Dual comment projection is independent
- **WHEN** payload contains legacy fields, supplements, both or neither
- **THEN** each representation follows its own presence policy with no inferred precedence or cross-population

### Requirement: Pull request and MCP changes remain entrypoint-scoped
`LinkedPullRequest` SHALL expose typed `pr_auto_complete` with required
`target_status`; its state SHALL remain an open string accepting `at_target`, and
`no_close_intent` SHALL not be treated as a closed enum value. `McpServer` SHALL
expose optional `agent_count` only from workspace MCP list; `0` SHALL be preserved,
while agent-scoped and add/update omissions SHALL remain `None`.

#### Scenario: Pull-request future state survives
- **WHEN** target returns a known or unknown open auto-complete state with valid target status
- **THEN** the value and required target status are preserved without closed-enum rejection

#### Scenario: MCP zero is not omission
- **WHEN** workspace MCP list returns `agent_count: 0`
- **THEN** the public model contains zero and no other MCP entrypoint fabricates the field

### Requirement: Issue timeline accepts wakeup v2 action domain
The existing issue-timeline envelope and pagination SHALL remain unchanged. Action
and details SHALL remain open and SHALL preserve the target wakeup action domain
`wakeup_created|triggered|timed_out|checkin|paused`
and approved detail shapes without converting unknown future actions into errors.

#### Scenario: New wakeup timeline actions preserve the generic envelope
- **WHEN** timeline returns any approved wakeup v2 action or an unknown open action
- **THEN** order, pagination, action string and structured details are preserved without a wakeup-specific alternate timeline API
