## ADDED Requirements

### Requirement: Target relation inventory excludes Plugin and retains run history

The bound relation inventory SHALL contain exactly `37` relations after
removing only `Workspace.plugins` / `plugins.list` from the existing `38`-row
inventory. Former rows R35 through R38 SHALL retain their stable IDs and SHALL
not be renumbered. `Workspace.properties`, `Workspace.mcp_servers`,
`Agent.mcp_servers`, and `Issue.properties` SHALL retain their existing loaders
and invalidation. `Issue.runs` SHALL retain the default full-history operation
and SHALL not opt into compact active/sibling modes.

#### Scenario: Relation discovery is exact
- **WHEN** bound relation members and governed loader operations are discovered
- **THEN** exactly 37 relations remain, R34 is absent, R35 through R38 retain their IDs, and no allowlist hides an extra or missing member

#### Scenario: Workspace has no Plugin relation
- **WHEN** a bound Workspace public surface is inspected
- **THEN** `plugins` and its cache/loader/invalidation state are absent

#### Scenario: Existing target-compatible relations do not drift
- **WHEN** properties and MCP relations load or mutate
- **THEN** their exact parent addressing, response types, cache ownership, and invalidation remain unchanged

#### Scenario: Issue runs retains the full envelope
- **WHEN** a bound Issue loads runs
- **THEN** it performs the existing default `issues.runs` call without active/sibling flags and yields full TaskRun values

## MODIFIED Requirements

### Requirement: Workspace relation graph

A bound `Workspace` MUST expose `members`, `agents`, `skills`, `projects`,
`issues`, `labels`, `autopilots`, `repositories`, `runtimes`, `squads`,
`properties`, and `mcp_servers` using the workspace identifier as server-side
scope and the original client runtime. It MUST NOT expose `plugins` against
target `0.4.42`. `Workspace.issues` MUST yield bound `Issue` entities.

#### Scenario: Workspace unpaged relations use one scoped call
- **WHEN** `members`, `agents`, `skills`, `projects`, `labels`, `repositories`, `runtimes`, `squads`, `properties`, or `mcp_servers` is completely loaded
- **THEN** exactly one governed workspace-scoped list operation runs and typed entities are returned in response order

#### Scenario: Workspace issues traverse offset pages
- **WHEN** `workspace.issues` is completely loaded
- **THEN** governed `issues.list` requests preserve workspace scope, yield bound issues, and advance offsets until truthful `has_more` is false without per-item gets

#### Scenario: Workspace autopilots preserve aggregate metadata
- **WHEN** `workspace.autopilots` loads the governed list response
- **THEN** its entities are available through the relation and upstream total metadata remains accessible

#### Scenario: Workspace Plugin access is removed
- **WHEN** a consumer or public-discovery check looks for `Workspace.plugins`
- **THEN** the member is absent and migration documentation explains the upstream removal
