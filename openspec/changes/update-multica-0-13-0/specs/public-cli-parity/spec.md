## MODIFIED Requirements

### Requirement: Reviewed target commands govern public parity

Every approved retained, adapted, supported, removed, or deferred command SHALL have an explicit contract disposition; public SDK methods SHALL exist only for approved operations.

#### Scenario: Changed command mappings are exact

- **WHEN** canonical operation cases preview and execute each approved changed command
- **THEN** positional args, flags, order, defaults, aliases, omission versus explicit values, constraints, execution mode, stdin, timeout, and output decoder equal the approved target mapping

#### Scenario: Deferred commands stay non-public

- **WHEN** root exports, client resources, generated inventories, docs, and operation tables are inspected
- **THEN** `squad briefs` and all other deferred target command families have no public SDK method while their reviewed dispositions remain recorded

#### Scenario: Retained commands do not drift

- **WHEN** help-identical approved nodes and unchanged response rows are checked
- **THEN** existing canonical vectors, signatures, and regression fixtures remain stable except for explicitly reviewed compatibility metadata

### Requirement: Update-style presence is explicit

Approved update/patch operations SHALL distinguish omitted values from explicit empty, false, zero, and null whenever upstream semantics differ.

#### Scenario: Omission and explicit values produce distinct plans

- **WHEN** a changed operation is called with omitted and each meaningful explicit value
- **THEN** command preview emits the exact distinct argv/body behavior and invalid combinations fail locally or with the documented typed CLI error

### Requirement: Public operation inventory is closed

The approved contract, generated projection, public methods, canonical operation cases, response fixtures, and documentation SHALL agree exactly after the upgrade.

#### Scenario: Inventory mismatch fails offline

- **WHEN** an approved operation lacks one canonical vector, a public method lacks approval, a removed method remains, or duplicate vectors exist
- **THEN** the offline contract gate fails with the mismatched operation identity
