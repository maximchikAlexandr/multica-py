## ADDED Requirements

### Requirement: Bound trigger mutations preserve relation cache semantics

Bound `Autopilot.trigger_add`, `trigger_update`, and their command forms SHALL delegate the complete typed parameter set to the matching governed resource command. A successful add or update SHALL invalidate only that autopilot's `triggers` relation when the command result is finalized. Command construction, preview, and failed execution SHALL leave loaded and unloaded relation state unchanged. The next relation load after successful invalidation SHALL use governed autopilot get and expose the server's updated trigger values.

#### Scenario: Bound schedule add delegates every field
- **WHEN** a bound autopilot builds a schedule add command with cron expression, timezone, and label
- **THEN** its exact command matches the direct resource command for that autopilot ID and construction does not invalidate the trigger relation

#### Scenario: Successful bound add invalidates once
- **WHEN** a bound schedule add command succeeds against a loaded trigger relation
- **THEN** the relation becomes unloaded only after result decoding and its next load observes the created schedule

#### Scenario: Successful bound update invalidates once
- **WHEN** a bound update changes cron from `*/30 * * * *` to `0 */3 * * *` with timezone `Europe/Minsk`
- **THEN** the relation becomes unloaded only after success and its next load exposes the changed cron and timezone

#### Scenario: Failed mutation preserves cache
- **WHEN** a bound trigger add or update command fails validation, execution, or decoding
- **THEN** the prior loaded/unloaded trigger-relation state and cached values are unchanged
