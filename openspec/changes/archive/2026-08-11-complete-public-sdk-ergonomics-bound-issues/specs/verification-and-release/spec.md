## ADDED Requirements

### Requirement: Remaining public ergonomics are release-gated
Offline verification SHALL cover the final natural project/issue inputs, exact status-string normalization for issue surfaces and `ProjectResource`, mode-sensitive raw CLI classification for token-login and interactive/process forms, bounded `workspace watch` raw compatibility, direct issue-children binding, and canonical documentation order. Repeated operation, invalid-input, raw-command, and collection-origin cases SHALL extend the repository's existing frozen dataclass tables and shared fixtures. The complete release gate SHALL remain backend-free and network-free.

#### Scenario: Natural-input matrices prove parity and exact plans
- **WHEN** project and issue create cases exercise inline, path-like, semantic description, identifier, entity-reference, omission, and conflict forms through eager and command APIs
- **THEN** signatures match, valid cases produce exact approved argv/results, and invalid cases raise `TypeError` or `ValueError` with zero filesystem/transport I/O

#### Scenario: Status matrices reject implementation errors
- **WHEN** issue list/filter, issue status actions, and `ProjectResource` status actions receive enum members, exact strings, unknown strings, and incompatible values
- **THEN** exact strings and enums produce identical argv while invalid values fail locally without `AttributeError`

#### Scenario: Raw CLI boundary is table-driven
- **WHEN** allowed `auth login --token <token>` forms with trailing options, rejected bare/no-token/malformed auth forms, every other reviewed rejected prefix with trailing arguments, bounded `workspace watch` argv, and representative unknown bounded commands are tested through both raw entry points
- **THEN** allowed cases retain exact structured argv, redaction, options, and result behavior; rejected cases have identical actionable errors, zero transport/spawn calls, and no token or raw secret leakage

#### Scenario: Direct children binding is exhaustive
- **WHEN** empty, children-only, unstaged-only, and mixed child envelopes are decoded through direct eager and command APIs
- **THEN** all issues are bound, metadata is unchanged, entity action construction succeeds, and subprocess counts prove one collection call with no hydration

#### Scenario: README teaches one working workflow in order
- **WHEN** the README introduction and typed documentation fixtures are inspected
- **THEN** they first show `MulticaClient()`, `issues.get(...)`, and a direct entity action, then listing with a valid status value, then command inspection, and all later examples use supported natural inputs without removed request DTOs

#### Scenario: Complete offline gate remains green
- **WHEN** the change is ready for delivery
- **THEN** OpenSpec validation, approved-contract validation/render/check, Ruff check and format check, `mypy src`, `mypy tests`, package validation, and `pytest -m "not live"` all pass without backend or network access
