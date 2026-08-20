## ADDED Requirements

### Requirement: v0.4.28 compatibility delta is verified end to end

Offline verification SHALL cover the pinned `v0.4.28` baseline, full command-tree
reconciliation, Plugin and Property resources, Workspace/Agent MCP operations,
skill refresh, issue status/assignee decoding, secret redaction for MCP and
plugin credentials, bound relations R34–R38, command preview, and documentation.
Repeated operation and decoding cases SHALL extend the repository's existing
frozen dataclass tables and shared fixtures. The full acceptance gate SHALL run
Ruff check and format check, `mypy src`, `mypy tests`, contract validation and
check, package validation, and `pytest -m "not live"` without requiring a
backend or network.

#### Scenario: Compatibility constants and provenance agree
- **WHEN** contract, generated runtime, compatibility policy, docs, and provenance fixtures are checked
- **THEN** tracked baseline values consistently identify `v0.4.28` and `[0.4.28, 0.4.29)`, with no stale `v0.4.20` expectation outside historical/archive material

#### Scenario: Plugin and property operations have table-driven coverage
- **WHEN** canonical and variant operation cases run
- **THEN** they cover plugin list/status/validate/pack/init/install, property catalog CRUD/archive, issue property list/set/unset, exact command preview, and zero-I/O validation failures

#### Scenario: MCP secret channels are negative-tested
- **WHEN** workspace MCP add is constructed with a config file
- **THEN** tests prove `--server-config` is absent, file/stdin exclusivity is enforced, and tokens never appear in preview or diagnostics

#### Scenario: Skill refresh and agent MCP are covered
- **WHEN** canonical operation cases run
- **THEN** they include `skill refresh <id>` and `agent mcp list|add|enable|disable|remove` with exact argv

#### Scenario: Canonical discovery includes new command methods
- **WHEN** public method discovery is compared with canonical operation cases
- **THEN** every eager CLI method still has exactly one canonical row, stored counts equal computed table partitions, and no allowlist is accepted

#### Scenario: Complete offline gate is green
- **WHEN** the change is ready for delivery
- **THEN** contract `validate --source-checkout`, deterministic render/check, Ruff check, Ruff format check, `mypy src`, `mypy tests`, package validation, and `pytest -m "not live"` all pass

#### Scenario: Audited binary mismatches have regressions
- **WHEN** Plugin init, Workspace MCP remove, root login, configuration, issue prioritization, and workspace watch surfaces are verified
- **THEN** exact argv/response tests agree with the pinned `v0.4.28` Cobra source and verified release binary rather than legacy fixture paths

#### Scenario: GitHub final authority is green
- **WHEN** the remediation commit is pushed to the feature branch
- **THEN** every required GitHub check for the feature PR completes successfully at the pushed HEAD

## REMOVED Requirements

### Requirement: v0.4.20 compatibility delta is verified end to end
**Reason**: Offline verification now certifies the `v0.4.28` baseline and new
Plugin/Property/MCP/skill-refresh coverage.
**Migration**: Use `v0.4.28 compatibility delta is verified end to end`. Retain
historical `v0.4.20` coverage only in archived OpenSpec material.
