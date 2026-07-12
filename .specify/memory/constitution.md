<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Template principle 1 -> I. Source-Driven CLI Contract
- Template principle 2 -> II. Thin Synchronous Wrapper
- Template principle 3 -> III. Typed Public Surface
- Template principle 4 -> IV. Offline Testability and Provenance
- Template principle 5 -> V. Secure Packaging and Release
Added sections:
- SDK Constraints
- Development Workflow and Quality Gates
Removed sections:
- Placeholder section names and example comments
Templates requiring updates:
- .specify/templates/plan-template.md: reviewed, no update required
- .specify/templates/spec-template.md: reviewed, no update required
- .specify/templates/tasks-template.md: reviewed, no update required
- .specify/templates/commands/*.md: not present in this Spec Kit installation
Follow-up TODOs: none
-->
# Multica Python SDK Constitution

## Core Principles

### I. Source-Driven CLI Contract

The pinned upstream Multica CLI source is the authority for command names,
aliases, flags, defaults, validation, output modes, response shapes, and error
signals. Specifications, plans, tasks, fixtures, and documentation MUST record
the upstream commit and source locations used for every command family. Prose
documentation MAY guide discovery, but it MUST NOT override the pinned source.

Rationale: the SDK is a wrapper over an external CLI, so correctness depends on
matching the actual command implementation rather than secondary descriptions.

### II. Thin Synchronous Wrapper

The SDK MUST call the installed `multica` executable through a controlled
subprocess transport and MUST NOT call undocumented Multica server APIs,
reimplement Multica business logic, or install the Multica executable. Version 1
MUST expose a synchronous Python API only; long-running, interactive, foreground,
or streaming commands MUST use explicit process-handle abstractions.

Rationale: a narrow wrapper keeps ownership clear and avoids divergent client
behavior from the Multica CLI.

### III. Typed Public Surface

Public and project-owned internal Python APIs MUST be precisely typed and MUST
NOT expose `Any` in callable signatures, models, or diagnostics. Runtime models
MUST use frozen `msgspec.Struct` classes or closed primitive types. Finite CLI
choices MUST use exact enums or literals, and unsupported or unclassifiable
states MUST be represented explicitly rather than inferred from localized prose.

Rationale: the SDK is intended for automation services where hidden dynamic
types and inferred semantics create fragile workflows.

### IV. Offline Testability and Provenance

The default test suite MUST run without a live Multica account, server, or
network connection. Command construction, decoding, error mapping, lifecycle
behavior, packaging, and coverage MUST be validated with pinned-source fixtures,
a deterministic fake executable, and provenance records that link each fixture
or coverage row to the upstream source.

Rationale: reliable local and CI validation must not depend on external service
state.

### V. Secure Packaging and Release

The package MUST be distributed as `multica-py`, importable as `multica_py`, and
released through `uv`-based build and validation workflows. PyPI publication MUST
use Trusted Publishing or an equivalently secure approved release identity.
Secrets MUST be redacted from exceptions, logs, debug output, process diagnostics,
object representations, and console-tool output.

Rationale: package consumers need reproducible installation behavior and safe
diagnostics when wrapping a CLI that may receive tokens and environment secrets.

## SDK Constraints

- Python 3.12 and 3.13 on Linux and macOS are the version 1 target platforms.
- Windows support is out of scope for version 1 except for commands that require
  no SDK-specific daemon, process-group, or child-process cleanup guarantees.
- Runtime dependencies MUST stay limited to dependencies needed by SDK execution;
  test, release, documentation, HTTP client, Pydantic, and dataclass-modeling
  dependencies MUST NOT become runtime dependencies.
- The package MUST import without an installed or running Multica CLI.
- The console entry point MUST expose package-level utilities only and MUST NOT
  become a second implementation of the Multica CLI.

## Development Workflow and Quality Gates

- Every implementation plan MUST complete a Constitution Check before task
  generation and re-check it after design changes.
- Every implementation task that maps a command or model MUST be traceable to
  a pinned upstream source location or to an explicit unsupported-command row.
- CI MUST run on pull requests and the default branch, using `uv` for setup,
  checks, tests, builds, and package validation.
- CI MUST run Ruff format/check, strict mypy, unit tests, contract tests,
  integration tests against the fake executable, distribution build checks,
  installation checks, and command-coverage audits.
- Release workflows MUST build and validate artifacts before publication and
  MUST publish production PyPI artifacts only from an approved release event.

## Governance

This constitution supersedes conflicting guidance in feature specs, plans,
tasks, templates, and ad hoc instructions for this repository. Amendments require
an explicit constitution update, a Sync Impact Report, and review of dependent
Spec Kit templates and active feature artifacts.

Versioning follows semantic versioning:

- MAJOR for removing or redefining a principle in a backward-incompatible way;
- MINOR for adding a principle or materially expanding governance;
- PATCH for wording clarifications that do not change required behavior.

Compliance with this constitution MUST be checked during specification analysis,
planning, task generation, implementation review, and release readiness review.

**Version**: 1.0.0 | **Ratified**: 2026-07-12 | **Last Amended**: 2026-07-12
