## ADDED Requirements

### Requirement: Multica 0.7.0 release provenance is authoritative

The approved contract SHALL identify Multica `0.7.0`, release id `421685918`,
tag object `db6e38c32bdbdd3fd1c98210414c458362df16d1`, peeled commit
`dbdbb299164347586e2650bb67684a490726a798`, the verified Darwin arm64 archive
and executable digests, and the pinned source URLs used by every changed mapping
or response. It SHALL retain `0.6.1` provenance as the effective direct migration
baseline.

#### Scenario: Provenance is complete

- **WHEN** strict contract validation inspects the target and release artifacts
- **THEN** every required identity and digest matches the reviewed `0.7.0` release and no draft SDK branch is represented as a baseline

### Requirement: Target inventory is closed before generation

The approved contract SHALL contain one reviewed verdict for every one of the
209 target CLI nodes and one unique verdict for every one of the 196 supported
response work items. The totals SHALL reconcile to four added, zero removed,
six changed CLI nodes and 60 changed plus 136 unchanged response items.

#### Scenario: An inventory item is absent or duplicated

- **WHEN** validation finds a missing, duplicated, or unresolved command or response verdict
- **THEN** validation fails and generation changes no public behavior

#### Scenario: Deferred commands remain non-public

- **WHEN** the four `daemon autostart` nodes are rendered
- **THEN** they remain explicit `defer` decisions and produce no SDK resource, model, method, or export

### Requirement: Reviewed mappings preserve destination and presence semantics

Every added or changed input SHALL record its path, query, JSON, header,
multipart, stdin, file, or local-control destination; omitted, null, empty,
zero, and false behavior; and all normalized constraints with positive and
negative test references.

#### Scenario: Names match without traced behavior

- **WHEN** an evidence field or enum candidate has no pinned `RunE` and helper trace to its destination and constraint behavior
- **THEN** the candidate remains review-only and strict validation rejects its promotion

### Requirement: Direct compatibility interval is generated

The generated default policy SHALL represent the reviewed direct migration from
Multica CLI `0.6.1` through the approved `0.7.0` target, with
`max_tested_cli_version` equal to `0.7.0` and the existing exclusive-next-version
policy applied above the reviewed interval.

#### Scenario: Reviewed endpoints are accepted

- **WHEN** compatibility preflight observes `0.6.1` or `0.7.0`
- **THEN** it applies the reviewed policy without requiring an intermediate SDK release

#### Scenario: A version exceeds the reviewed ceiling

- **WHEN** compatibility preflight observes a version above the generated exclusive ceiling
- **THEN** the configured strict or warning policy is applied and no unreviewed behavior is claimed

### Requirement: Generation remains deterministic and contract-only

The approved contract SHALL remain the only production generator input. Rendering
twice from the same contract SHALL produce byte-identical committed runtime and
transient projections; evidence, audit copies, and upgrade bundles SHALL NOT be
tracked or imported at runtime.

#### Scenario: Evidence contains a candidate change

- **WHEN** a candidate exists only in evidence or an audit projection
- **THEN** deterministic generation leaves the public runtime unchanged
