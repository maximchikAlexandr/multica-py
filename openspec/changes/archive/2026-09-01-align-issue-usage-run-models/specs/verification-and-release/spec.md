## ADDED Requirements

### Requirement: Issue activity compatibility is verified without silent defaulting
Offline verification SHALL use provenance-backed legacy and current JSON envelopes to cover issue assignee, issue usage, and task-run decoding. A gated live smoke SHALL exercise the installed supported CLI without entering the default offline suite.

#### Scenario: Contract matrix covers assignee projections
- **WHEN** contract tests decode nested-only, scalar-only, matching dual, conflicting dual, partial scalar, null, and omitted assignee projections
- **THEN** supported cases preserve exact public values and contradictory shapes raise `OutputShapeError`

#### Scenario: Usage matrix covers exact categories
- **WHEN** legacy and current usage fixtures are decoded
- **THEN** task or run count and every present token/cost category match the fixture exactly, and no known current field silently defaults to `None` or `0`

#### Scenario: Run matrix covers worktree and runtime context
- **WHEN** legacy and current issue-run fixtures are decoded
- **THEN** current reviewed worktree/runtime/result fields are preserved and legacy omissions retain documented compatibility defaults

#### Scenario: Full offline gates remain backend-free
- **WHEN** the repository's offline pytest, Ruff, mypy, approved-contract render/check, and strict OpenSpec gates run
- **THEN** they pass without network or backend access

#### Scenario: Live smoke is explicitly gated
- **WHEN** live verification is enabled against CLI 0.4.32 and an authorized workspace with issue activity
- **THEN** typed usage and run values match the CLI envelope and the test remains marked live and serial
