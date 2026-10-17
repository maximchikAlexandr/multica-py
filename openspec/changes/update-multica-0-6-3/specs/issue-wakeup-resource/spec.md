## ADDED Requirements

### Requirement: Wakeup diagnostics preserve target context safely
Wakeup create, get, list, update, trigger, runs, and events SHALL preserve reviewed 0.6.3 diagnostic fields and stable failure messages through their existing models and exception paths. Unknown additive fields SHALL follow the existing compatible decoder policy, while sensitive backend detail MUST remain redacted.

#### Scenario: Diagnostic failure is actionable and redacted
- **WHEN** a wakeup command fails with a reviewed 0.6.3 diagnostic
- **THEN** the public exception preserves the safe reason and command context without secrets, backend stack data, or a second request

#### Scenario: Successful lifecycle remains unchanged
- **WHEN** existing wakeup lifecycle fixtures run against retained 0.6.3 shapes
- **THEN** cursor, condition, event, run, and action-result behavior matches the approved 0.6.1 public API
