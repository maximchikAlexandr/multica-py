## MODIFIED Requirements

### Requirement: Issue blockers preserve identity, kind, count, and privacy

Issue values SHALL expose ordered blocker relationships, open reference kind, and server-provided blocked count without manufacturing identities for invisible blockers.

#### Scenario: Visible blocker collections decode

- **WHEN** issue payloads contain empty or populated `blocked_by` and `blocking` arrays with `manual`, `stage`, or unknown future kind values
- **THEN** immutable bound references preserve order, issue identity, open kind value, and originating client without implicit hydration

#### Scenario: Older omission remains compatible

- **WHEN** an older supported payload omits blocker arrays, count, or kind
- **THEN** collections decode empty, optional metadata uses its documented default, and unrelated issue fields are unchanged

#### Scenario: Hidden blockers do not leak

- **WHEN** the server returns a blocked count greater than the visible `blocked_by` collection
- **THEN** the count is preserved, no hidden identity is synthesized, and representations, errors, logs, and relation traversal expose only visible references

#### Scenario: Malformed blocker payload fails typed decoding

- **WHEN** blocker arrays, identities, counts, or kinds have an invalid shape
- **THEN** decoding raises the existing output-shape error and does not return a partial issue

### Requirement: Issue blocker mutations enforce local and authoritative constraints

The issue resource and bound issue entity SHALL provide matching eager/command operations for approved blocker add/remove behavior using typed issue references and existing execution options.

#### Scenario: Valid mutation has exact transport and invalidation

- **WHEN** a caller adds or removes a distinct visible blocker
- **THEN** the command preview and eager call use the exact approved argv, return the approved issue/action shape, and invalidate only affected blocker relation state

#### Scenario: Local failures avoid transport

- **WHEN** a caller supplies self-reference, a blank/malformed identity, incompatible entity type, or more than the approved maximum of 100 references
- **THEN** validation raises `TypeError` or `ValueError` before any subprocess call

#### Scenario: Authoritative graph failures remain typed

- **WHEN** the CLI rejects a cycle, cross-workspace reference, closed issue, hidden issue, or another authoritative lifecycle constraint
- **THEN** the shared typed CLI error preserves status/code/message after redaction and no successful mutation is cached

### Requirement: Removed issue rerun has one migration target

The SDK SHALL remove public legacy `issue rerun` behavior and SHALL support `issue rerun-task` as its sole approved replacement.

#### Scenario: Replacement executes exact target command

- **WHEN** a caller previews or executes rerun-task with each approved optional-field presence combination
- **THEN** exact target argv, stdin, timeout, output model, and typed errors match the approved contract

#### Scenario: Legacy surface is absent

- **WHEN** public symbols, resources, generated inventories, operation cases, docs, and type fixtures are scanned
- **THEN** no callable legacy rerun alias remains and migration documentation points to rerun-task

### Requirement: Squad handoff mode is forward-compatible

Squad payloads and approved create/update operations SHALL preserve handoff mode as an open value with known `manual` and `stage` spellings.

#### Scenario: Known modes round-trip

- **WHEN** create, update, get, or list returns `manual` or `stage`
- **THEN** the public squad value preserves the mode and exact create/update presence semantics

#### Scenario: Omitted and unknown modes decode

- **WHEN** an older payload omits handoff mode or a future server returns an unknown nonblank mode
- **THEN** omission uses the documented compatibility default/optional state and the unknown string is retained without a closed-enum failure

### Requirement: Task-run document attribution remains typed and access-safe

Existing task/run models SHALL decode approved document attribution and kind fields without adding a new public document resource or bypassing server access controls.

#### Scenario: Accessible attribution decodes

- **WHEN** a task/run payload contains approved document identity, kind, and actor/source attribution
- **THEN** fields preserve exact identity, open kind value, nullability, and omission semantics through existing task/run APIs

#### Scenario: Inaccessible document does not leak

- **WHEN** a caller lacks access to an attributed document
- **THEN** the SDK preserves the server's omission or typed error behavior and does not infer title, owner, content, or URL

### Requirement: Retained responses remain backward and forward decodable

All changed approved response rows SHALL preserve documented field names, types, nullability, omission, pagination, privacy, and standard error semantics across the supported interval.

#### Scenario: Presence matrix is complete

- **WHEN** fixtures exercise omitted, explicit null, empty, populated, false, zero, and unknown open values where allowed
- **THEN** each changed row produces the approved model or typed failure without silently coercing incompatible data
