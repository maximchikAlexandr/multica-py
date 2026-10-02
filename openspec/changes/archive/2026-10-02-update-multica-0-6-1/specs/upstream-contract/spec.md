## ADDED Requirements

### Requirement: Multica 0.6.1 provenance is exact and separable
The approved contract SHALL identify SDK baseline commit
`48745d2fe9e80ee9c027293ef22971ff5723f5f5` and tree
`3afc72c975052cfb92506e5d20df95a5b925da92`, stable tag `v0.6.1`, release
`400860726`, annotated tag object `09e5d78ad340c46dec83839e858632e96c2b07a0`
and peeled target commit `2ea01ae4ef55de4310b99af192d2dbd367832883`.
It SHALL store archive SHA-256
`f2cc3ef1a142bbf5f419d625cd98323602ca96007b4b29f2e0068439be32a2e9`,
executable SHA-256
`a6a73b6c13a8da4fe9591b0884ee24aaac8a8f0913f1dfb3d8d34eda6a23371e`
and verified version-output identity as distinct facts. Compatibility SHALL be
the direct interval `[0.6.0,0.6.2)`, with `0.6.1` maximum-tested.

#### Scenario: Every identity agrees before promotion
- **WHEN** strict validation checks baseline, tag peel, release, archive, executable, version output and compatibility
- **THEN** every exact identity agrees or promotion fails

#### Scenario: Evidence classes are not conflated
- **WHEN** archive, extracted executable and version-output evidence are rendered or audited
- **THEN** each retains its own digest/identity field and none substitutes for another

### Requirement: Complete target CLI inventory is reconciled
The approved contract SHALL account for all 205 target public CLI nodes as 203
unchanged and two adapted nodes, `issue status` and `issue update`, with zero
added, removed, renamed, moved, deprecated or alias changes. The root command,
hidden `probe-runtimes` and source-augmented dynamic `issue wakeup checkin`
classifications SHALL remain explicit. Both adapted nodes SHALL trace
`--duplicate-of` arity, `Flags().Changed` behavior, resolution, request-body
destination, response-field verification and every local conflict.

#### Scenario: Every target node has one disposition
- **WHEN** strict validation compares approved baseline and target inventories
- **THEN** all 205 nodes have exactly one source-pinned disposition and only the two approved nodes are adapted

#### Scenario: Dynamic source evidence does not create a command gap
- **WHEN** the static collector omits dynamically assembled `issue wakeup checkin`
- **THEN** pinned source plus verified help supplies review evidence while production behavior still comes only from the approved contract

### Requirement: Complete response registry records nine semantic changes
The approved response audit SHALL account for all 196 supported entrypoints,
with nine changed semantics and 187 unchanged. The changed set SHALL be the four
direct/bound issue update/status entrypoints, `agents.tasks`, `issues.runs`,
`issues.usage`, `runtimes.usage` and `repositories.checkout`. The registry SHALL
preserve existing envelopes, open strings, null/absence policies and integer
cost-tick precision while pinning old and target sources, fixtures, adapters and
tests for every changed row.

#### Scenario: Response review is complete
- **WHEN** response-review validation runs
- **THEN** 196 of 196 entrypoints are accounted for, nine are changed, 187 are unchanged and every changed row has source, implementation and test mapping

#### Scenario: Compatible semantic changes do not invent models
- **WHEN** quota, pricing or checkout behavior changes without a wire-shape change
- **THEN** existing public models/adapters remain authoritative and only provenance, fixtures, tests and documentation are updated

### Requirement: Scope remains review-gated
The approved contract SHALL adapt only the four existing issue mutation
entrypoints for `duplicate_of`, retain compatible open-string quota and numeric
usage surfaces, retain repository checkout success shape, and classify model
catalog, UI/chat/performance and daemon-internal changes as not SDK surface.
Collector output, binaries and evidence SHALL NOT generate public behavior.

#### Scenario: Unapproved candidates cannot become SDK surface
- **WHEN** target evidence contains a model label, UI feature or internal policy absent from approved operations
- **THEN** no operation, enum, model, adapter or dependency is added
