## ADDED Requirements

### Requirement: Multica v0.4.28 is the reviewed compatibility baseline

The approved SDK contract SHALL target tag `v0.4.28`, version `0.4.28`, release
ID `371790559`, and commit
`38c992ad0a757434fb51584fa34e3bc57d1b78e1`. Every retained or added source
reference SHALL point to that exact commit and a reviewed path, symbol, and line
range. Release evidence SHALL be collected from a verified `v0.4.28` CLI asset
whose name, operating system, architecture, SHA-256, and `version --output
json` bytes agree with release metadata. Evidence and transient projections
SHALL remain outside version control and SHALL NOT directly promote public SDK
behavior.

#### Scenario: Baseline metadata is exact
- **WHEN** `contracts/sdk-contract.json` and the generated runtime projection are inspected
- **THEN** they identify `v0.4.28` at commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`, release ID `371790559`, and no retained `v0.4.20` target or source commit remains except in historical/archive material

#### Scenario: Compatibility interval advances one patch
- **WHEN** default compatibility policy is generated from the approved target
- **THEN** its minimum is `0.4.28` and its exclusive maximum is `0.4.29`

#### Scenario: Promotion uses the complete workflow
- **WHEN** maintainers prepare the baseline upgrade
- **THEN** they run `collect` with pinned source and verified binary evidence, `validate --source-checkout` against the approved contract, deterministic `render`, and `check` in that order before offline release verification

#### Scenario: Unreleased main commands stay excluded
- **WHEN** upstream `main` contains commands or behavior absent from tag `v0.4.28`
- **THEN** those candidates do not enter the approved contract, generated runtime, public SDK, or canonical operation inventory through this change

### Requirement: v0.4.28 command tree is reconciled before promotion

The approved contract SHALL classify every tagged `v0.4.28` Cobra command as
retained, newly approved, or explicitly deferred with rationale. Newly approved
families SHALL include plugins, properties, issue properties, workspace MCP,
agent MCP, and skill refresh unless source proves a command is hidden,
interactive, or otherwise unsafe. Every exposed positional argument and flag
SHALL record its CLI binding, actual landing destination or local-control role,
presence policy, normalized constraint, response/adapter policy, exact source
references, and positive/negative test references. Name similarity SHALL NOT
prove mapping.

#### Scenario: Plugin operations are source-governed
- **WHEN** `plugins.list` and `plugins.install` are inspected
- **THEN** list traces to `/api/workspaces/{id}/plugins/private` and install traces to the private install upload path, with human-local guards recorded from `requireHumanLocalCommand`

#### Scenario: Property actor types are source-governed
- **WHEN** `properties.create` and `issues.properties.set` are inspected
- **THEN** `actor` / `multi_actor` types, option rejection, and `--value` encoding are traced through `cmd_property.go` rather than inferred from flag names

#### Scenario: MCP config channels are source-governed
- **WHEN** `workspaces.mcp.add` is inspected
- **THEN** exactly-one config input among inline JSON, file, and stdin is recorded from `resolveMcpJSONObject`, and list decoding cites the write-only public fields

#### Scenario: Deferred commands are explicit
- **WHEN** a tagged command is not approved
- **THEN** contract compatibility metadata names the command and the deferral rationale, and generated public SDK behavior does not include it

## REMOVED Requirements

### Requirement: Multica v0.4.20 is the reviewed compatibility baseline
**Reason**: The reviewed compatibility baseline advances to tagged `v0.4.28`.
**Migration**: Use the added `v0.4.28` baseline requirement, commit
`38c992ad0a757434fb51584fa34e3bc57d1b78e1`, release ID `371790559`, and interval
`[0.4.28, 0.4.29)`.

### Requirement: v0.4.20 changed operations are source-governed
**Reason**: Source governance for this upgrade is the full `v0.4.28` command tree,
not the `v0.4.20` copy/search/cascade delta.
**Migration**: Follow `v0.4.28 command tree is reconciled before promotion`. Keep
existing `agents.copy`, `issues.search`, and `runtimes.delete` mappings unless
pinned-source review finds drift.
