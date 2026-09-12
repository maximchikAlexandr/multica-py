## MODIFIED Requirements

### Requirement: Autopilot create aligns to upstream flags

`AutopilotResource.create` MUST accept `title`, `description`, `agent`,
`execution_mode`, `project_id`, `issue_title_template`, and `subscribers`,
emitting the corresponding target flags. It MUST NOT accept or emit
`priority`. `agent` and `execution_mode` MUST be required (no default).
`execution_mode` MUST be the `AutopilotExecutionMode` enum.

#### Scenario: Create emits supported flags
- **WHEN** create receives all supported optional fields
- **THEN** exact argv contains description, agent, mode, project, issue-title-template, subscriber, and JSON-output flags and contains no `--priority`

#### Scenario: Create minimal has no legacy priority
- **WHEN** create receives only title, agent, and execution mode
- **THEN** exact argv contains those values plus `--output json` and does not emit `--priority none`

#### Scenario: Legacy create priority is absent
- **WHEN** the create signature, type-check fixtures, docs, and canonical cases are inspected
- **THEN** no `priority` parameter or `--priority` mapping remains

#### Scenario: Create emits required and optional flags
- **WHEN** create receives every supported optional field
- **THEN** exact argv contains description, agent, mode, project, issue-title-template, subscribers, and JSON output, with no `--priority` flag

#### Scenario: Create minimal
- **WHEN** create receives only title, agent, and execution mode
- **THEN** exact argv contains those values and JSON output, with no description, project, issue-title-template, subscriber, or priority flag

### Requirement: Autopilot update uses presence semantics

`AutopilotResource.update` MUST emit only flags for supported fields that are
not `Unset`; it MUST NOT accept or emit `priority`. Omitted, `None`, empty
string, zero, and false SHALL follow each target field's reviewed
`Flags().Changed` and request encoding. `project_id` SHALL distinguish omission
from the target's explicit clear form. `clear_subscribers=True` SHALL emit
`--clear-subscribers` and SHALL conflict with present subscribers.

#### Scenario: Update emits changed flags only
- **WHEN** update receives title and status only
- **THEN** exact argv contains only those changed flags plus JSON output and no priority flag

#### Scenario: Update preserves explicit clear and omission
- **WHEN** project ID is omitted versus supplied as the reviewed empty clear value
- **THEN** omission emits no project flag and clear emits `--project ""`

#### Scenario: Update preserves false and empty presence
- **WHEN** a supported boolean is explicitly false or a supported string is explicitly empty
- **THEN** target `Flags().Changed` semantics are preserved and neither value is collapsed into omission

#### Scenario: Subscriber channels remain exclusive
- **WHEN** clear-subscribers and subscribers are both present
- **THEN** construction raises `ValueError` before transport

#### Scenario: Legacy update priority is absent
- **WHEN** update signatures, generated bindings, docs, and cases are inspected
- **THEN** no priority parameter, mapping, or compatibility alias remains

#### Scenario: Update clears project_id with empty string
- **WHEN** update receives `project_id=""`
- **THEN** exact argv contains `--project ""`

#### Scenario: Update omits project_id when None
- **WHEN** update receives another changed field while `project_id` is omitted
- **THEN** exact argv contains no `--project` flag

#### Scenario: Update rejects clear_subscribers with subscribers
- **WHEN** `clear_subscribers=True` and subscribers are both present
- **THEN** `ValueError` is raised before transport

#### Scenario: Update emits repeatable subscribers
- **WHEN** update receives multiple subscribers
- **THEN** exact argv emits one `--subscriber` flag per value in input order
