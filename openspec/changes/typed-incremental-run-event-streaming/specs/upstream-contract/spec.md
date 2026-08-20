## ADDED Requirements

### Requirement: Incremental run-message input is contract-approved
The approved `v0.4.28` `issues.run_messages` operation SHALL add `since: int = 0` to its eager and command signatures, map the value to the Cobra `--since <sequence>` integer flag and, for a positive value, its `since` query parameter, and require an exact non-boolean integer in the inclusive DB/server-safe range `0..2_147_483_647`. The canonical vector SHALL include `--since 0`; positive and negative vectors SHALL prove boundary mapping and pre-I/O rejection. Source references SHALL pin the tagged Cobra flag and `runIssueRunMessages` query construction, the user-authenticated handler's `strconv.Atoi` and subsequent `int32(sinceSeq)` query argument, and the server strict-greater-than sequence query. The SDK SHALL enforce the `int32` upper bound even on a 64-bit CLI host so the handler cast cannot wrap to an incorrect SQL cursor. Rendering zero is the deterministic SDK argv form; the tagged CLI omits the query parameter when zero and therefore requests full history.

#### Scenario: Zero cursor is explicit
- **WHEN** `run_messages(task_id, issue_id=issue_id, since=0)` executes
- **THEN** argv is exactly `issue run-messages <task-id> --issue <issue-id> --since 0 --output json` and the full ordered history is decoded

#### Scenario: Positive cursor requests only newer messages
- **WHEN** `since=42` is supplied
- **THEN** argv contains `--since 42` and pinned upstream returns only rows whose sequence is greater than 42 in ascending sequence order

#### Scenario: Maximum server-safe cursor is accepted
- **WHEN** `since=2_147_483_647` is supplied
- **THEN** argv contains `--since 2147483647` and the handler's `int32` query cursor preserves the requested value

#### Scenario: Invalid or overflowing cursor fails before transport
- **WHEN** `since` is negative, boolean, noninteger, or greater than `2_147_483_647` (including `2_147_483_648` on a 64-bit CLI host)
- **THEN** construction raises `TypeError` or `ValueError` before subprocess execution

### Requirement: Run-message response schema is source-governed
The approved contract SHALL replace the unsupported run-message response schema retained after the `v0.4.28` upgrade with the pinned tagged payload: required `task_id`, `seq`, and `type`; optional `issue_id`, `tool`, `content`, `input`, `output`, and `created_at`. It SHALL record `type` as an open string and structured `input` as recursive JSON. Source references SHALL trace the database row through `taskMessageToPayload`, `TaskMessagePayload`, and the user-authenticated task-message handler at commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`. The approved response SHALL NOT claim fields absent from upstream.

#### Scenario: Contract matches source payload
- **WHEN** contract integrity and source validation inspect `issues.run_messages`
- **THEN** every approved response field maps to the pinned handler payload and `id`, `run_id`, and `role` are absent

#### Scenario: Semantic events do not alter the transport contract
- **WHEN** event streaming converts a decoded `RunMessage`
- **THEN** the governed operation still returns raw messages and semantic classification remains handwritten SDK policy above the approved transport adapter
