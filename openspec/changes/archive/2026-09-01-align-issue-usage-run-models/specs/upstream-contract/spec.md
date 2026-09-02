## ADDED Requirements

### Requirement: Issue activity contract records the reviewed compatibility window
The approved SDK contract SHALL distinguish the pinned source target from verified release binaries and SHALL record response mappings, presence semantics, and positive/negative tests for issue assignee, issue usage, and issue runs across the supported CLI 0.4.28 through 0.4.32 compatibility window. Generated default compatibility bounds SHALL come only from that approved contract.

#### Scenario: Reviewed contract generates default bounds
- **WHEN** the approved contract is rendered
- **THEN** the generated compatibility projection accepts CLI versions 0.4.28 through 0.4.32 and rejects or warns at 0.4.33 according to policy, without using evidence files directly as generator input

#### Scenario: Binary and source provenance are not conflated
- **WHEN** CLI 0.4.32 is verified from release binary metadata and its exact source commit is reviewed for the affected response mappings
- **THEN** the contract retains the catalog-wide source target for existing mappings, records binary metadata separately, and pins each new response mapping to the exact reviewed source commit

#### Scenario: Response mappings have provenance
- **WHEN** a reviewer inspects issue get, usage, and runs operations
- **THEN** each newly supported public field has a source reference, response destination, omission/null policy, and named test reference

#### Scenario: Unknown future projection remains review-gated
- **WHEN** a CLI response adds an unreviewed field beyond the approved issue activity mappings
- **THEN** that field does not automatically alter the public SDK contract or generated behavior
