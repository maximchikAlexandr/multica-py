## ADDED Requirements

### Requirement: v0.4.20 compatibility delta is verified end to end

Offline verification SHALL cover the pinned baseline, contract reconciliation,
runtime cascade semantics, agent copy, issue-search response adaptation,
forward-compatible upstream strings, conflict/validation detail preservation,
the retained autopilot trigger mapping, command preview, and documentation.
Repeated operation and decoding cases SHALL extend the repository's existing
frozen dataclass tables and shared fixtures. The full acceptance gate SHALL run
Ruff check and format check, `mypy src`, `mypy tests`, contract validation and
check, package validation, and `pytest -m "not live"` without requiring a
backend or network.

#### Scenario: Compatibility constants and provenance agree
- **WHEN** contract, generated runtime, compatibility policy, docs, and provenance fixtures are checked
- **THEN** tracked baseline values consistently identify `v0.4.20` and `[0.4.20, 0.4.21)`, with no stale `v0.4.9` expectation outside historical/archive material

#### Scenario: Agent copy has table-driven command coverage
- **WHEN** canonical and variant operation cases run
- **THEN** they cover same-runtime copy, cross-runtime default model, explicit portable overrides, repeated permission members, `copy_skills=False`, exact command preview, bound result decoding, and zero-I/O validation failures

#### Scenario: Secret and machine-local copy behavior is negative-tested
- **WHEN** agent copy is constructed without secret configuration
- **THEN** tests prove `--custom-env`, `--mcp-config`, and `--runtime-config` are absent from signature, preview, executed argv, and copied behavior

#### Scenario: Issue search shapes and sources are covered
- **WHEN** search decoding tests run
- **THEN** they cover a `v0.4.20` envelope and legacy array, present title/description/comment sources, a number-shaped query, an omitted source, an unknown future source, exact argv, and the unchanged tuple return type

#### Scenario: Conflict and validation matrices preserve detail
- **WHEN** transport failure cases run
- **THEN** raw statuses, pinned English/Chinese prefixes, generic fallbacks, exit `5`, reviewed local validation, empty diagnostics, and secret-bearing diagnostics assert exact exception class, reported exit code, redacted attributes, and useful `str(exc)` text

#### Scenario: Runtime cascade docs and tests use unbind semantics
- **WHEN** runtime resource tests and public/maintainer documentation are inspected
- **THEN** `cascade=True` is described and asserted as unbinding agents and cancelling active work while preserving configuration, chats, and history, and no current documentation claims that agents are deleted or archived

#### Scenario: Autopilot source-contract regression rejects run spelling
- **WHEN** the approved binding, generated descriptor, canonical operation case, and source-validation fixture are checked
- **THEN** every expected command uses `autopilot trigger` and a mutation back to `autopilot run` fails at least one offline gate

#### Scenario: Unknown upstream-owned strings stay decodable
- **WHEN** typed model and command cases use future provider, model, thinking-level, service-tier, or match-source strings
- **THEN** no closed-enum decode or construction failure occurs before upstream validation

#### Scenario: Canonical discovery includes new command methods
- **WHEN** public method discovery is compared with canonical operation cases
- **THEN** `agents.copy` and `agents.copy_command` follow the repository's command-preview completeness convention, every eager CLI method still has exactly one canonical row, and stored counts equal computed table partitions

#### Scenario: Complete offline gate is green
- **WHEN** the change is ready for delivery
- **THEN** contract `validate --source-checkout`, deterministic render/check, Ruff check, Ruff format check, `mypy src`, `mypy tests`, package validation, and `pytest -m "not live"` all pass
