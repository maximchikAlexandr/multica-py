## MODIFIED Requirements

### Requirement: Multica 0.5.3 patch coverage is table-driven
Offline verification SHALL extend existing frozen contract, provenance,
operation, response, usage, compatibility, documentation, and package case
tables. It SHALL prove exact target identity and full public CLI parity rather
than only the `0.5.2` to `0.5.3` version delta. Source-linked cases SHALL cover
broken contracts A1 through A10, missing operations B1 through B17, missing
inputs C1 through C24, response gaps D1 through D17, and every additional
public item found by the closed inventory without creating a parallel fixture
framework.

#### Scenario: Native mismatch fixtures reproduce and close regressions
- **WHEN** daemon, comment, attachment, squad, project-resource, auth, and lifecycle regression cases run through public operations
- **THEN** exact argv, transport, cursor parsing, output decoding, field preservation, and error behavior match pinned source evidence

#### Scenario: Public surface matches complete parity inventory
- **WHEN** model, symbol, operation, signature, dependency, relation, transport, command, flag, response, and field inventories are checked
- **THEN** every public target item has one passing evidence-backed disposition and no partial, unknown, deferred, or unreviewed public item remains

### Requirement: Complete upstream audits are reproducible for 0.5.3
Maintainer evidence SHALL reproduce official release and checksum identities,
separate baseline and target binaries, version output, recursive binary help,
pinned source registration, dynamic factories, aliased flags, the complete
public command/input inventory, all response output paths and nested fields,
and final SDK dispositions. Tracked files and distributions SHALL NOT contain
release archives, executables, source checkouts, collector output, or transient
render directories.

#### Scenario: Reproduced audits agree with the approved contract
- **WHEN** pinned evidence and the public-parity audit are regenerated
- **THEN** exact identities and every command, input, response, field, transport, and exclusion disposition agree or validation fails

#### Scenario: Evidence stays outside source and packages
- **WHEN** tracked and built contents are audited
- **THEN** no binary, archive, checkout, collector, gap audit, or transient render artifact is included

## ADDED Requirements

### Requirement: Parity validation fails on omissions and false positives
Strict validation SHALL compare recursive public help, pinned source,
approved contract entries, generated bindings, handwritten public methods,
canonical operation cases, native response fixtures, documentation tables, and
package exports. The comparison SHALL fail on missing rows, duplicates,
unresolved aliases/factories, false equivalent claims, stale deferrals,
unmapped emitted fields, or public symbols lacking test evidence.

#### Scenario: Unknown source pattern remains blocking
- **WHEN** a relevant extractor review item has no reviewed resolution
- **THEN** strict validation fails and generated behavior remains unchanged

#### Scenario: Public method without canonical evidence fails
- **WHEN** discovery finds a CLI-executing method without one canonical argv/transport/response case
- **THEN** offline completeness validation fails

### Requirement: Verification is safe and layered
Unit and contract tests SHALL prove exact mappings, presence, validation,
redaction, decoder shapes, and contract closure. Component tests SHALL exercise
public methods against the fake CLI, including text, bytes, stdin, streaming,
foreground, and interactive-safe fixtures. Packaging tests SHALL verify exports
and clean imports. Destructive daemon/auth lifecycle behavior SHALL be proven
with source-linked fixtures or isolated child processes and SHALL NOT stop,
restart, or log out the developer environment.

#### Scenario: Offline acceptance remains backend-free
- **WHEN** the mandatory verification suite runs
- **THEN** it needs no authenticated backend or developer daemon mutation and collects no `tests/live/*` node

#### Scenario: Live smoke remains separately gated
- **WHEN** prepared credentials and a safe target are unavailable
- **THEN** live status is reported separately without weakening source-backed offline acceptance

### Requirement: Documentation separates coverage dimensions
Coverage documentation SHALL report API coverage, transport coverage,
presentation equivalence, test evidence, exclusions, and version compatibility
as separate dimensions. It SHALL describe breaking corrections and secret or
interactive behavior without claiming that raw argv alone is typed parity.

#### Scenario: Coverage claims trace to inventory rows
- **WHEN** a documentation claim says a CLI capability is covered
- **THEN** it links to the approved inventory disposition and its public operation or transport and test references

### Requirement: Final delivery is reproducible at one clean SHA
Strict OpenSpec validation, approved-contract validation against pinned source,
deterministic render comparison, generated freshness, source-link audit, Ruff
check and format, mypy for source and tests, non-live pytest with coverage,
live-node exclusion, build, package validation, and tracked-content audit SHALL
all pass at one exact clean commit before release readiness.

#### Scenario: Complete offline gate passes
- **WHEN** final verification runs at the delivery SHA
- **THEN** every mandatory command exits successfully and the worktree remains clean
