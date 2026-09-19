## ADDED Requirements

### Requirement: Comment-update conflict fidelity
The subprocess boundary SHALL preserve target comment-update optimistic conflicts through the centralized error classifier without automatic retry, secondary reads, or content-channel fallback.

#### Scenario: Stale revision is classified once
- **WHEN** comment update exits with the target stale-revision response
- **THEN** one CLI invocation SHALL produce the established conflict exception with safe code/message and no follow-up command

### Requirement: Runtime-delete guidance fidelity
The subprocess boundary SHALL parse reviewed target JSON conflict guidance when present and SHALL fall back to safe plain-text conflict messages for legacy or proxy bodies. Optional structured fields SHALL not be required for classification.

#### Scenario: JSON guidance is preserved
- **WHEN** runtime delete returns a valid target JSON conflict body
- **THEN** the centralized exception SHALL preserve reviewed structured fields without leaking unreviewed payload data

#### Scenario: Non-JSON guidance remains readable
- **WHEN** runtime delete returns plain text or malformed JSON with a usable message
- **THEN** the centralized exception SHALL retain the safe message and SHALL not retry with cascade
