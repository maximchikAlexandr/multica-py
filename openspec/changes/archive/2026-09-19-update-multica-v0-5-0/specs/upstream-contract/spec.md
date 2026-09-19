## ADDED Requirements

### Requirement: Multica 0.5.0 source authority
The approved contract SHALL pin stable Multica `0.5.0` to exact commit `2df765a3c8f39789c9fb76316378bcffc20d22d9`, release ID `391379076`, verified archive and executable digests, and exact source locations for every changed mapping and response.

#### Scenario: Identity is independently reproducible
- **WHEN** maintainers reproduce the target evidence
- **THEN** release, tag, archive, executable, version JSON, and source commit identities SHALL match the approved contract before public behavior changes

### Requirement: Complete 0.4.44 to 0.5.0 command reconciliation
The approved contract SHALL reconcile all 189 baseline and 194 target public help nodes, including five additions, zero removals, renames, or moves, and the three changed label commands. Every retained or added command SHALL record positional arity, aliases, local and persistent flags, defaults, required and conflict rules, presence-sensitive constraints, secret channels, destination encoding, and positive and negative test references.

#### Scenario: Command topology is exact
- **WHEN** strict validation compares approved command inventory with pinned evidence
- **THEN** it SHALL prove 189 baseline nodes, 194 target nodes, five additions, zero removals/renames/moves, and exact changed label mappings

#### Scenario: Imperative constraints remain review-gated
- **WHEN** a changed command uses `Flags().Changed`, custom validation, or helper logic
- **THEN** the approved mapping SHALL normalize the behavior and SHALL NOT promote collector output directly

### Requirement: Complete response reconciliation
The approved contract SHALL contain one decision for each of the 163 supported response entrypoints: targeted reviewed mappings and fixtures for six changed entrypoints and exact-equality evidence for 157 unchanged entrypoints. Every source-link work item SHALL occur exactly once.

#### Scenario: Response audit is complete
- **WHEN** the response and source-link audit runs
- **THEN** all 163 entrypoints SHALL be accounted for exactly once with a `changed` or `unchanged` disposition and resolvable pinned source

### Requirement: Reviewed 0.5.0 compatibility
The generated default compatibility interval SHALL be `[0.4.42,0.5.1)`, with `0.5.0` as maximum tested and operation-level `0.5.0` minimums for new comment-update, skill-label, label-input, and target-only response behavior.

#### Scenario: Retained operations preserve the floor
- **WHEN** a retained operation is checked against CLI `0.4.42` through `0.5.0`
- **THEN** the generated policy SHALL preserve its reviewed compatibility unless an operation-specific target gate applies

#### Scenario: Unreviewed future CLI is outside the interval
- **WHEN** CLI version `0.5.1` or later is detected
- **THEN** compatibility policy SHALL reject or warn according to the existing mode and SHALL NOT claim unreviewed support

### Requirement: Evidence remains non-authoritative
Only the human-reviewed `contracts/sdk-contract.json` SHALL drive generated production behavior. Archives, binaries, collector output, gap audits, response reviews, and transient renders SHALL remain untracked evidence.

#### Scenario: Candidate evidence cannot add API
- **WHEN** evidence contains a new command or field absent from the approved contract
- **THEN** rendering SHALL leave public behavior unchanged and strict review SHALL remain required
