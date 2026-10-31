## ADDED Requirements

### Requirement: Select property option capacity follows Multica 0.7.2
Property create and update SHALL accept at most 200 ordered, nonblank options only for `select` and `multi_select`, preserve existing omission and property-type restrictions, and reject 201 options before transport with the established typed validation category.

#### Scenario: Former and new boundaries are accepted
- **WHEN** select or multi-select create/update receives 50, 51, or 200 valid options
- **THEN** each operation SHALL emit every repeatable option exactly once in caller order and decode the existing property definition

#### Scenario: Above-target capacity fails before transport
- **WHEN** select or multi-select create/update receives 201 options
- **THEN** construction SHALL raise the documented validation error, perform zero executor calls, and SHALL not truncate or split the options

#### Scenario: Non-select restrictions remain intact
- **WHEN** actor, multi-actor, multi-text, multi-url, or another unsupported property type receives options
- **THEN** the existing type-specific rejection SHALL occur before transport regardless of the 200-option capacity
