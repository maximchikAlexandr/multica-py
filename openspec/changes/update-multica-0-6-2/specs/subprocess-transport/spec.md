## ADDED Requirements

### Requirement: Interrupted upload response reads are network failures

When attachment upload starts successfully but reading the CLI response body is interrupted by a network-class failure, the existing transport boundary SHALL raise `NetworkError`, preserve its redaction contract, and SHALL NOT return an attachment success model.

#### Scenario: Interrupted response body fails upload
- **WHEN** the upload response body cannot be read to completion because of the reviewed interruption
- **THEN** attachment upload raises `NetworkError` with no partial `AttachmentResult`

### Requirement: Target server errors preserve safe classification

HTTP 500 diagnostics redacted by Multica `0.6.2` SHALL retain the existing stable SDK exception classification. Tests and documentation SHALL assert safe stable text or type rather than backend raw messages.

#### Scenario: Redacted 500 does not leak backend detail
- **WHEN** any supported operation returns the target redacted HTTP 500 payload
- **THEN** the SDK raises the reviewed typed command error and no backend-internal message appears in the public exception
