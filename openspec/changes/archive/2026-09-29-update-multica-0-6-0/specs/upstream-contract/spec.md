## ADDED Requirements

### Requirement: Refreshed SDK baseline and target provenance are exact
The approved contract SHALL record SDK baseline
`c1842ae2dfcd0cc5e739b7785d3209d5e72d01ed`, its tree and contract blob, and the
193-operation/196-entrypoint `0.5.3` state merged by PR #95. Target identity SHALL
record stable tag `v0.6.0`, release `398016451`, commit
`ea94c7cd5bbce9c8e1f28c5fa049c47ee7651d02`, official archive/checksum, verified
binary hash and version output. Compatibility SHALL be direct from `0.5.3`, with
maximum-tested `0.6.0` and exclusive next ceiling `0.6.1`.

#### Scenario: Every identity agrees before promotion
- **WHEN** contract validation checks baseline, release, source, binary and compatibility facts
- **THEN** every pinned identity agrees exactly or promotion fails

#### Scenario: Merged baseline work is not recast as target delta
- **WHEN** baseline and target reconciliation classifies the 29 operations added by PR #95
- **THEN** all already approved operations are retained or adapted from baseline and none is planned as duplicate creation

### Requirement: Complete target CLI inventory is reconciled
The approved contract SHALL account for all 205 target CLI nodes as four added,
zero removed, six changed and all remaining nodes retained. Every added or changed
node SHALL trace arity, defaults, accepted values, presence, conflicts and exact
path/query/body/header/file/process destinations. Root, hidden, test-only and
dynamic-Cobra classifications SHALL remain explicit, including source-pinned
recovery of `issue wakeup checkin` without changing collector/runtime code.

#### Scenario: Every target node has one disposition
- **WHEN** strict validation compares approved baseline and target inventories
- **THEN** all 205 nodes have exactly one retain, adapt, support, defer or not-SDK decision with no unexplained gap

#### Scenario: Evidence defect does not promote runtime behavior
- **WHEN** raw collector output omits dynamic checkin or includes unattached source names
- **THEN** pinned source augmentation supplies review evidence while approved contract remains the sole runtime-generation input

### Requirement: Complete 0.6.0 response registry is approved
The approved response registry SHALL contain all 196 baseline-supported
entrypoints with pinned old/target trace, envelope, fields/types, five-state
presence, pagination, enum openness, error decoding, adapter and tests. Exactly 18
entrypoints SHALL be changed: agent tasks, issue runs, seven comment entrypoints,
issue pull requests, workspace MCP list, six existing wakeup entrypoints and issue
timeline. The other 178 SHALL be proven unchanged.

#### Scenario: Response review is complete
- **WHEN** response-review validation runs
- **THEN** 196 of 196 entrypoints are accounted for, 18 are changed, 178 are unchanged and every changed row has implementation/test mapping

#### Scenario: New target-only leaves have explicit results
- **WHEN** trigger, delete, checkin and wakeup-runs operations are approved
- **THEN** each has one exact result/envelope contract even though it was absent from the baseline response registry

### Requirement: Scope decisions remain review-gated
The contract SHALL adapt existing wakeup and timeline surfaces, support the four
target-only wakeup leaves, issue attachments and agent-task pagination, adapt all
18 changed responses, retain unchanged PR #95 operations, defer
`steer_task_ids`, and classify excluded UI/mobile/desktop/search/channel/WeCom/
internal scheduler behavior as not SDK surface. Removed public operations SHALL be
none.

#### Scenario: Candidate evidence cannot become public API
- **WHEN** source or collector evidence contains a deferred or excluded candidate
- **THEN** no public operation, signature, model, dependency or generated binding is added without a new approved disposition
