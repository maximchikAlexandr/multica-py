## ADDED Requirements

### Requirement: Incremental run-message input is contract-approved
The approved `issues.run_messages` operation SHALL add `since: int = 0` to its eager and command signatures, map a present value to `--since <sequence>`, and require an exact nonnegative integer that is not a boolean. The canonical vector SHALL include `--since 0`; positive and negative vectors SHALL prove positive cursor mapping and pre-I/O rejection of negative, boolean, and noninteger values. Source references SHALL pin the `v0.4.20` Cobra flag, `runIssueRunMessages` query mapping, and server strict-greater-than sequence query.

#### Scenario: Zero cursor is explicit
- **WHEN** `run_messages(task_id, issue_id=issue_id, since=0)` executes
- **THEN** argv is exactly `issue run-messages <task-id> --issue <issue-id> --since 0 --output json` and the full ordered history is decoded

#### Scenario: Positive cursor requests only newer messages
- **WHEN** `since=42` is supplied
- **THEN** argv contains `--since 42` and pinned upstream returns only rows whose sequence is greater than 42 in ascending sequence order

#### Scenario: Invalid cursor fails before transport
- **WHEN** `since` is negative, boolean, noninteger, or outside the supported CLI integer range
- **THEN** construction raises `TypeError` or `ValueError` before subprocess execution

### Requirement: Run-message response schema is source-governed
The approved contract SHALL replace the unsupported run-message response schema with the pinned `v0.4.20` payload: required `task_id`, `seq`, and `type`; optional `issue_id`, `tool`, `content`, `input`, `output`, and `created_at`. It SHALL record `type` as an open string and structured `input` as recursive JSON. Source references SHALL trace the database row through `taskMessageToPayload` and the user-authenticated task-message handler. The approved response SHALL NOT claim fields absent from upstream.

#### Scenario: Contract matches source payload
- **WHEN** contract integrity and source validation inspect `issues.run_messages`
- **THEN** every approved response field maps to the pinned handler payload and `id`, `run_id`, and `role` are absent

#### Scenario: Semantic events do not alter the transport contract
- **WHEN** event streaming converts a decoded `RunMessage`
- **THEN** the governed operation still returns raw messages and semantic classification remains handwritten SDK policy above the approved transport adapter

