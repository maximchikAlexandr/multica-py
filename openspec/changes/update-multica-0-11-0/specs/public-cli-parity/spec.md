## ADDED Requirements

### Requirement: Target operation coverage is disposition-complete
Every command in the exact Multica `0.11.0` inventory SHALL map to one
approved SDK operation or one explicit non-public disposition. Every approved
operation SHALL identify exact source evidence, public symbol, input
destinations, constraints, response adapter, compatibility policy, and canonical
test reference.

#### Scenario: Supported operation is audited
- **WHEN** the target inventory and approved operation registry are compared
- **THEN** the operation resolves to one public symbol and one canonical transport case

#### Scenario: Target command has no disposition
- **WHEN** any target or source-only command cannot be joined to an approved operation or explicit non-public disposition
- **THEN** the parity gate fails

### Requirement: Existing operation tables remain the coverage seam
Changed and retained command behavior SHALL extend the existing frozen
`ArgvCase`, `CommandCase`, decode, operation-completeness, and payload
fingerprint tables. Repeated coverage SHALL be added as rows before a new test
function or file, and canonical public-method set equality SHALL remain closed.

#### Scenario: Changed operation adds coverage
- **WHEN** an approved operation changes argv, validation, decoding, or errors
- **THEN** its existing canonical row and focused positive or negative rows are updated without a parallel case hierarchy

#### Scenario: Public method is added without a canonical row
- **WHEN** public-method discovery finds a method absent from canonical operation cases
- **THEN** offline verification fails

### Requirement: Compatibility describes one direct migration
Compatibility and migration documentation SHALL describe the supported direct
transition from Multica `0.7.1` to `0.11.0`, including the breaking rerun
replacement, all mandatory adaptations, retained behavior, explicit deferred
families, and the tested target ceiling. It SHALL NOT imply that absence of
official breaking notes proves compatibility.

#### Scenario: Consumer follows the migration guide
- **WHEN** a consumer replaces the legacy rerun call and updates affected inputs and response handling
- **THEN** every example resolves against the approved public surface and target compatibility policy

#### Scenario: Deferred command is documented
- **WHEN** a deferred family appears in compatibility documentation
- **THEN** it is identified as unsupported rather than presented as an SDK capability
