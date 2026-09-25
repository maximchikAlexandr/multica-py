## ADDED Requirements

### Requirement: Corrected resumed-session usage remains wire-compatible
Existing task, issue, and runtime usage models SHALL preserve target-provided
per-run values after Multica `0.5.3` applies resumed Claude session accounting.
The SDK SHALL NOT read provider session files, subtract baselines, recompute
aggregates, change numeric fields or omission rules, or add a provider-specific
public type or operation.

#### Scenario: Resumed target values are preserved exactly
- **WHEN** target fixtures contain per-run multi-model input, output, cache-read, and cache-write values after baseline subtraction
- **THEN** existing task, issue, and runtime usage projections expose exactly those values without client-side arithmetic

#### Scenario: Fallback and rejected-resume values remain authoritative
- **WHEN** target fixtures represent a reset counter, missing or corrupt snapshot, no-result fallback, or rejected resume
- **THEN** the SDK preserves the values and existing absence semantics emitted by Multica without applying a stale baseline

#### Scenario: Public SDK surface remains unchanged
- **WHEN** public models, symbols, operations, signatures, response fields, and dependency metadata are compared before and after the upgrade
- **THEN** no usage-specific public surface or dependency is added and existing numeric validation remains unchanged
