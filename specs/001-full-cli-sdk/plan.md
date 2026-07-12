# Implementation Plan: Complete Python SDK for Multica CLI

**Feature:** `001-full-cli-sdk`  
**Repository:** `maximchikAlexandr/multica-py`  
**Upstream baseline:** `multica-ai/multica@48b8dbf43971e5ea974bf827220cd212a1240c72`  
**Baseline date:** 2026-06-22  
**Implementation source of truth:** upstream Go CLI source at the pinned commit, not prose documentation.

## 1. Final architecture decisions

The package is a thin, synchronous Python wrapper around the installed `multica` binary. It does not call Multica HTTP APIs, does not replicate server behavior, and does not install the Multica binary.

Public structure:

```text
MulticaClient
├── auth
├── setup
├── daemon
├── workspaces
├── issues
│   ├── comments
│   ├── metadata
│   └── subscribers
├── projects
├── labels
├── agents
│   └── skills
├── autopilots
│   └── triggers
├── skills
│   └── files
├── repositories
├── runtimes
├── attachments
├── configuration
└── maintenance
```

Internal structure:

```text
resource method
  -> immutable request model
  -> argument builder
  -> CliTransport
  -> subprocess without shell
  -> output classifier
  -> msgspec decoder
  -> immutable result model
```

Decisions are fixed as follows:

- Import package: `multica_py`.
- PyPI distribution: `multica-py`.
- Console entry point: `multica-py`.
- Primary installation: `uv tool install multica-py`.
- Primary ephemeral execution: `uvx multica-py`.
- Library use: `uv add multica-py`.
- Compatibility installation: `uv pip install multica-py` and `pip install multica-py`.
- Minimum Python: 3.12.
- Build backend: `hatchling`, invoked through `uv build`.
- Runtime dependencies: `msgspec` only.
- Test runner: `pytest` plus standard-library fakes; no live server in default CI.
- Type checker: strict mypy with `disallow_any_expr`, `disallow_any_decorated`, `disallow_any_explicit`, `disallow_any_generics`, and `warn_return_any` enabled.
- Linter/formatter: Ruff; Odoo-only isort sections removed; `COM812` ignored.
- Public models: frozen `msgspec.Struct` classes.
- Public enums: `enum.StrEnum` or `enum.IntEnum`, never unconstrained strings for finite choices.
- No async public client in v1. Temporal/FastAPI callers run the synchronous SDK inside their normal worker/thread boundary. An async wrapper would duplicate cancellation semantics and is out of scope.
- No Active Record methods. Models contain data only.
- Unknown additive JSON fields are ignored by `msgspec`; missing or incompatible required fields fail decoding.
- Commands without stable JSON output return explicit text/process models, not invented domain models.

## 2. Repository layout

```text
multica-py/
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE
├── CHANGELOG.md
├── src/multica_py/
│   ├── __init__.py
│   ├── py.typed
│   ├── client.py
│   ├── config.py
│   ├── exceptions.py
│   ├── enums.py
│   ├── sentinels.py
│   ├── types.py
│   ├── compatibility.py
│   ├── provenance.py
│   ├── process.py
│   ├── _generated/
│   │   └── cli_manifest.json
│   ├── _internal/
│   │   ├── argv.py
│   │   ├── concurrency.py
│   │   ├── decoders.py
│   │   ├── executable.py
│   │   ├── manifest.py
│   │   ├── processes.py
│   │   ├── redaction.py
│   │   ├── specs.py
│   │   └── transport.py
│   ├── cli/
│   │   ├── main.py
│   │   ├── doctor.py
│   │   ├── version.py
│   │   ├── coverage.py
│   │   └── exec.py
│   ├── models/
│   │   ├── common.py
│   │   ├── auth.py
│   │   ├── daemon.py
│   │   ├── workspaces.py
│   │   ├── issues.py
│   │   ├── issue_activity.py
│   │   ├── projects.py
│   │   ├── labels.py
│   │   ├── agents.py
│   │   ├── skills.py
│   │   ├── autopilots.py
│   │   ├── system.py
│   │   └── runtime.py
│   └── resources/
│       ├── _base.py
│       ├── auth.py
│       ├── setup.py
│       ├── daemon.py
│       ├── workspaces.py
│       ├── issues.py
│       ├── issue_comments.py
│       ├── issue_metadata.py
│       ├── issue_subscribers.py
│       ├── issue_labels.py
│       ├── projects.py
│       ├── labels.py
│       ├── agents.py
│       ├── agent_skills.py
│       ├── skills.py
│       ├── skill_files.py
│       ├── autopilots.py
│       ├── autopilot_triggers.py
│       ├── repositories.py
│       ├── runtimes.py
│       ├── attachments.py
│       ├── squads.py
│       ├── users.py
│       ├── configuration.py
│       └── maintenance.py
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── fixtures/upstream-48b8dbf/
│   └── fake_multica.py
├── scripts/
│   ├── audit_upstream.py
│   └── verify_coverage.py
├── docs/
│   ├── coverage.md
│   ├── compatibility.md
│   └── contributing.md
└── .github/workflows/
    ├── ci.yml
    ├── upstream-drift.yml
    └── publish.yml
```

## 3. Client and configuration contract

`MulticaClient` owns one immutable `ClientConfig` and constructs each resource exactly once. Resources hold only a reference to the shared transport.

`ClientConfig` fields are fixed:

- `executable: pathlib.Path | str = "multica"`
- `server_url: str | None`
- `workspace_id: str | None`
- `profile: str | None`
- `cwd: pathlib.Path | None`
- `environment: Mapping[str, str]` copied into an immutable internal tuple
- `timeout: datetime.timedelta | None`
- `compatibility: CompatibilityPolicy`
- `debug: bool = False`
- `encoding: str = "utf-8"`

Global CLI flags are emitted after the executable and before the command family in this order:

```text
multica [--server-url X] [--workspace-id X] [--profile X] <family> ...
```

This order mirrors `server/cmd/multica/main.go` and remains stable in SDK snapshots.

## 4. Transport behavior

`CliTransport` has exactly three execution modes:

1. `run_json(args, decoder, *, stdin=None, timeout=None)`
2. `run_text(args, *, stdin=None, timeout=None)`
3. `spawn(args, *, stdin=None)` for foreground/follow/interactive operations

Rules:

- Always call `subprocess.Popen`/`subprocess.run` with an argument sequence and `shell=False`.
- Create a new process group/session so cancellation terminates descendants.
- On timeout, send graceful termination, wait 2 seconds, then force kill.
- Decode stdout/stderr as UTF-8 with strict errors. Invalid UTF-8 is a protocol failure.
- Never parse localized or human-readable stderr to infer domain errors. Domain subclasses are used only when the pinned source, exit status, or a stable machine-readable envelope permits reliable classification.
- Preserve raw stdout and stderr on every raised command exception.
- Redact token values and arguments for `login --token`, but execute with the original value.
- `--output json` is appended only to commands whose source defines the flag or whose implementation explicitly supports JSON.
- Empty successful output decodes to the operation-specific `EmptyResult`, never `None` unless the public method is explicitly declared `-> None`.

## 5. Error taxonomy

```text
MulticaError
├── ExecutableNotFoundError
├── ExecutableNotRunnableError
├── UnsupportedCliVersionError
├── CommandTimeoutError
├── CommandCancelledError
├── CommandExecutionError
│   ├── AuthenticationError
│   ├── AuthorizationError
│   ├── NotFoundError
│   ├── ConflictError
│   ├── ValidationError
│   ├── NetworkError
│   └── UnknownCommandError
└── ProtocolError
    ├── JsonOutputError
    ├── OutputShapeError
    └── EncodingError
```

Because upstream currently exits through Cobra with a general non-zero status, domain subclasses are assigned only where the pinned source or stable JSON error envelope permits exact classification. Otherwise the SDK raises `CommandExecutionError`; it must not guess from localized prose. This is safer than claiming an unsupported exit-code taxonomy.

## 6. Command coverage strategy

The SDK covers every command registered by `server/cmd/multica/main.go` at the pinned commit. The canonical matrix is `contracts/cli-coverage.md`.

Implementation order is fixed by dependency:

1. Core infrastructure: config, transport, errors, decoding, version probe.
2. MVP issue-family slice: client/resource scaffolding, issue models, issue read/write operations, nested issue comments/metadata/subscribers/runs, fixtures, and integration tests.
3. Broad read-only structured resources: workspace, project, label, agent, skill, repository, runtime, attachment, configuration, squad, user, auth, daemon, setup, and maintenance models.
4. Mutations and process-oriented operations for the same broad resource families.
5. Autopilot and triggers.
6. Safe automation support: client cloning, per-client process concurrency, service examples, and compatibility tests.
7. Console entry point and passthrough diagnostic commands.
8. Packaging, documentation, release, coverage audit, and drift automation.

No command family may be declared complete until its command registration, flags, validation, output branch, and source-defined response structs have contract tests.

## 7. Source-driven implementation procedure

For each command method, the implementer must perform the following checklist and record it in the coverage matrix:

1. Read the Cobra command declaration (`Use`, `Args`, aliases, subcommands).
2. Read the entire `run...` implementation.
3. Record every flag, shorthand, default, repeated flag, and mutually exclusive group from `init()`.
4. Trace calls into `server/internal/cli` and record request/response structs.
5. Record whether output is table, JSON, plain text, binary/file, interactive, or stream.
6. Copy enum values from source-defined validation lists.
7. Create the exact SDK request and response models.
8. Add command-construction tests and decoder fixtures.
9. Run the fake executable integration test.
10. Mark the matrix row complete only after all checks pass.

The upstream baseline is immutable for v1. A separate drift workflow compares a newer upstream checkout to the pinned manifest; it does not silently alter v1 models.

## 8. Model design

All domain models are `msgspec.Struct(frozen=True, kw_only=True)`. Model fields mirror JSON keys using `rename` where Go JSON names differ from Python naming.

Closed primitive aliases:

```text
MetadataValue = str | int | float | bool | None
Identifier = NewType wrappers only where they improve overload safety
Timestamp = datetime.datetime
Duration = datetime.timedelta only after parsing source format
```

Identifier wrappers are not used as dozens of runtime classes. Public IDs remain `str` unless two same-position IDs would otherwise be easy to swap; request models use explicit field names for safety.

Lists returned by the public SDK are immutable tuples. Arbitrary server metadata uses recursive closed JSON types:

```text
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | tuple[JsonValue, ...] | dict[str, JsonValue]
```

`dict[str, JsonValue]` is permitted; `Any` is not.

## 9. Resource method conventions

- Read: `list`, `get`, `search`, `children`, `runs`, `messages`.
- Create: `create(request: CreateXRequest) -> X`.
- Update: `update(id, request: UpdateXRequest) -> X`.
- Delete/archive actions: return `ActionResult` when upstream JSON provides one, otherwise `None` with raw diagnostics available only through exceptions.
- Action names remain explicit: `set_status`, `assign`, `rerun`, `cancel_task`, not generic `execute`.
- Optional CLI flags are represented by `msgspec.UNSET` through dedicated patch request structs so “omit” differs from “clear”. Public patch fields use `UnsetType | T`; the alias is exported as `Unset`.
- Repeated flags take tuples.
- Mutually exclusive flag groups are represented by separate request variants whenever the pinned source, CLI help, or SDK request type identifies the exclusivity; otherwise the uncovered constraint must be recorded in the coverage matrix.

Example design decision:

```text
IssueDescriptionInput = InlineDescription | FileDescription | StdinDescription | NoDescription
```

The implementer does not decide this later.

## 10. Interactive and streaming commands

The following are process-oriented, not ordinary domain methods:

- browser login without token;
- setup flows that prompt;
- daemon start in foreground;
- daemon logs with follow;
- CLI update when it replaces the executable;
- commands that open external browser/UI if present in source.

They return `ManagedProcess`, which supports:

- `pid`
- `poll()`
- `wait(timeout)`
- `terminate()`
- `kill()`
- iterators `stdout_lines()` and `stderr_lines()`
- context-manager cleanup

No asynchronous iterator is included in v1.

## 11. Console entry point

`multica-py` is an SDK utility, not a competing clone of the Multica CLI. Its fixed commands are:

```text
multica-py doctor
multica-py version
multica-py coverage
multica-py exec -- <multica arguments>
```

- `doctor` verifies Python package, `multica` executable, CLI version, authentication status, and configured profile/workspace.
- `version` prints SDK and detected CLI versions.
- `coverage` prints the pinned upstream baseline and implemented command coverage.
- `exec` is an explicitly untyped escape hatch returning the child exit code; it is for diagnostics only and is not part of the typed SDK guarantee.

The tool does not replicate every Multica command because that would add a second CLI surface to maintain.

## 12. Packaging and release

`pyproject.toml` decisions:

- backend: `hatchling.build`;
- source layout under `src/`;
- dynamic version is not used;
- version is stored in `project.version` and changed by release PR;
- classifiers include Python 3.12/3.13, MIT, typed;
- wheel includes `py.typed`;
- scripts: `multica-py = multica_py.cli:main`.

Release workflow:

1. Trigger only on GitHub release publication.
2. `uv sync --frozen --all-groups`.
3. Run full CI.
4. `uv build`.
5. Install wheel with `uv tool install --from dist/*.whl multica-py` and run `multica-py version`.
6. Install wheel in a clean venv with `python -m pip install dist/*.whl` and import `multica_py`.
7. Publish with PyPI trusted publishing using `uv publish`.
8. Never publish from ordinary branch pushes.

## 13. Ruff configuration decisions

Start from the supplied Ruff rules, then:

- remove `external = ["OLS"]`;
- remove Odoo and Odoo-addons isort sections;
- use standard section order;
- keep `COM` selected but add `COM812` to ignore;
- remove gettext-specific `INT` because the SDK has no gettext integration;
- remove executable-script `EXE` because package entry points are generated from metadata;
- retain BLE, C, E, EM, F, FA, FLY, G, I, ICN, ISC, LOG, PGH, PIE, PLC, PLE, PLW, PYI, RET, RUF, SIM, SLOT, T, TC, TID, TRY, UP, W, YTT;
- add `ANN` is unnecessary because mypy strict is authoritative and Ruff annotation rules conflict with overloads and test fixtures;
- test files may ignore `S101` only if `S` is later enabled; `S` is not enabled in v1.

## 14. CI matrix

Required jobs:

- `lint`: Ruff check and format check.
- `types`: mypy strict over `src`, `tests`, and `scripts`.
- `unit`: Python 3.12 and 3.13.
- `contract`: compare all method command snapshots to pinned fixtures.
- `build`: wheel and sdist, metadata validation.
- `install-uv-tool`: install local wheel as uv tool and run doctor/version against fake executable.
- `install-uvx`: run local wheel through `uvx --from`.
- `install-pip`: clean venv installation and import.
- `coverage-manifest`: fail if a registered upstream command has no matrix row.

No Windows support is promised in v1 beyond commands whose upstream CLI itself is cross-platform. CI runs Linux and macOS. Windows support is deferred until daemon/process-group behavior is implemented and tested natively; this is an explicit scope decision, not left to implementers.

## 15. Testing strategy

The fake executable is a Python script named `multica` placed first on PATH. It:

- records argv and stdin as JSON Lines;
- selects response fixtures by exact argv pattern;
- emits stdout/stderr bytes;
- controls exit codes, delays, signals, and child processes;
- supports streaming fixtures.

Tests are divided into:

- argument contract tests for every method;
- decoding tests for every model family;
- negative decoder tests for missing/type-changed fields;
- timeout/cancellation/process-tree tests;
- redaction tests;
- package installation tests;
- optional real-CLI smoke tests behind `MULTICA_REAL_CLI=1`.

The default suite never authenticates or contacts Multica.

## 16. Compatibility policy

- SDK `1.x` targets the pinned CLI baseline and later upstream versions that preserve required JSON fields and command syntax.
- At client initialization, no subprocess is spawned.
- `client.maintenance.cli_version()` probes on demand.
- `CompatibilityPolicy.STRICT` requires a configured minimum and maximum tested CLI version.
- `WARN` allows newer versions and emits a typed warning.
- `IGNORE` skips version validation.
- Older CLI versions that lack a called command raise `UnsupportedCliVersionError` before execution when the capability manifest can determine it; otherwise `UnknownCommandError` wraps the CLI failure.

## 17. Implementation phases

### Phase A — foundation

Create package metadata, uv groups, Ruff, mypy, base CI, config, transport, exceptions, msgspec codec, fake executable.

**Exit:** package metadata, base CI checks, transport/error/decoder tests, manifest audit, and a local typed version command pass. Full installation-path validation is completed in Phase G.

### Phase B — MVP issue-family slice

Implement `MulticaClient`, base resources, issue models, issue read/write operations, comments, metadata, subscribers, runs/messages/usage, fixtures, and integration tests.

**Exit:** the issue family is usable end to end through typed resource methods with source-linked fixtures and tests.

### Phase C — broad read models

Implement workspace, project, label, agent, skill, repository, runtime, attachment, configuration, squad, user, auth, daemon, setup, and maintenance models and read/status/version operations.

**Exit:** read-only and status/version command families have source-linked coverage.

### Phase D — broad mutations and process commands

Implement create/update/delete/archive/restore/file operations, auth/login/setup/daemon/update process operations, and `ManagedProcess`.

**Exit:** all non-autopilot finite and process-oriented command families are covered.

### Phase E — automation surface

Implement autopilot, triggers, repository, runtime, attachment, configuration.

**Exit:** autopilot and trigger commands are complete and the registered command matrix has no omissions.

### Phase F — service safety and console tool

Implement client cloning, per-client process concurrency, service examples, compatibility tests, and the `multica-py` utility commands.

**Exit:** orchestration-safety tests pass and `doctor`, `version`, `coverage`, and diagnostic `exec` are documented and tested.

### Phase G — release readiness

Documentation, upstream audit script, local wheel uv-tool/uvx/pip checks, trusted publishing.

**Exit:** publishable `1.0.0` candidate.

## 18. Constitution check

Constitution file exists at `.specify/memory/constitution.md` and is version 1.0.0.
The plan satisfies the active principles:

- Source-driven CLI contract: pinned upstream commit is recorded and coverage/model provenance tasks are required.
- Thin synchronous wrapper: the SDK remains subprocess-based, synchronous, and process-handle based for streaming/interactive commands.
- Typed public surface: runtime models use frozen `msgspec`, strict mypy rejects `Any`, and unclassifiable failures remain generic.
- Offline testability and provenance: default tests use pinned fixtures and a deterministic fake executable, with no live server requirement.
- Secure packaging and release: `uv` workflows, Trusted Publishing, installation checks, and secret redaction are required.

## 19. Remaining risks

Only two external risks remain; neither is left as an implementation design choice:

1. Some upstream commands may not provide stable JSON output. They are handled as `TextResult` or `ManagedProcess`, not modeled speculatively.
2. The user repository could not be inspected from this environment. The plan assumes a new or minimally initialized repository. Existing conflicting files must be reconciled mechanically with this layout, not used to change the architecture.
