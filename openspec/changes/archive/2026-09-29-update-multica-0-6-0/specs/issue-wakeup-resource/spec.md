## ADDED Requirements

### Requirement: Existing wakeup resource evolves without duplicate surface
`IssueResource.wakeups` SHALL retain its approved create, update, list, get,
disable and events eager/command pairs. The same `IssueWakeupResource` SHALL add
trigger, delete, checkin and runs eager/command pairs; no parallel resource,
duplicate attachment seam or renamed baseline operation SHALL be introduced.
Create/update/list/get/disable SHALL use the evolved `IssueWakeup` model, events
SHALL use the evolved event catalog, and new lifecycle leaves SHALL use their
approved typed results.

#### Scenario: Baseline methods are adapted rather than rebuilt
- **WHEN** the public resource and approved inventory are compared with baseline `c1842ae2…`
- **THEN** the six baseline pairs preserve their names and ownership while exactly four target-only pairs are added

#### Scenario: Complete wakeup inventory is exact
- **WHEN** public discovery and canonical operation rows are compared
- **THEN** all ten approved wakeup pairs are present exactly once and no unapproved wakeup leaf exists

### Requirement: Wakeup create and update implement target v2 inputs
Create/update SHALL extend the existing shared argv builder with
`expires_in_seconds`, `expires_at`, `on_timeout`, `max_fires` and at most one of
status, assignee, label, property, children-done, pull-request or referenced-issue
conditions. Relative expiry SHALL be an exact integer in `60..31536000`; absolute
expiry SHALL be a future RFC3339 instant no more than one year ahead; the two forms
SHALL conflict. Timeout action SHALL be `end|wake`, require a deadline, and `wake`
SHALL require event kind. At-kind SHALL conflict with all deadline fields.
Max fires SHALL be an integer in `1..1000`, require continuous mode, and omission
SHALL preserve the target continuous-event default cap of `20`. Update SHALL remain
complete replacement and SHALL re-enable the returned rule.

#### Scenario: Valid v2 input maps exactly once
- **WHEN** one valid deadline, timeout, max-fire or condition configuration is supplied
- **THEN** eager and command paths emit the exact approved flags/body mapping with no duplicate or fabricated field

#### Scenario: Local v2 conflicts fail before I/O
- **WHEN** types, ranges, deadline forms, timeout dependencies, mode, condition exclusivity or required-together rules fail
- **THEN** the shared builder rejects the request before process execution

#### Scenario: Omitted max fires preserves server default
- **WHEN** continuous event mode omits max fires
- **THEN** the SDK emits no max-fire flag and evidence proves the target default cap is `20`

### Requirement: Wakeup conditions are mutually exclusive and source-exact
Status SHALL map to issue-field status. Assignee SHALL require
`member|agent|squad:ID`. Property SHALL preserve canonical non-null JSON or a
string value no larger than 1 KiB. Stage SHALL be `1..1000` and require
children-done. Pull request SHALL map `checks|merged` to the approved target
values. Referenced issue state SHALL be `done|ended|in_review`, require a different
same-workspace issue, and default exactly as approved. Any condition SHALL require
event kind and conflict with explicit events, filters and schedules. Workspace
existence, ownership, active-property and referenced-issue checks SHALL remain
server-authoritative typed validation errors.

#### Scenario: Each condition has one canonical shape
- **WHEN** one syntactically valid condition family is supplied
- **THEN** create/update emits exactly one approved condition object and preserves canonical value semantics

#### Scenario: Invalid local condition combination fails before I/O
- **WHEN** multiple families, incompatible event/filter/schedule input, orphan stage/state or invalid local value is supplied
- **THEN** construction fails before process execution

#### Scenario: Authoritative ownership is not fabricated locally
- **WHEN** a syntactically valid member, agent, squad, label, property or issue is absent or outside the workspace
- **THEN** the SDK invokes target once and surfaces its typed validation error without retry

### Requirement: Target-only lifecycle leaves preserve exact semantics
Trigger SHALL POST an empty object and decode `{id, triggered:true}`. Delete SHALL
decode `{id, deleted:true}` and document revocation of not-yet-started runs.
Checkin SHALL require only a nonblank string note locally, return
`ActionResult[None]`, and leave the 500-code-point limit plus applicability only to
every/cron runs server-authoritative. Runs SHALL decode the ordered bare array as
`Page[IssueWakeupRun]` with required ID/status/created-at and presence-aware
optional checkin note. Trigger, delete, checkin and update SHALL receive no SDK
retry after an ambiguous failure.

#### Scenario: Trigger and delete acknowledge the selected rule
- **WHEN** trigger or delete succeeds
- **THEN** the typed result contains the requested wakeup ID and a true operation-specific acknowledgement

#### Scenario: Checkin local and server boundaries remain distinct
- **WHEN** a note is missing, blank or non-string, or a valid string violates server length/run-kind policy
- **THEN** local shape failures occur before I/O while server-owned failures are invoked once and remain typed

#### Scenario: Runs preserve note presence and order
- **WHEN** run rows contain omitted, null or string checkin notes
- **THEN** the approved presence policy is applied without reordering rows or inventing pagination

### Requirement: Existing wakeup responses adapt to v2 presence semantics
The six baseline response entrypoints SHALL decode approved deadline/timeout,
condition, max-fire/count, pause and provenance fields with exact required,
optional, nullable and omission behavior. Kind, mode, status, timeout action,
condition/action and provenance vocabulary SHALL remain open where the approved
registry marks it open. Events SHALL preserve existing event catalog behavior and
add the approved condition and loop-protection mapping. Malformed present values
SHALL fail typed decoding; omission SHALL not synthesize target state.

#### Scenario: Existing entrypoints retain independent response contracts
- **WHEN** create, update, list, get, disable and events decode target payloads
- **THEN** every approved v2 field is projected at its specified presence boundary and baseline fields remain compatible

#### Scenario: Unknown open values survive
- **WHEN** an approved open wakeup status, action, condition or provenance value is unknown to this SDK release
- **THEN** the typed model preserves the string while malformed structural values still fail
