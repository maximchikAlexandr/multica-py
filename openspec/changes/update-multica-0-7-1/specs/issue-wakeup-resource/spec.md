## ADDED Requirements

### Requirement: Issue-state wakeups accept blocked through the existing open contract
The existing issue wakeup resource SHALL accept `blocked` as an issue-state condition for create and update and SHALL preserve that value through get, list, and events without introducing a second resource or closed SDK enum.

#### Scenario: Create a blocked-state condition
- **WHEN** a caller creates a wakeup with an issue dependency and `until_issue_state="blocked"`
- **THEN** the SDK SHALL emit the reviewed target arguments and decode the returned condition as `blocked`

#### Scenario: Update a blocked-state condition
- **WHEN** a caller replaces a wakeup configuration with an issue dependency and `until_issue_state="blocked"`
- **THEN** the SDK SHALL emit the same reviewed mapping and preserve `blocked` in the update response

#### Scenario: Read blocked through every response path
- **WHEN** get, list, or events returns an issue condition whose state is `blocked`
- **THEN** each existing decoder SHALL preserve the exact open string without coercion or rejection

#### Scenario: Missing issue dependency is rejected
- **WHEN** `until_issue_state="blocked"` is supplied without the required issue condition target
- **THEN** validation SHALL fail before transport with the existing dependency error contract

#### Scenario: Mutually exclusive conditions remain rejected
- **WHEN** a blocked issue condition is combined with another top-level wake condition that the source marks mutually exclusive
- **THEN** validation SHALL fail before transport and SHALL identify the conflicting inputs

#### Scenario: Unknown issue state remains invalid at the command boundary
- **WHEN** a caller supplies an issue-state value not accepted by the pinned target CLI
- **THEN** the SDK SHALL surface the standard validation failure without fabricating a known state
