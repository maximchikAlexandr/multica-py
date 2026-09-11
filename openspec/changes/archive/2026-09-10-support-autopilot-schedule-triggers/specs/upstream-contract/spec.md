## MODIFIED Requirements

### Requirement: Issue activity contract records the reviewed compatibility window

The approved SDK contract SHALL distinguish the pinned `v0.4.28` source target from verified release binaries and SHALL retain the reviewed issue assignee, issue usage, and issue runs mappings from CLI `0.4.28` through `0.4.32`. It SHALL additionally record CLI `0.4.38` binary identity and version-command provenance for the compatibility preflight and schedule-trigger live lifecycle without claiming unreviewed `0.4.38` response fields for other operations. Generated default compatibility bounds SHALL come only from that approved contract, SHALL accept versions `0.4.28` through `0.4.38`, and SHALL use exclusive maximum `0.4.39`.

#### Scenario: Reviewed contract generates default bounds
- **WHEN** the approved contract is rendered
- **THEN** the generated compatibility projection accepts CLI versions `0.4.28` through `0.4.38` and rejects or warns at `0.4.39` according to policy, without using evidence files directly as generator input

#### Scenario: Binary and source provenance are not conflated
- **WHEN** CLI `0.4.38` is verified from release binary metadata and its exact version-command source is reviewed at commit `47dc75741cd03127d32f1b78d04c644ccf690e7f`
- **THEN** the contract retains catalog target `v0.4.28` for trigger mappings, retains the existing `0.4.32` reviewed response provenance, and records the `0.4.38` binary/version-command evidence separately

#### Scenario: Response mappings have provenance
- **WHEN** a reviewer inspects issue get, usage, runs, trigger add/update, and compatibility version-probe operations
- **THEN** each newly supported public field has a source reference, response destination, omission/null policy where applicable, and named test reference

#### Scenario: Unknown future projection remains review-gated
- **WHEN** a CLI response adds an unreviewed field beyond the approved issue activity, trigger, or version-envelope mappings
- **THEN** that field does not automatically alter the public SDK contract or generated behavior

## ADDED Requirements

### Requirement: Approved trigger contract matches pinned source

`contracts/sdk-contract.json` SHALL govern trigger add and update from Multica `v0.4.28` commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`. Source references SHALL cover the Cobra declarations, flag registrations, `RunE` validation, `Flags().Changed` handling, JSON body destinations, and trigger response fields. Add mappings SHALL be `kind -> --kind -> json_body:kind`, `cron_expression -> --cron -> json_body:cron_expression`, `timezone -> --timezone -> json_body:timezone`, and `label -> --label -> json_body:label`. Update mappings SHALL be `cron_expression -> --cron -> json_body:cron_expression`, `timezone -> --timezone -> json_body:timezone`, `label -> --label -> json_body:label`, and `enabled -> --enabled -> json_body:enabled`. The contract SHALL contain five-state presence semantics, normalized kind/required/conditional/at-least-one constraints, compatibility rationale, response provenance, and positive/negative test references.

#### Scenario: Obsolete mappings are absent
- **WHEN** the approved trigger add/update bindings and signatures are inspected
- **THEN** neither contains `--title`, trigger update contains no `--kind`, and every supported schedule field has one reviewed mapping

#### Scenario: Presence semantics are closed
- **WHEN** contract validation inspects each trigger mutation field
- **THEN** omitted, null, empty, zero, and false behavior is explicit or marked not applicable, including false-as-emitted for enabled

#### Scenario: Constraints cite imperative source
- **WHEN** schedule cron requirements, webhook incompatibilities, allowed kind values, or nonempty update constraints are inspected
- **THEN** each normalized constraint cites the pinned imperative source and has positive and negative test references

### Requirement: Trigger bindings regenerate deterministically

The approved contract SHALL remain the only input that generates trigger runtime constants and conventions. Rendering SHALL produce trigger add/update mappings and validators equivalent to the approved contract, and `check` SHALL reject any handwritten drift. Transient provenance and documentation projections SHALL be generated outside tracked paths and SHALL cite the same pinned source revision.

#### Scenario: Generated add binding is exact
- **WHEN** the approved contract is rendered
- **THEN** `AUTOPILOT_TRIGGER_ADD_BINDING` contains only the approved identifier, kind, cron-expression, timezone, and label mappings and constraints

#### Scenario: Generated update binding is exact
- **WHEN** the approved contract is rendered
- **THEN** `AUTOPILOT_TRIGGER_UPDATE_BINDING` contains only the approved identifiers and cron-expression, timezone, label, and enabled mappings and constraints

#### Scenario: Contract check detects drift
- **WHEN** a generated trigger binding differs from a deterministic render of the approved contract
- **THEN** `scripts/upstream_contract.py check` fails without modifying tracked files

### Requirement: CLI 0.4.38 version evidence is exact

The approved compatibility block SHALL record maximum-tested CLI `0.4.38`. Following its existing verified-binary schema, the record SHALL store resolved full release-source `commit=47dc75741cd03127d32f1b78d04c644ccf690e7f`, `build_date=2026-09-02T09:52:29Z`, `go_version=go1.26.7`, `os=darwin`, and `arch=arm64`. The record's named test reference SHALL use exact raw envelope values `version=0.4.38`, `commit=47dc75741`, `date=2026-09-02T09:52:29Z`, `go=go1.26.7`, `os=darwin`, and `arch=arm64`, SHALL assert that the raw short commit prefixes the stored full SHA, and SHALL govern the mappings `date -> CliVersion.build_date` and `go -> CliVersion.go_version` in addition to the same-name fields. Source provenance SHALL cite the `version --output json` command definition at the full SHA. Rendering SHALL produce `MIN_CLI_VERSION = "0.4.28"` and exclusive `MAX_CLI_VERSION = "0.4.39"`.

#### Scenario: Exact binary envelope matches the approved record
- **WHEN** the reviewed CLI `0.4.38` binary runs `version --output json`
- **THEN** its six-key envelope contains the exact short commit and remaining values above, the provenance resolves that commit to the approved full source SHA, and decoding populates all six corresponding public `CliVersion` fields regardless of object-key order

#### Scenario: Generated strict interval includes 0.4.38
- **WHEN** default strict compatibility checks the decoded version `0.4.38`
- **THEN** generated bounds `[0.4.28, 0.4.39)` accept it without a warning-policy or local-bound override
