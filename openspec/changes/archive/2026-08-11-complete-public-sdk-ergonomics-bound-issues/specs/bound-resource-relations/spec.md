## ADDED Requirements

### Requirement: Direct issue children results retain origin binding
`IssueResource.children` and `children_command` SHALL return an `IssueChildrenResult` whose `children`/`items` and `unstaged` tuples contain `Issue` entities bound to the originating `MulticaClient`. Binding SHALL be a pure result-finalization step over the already decoded collection payload; it SHALL preserve all page and child-stage metadata, issue snapshots, command inspection, and lazy relation behavior and SHALL issue no per-row or follow-up CLI calls.

#### Scenario: Child rows are immediately actionable
- **WHEN** `client.issues.children(parent_id)` returns one or more values in `children`
- **THEN** every child can immediately construct and run entity actions and lazy relation commands through the originating client without `client.issues.get(child.id)`

#### Scenario: Unstaged rows are immediately actionable
- **WHEN** a direct children result contains values in `unstaged`
- **THEN** every unstaged issue has the same originating-client binding as values in `children`

#### Scenario: Command execution binds both collections
- **WHEN** a caller inspects and runs `client.issues.children_command(parent_id)`
- **THEN** the inspected plan remains the single governed `issue children` command and its final result binds both issue tuples

#### Scenario: Binding preserves the complete result envelope
- **WHEN** the upstream result includes `total`, `child_stages`, `limit`, `offset`, `has_more`, or `next_cursor`
- **THEN** the bound `IssueChildrenResult` preserves those values exactly while replacing only each issue's client reference

#### Scenario: N child rows do not cause N plus one reads
- **WHEN** a result contains any number of children and unstaged issues
- **THEN** exactly one `issue children` transport call executes and zero implicit `issue get` calls execute
