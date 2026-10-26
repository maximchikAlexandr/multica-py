## ADDED Requirements

### Requirement: Multica 0.7.0 command parity has explicit decisions

Every target CLI node and every positional, local, and persistent flag SHALL
have an approved `retain`, `adapt`, `defer`, or `not_sdk_surface` decision with
pinned source provenance and applicable SDK operation references.

#### Scenario: Target help inventory is checked offline

- **WHEN** the committed target inventory is compared with the approved contract
- **THEN** all 209 nodes reconcile with no unresolved flag or positional argument

#### Scenario: Upstream-only behavior is discovered

- **WHEN** a node or endpoint has no approved SDK operation
- **THEN** it is recorded as `defer` or `not_sdk_surface` with rationale and generates no public symbol

### Requirement: Accepted PR 101 operations remain compatible

All PR #101 public signatures, list-property rules, daemon commit decoding,
wakeup diagnostics, upload/network/server classification, search behavior, and
project partial-update semantics SHALL remain unchanged unless a reviewed
`0.7.0` adapt decision names the exact difference.

#### Scenario: An accepted operation drifts

- **WHEN** generated or handwritten discovery differs from its retained PR #101 record
- **THEN** parity and regression tests fail before packaging

#### Scenario: A remaining adaptation is introduced

- **WHEN** a retained operation needs a `0.7.0` behavior change
- **THEN** its contract row identifies the pinned difference, owning task, positive and negative tests, and documentation action
