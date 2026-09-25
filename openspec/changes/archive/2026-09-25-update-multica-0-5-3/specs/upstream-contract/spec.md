## MODIFIED Requirements

### Requirement: Generated compatibility
The generated runtime module MUST provide the tested CLI interval from the
approved target version. For the Multica `0.5.3` target, the interval SHALL be
`[0.4.42,0.5.4)`: `0.4.42` remains the minimum compatible CLI for retained
operations, `0.5.3` is the maximum tested CLI, the duplicate and supplement
fields SHALL continue to require `0.5.2` where field-level compatibility is
represented, atomic create-time properties SHALL continue to require `0.5.2`,
and `0.5.4` is the exclusive next-patch ceiling. Existing operation-level
minimums SHALL remain unchanged because target source proves no operation delta.

#### Scenario: Compatibility uses the reviewed direct-patch interval
- **WHEN** a client reads the generated default policy after the `0.5.3` contract is rendered
- **THEN** it accepts retained operations on `0.4.42` through `0.5.3`, rejects or warns at `0.5.4` according to policy, and retains the existing `0.5.2` gates for duplicate and supplement fields and atomic create properties

#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads default policy
- **THEN** it uses generated minimum and exclusive next-patch maximum versions.
<!-- Source IDs: 002:FR-025,FR-033 -->

## ADDED Requirements

### Requirement: Multica 0.5.3 provenance is exact
The approved contract SHALL identify stable tag `v0.5.3`, release `395523214`,
peeled commit `ff8b285497809e084915016c40c2bc5e5991ffbc`, and the direct comparison
from `d45aba1cd7582bef9210b921bbb7dc198b48e1ee`. It SHALL keep baseline and target
release archives, extracted executables, version JSON records, checksum manifests,
and unsigned-tag evidence distinct. Collector and audit output SHALL remain
non-authoritative and untracked.

#### Scenario: Independent target identities agree
- **WHEN** release metadata, checksum manifest, archive digest, executable identity, binary version output, tag, and source checkout are compared
- **THEN** version and exact commit agree with the approved `0.5.3` target or promotion fails

#### Scenario: Baseline is the approved 0.5.2 delivery
- **WHEN** the direct comparison and implementation base are inspected
- **THEN** they start from commit `d45aba1cd7582bef9210b921bbb7dc198b48e1ee` and repository SHA `b6431903945479d4b54915362a48b17543ff093c` without replaying `0.5.2` requirements

### Requirement: Complete 0.5.2 to 0.5.3 command inventory is retained
The approved contract SHALL reconcile the full baseline and target public CLI
trees. All 201 command nodes SHALL be retained with no added, removed, renamed,
moved, or help-changed node. Positional arity, local and inherited flags, aliases,
defaults, accepted values, required and presence semantics, conflicts, and
path/query/JSON/header/multipart/stdin/file/process destinations SHALL remain
reviewed for every node. Stable source-only classifications SHALL remain explicit.

#### Scenario: Zero command delta reconciles completely
- **WHEN** pinned baseline and target command evidence is compared
- **THEN** both trees contain 201 nodes, every node is retained, and no earlier `0.5.2` help delta is attributed to `0.5.3`

#### Scenario: Source-only names do not become SDK operations
- **WHEN** root normalization, hidden, test-only, and parser-only source names are reconciled
- **THEN** their prior classifications remain explicit and none is promoted by the zero-delta target

### Requirement: Complete 0.5.3 response review preserves existing shapes
The approved contract SHALL review all 167 supported response entrypoints against
the pinned `0.5.2` and `0.5.3` sources and record `response_review_complete=true`.
Every entrypoint SHALL retain its existing envelope, fields, types, nullability,
omission, pagination, timestamp and numeric encoding, enum openness, error
decoding, adapter, and test mapping. The resumed Claude usage correction SHALL be
recorded as a semantic provenance change behind existing usage values, not as a
new SDK response field or operation.

#### Scenario: Every approved response entry is accounted for
- **WHEN** response review is validated
- **THEN** all 167 approved entrypoints have baseline and target source evidence, a retained wire decision, and existing model and test references

#### Scenario: Usage semantic correction does not alter the wire contract
- **WHEN** the target backend subtracts a valid prior-session baseline or selects a documented fallback
- **THEN** existing task, issue, and runtime usage fields carry the resulting values with unchanged types and omission rules

### Requirement: Unrelated 0.5.3 changes remain outside the SDK
PR automation, closing-keyword policy, UI cache-hit calculations, daemon identity
and Windows behavior, messaging/media, mobile/localization, live steering,
attachment-viewer, pricing, documentation-site, and other changes without an
approved CLI or response delta SHALL NOT add public Python symbols, operations,
models, request inputs, fields, or dependencies.

#### Scenario: Negative inventory remains stable
- **WHEN** contract, generated operation, public-symbol, and dependency inventories are compared with the `0.5.2` baseline
- **THEN** no excluded `0.5.3` feature appears and the canonical SDK surface remains unchanged
