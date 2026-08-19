## MODIFIED Requirements

### Requirement: Public status inputs normalize exact enum values
Issue status inputs on direct list fields, `IssueListFilter`, issue resource
`set_status`, and bound `Issue.set_status` SHALL accept `IssueStatus | str`.
Canonical `IssueStatus` members remain the seven values `backlog`, `todo`,
`in_progress`, `in_review`, `done`, `blocked`, and `cancelled`. List, filter,
and `set_status` construction SHALL pass the enum value or string through to
argv without a local enum membership check for unknown custom names; invalid
names fail at the CLI after construction. Non-str/non-enum values SHALL raise
`TypeError` before transport. Documentation SHALL use real values such as
`"todo"`, `"in_progress"`, and `"done"`. `"open"` SHALL remain a documentation
anti-example of a non-status spelling and SHALL NOT be a local `ValueError`
oracle for unknown issue status strings. Get/list/`Issue.status` /
`_IssueWire.status` decoding SHALL use `IssueStatus | str` and SHALL preserve
unknown status names without a constructor crash. This change SHALL NOT add
workspace-status CRUD. Whether tagged CLI accepts custom names is a source
mapping note, not a second SDK construction rule.

`ProjectResource.set_status` SHALL continue to accept a `ProjectStatus` member
or its exact case-sensitive string value. Unknown project status strings SHALL
raise `ValueError` before transport. `Project` has no `set_status[_command]`
bound-entity surface, and this change SHALL NOT add one.

#### Scenario: Exact issue status string is accepted
- **WHEN** a caller uses `issues.list(status="todo")` or `issue.set_status("done")`
- **THEN** the command contains the same governed status value as the corresponding `IssueStatus` member

#### Scenario: Exact project resource status string is accepted
- **WHEN** a caller uses `client.projects.set_status(project_id, "in_progress")`
- **THEN** the command contains the same governed status value as `ProjectStatus.in_progress`

#### Scenario: Unknown issue status strings pass through on set_status
- **WHEN** a caller passes a non-canonical status string to resource or bound `set_status`
- **THEN** construction emits that string in argv and does not raise `ValueError` for unknown membership; invalid names fail at the CLI

#### Scenario: Unknown issue status strings pass through on list and IssueListFilter
- **WHEN** a caller passes a non-canonical status string to `issues.list(status=...)` or `IssueListFilter`
- **THEN** construction emits that string in argv and does not raise `ValueError` for unknown membership; invalid names fail at the CLI

#### Scenario: Incompatible issue status types fail locally
- **WHEN** a caller passes a non-string/non-enum value to an issue status input
- **THEN** construction raises `TypeError` before transport and does not raise `AttributeError`

#### Scenario: Unknown status fails with a typed local error
- **WHEN** a caller passes a non-string/non-enum value to any public status input, or passes `"open"`, a differently cased spelling, or another unknown string to `ProjectResource.set_status`
- **THEN** construction raises `TypeError` for incompatible types or `ValueError` for unknown project status strings before transport and does not raise `AttributeError`

## ADDED Requirements

### Requirement: Workspace and agent MCP libraries are public operations

The SDK SHALL expose tagged `v0.4.28` MCP library commands as eager/command
pairs on nested resource classes: `workspace mcp list|add|update|remove` and
`agent mcp list|add|enable|disable|remove`. Those nested surfaces SHALL register
in `RESOURCE_SPECS` / `_NESTED_RESOURCE_ATTRS` (and `__init__` / docs exports)
the same way `issues.metadata` does, so discovery tests see the methods. Workspace add and update SHALL
accept exactly one of `server_config_file`, `server_config_stdin`, or an inline
`server_config` string. File and stdin SHALL be the documented default channels.
When an inline JSON string is accepted, it SHALL be redacted from preview,
diagnostics, and exception attributes. Workspace MCP list decoding SHALL use
only reviewed public fields and SHALL NOT claim to return stored server
config or tokens. Agent MCP mutations SHALL take `agent_id` and `server_id`
only. Workspace and agent MCP mutations SHALL emit `--output json` unless
source proves a given command is non-JSON.

#### Scenario: Workspace MCP list omits secrets
- **WHEN** `workspace.mcp_servers.all()` loads
- **THEN** argv is `workspace mcp list --output json` (command tokens only; workspace scope is client `--workspace-id`, not a required command `--workspace`) and decoded rows contain reviewed public identity fields without config JSON or credentials

#### Scenario: Workspace MCP add prefers a config file
- **WHEN** add is called with `server_config_file=path`
- **THEN** argv contains `--server-config-file <path>` and does not contain `--server-config` or `--server-config-stdin`

#### Scenario: Workspace MCP add rejects mixed config channels
- **WHEN** more than one of inline JSON, file, and stdin is present
- **THEN** construction raises `ValueError` before transport

#### Scenario: Inline MCP JSON is redacted
- **WHEN** add is called with inline `server_config` containing a token
- **THEN** preview and exception diagnostics omit the token while the executed argv still carries the JSON flag if that channel is used

#### Scenario: Agent MCP enable is a distinct command
- **WHEN** `agents.mcp.enable(agent_id, server_id)` runs
- **THEN** argv is `agent mcp enable <agent-id> <server-id> --output json` unless source proves enable is non-JSON, and is not implemented as add or update

### Requirement: Skill refresh is a governed operation

`SkillResource` SHALL expose `refresh` / `refresh_command` mapping to
`skill refresh <id> --output json`. The method SHALL validate a nonblank skill
id before transport and SHALL decode the reviewed JSON result into the existing
`Skill` model or the reviewed action envelope, whichever source returns.

#### Scenario: Skill refresh emits exact argv
- **WHEN** `client.skills.refresh(skill_id)` runs
- **THEN** argv is `skill refresh <skill-id> --output json` and construction performs no subprocess I/O until `run()`

### Requirement: Issue status and assignee follow tagged CLI semantics

`IssueStatus` SHALL retain the seven canonical values `backlog`, `todo`,
`in_progress`, `in_review`, `done`, `blocked`, and `cancelled`. Get/list,
`Issue.status`, and `_IssueWire.status` decoding SHALL accept `IssueStatus | str`
and SHALL preserve unknown names without a constructor crash. Issue list,
filter, and `set_status` SHALL accept `IssueStatus | str` and SHALL pass the
value through to argv without a local enum membership check; invalid names
fail at the CLI after construction. The SDK SHALL NOT invent a
workspace-status CRUD API. Source-trace of whether tagged CLI accepts custom
names is a mapping note, not a second SDK rule. Any reviewed category
field SHALL be an optional open string on issue models and SHALL default to
`None` when omitted.

`--assignee` SHALL remain a single string flag. When source resolves email
addresses through that flag, canonical vectors MAY use an email value; the SDK
SHALL NOT add a separate `assignee_email` parameter.

#### Scenario: Canonical statuses still construct
- **WHEN** `set_status(issue_id, IssueStatus.in_review)` runs
- **THEN** argv is `issue status <issue-id> in_review`

#### Scenario: Unknown status strings pass through on set_status
- **WHEN** a caller passes a non-canonical status string to `set_status`
- **THEN** construction emits that string in argv and does not raise `ValueError` for unknown membership; invalid names fail at the CLI

#### Scenario: Unknown status strings pass through on list and IssueListFilter
- **WHEN** a caller passes a non-canonical status string to `issues.list(status=...)` or `IssueListFilter`
- **THEN** construction emits that string in argv and does not raise `ValueError` for unknown membership; invalid names fail at the CLI

#### Scenario: Unknown status strings decode
- **WHEN** issue get JSON contains a status name absent from the seven canonical values
- **THEN** decoding succeeds and `Issue.status` preserves that string

#### Scenario: Assignee email uses the existing flag
- **WHEN** create or assign is called with `assignee="user@example.com"` and source accepts email on `--assignee`
- **THEN** argv contains `--assignee user@example.com` and does not add a second email flag
