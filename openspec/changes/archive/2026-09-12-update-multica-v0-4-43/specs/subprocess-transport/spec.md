## ADDED Requirements

### Requirement: Run-message lookup failures follow target status boundaries
For `issues.run_messages`, the SDK SHALL preserve the existing centralized
HTTP diagnostic classification while pinning fixtures to `0.4.43`: task or
workspace not-found/mismatch responses are 404 and map to `NotFoundError`, while
non-not-found task lookup failures are 500 and remain an internal command
failure rather than being misclassified as absence. Actual exit/payload detail
SHALL remain redacted according to the existing transport contract.

#### Scenario: Missing or mismatched task is not found
- **WHEN** the target returns its reviewed 404 diagnostic for a missing task or workspace mismatch
- **THEN** the SDK raises `NotFoundError` with safe actionable detail

#### Scenario: Internal lookup failure is not absence
- **WHEN** the target returns its reviewed 500 diagnostic for a non-not-found task lookup failure
- **THEN** the SDK raises the approved generic/internal command failure and does not convert it to `NotFoundError`

#### Scenario: Malformed success output is not an HTTP failure
- **WHEN** a successful target command returns a malformed run-message payload
- **THEN** decoding raises `OutputShapeError` and does not misclassify the payload as either the reviewed 404 or 500 path
