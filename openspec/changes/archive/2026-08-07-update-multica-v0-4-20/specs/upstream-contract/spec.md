## ADDED Requirements

### Requirement: Multica v0.4.20 is the reviewed compatibility baseline

The approved SDK contract SHALL target tag `v0.4.20`, version `0.4.20`, release
ID `366120041`, and commit
`93342d04a7a9f788fec921e5aa736f86c7f22d8f`. Every retained or added source
reference SHALL point to that exact commit and a reviewed path, symbol, and line
range. Release evidence SHALL be collected from a verified `v0.4.20` CLI asset
whose name, operating system, architecture, SHA-256, and `version --output
json` bytes agree with release metadata. Evidence and transient projections
SHALL remain outside version control and SHALL NOT directly promote public SDK
behavior.

#### Scenario: Baseline metadata is exact
- **WHEN** `contracts/sdk-contract.json` and the generated runtime projection are inspected
- **THEN** they identify `v0.4.20` at commit `93342d04a7a9f788fec921e5aa736f86c7f22d8f`, release ID `366120041`, and no retained `v0.4.9` target or source commit remains

#### Scenario: Compatibility interval advances one patch
- **WHEN** default compatibility policy is generated from the approved target
- **THEN** its minimum is `0.4.20` and its exclusive maximum is `0.4.21`

#### Scenario: Promotion uses the complete workflow
- **WHEN** maintainers prepare the baseline upgrade
- **THEN** they run `collect` with pinned source and verified binary evidence, `validate --source-checkout` against the approved contract, deterministic `render`, and `check` in that order before offline release verification

#### Scenario: Unreleased main commands stay excluded
- **WHEN** upstream `main` contains commands or behavior absent from tag `v0.4.20`
- **THEN** those candidates do not enter the approved contract, generated runtime, public SDK, or canonical operation inventory through this change

### Requirement: v0.4.20 changed operations are source-governed

The approved contract SHALL add governed `agents.copy` and `issues.search`
operations and SHALL update the reviewed semantics and source evidence for
`runtimes.delete`, error classification, and `autopilots.trigger`. Every exposed
positional argument and flag SHALL record its CLI binding, actual landing
destination or local-control role, presence policy, normalized constraint,
response/adapter policy, exact source references, and positive/negative test
references. Imperative `Flags().Changed(...)` behavior and runtime-specific
copy rules SHALL be reviewed explicitly rather than inferred from flag names.

#### Scenario: Agent copy mapping traces GET and create behavior
- **WHEN** `agents.copy` is inspected in the approved contract
- **THEN** source-agent lookup, copied/defaulted portable fields, each exposed override, cross-runtime model policy, permission targets, skill omission, and excluded secret/machine-local fields are traced through `runAgentCopy` to path, JSON-body, or local-control destinations

#### Scenario: Issue search adapter is governed
- **WHEN** `issues.search` is inspected in the approved contract
- **THEN** the query maps to the search path/query behavior, exact CLI argv is fixed, the `issues` envelope and optional open-string `match_source` adapter are approved, and legacy array compatibility is identified as handwritten SDK policy

#### Scenario: Runtime cascade semantics are reviewed
- **WHEN** `runtimes.delete` contract rationale and source references are inspected
- **THEN** `cascade=True` is documented as conflict discovery followed by unbind-agents-and-delete, with active work cancellation and preserved agent configuration/history rather than agent archive or destruction

#### Scenario: Existing autopilot trigger cannot regress
- **WHEN** approved bindings and canonical vectors are validated against `v0.4.20`
- **THEN** `autopilots.trigger` emits `autopilot trigger <id>`, no `autopilot run` binding or legacy public method is present, and source-contract validation fails if the old spelling returns

#### Scenario: Error source evidence pins actionable prefixes
- **WHEN** conflict and validation classification rules are reviewed
- **THEN** their accepted HTTP statuses, exit behavior, localized formatter prefixes, safe-detail extraction, and fallback behavior cite the `v0.4.20` CLI error implementation and matching tests
