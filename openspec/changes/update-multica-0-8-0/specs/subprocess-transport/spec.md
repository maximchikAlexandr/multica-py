## ADDED Requirements

### Requirement: Repeated attachment paths remain literal argv values
Issue create and update SHALL accept ordered attachment paths and emit one
`--attachment <path>` pair per supplied value. Paths SHALL be normalized only
by the existing filesystem-input policy and SHALL never be comma-split,
shell-parsed, glob-expanded, or combined into one CSV-like argument.

#### Scenario: Commas remain part of one path
- **WHEN** an attachment path contains a comma
- **THEN** command preview and execution preserve the full path as one argv value

#### Scenario: Multiple paths preserve order
- **WHEN** a caller supplies multiple valid attachment paths
- **THEN** exact argv contains repeated attachment flags in caller order

#### Scenario: Invalid path input fails before execution
- **WHEN** a path violates the existing normalization or presence rules
- **THEN** validation fails before subprocess access and no partial command is run

### Requirement: CLI warnings and structured errors retain channel boundaries
The transport SHALL preserve successful JSON decoding when the target CLI emits
a reviewed warning on stderr and SHALL continue to map nonzero exits through
the sanitized exception boundary. Warning text SHALL not be parsed as JSON,
merged into stdout, or used to fabricate result fields.

#### Scenario: Stale-checkout warning preserves success result
- **WHEN** repo checkout returns a valid path on stdout and a stale-cache warning on stderr
- **THEN** the typed checkout result decodes from stdout and the warning remains observable through the existing process-result channel

#### Scenario: Workflow conflict remains a failure result
- **WHEN** a workflow mutation exits nonzero with a reviewed structured conflict
- **THEN** the transport maps only approved status/code/message fields and does not retry or leak raw private diagnostics

### Requirement: Force-stop safety stays outside the SDK process layer
The SDK transport SHALL invoke `daemon stop --force` as an ordinary CLI command
and SHALL not enumerate processes, compare daemon state, send signals, or remove
PID/profile files itself.

#### Scenario: CLI refusal is not bypassed
- **WHEN** the CLI reports a PID/profile mismatch, unconfirmed child, timeout, or cleanup failure
- **THEN** the SDK surfaces the sanitized failure and performs no local termination or cleanup action
