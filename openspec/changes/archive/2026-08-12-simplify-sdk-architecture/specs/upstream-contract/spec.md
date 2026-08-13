## ADDED Requirements

### Requirement: Approved-operation realization starts with one bounded pilot
The approved SDK contract SHALL remain the only production generator input. The generator SHALL emit ordinary private Python argv builders and validators for exactly the homogeneous `squads.members.list`, `squads.members.add`, and `squads.members.remove` pilot family only when the pilot's stop/go decision succeeds. On a failed stop/go decision, the rollback SHALL be the normative terminal state: generation SHALL remain descriptor-only for this family, with no private argv builders, and `SquadMemberResource` eager and `*_command()` methods SHALL retain manual validation and argv construction. No other marker-only binding may be considered after a failed pilot. When the pilot succeeds, explicit typed `SquadMemberResource` eager and `*_command()` methods SHALL call the private generated functions and SHALL retain their public signatures, return types, eager delegation, validation timing, exact argv, decoding, options, and error behavior.

#### Scenario: Pilot builder emits exact list argv
- **WHEN** `SquadMemberResource.list_command(squad_id)` receives a valid identifier
- **THEN** the generated private builder validates before I/O and returns exactly `squad member list <squad_id>` for the existing decoded-page command path

#### Scenario: Pilot builder emits exact mutation argv
- **WHEN** add or remove receives valid squad and member identifiers
- **THEN** the generated private builder returns exactly `squad member add|remove <squad_id> <member_id>` for the existing action-command path

#### Scenario: Explicit public methods remain the API
- **WHEN** the generated module and resource are inspected
- **THEN** no runtime registry dispatch, reflection over `python_path`, dynamic public method, generated composite workflow, or second command namespace exists

### Requirement: Generated-operation expansion is evidence-gated
After the pilot, expansion to another marker-only family SHALL occur only when a committed stop/go report records all required evidence for the pilot: deterministic generation from `sdk-contract.json`, unchanged signatures/return types/validation timing/exact argv/results, table-driven canonical vectors, an independent expected-result guard, and a measured net deletion across production plus tests. A failed criterion SHALL stop expansion; it SHALL NOT be offset by projected future savings. Imperative, composite, temporary-file, spawn, pagination, and runtime-specific operations SHALL remain manual in this change.

#### Scenario: Pilot passes every go criterion
- **WHEN** the implementer compares the pilot baseline and final implementation
- **THEN** expansion may be proposed only if every criterion is recorded as passing with commands and line/concept counts

#### Scenario: Pilot fails any criterion
- **WHEN** generated realization adds runtime interpretation, changes a public/command contract, weakens independent verification, or does not produce net deletion
- **THEN** expansion stops and the normative terminal state is descriptor-only generation for the three `squads.members.*` descriptors plus manual validation and argv construction in `SquadMemberResource`; no private builders or resource delegation are retained

#### Scenario: Deferred families remain markers
- **WHEN** a marker-only binding lies outside an explicitly recorded passing expansion decision
- **THEN** its current handwritten resource implementation and generated descriptor remain unchanged
