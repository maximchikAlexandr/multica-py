## MODIFIED Requirements

### Requirement: Focused process and offline checks

Offline tests MUST use stdlib and pytest, keep exact argv assertions including
operations with dynamic temporary paths, retain the focused real-process cases
listed below, and use deterministic synchronization or subprocess test doubles
for additional lifecycle branches.

#### Scenario: Offline checks keep focused process cases

- **WHEN** the process module is collected
- **THEN** IDs are `bytes-env`, `text-stdin`, `pipe-capacity-stdin`,
  `spawn-gated-stdin`, `close-stdin-gated`, `close-gated`,
  `bounded-spawn-capture`, `timeout-gated-stdin`, and
  `timeout-tree-cleanup`.
