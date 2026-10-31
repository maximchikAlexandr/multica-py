## ADDED Requirements

### Requirement: Run-targeted rerun is typed and legacy rerun is explicitly deprecated
`IssueResource` SHALL expose eager and command `rerun_task(run_id, *, issue_id=None, fresh=False) -> TaskRun` operations. They SHALL accept a nonblank full or short run ID, optional nonblank issue reference, and exact boolean `fresh`; emit `issue rerun-task <run-id>`, optional `--issue`, presence-only `--fresh`, and JSON output; and decode the existing bound `TaskRun`. Existing `rerun(issue_id) -> ActionResult[None]` SHALL remain only as a `DeprecationWarning`-emitting shim over the target hidden legacy command for this compatibility interval and SHALL not count as a target public command node.

#### Scenario: Full run ID returns the rerun task
- **WHEN** a caller reruns a full run ID with default inputs
- **THEN** exact argv SHALL contain no `--issue` or `--fresh`, the response SHALL decode as `TaskRun`, and it SHALL not be coerced to the legacy action result

#### Scenario: Short ID can be narrowed and fresh
- **WHEN** a caller passes a short run ID, `issue_id`, and `fresh=True`
- **THEN** exact argv SHALL contain one `--issue <ref>` and one `--fresh`, and ambiguous, missing, or unauthorized resolution SHALL surface the existing typed CLI error without local ID inference

#### Scenario: Legacy rerun is a temporary distinct operation
- **WHEN** a caller invokes `rerun(issue_id)` on a compatible target
- **THEN** one deprecation warning SHALL direct migration to `rerun_task`, legacy argv and `ActionResult[None]` SHALL remain unchanged, and no issue ID SHALL be silently treated as a run ID

### Requirement: Comment creation exposes safe typed steering
Comment add/reply eager and command forms SHALL accept ordered `steer_run_ids: tuple[str, ...] = ()` and exact boolean `steer_active: bool = False`. They SHALL emit repeatable `--steer` values and presence-only `--steer-active`, retain exactly-one inline/file/stdin content validation, and reject any attachment combined with steering before transport.

#### Scenario: Ordered explicit steering preserves the content channel
- **WHEN** a text comment supplies two run IDs
- **THEN** argv SHALL preserve both IDs in caller order, retain the selected text channel, and decode the existing comment response

#### Scenario: Active steering is presence-sensitive
- **WHEN** `steer_active` is false versus true
- **THEN** false SHALL emit no flag, true SHALL emit exactly one `--steer-active`, and non-boolean input SHALL fail before transport

#### Scenario: Steering and attachments conflict
- **WHEN** either steering input is combined with an attachment
- **THEN** construction SHALL fail before file access or transport and SHALL not fall back to ordinary comment creation

### Requirement: Comment steering outcomes remain typed and open
`Comment` SHALL expose ordered `trigger_outcomes` using an immutable `CommentTriggerOutcome` with optional agent/task identifiers, required nonblank open `status`, and optional open `reason_code`; existing `supplements` SHALL remain independent and unchanged. Permission denial, self-steer, caps, race fallback, coalesced/deferred/blocked outcomes, and multiple receipts SHALL decode without closed enums or locally predicted authority.

#### Scenario: Permission and cap outcomes remain lossless
- **WHEN** target returns authorized, permission-denied, self, per-run-cap, or global-cap outcomes
- **THEN** ordered IDs and open status/reason values SHALL be preserved exactly and unknown valid future strings SHALL decode

#### Scenario: Race fallback and multiple receipts coexist
- **WHEN** steering races run completion and the comment also receives multiple supplement receipts
- **THEN** each trigger outcome and supplement SHALL remain independently ordered and no field SHALL be synthesized from another

#### Scenario: Malformed outcomes fail at the protocol boundary
- **WHEN** a present outcome lacks required status, has blank status, or uses invalid identifier/value types
- **THEN** decoding SHALL raise the established output-shape error without dropping the malformed row

### Requirement: Task and chat privacy preserve open existing models
`agents.tasks` and `issues.runs` SHALL preserve optional open `can_supplement` while reflecting member, authorized agent, self, and permission-denied authority without borrowing another actor's rights. Foreign chat-task content SHALL be absent/redacted. `issues.run_messages` SHALL preserve its `RunMessage` payload and classify the target foreign-chat 404 as the existing not-found error.

#### Scenario: Supplement permission follows the actual caller
- **WHEN** otherwise identical task pages are requested by a member, an authorized agent, the task agent, and a denied agent
- **THEN** each optional boolean SHALL match target authority, explicit false SHALL remain false, omission SHALL remain compatible, and private chat content SHALL not leak

#### Scenario: Foreign chat transcript is not discoverable
- **WHEN** a caller requests run messages for another actor's private chat session
- **THEN** the SDK SHALL raise the existing not-found error with redacted safe detail and SHALL expose no transcript or existence-confirming metadata
