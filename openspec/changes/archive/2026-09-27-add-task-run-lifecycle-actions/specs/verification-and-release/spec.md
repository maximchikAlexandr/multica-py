## ADDED Requirements

### Requirement: TaskRun lifecycle aliases are verified as governed additive surface
Offline verification SHALL cover the four new bound `TaskRun` lifecycle methods through the repository's existing frozen dataclass tables, shared fixtures, bound-operation discovery, public-signature checks, and documentation gates. Verification SHALL prove exact argv and option propagation, command construction without I/O, eager/command equivalence, immutable snapshots, returned-client binding, exact-run selection, typed context and protocol failures, root exception propagation, and unchanged run/message relations. The canonical root operation inventory and approved upstream contract SHALL remain unchanged.

#### Scenario: Bound-operation inventory is exact
- **WHEN** public bound methods are discovered after the change
- **THEN** `TaskRun.refresh`, `TaskRun.refresh_command`, `TaskRun.cancel`, and `TaskRun.cancel_command` correspond to explicit governed bound declarations and no unrelated public method is admitted

#### Scenario: Exact command and result behavior is covered
- **WHEN** table-driven lifecycle cases exercise refresh and cancel with default and explicit operation options
- **THEN** complete previews, transport mode, argv, result type, selected run ID, client binding, call count, and original snapshot values match the underlying root plans exactly

#### Scenario: Failure boundaries are covered
- **WHEN** cases exercise detached runs, missing refresh issue context, a successful runs page without the target, invalid root inputs, and root command failures
- **THEN** the specified typed error occurs before or during the same phase as the underlying contract and no extra transport call, retry, mutation, or exception translation occurs

#### Scenario: Existing activity APIs regress neither behavior nor shape
- **WHEN** the focused issue-resource and bound-relation suites run
- **THEN** `Issue.runs`, `TaskRun.messages`, and `TaskRun.stream_events` retain their existing signatures, caching, addressing, and result behavior

#### Scenario: Public documentation preserves the lifecycle boundary
- **WHEN** API and service-usage documentation are checked
- **THEN** they show inspectable refresh and cancel commands, explicit refresh after cancellation, and no new polling, waiting, terminal, verification, or message abstraction
