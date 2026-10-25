## ADDED Requirements

### Requirement: Multica 0.7.0 command parity has explicit decisions

Every target CLI node and every positional, local, and persistent flag SHALL
have an approved `support`, `retain`, `adapt`, `remove`, `defer`, or
`not_sdk_surface` decision with pinned source provenance and applicable SDK
operation references.

#### Scenario: Target help inventory is checked offline

- **WHEN** the committed target inventory is compared with the approved contract
- **THEN** exactly 209 nodes reconcile with four additions, zero removals, six changes, and no unresolved flag or positional argument

#### Scenario: Upstream-only behavior is discovered

- **WHEN** a node or endpoint has no approved SDK operation
- **THEN** it is recorded as `defer` or `not_sdk_surface` with rationale and generates no public symbol

### Requirement: Retained operations remain compatible

All retained command mappings, signatures, validators, response adapters, and
public return types SHALL remain unchanged unless a reviewed `adapt` decision
in this change names the exact difference.

#### Scenario: A retained operation drifts

- **WHEN** generated or handwritten discovery differs from its approved retained record
- **THEN** closed parity tests fail before packaging
