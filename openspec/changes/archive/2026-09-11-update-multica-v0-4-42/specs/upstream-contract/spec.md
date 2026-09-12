## ADDED Requirements

### Requirement: Multica 0.4.42 is the exact reviewed authority

The approved SDK contract SHALL target tag `v0.4.42`, version `0.4.42`, release
ID `385445715`, and commit
`76f59f5f1cd9b6e779d0d34c603407d5d4001bf7`. The compatibility interval SHALL
have minimum and maximum-tested version `0.4.42` and SHALL render the exclusive
upper bound `0.4.43`. Every retained, changed, or removed operation SHALL cite
exact source URLs pinned to either the approved old commit
`38c992ad0a757434fb51584fa34e3bc57d1b78e1` or the target commit.

#### Scenario: Target and generated interval agree
- **WHEN** the approved contract, generated runtime, and compatibility docs are inspected
- **THEN** they identify `v0.4.42` at the exact target commit and generated bounds `[0.4.42, 0.4.43)`

#### Scenario: Moving source references fail
- **WHEN** a changed or retained mapping cites a branch, tag URL, abbreviated object, or any commit other than its reviewed old/target SHA
- **THEN** strict validation or the source-link audit fails before promotion

### Requirement: Release archive and executable identities remain distinct

The review SHALL record the `multica-cli-0.4.28-darwin-arm64.tar.gz` archive
SHA-256 `e42c1c6df05201d2d0feff1a9d8032a9ea11c6644721fd465496826124007acf`
and extracted executable SHA-256
`26a722384d8ef39a30cb83fec4e76f3185768369536d1f13a546b03e6c7fbeb9` as
separate baseline values. It SHALL likewise record the `0.4.42` archive SHA-256
`a3bb48baeeb757361686978210e6195aaf50bc69edf83bf3b9c52ca3efc12e41`
and executable SHA-256
`22abcd910562e8800c0e9db561229731e19486ec94b4815d6b1a075dc92ef36c`
as separate target values. Collector binary identity validation SHALL receive
the executable digest, while release verification SHALL verify the archive
against the official manifest and asset digest.

#### Scenario: Archive digest is not passed as binary digest
- **WHEN** a maintainer follows the compatibility collection example
- **THEN** the archive is verified with its archive SHA-256 and collector `--sha256` receives the extracted executable SHA-256

#### Scenario: Binary version envelope is exact
- **WHEN** the target executable runs `version --output json`
- **THEN** it reports version `0.4.42`, commit prefix `76f59f5f1`, date `2026-09-09T11:06:33Z`, Go `1.26.8`, and `darwin/arm64`, and the prefix resolves to the approved full SHA

### Requirement: Complete 0.4.28 to 0.4.42 command and response reconciliation

The approved review SHALL account for all `199` baseline and `189` target
Cobra nodes as `166` unchanged, `21` changed, `2` added, and `12` removed.
It SHALL classify `multica` as the root, `probe-runtimes` as hidden, and
`repo-test`, `test`, and `x` as test-only/unattached. It SHALL also account for
all `173` exact SDK response work items exactly once, with `51` changed and
`122` unchanged, without duplicate IDs or missing target source URLs.

#### Scenario: Inventory totals are exact
- **WHEN** strict validation reconciles baseline and target inventories
- **THEN** every command node and response entrypoint appears exactly once and the required totals match

#### Scenario: Retained mappings are fully traced
- **WHEN** a retained or changed command is approved
- **THEN** every positional validator, local and inherited flag, default, alias, required flag, enum/range, `Flags().Changed` branch, destination, encoding, conflict, and secret channel is traced through `RunE` and helpers

#### Scenario: Extractor output cannot approve behavior
- **WHEN** evidence or a generated suggestion contains a new command, enum, mapping, or response field
- **THEN** generated public behavior remains unchanged until the reviewed fact exists in `contracts/sdk-contract.json`

### Requirement: Target command dispositions are explicit

The approved contract SHALL remove all Plugin operations and autopilot priority
inputs because the target CLI lacks them. It SHALL retain the default
`issues.runs` history operation and safe redacted autopilot reads. It SHALL
defer `issue timeline`, `autopilot trigger-list`, and compact
`issues.runs --active/--siblings` until separate typed response contracts are
approved. It SHALL approve opt-in `issue get --resolve-properties` and issue
list `--fields`, repeatable `--property`, `--resolve-properties`, and property
sort while preserving existing defaults.

#### Scenario: Removed Plugin tree cannot remain approved
- **WHEN** approved operation paths are compared with target root registration
- **THEN** no `plugins.*` operation, binding, response adapter, or canonical vector remains

#### Scenario: Deferred commands do not become public methods
- **WHEN** target evidence contains timeline, trigger-list, active, or sibling command facts
- **THEN** the review records the stated deferral and generation creates no public method or alternate response adapter for them

#### Scenario: Issue query additions are opt-in
- **WHEN** no new issue projection or property option is supplied
- **THEN** approved argv and default response adapters remain compatible with the existing issue get/list behavior

## REMOVED Requirements

### Requirement: Multica v0.4.28 is the reviewed compatibility baseline

**Reason**: The exact reviewed source and binary authority advances directly to stable `0.4.42`.

**Migration**: Replace target `0.4.28` and bounds through `0.4.38` with exact target `0.4.42` and `[0.4.42, 0.4.43)`.

### Requirement: v0.4.28 command tree is reconciled before promotion

**Reason**: The complete review range is now `0.4.28` through `0.4.42`, including removals after `0.4.28`.

**Migration**: Use the target-wide command and response reconciliation requirement above.

### Requirement: CLI 0.4.38 version evidence is exact

**Reason**: `0.4.42` supersedes `0.4.38` as the maximum-tested stable CLI.

**Migration**: Preserve `0.4.38` only as historical reviewed evidence and generate the strict interval from `0.4.42`.
