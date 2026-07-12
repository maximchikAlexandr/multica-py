# Feature Specification: Complete Python SDK for the Multica CLI

**Feature ID:** 001-full-cli-sdk  
**Repository:** `maximchikAlexandr/multica-py`  
**Status:** Ready for implementation

## Overview

Create a distributable Python SDK that exposes the complete Multica CLI surface from a pinned upstream CLI source baseline through a typed Python interface. The SDK is a thin wrapper over the installed `multica` executable and does not call undocumented server APIs or reimplement Multica business logic.

The public API follows a hybrid resource-oriented design:

- one top-level client;
- resource classes that group operations by CLI domain;
- immutable typed result and input models;
- an internal CLI transport responsible for process execution and output/error conversion.

The project must be published as a standard package on PyPI and expose both a Python library and an installable command-line tool. The primary end-user installation and execution workflow is `uv tool install multica-py` and `uvx multica-py`; project-level library integration uses `uv add multica-py`. Standard `pip install multica-py` remains supported as a compatibility path. Development, dependency management, environment execution, testing, building, and publishing are performed through `uv` commands and tools.

## Scope Boundaries

- Version 1 targets Python 3.12 and 3.13 on Linux and macOS.
- Windows support is explicitly out of scope for version 1 except for commands that work without SDK-specific daemon, process-group, or child-process cleanup guarantees.
- The public SDK is synchronous only. A public async client and async process streams are out of scope for version 1.
- The authoritative command coverage denominator is the pinned upstream CLI source baseline, not prose documentation. Documentation is a secondary aid.
- The package does not install the Multica CLI and does not own Multica authentication state.

## User Scenarios and Testing

### US-001: Use Multica from a Python application

As a Python developer, I can create a client and invoke Multica operations through discoverable resource methods so that I do not have to construct shell commands or parse JSON manually.

**Acceptance scenarios:**

1. Given an installed and configured Multica CLI, when a caller lists issues, the SDK returns an immutable tuple of exact issue models with no public `Any`.
2. Given an issue identifier, when a caller changes its status or assignee, the SDK invokes the equivalent CLI command and returns a typed result.
3. Given a CLI validation, authentication, network, or not-found failure that the pinned source exposes through a stable machine-readable signal, the SDK raises the corresponding typed exception; otherwise it raises a generic command execution exception with preserved diagnostics.

### US-002: Cover the full pinned CLI

As an automation author, I can access every command registered by the pinned Multica CLI source baseline through the SDK so that Python automation is not forced to fall back to direct subprocess calls.

**Acceptance scenarios:**

1. Every command registered by the pinned source baseline has exactly one SDK operation, one process-oriented operation, or one explicit coverage-matrix row explaining why the command is intentionally unsupported.
2. Commands that support JSON output are decoded into exact typed models.
3. Commands that are interactive, streaming, textual, binary, empty, or mixed-output expose the appropriate typed result shape without pretending that undocumented JSON exists.
4. Aliases are recorded as alternate spellings of one command unless the pinned source implements different behavior; hidden and deprecated commands are included in the coverage matrix and either mapped or explicitly excluded with a source-backed reason.

### US-003: Use the SDK safely in orchestration services

As a FastAPI or Temporal developer, I can configure executable path, profile, workspace, environment, timeout, and debug behavior once on the client and reuse those settings across resources.

**Acceptance scenarios:**

1. The caller can select a profile and workspace without mutating global process state.
2. Concurrent client instances with different profiles or workspaces do not interfere with each other.
3. The transport never invokes a shell and passes arguments as an explicit sequence.
4. Timeouts and cancellation terminate child processes and return typed failures.
5. Callers use the synchronous SDK inside their own service thread, worker, or activity boundary; no public async API is required in version 1.

### US-004: Install and run from PyPI primarily as a uv tool

As a package consumer, I can install and execute the package from PyPI primarily as an isolated `uv` tool, while also adding it as a Python library to a project and retaining standard `pip` compatibility.

**Acceptance scenarios:**

1. `uv tool install multica-py` installs the released package from PyPI as an isolated executable tool.
2. `uvx multica-py` runs the released tool directly from PyPI without requiring a persistent project dependency and exits successfully by printing the package help or another documented default command response when no subcommand is provided.
3. `uv add multica-py` adds the released package as a Python library dependency to a consumer project.
4. `uv pip install multica-py` and `pip install multica-py` remain supported compatibility paths.
5. The installed tool exposes a documented console entry point backed by the same typed SDK and CLI transport.
6. Installing the package does not install the Multica CLI itself; absence of the executable produces a clear typed error.
7. Contributors can bootstrap, run, test, lint, type-check, build, and publish the source project through `uv` commands and tools.
8. A release workflow can publish validated wheel and source distributions to PyPI using trusted publishing or an equivalently secure mechanism.

### US-005: Diagnose installation and coverage from the package tool

As a package consumer or maintainer, I can run package-level diagnostic commands without learning Python APIs so that installation, upstream CLI compatibility, and coverage status are easy to verify.

**Acceptance scenarios:**

1. `multica-py doctor` verifies the Python package, Multica executable discovery, detected CLI version, authentication status, and configured profile/workspace.
2. `multica-py version` prints the SDK version and detected Multica CLI version.
3. `multica-py coverage` prints the pinned upstream baseline and command coverage status.
4. `multica-py exec -- <multica arguments>` passes arguments to the Multica executable for diagnostics and returns the child exit code without becoming part of the typed SDK guarantee.

## Functional Requirements

### Public architecture

- **FR-001:** The SDK MUST expose one top-level `MulticaClient`-style entry point.
- **FR-002:** The client MUST expose resource objects grouped by CLI domain rather than a single flat method namespace.
- **FR-003:** Resource objects MUST be stateless procedure containers backed by the parent client configuration.
- **FR-004:** Returned domain objects MUST be immutable typed models and MUST NOT perform hidden network or subprocess operations.
- **FR-005:** The SDK MUST NOT use an Active Record interface such as implicit `save()` operations.
- **FR-006:** The SDK MUST be a CLI wrapper only and MUST NOT call Multica REST endpoints directly.
- **FR-006A:** The PyPI distribution MUST expose a console entry point named `multica-py` for use through `uv tool install` and `uvx`.
- **FR-006B:** The console entry point MUST delegate to the same resource and transport layer used by the Python API and MUST NOT maintain a second implementation of Multica command semantics.
- **FR-006C:** The console entry point MUST expose only package-level utility commands: `doctor`, `version`, `coverage`, and diagnostic `exec`.
- **FR-006D:** Diagnostic `multica-py exec` MUST be explicitly documented as an untyped passthrough outside the typed resource API guarantee.

### CLI transport

- **FR-007:** All commands MUST run through a single internal transport abstraction.
- **FR-008:** The transport MUST invoke the Multica executable without a shell.
- **FR-009:** The transport MUST support executable path, profile, workspace ID, environment overrides, request timeout, working directory, and debug mode.
- **FR-010:** The transport MUST capture exit code, stdout, and stderr without losing diagnostic content.
- **FR-011:** Commands supporting structured output MUST be called with JSON output whenever available.
- **FR-012:** JSON output MUST be decoded into exact `msgspec` models; additive unknown fields MAY be ignored only under the compatibility policy, while missing or incompatible required fields MUST fail decoding.
- **FR-013:** The SDK MUST detect missing or non-executable Multica binaries before or during the first invocation and raise a typed executable error.
- **FR-014:** The SDK MUST expose the detected Multica CLI version and support compatibility policies for strict baseline matching, warning on newer compatible versions, ignoring version checks, rejecting older unsupported versions, and failing on unparsable version output.
- **FR-015:** The SDK MUST preserve command ordering and repeated flags exactly where the CLI semantics depend on them.
- **FR-016:** The SDK MUST support cancellation and timeouts for finite commands, terminate the process group where the platform supports it, escalate from graceful termination to forced kill, and surface a typed failure if descendant cleanup cannot be confirmed.
- **FR-017:** Long-running, streaming, foreground, update, browser-opening, or interactive commands MUST expose an explicit stream/process handle abstraction and MUST NOT block through an ordinary finite-result method unintentionally.
- **FR-017A:** Process handles MUST define behavior for partial output, unexpected exit, consumer abandonment, repeated close/cancel calls, timeout, and context-manager cleanup.
- **FR-017B:** The SDK MUST define bounded per-client process concurrency, or explicitly document that concurrency is caller-owned for version 1.

### Complete command coverage

- **FR-018:** The SDK MUST cover authentication operations: login, authentication status, and logout.
- **FR-019:** The SDK MUST cover setup operations, including cloud and self-hosted setup options.
- **FR-020:** The SDK MUST cover daemon operations: start, stop, status, and logs, including foreground/follow behavior where supported.
- **FR-021:** The SDK MUST cover workspace operations: list, switch, get, and member listing.
- **FR-022:** The SDK MUST cover issue operations: list, get, create, update, reorder, assign/unassign, and status changes.
- **FR-023:** The SDK MUST cover issue comments: flat listing, thread listing, recent threads, cursor pagination, incremental polling, add, reply, and delete.
- **FR-024:** The SDK MUST cover issue metadata: list, get, set with explicit or inferred primitive type, delete, and list filtering by repeated metadata predicates.
- **FR-025:** The SDK MUST cover issue subscribers: list, subscribe, unsubscribe, and acting on the caller or an explicitly selected user.
- **FR-026:** The SDK MUST cover execution history: issue runs, run messages, incremental message polling, and issue usage.
- **FR-027:** The SDK MUST cover project operations: list, get, create, update, status, and delete.
- **FR-028:** The SDK MUST cover configuration operations: show and set.
- **FR-029:** The SDK MUST cover autopilot operations: list, get, create, update, delete, manual trigger, run history, and schedule trigger create/update/delete.
- **FR-030:** The SDK MUST cover agent listing.
- **FR-031:** The SDK MUST cover CLI version and update commands.
- **FR-032:** Each resource method MUST document the equivalent Multica CLI command and supported CLI version when compatibility differs.
- **FR-032A:** The implementation MUST derive command names, flags, defaults, validation rules, output shapes, identifiers, enums, and exit behavior from the upstream Multica CLI source code, not from documentation alone.
- **FR-032B:** The planning and implementation workflow MUST pin an upstream Multica commit or release and record the exact source files used for every command family and model family.
- **FR-032C:** When upstream documentation and CLI source disagree, the pinned CLI source behavior MUST be treated as authoritative and the discrepancy MUST be recorded in the coverage matrix.
- **FR-032D:** The CLI-to-SDK coverage matrix MUST include the upstream command implementation location and the upstream type/model source location where applicable.
- **FR-032E:** Complete CLI coverage MUST include all root commands, subcommands, source-registered aliases, hidden commands, deprecated commands, and commands represented in the pinned manifest.
- **FR-032F:** Aliases MUST map to the same SDK operation as their canonical command unless the pinned source gives the alias different semantics.
- **FR-032G:** An unsupported-command row satisfies coverage only when the pinned source proves that the command cannot be represented safely in version 1, and the row records the reason, user-visible behavior, and planned resolution or permanent exclusion.
- **FR-032H:** The SDK MUST cover every pinned command family, including labels, skills, repositories, runtimes, attachments, squads, users, and any additional command families discovered in the pinned source baseline.

### Typed models

- **FR-033:** Runtime and public models MUST use `msgspec`; Pydantic and dataclasses MUST NOT be runtime model dependencies.
- **FR-034:** Public and internal project annotations MUST NOT contain explicit or implicit `Any`; third-party stub internals are not part of this requirement unless they leak into the public SDK surface.
- **FR-035:** Unknown JSON fields MUST be handled according to an explicit compatibility policy without exposing `dict[str, Any]`; tagged unions, discriminators, enums, and changed semantics of existing fields MUST remain strict.
- **FR-036:** Open-ended primitive metadata values MUST use a closed union of supported primitive types.
- **FR-037:** Identifiers, statuses, priorities, sort fields, directions, output modes, trigger modes, metadata value types, and other finite CLI choices MUST use precise enums or literal types.
- **FR-038:** Timestamps, durations, pagination cursors, token usage, task messages, and process results MUST have dedicated exact models where they appear in public results.
- **FR-039:** Input option models MUST reject mutually exclusive CLI options before invoking the process whenever the exclusivity is known from the pinned source, the CLI help, or the SDK request type.
- **FR-040:** Output decoding errors MUST identify the command and preserve redacted output needed for diagnosis, including warnings, non-JSON prefixes, stdout/stderr split output, and empty successful output.

### Errors

- **FR-041:** The SDK MUST map command failures to the most specific exception type only when the pinned source, exit status, or a stable machine-readable error envelope permits reliable classification. If reliable classification is unavailable, the SDK MUST raise `CommandExecutionError` and MUST NOT infer domain errors from localized prose alone.
- **FR-042:** Timeout, cancellation, missing executable, malformed output, unsupported CLI version, and process termination MUST have dedicated exception types.
- **FR-043:** Exceptions MUST expose typed diagnostic fields, including command arguments in safely redacted form, exit code when available, and stderr.
- **FR-044:** Secrets such as login tokens MUST be redacted from exception text, logs, debug output, stdout/stderr excerpts, environment diagnostics, stdin diagnostics, object representations, and console-tool output.

### Packaging and installation

- **FR-045:** The project MUST use `uv` as the primary tool for consumer installation examples, dependency management, locking, environments, command execution, testing, builds, and publishing workflows.
- **FR-046:** The produced distribution MUST be a standard Python wheel and source distribution published to PyPI and installable using `pip`.
- **FR-047:** PyPI package metadata MUST declare the supported Python versions, MIT license, repository URL, description, and typed-package marker.
- **FR-048:** The package MUST include `py.typed` so downstream type checkers consume its annotations.
- **FR-049:** Runtime dependencies MUST be limited to dependencies needed for SDK execution; version 1 MUST include `msgspec` as the model/codec dependency and MUST NOT add runtime dependencies for test, release, documentation, HTTP clients, Pydantic, or dataclasses-based modeling.
- **FR-050:** Importing the package MUST NOT require an installed or running Multica CLI.
- **FR-050A:** The import package name MUST be `multica_py`.
- **FR-050B:** The project MUST verify PyPI distribution-name availability or ownership before publishing and MUST use PyPI Trusted Publishing or an equivalently secure release identity.

### Quality and CI

- **FR-051:** CI MUST run on pull requests and the default branch.
- **FR-052:** CI MUST install and execute project tasks through `uv`.
- **FR-053:** CI MUST run Ruff formatting checks and Ruff lint checks.
- **FR-054:** Ruff rules MUST be based on the supplied configuration, removing Odoo-specific sections and rules that are not applicable to a standalone Python SDK.
- **FR-055:** Ruff rule `COM812`, which requires trailing commas in multiline constructs, MUST be disabled; formatting MAY still introduce commas where required by the formatter.
- **FR-056:** CI MUST run mypy in strict mode or an equivalently explicit configuration that rejects all untyped public and internal definitions and disallows `Any`.
- **FR-057:** CI MUST run unit and integration tests and build both wheel and source distribution.
- **FR-058:** CI MUST verify on Linux and macOS with Python 3.12 and 3.13 that the built wheel can be installed with `uv tool install`, executed with `uvx`, installed with `uv add` or `uv pip install`, and installed with standard `pip install` in clean environments.
- **FR-059:** CI MUST verify package metadata and typed-package contents.
- **FR-059A:** Release CI MUST build with `uv`, validate both distributions, and publish to PyPI only from an approved release event.
- **FR-059B:** CI MUST verify that the intended PyPI distribution name and import package name remain stable and do not collide with unintended packages.
- **FR-059C:** Release validation MUST distinguish local/TestPyPI validation from production PyPI publication and MUST require an approved release event before production publication.
- **FR-060:** Test fixtures MUST not require access to a live Multica server for the default unit-test suite.

### Testing

- **FR-061:** Unit tests MUST verify command construction for every SDK operation against fixtures derived from the pinned upstream CLI source.
- **FR-062:** Unit tests MUST verify decoding of representative JSON output for every structured model family.
- **FR-063:** Unit tests MUST verify every reliable source-backed failure classification and every SDK-specific transport failure; unclassifiable CLI failures MUST be tested as generic command execution errors.
- **FR-064:** Integration tests MUST run against a controllable fake Multica executable that records arguments and emits fixtures.
- **FR-065:** Optional compatibility tests MAY run against a real installed Multica CLI and MUST be separable from the default test suite.
- **FR-066:** Coverage reporting MUST distinguish transport, resources, models, and error mapping.

### Documentation

- **FR-067:** Documentation MUST lead with the primary consumer workflows: `uv tool install multica-py`, `uvx multica-py`, and `uv add multica-py`; compatibility installation and contributor workflows MUST be linked from that primary path.
- **FR-068:** Documentation MUST clearly state that the Multica CLI must be installed and authenticated separately.
- **FR-069:** Documentation MUST include a CLI-to-SDK coverage matrix with command, SDK method, output model, upstream source file, and baseline commit.
- **FR-070:** Documentation MUST explain the compatibility policy for new Multica versions and unknown output fields.
- **FR-071:** Contributor documentation MUST explain how to refresh the SDK from a newer Multica CLI source baseline and how to detect command or type drift.
- **FR-072:** Installation documentation MUST include a maintained installation matrix that distinguishes primary tool installation/execution through `uv tool install` and `uvx`, project-library integration through `uv add`, compatibility installation through `uv pip install` and `pip`, and contributor workflows executed through `uv`.
- **FR-073:** Documentation MUST state supported platforms, Python versions, synchronous-only behavior, no public async client in version 1, package-name/import-name distinction, and the diagnostic-only status of `multica-py exec`.
- **FR-074:** Documentation MUST define executable trust and path-resolution behavior, environment inheritance, working-directory handling, dependency provenance expectations, and release approval authority.
- **FR-075:** Console documentation MUST define whether each `multica-py` command supports human-readable output, machine-readable output, exit-code conventions, and accessible plain-text diagnostics.

## Resource Model

The exact names are finalized during planning, but the public API must separate at least these domains:

- authentication;
- setup;
- daemon;
- workspaces and members;
- issues;
- comments;
- metadata;
- subscribers;
- runs/messages/usage;
- projects;
- configuration;
- autopilots and triggers;
- agents;
- CLI maintenance/version information;
- labels;
- skills and skill files;
- repositories;
- runtimes;
- attachments;
- squads and users where registered by the pinned source.

Nested resources MAY be exposed through parent resources where this mirrors the CLI hierarchy, for example issue comments, issue metadata, and autopilot triggers.

## Key Entities

- **Client configuration:** executable, profile, workspace, environment, timeout, working directory, debug and compatibility policy.
- **Command request:** executable arguments, execution mode, redaction policy and expected output decoder.
- **Command result:** exit status, stdout, stderr and decoded payload when applicable.
- **Resource:** typed operation group sharing client transport and configuration.
- **Domain models:** workspace, member, issue, comment/thread, metadata entry, subscriber, task run, run message, usage, project, autopilot, trigger, agent and daemon status.
- **Stream handle/event:** lifecycle and output records for follow/foreground commands.

## Edge Cases

- The Multica executable is absent, renamed, not executable, or is an unsupported version.
- JSON output contains additive fields introduced by a newer compatible CLI.
- JSON output removes or changes a required field.
- stdout contains warnings or non-JSON prefixes despite requesting JSON.
- stderr contains pagination cursor information alongside successful JSON output.
- A command returns success with an empty body.
- A process is cancelled or times out while a child process remains alive.
- A process times out or is cancelled and the SDK cannot confirm that every descendant process exited.
- A managed process produces partial output before an unexpected exit.
- A consumer abandons or closes a managed process more than once.
- The Multica executable changes between discovery, compatibility validation and a later invocation.
- A login token or other secret appears in command arguments.
- A secret appears in environment variables, stdin, stdout, stderr, debug logging or object representations.
- Multiple metadata filters or subscribers require repeated flags.
- Mutually exclusive flags are provided together.
- A streaming log process exits unexpectedly.
- A short identifier is ambiguous and the CLI rejects it.
- The CLI changes locale and emits localized error text while preserving exit-code semantics.
- Environment overrides, working directory, profile or workspace values are invalid or conflict with upstream CLI defaults.
- Upstream source, pinned commit, PyPI project ownership or trusted-publishing identity is unavailable during release preparation.

## Assumptions

- The public package/distribution name is `multica-py`; the import package name is `multica_py`.
- The supported Multica command surface and exact output contracts are taken from the pinned upstream Multica CLI source code at the baseline selected during planning; `CLI_AND_DAEMON.md` is a secondary reference.
- The Multica CLI remains the authority for authentication, stored profiles, workspace resolution and server communication.
- Additive JSON fields should be tolerated for forward compatibility only when they do not change discriminators, enum values, required fields, or semantics of existing fields; missing or incompatible required fields should fail decoding.
- Interactive commands are included, but their SDK shape may be process/stream oriented rather than returning a domain model.
- The project is licensed under MIT.
- The pinned upstream source commit remains available during implementation or is retained in a local fixture/snapshot sufficient to reproduce the coverage matrix.

## Success Criteria

- **SC-001:** 100% of commands, aliases, hidden commands and deprecated commands discovered in the pinned upstream CLI source baseline appear in the CLI-to-SDK coverage matrix with source locations and one mapped, process-oriented, or explicitly unsupported outcome.
- **SC-002:** 100% of project-owned public callables, project-owned internal callables, public models, and tests pass strict mypy with no explicit or implicit `Any` allowances, excluding third-party stub internals and the explicitly untyped `multica-py exec` diagnostic passthrough.
- **SC-003:** Every structured command result is decoded into a `msgspec` model or a documented closed primitive type.
- **SC-004:** Every source-backed, reliably classifiable CLI failure category has a tested SDK exception mapping, and every unclassifiable non-zero CLI failure is tested as `CommandExecutionError` without localized-prose inference.
- **SC-005:** Clean Linux and macOS environments on Python 3.12 and 3.13 can install and execute the built package using `uv tool install` and `uvx`, add it as a library through `uv add`, and install/import it through `uv pip install` and standard `pip install`.
- **SC-006:** The default test suite completes without a Multica server, account or network connection.
- **SC-007:** CI passes Ruff format, Ruff lint, strict mypy, tests, distribution build and clean-wheel installation checks.
- **SC-008:** Starting from the top of the coverage matrix, a developer can identify the SDK method and upstream implementation/type source corresponding to any sampled Multica CLI command in under one minute.
- **SC-009:** A release candidate can be built and validated against local artifacts or TestPyPI using only documented `uv`-based contributor commands, and production PyPI publication occurs only through the approved release workflow.
- **SC-010:** The package console tool exposes `doctor`, `version`, `coverage`, and diagnostic `exec`, and each command has documented human-readable output, machine-readable output status, and exit-code behavior.
