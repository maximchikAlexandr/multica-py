## ADDED Requirements

### Requirement: Duplicate transitions extend existing issue mutations
`IssueResource.set_status[_command]`, bound `Issue.set_status[_command]`,
`IssueResource.update[_command]` and bound `Issue.update[_command]` SHALL accept
optional `duplicate_of: str | None = None`. A non-`None` value SHALL be nonblank,
map once to `--duplicate-of <reference>` and require Multica CLI `0.6.1` without
raising the minimum for calls that omit it. The existing `Issue.duplicate_of`
projection SHALL decode the authoritative result; no competing duplicate model,
adapter or standalone operation SHALL be created.

#### Scenario: Omitted duplicate reference preserves baseline argv
- **WHEN** any direct or bound mutation omits `duplicate_of`
- **THEN** `--duplicate-of` is absent and pre-`0.6.1` compatible behavior is unchanged

#### Scenario: Valid duplicate status transition maps exactly
- **WHEN** direct or bound `set_status` receives `cancelled` and a nonblank duplicate reference
- **THEN** exact argv contains one `--duplicate-of <reference>` before `--output json` and the returned existing `Issue.duplicate_of` snapshot is preserved

#### Scenario: Blank duplicate reference fails before transport
- **WHEN** any mutation receives an empty or whitespace-only `duplicate_of`
- **THEN** SDK validation fails before executor or CLI transport activity

### Requirement: Duplicate transition conflicts are presence-aware and atomic
For `set_status`, a present `duplicate_of` SHALL require status `cancelled`. For
`update`, a present `duplicate_of` SHALL allow omitted status or explicit
`cancelled`, SHALL reject every other status, and SHALL conflict with every
emitted description or attachment channel before transport. A present inline
description SHALL conflict even when its value is `None` or empty. Contract
evidence SHALL also retain upstream conflicts with description-file and
description-stdin channels even though those channels are not separate public
update parameters. Attachment validation SHALL complete without upload and no
plan containing a conflicting upload step SHALL be executable.

#### Scenario: Update can perform duplicate-only transition
- **WHEN** `update` receives only a valid `duplicate_of`
- **THEN** exact argv emits `issue update <id> --duplicate-of <reference> --output json` once

#### Scenario: Explicit cancelled status can accompany duplicate reference
- **WHEN** `update` receives `status=cancelled` and valid `duplicate_of`
- **THEN** both flags are emitted exactly once and all other update inputs retain existing presence semantics

#### Scenario: Status conflict fails before transport
- **WHEN** `set_status` or `update` combines `duplicate_of` with any status other than `cancelled`
- **THEN** validation fails before transport

#### Scenario: Content or attachment conflict causes no partial upload
- **WHEN** `update` combines `duplicate_of` with a present description or any emitted attachment
- **THEN** validation fails before any executor, upload or issue mutation call

### Requirement: CLI compatibility verification remains authoritative
The SDK SHALL delegate issue-reference resolution, duplicate request submission
and target response-field verification to Multica CLI `0.6.1`. If the target
server accepts the transition but the response omits `duplicate_of`, the SDK SHALL
surface the CLI compatibility failure through the existing typed command-error
boundary and SHALL NOT retry, synthesize the field or issue a secondary mutation.

#### Scenario: Server without duplicate response field fails closed
- **WHEN** CLI `0.6.1` reports its local compatibility error after a successful server response lacking `duplicate_of`
- **THEN** the SDK raises the existing typed command failure once with redacted detail and performs no retry

### Requirement: Compatible target semantics preserve open and numeric contracts
`TaskRun.failure_reason` SHALL remain an open optional string and preserve the
target provider-quota classification derived from HTTP 403 `usage limit`.
Issue/runtime usage SHALL preserve server-supplied integer `cost_usd_ticks`, token
counts and uncosted categories for newly priced GPT-6.1 Sol, GPT-6 Sol and GPT-6
Luna values without embedding the upstream price table. Repository checkout SHALL
retain its existing successful path result and centralized error boundary while
accepting target junction-safe containment and actionable rejected-workdir detail.

#### Scenario: Provider quota reason remains forward-compatible
- **WHEN** agent tasks or issue runs returns the target normalized provider-quota failure reason or an unknown future reason
- **THEN** the exact open string is preserved without enum rejection

#### Scenario: Usage precision remains server-owned
- **WHEN** issue or runtime usage includes a newly priced model or uncosted category
- **THEN** integer ticks and category values decode exactly and the SDK performs no local price calculation

#### Scenario: Checkout semantics remain portable
- **WHEN** target checkout succeeds through a junction-safe path or rejects containment with actionable detail
- **THEN** success returns the existing path model and failure follows the existing typed/redacted process-error boundary without a second checkout implementation
