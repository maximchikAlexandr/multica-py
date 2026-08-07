## MODIFIED Requirements

### Requirement: Governed autopilot resource

The SDK MUST expose governed `autopilots.list/get/create/update/delete/trigger/history`
operations in the approved contract. Legacy `autopilots.run` MUST remain
renamed to `autopilots.trigger` and emit `autopilot trigger <autopilot-id>`.
`autopilots.get_run` MUST remain absent because pinned CLI `0.4.20` has no
single-run fetch; callers MUST use `history()` and select from its page.
Trigger reads MUST come from the governed autopilot get envelope; mutations
MUST use `trigger_add`, `trigger_update`, and `trigger_delete` methods backed
by upstream `trigger-add`, `trigger-update`, and `trigger-delete` commands.
All bindings and source references SHALL be revalidated at pinned commit
`93342d04a7a9f788fec921e5aa736f86c7f22d8f`.

#### Scenario: Autopilot operations are governed
- **WHEN** `contracts/sdk-contract.json` is inspected
- **THEN** it governs list, get, create, update, delete, trigger, history, trigger-add, trigger-update, and trigger-delete with `v0.4.20` bindings, signatures, responses, source refs, and migration compatibility

#### Scenario: Unsupported get-run is absent
- **WHEN** canonical public methods are discovered
- **THEN** `autopilots.get_run` is absent, while `autopilots.trigger` and `autopilots.history` are present

#### Scenario: Legacy autopilot run is absent
- **WHEN** canonical public methods are discovered
- **THEN** legacy `autopilots.run` is absent, while `autopilots.trigger` is present

#### Scenario: Manual trigger emits the supported command
- **WHEN** `client.autopilots.trigger("a1")` or its command form is used
- **THEN** exact argv contains `autopilot trigger a1 --output json` and never `autopilot run`

#### Scenario: Autopilot operations decode via wire converters
- **WHEN** `client.autopilots.get("a1")` receives the upstream get envelope
- **THEN** it adapts the `autopilot` member to a bound `Autopilot` and seeds explicitly present complete triggers/subscribers
