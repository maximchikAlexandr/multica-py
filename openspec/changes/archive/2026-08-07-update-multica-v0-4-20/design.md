## Context

Planning is based on repository `main` at `c1309c852546f8d2321754a5e81bc07d34b28018`
(PR #29), after refreshing `main` from `origin/main`. The approved SDK contract
still targets Multica `v0.4.9` at
`ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`; its generated runtime sets
`TARGET_VERSION = "0.4.9"`. The new authority is released tag `v0.4.20`, commit
`93342d04a7a9f788fec921e5aa736f86c7f22d8f`, GitHub release ID `366120041`.
On the planning host, the matching `darwin-arm64` CLI archive has published
SHA-256 `2ff226b0d8c086736ad3e7ab223bf53d6cbce7e6961deadf6922e13dce4f6f08`.

Relevant current SDK behavior:

- `AgentResource` has typed eager/command pairs and returns a bound immutable
  `Agent`, but no copy operation. `AgentCreateRequest` is intentionally much
  narrower than upstream copy and is not a suitable copy-request surrogate.
- `Command[T]` already owns preview and execution. A new resource operation
  must build one `Command[Agent]`; adding a second preview path would violate
  the command-plan contract.
- `IssueResource.search()` currently decodes a top-level list directly into
  `IssueSummary`. Multica `v0.4.20` emits an object with an `issues` member, and
  search rows add `match_source`. Normal issue-list rows still use
  `_IssueSummaryWire` for `parent_issue_id`, labels, and metadata adaptation.
- `CliTransport.classify_cli_failure()` understands semantic exit codes and
  raw `returned <status>` diagnostics, but has no `ConflictError` mapping.
  `_raise_command_error()` always uses a generic string even when redacted
  stderr contains the actionable reason.
- `RuntimeResource.delete(..., cascade=True)` already emits the right flag but
  its SDK docs/tests do not state the changed preservation semantics.
- Current `AutopilotResource.trigger()` and its approved binding already emit
  `autopilot trigger`; GitHub issue #30 describes drift that predates current
  `main`, so this part is a revalidation guard rather than another rename.
- Runtime/provider/model values currently used by the SDK are strings. The
  forward-compatibility work is an audit and regression guarantee, not a new
  enum hierarchy.

Pinned upstream source establishes the implementation contract:

- `server/cmd/multica/cmd_agent_copy.go:23-289` defines copy flags, defaulted
  portable fields, cross-runtime policy, permission targets, skill behavior,
  and the rule that `custom_env`, `mcp_config`, and `runtime_config` are never
  copied.
- `server/cmd/multica/cmd_runtime.go:60-100,215-255,353-424` defines the
  conflict-first cascade flow and the unbind/preserve result semantics.
- `server/cmd/multica/cmd_issue.go:354-369,563-565,2297-2353` and
  `server/internal/handler/issue.go:234-241,546-621,726-745` define search argv,
  envelope, and open textual match-source values.
- `server/internal/cli/errors.go:154-174,318-354` defines HTTP kinds and the
  English/Chinese conflict and validation formatting used by the subprocess
  boundary.
- `server/cmd/multica/cmd_autopilot.go:56-61,98-109,146-147` confirms the
  supported trigger spelling.

## Goals / Non-Goals

**Goals:**

- Promote only the reviewed `v0.4.20` release contract and generate the exact
  default compatibility interval `[0.4.20, 0.4.21)`.
- Add an idiomatic, presence-aware agent-copy API with command preview and a
  conservative cross-runtime default.
- Preserve the existing issue-search return type while accepting both the new
  envelope and legacy array and exposing `match_source`.
- Preserve useful redacted CLI reasons in typed conflict/validation exceptions.
- Align runtime cascade documentation/tests and make the already-correct
  autopilot trigger mapping fail closed against regression.
- Keep public upstream-owned string vocabularies open and all existing quality,
  contract, typing, and packaging gates green.

**Non-Goals:**

- Import every command or response field added between `v0.4.9` and upstream
  `main`; only tagged `v0.4.20` behavior required by this change is promoted.
- Rename `autopilots.trigger()` back to `run()`, add a second search result
  wrapper, or change existing eager return types.
- Expose `custom_env`, `mcp_config`, or `runtime_config` through agent copy.
  Those fields are machine-local/secret-bearing and require a separate,
  explicitly secret-safe configuration surface.
- Reproduce the CLI's internal GET/POST copy workflow in Python, add direct HTTP
  transport, or interpret whether arbitrary future upstream strings are valid.
- Change server persistence, runtime deletion behavior, or UI-only Multica
  features.

## Decisions

### Decision 1: Upgrade the approved contract before generating runtime behavior

Run the existing maintainer pipeline with a clean checkout of tagged
`v0.4.20`, the platform-matching verified CLI binary, its exact `version
--output json` bytes, release ID, asset name, checksum, OS, and architecture.
Keep collection output under ignored `.devlocal` storage. Update
`contracts/sdk-contract.json` only after review:

1. Replace target metadata with tag/version/commit/release for `v0.4.20`.
2. Re-resolve every retained source reference at the new commit; update path,
   symbol, and line range individually rather than globally replacing commit
   strings and assuming the old ranges remain sound.
3. Add source references and complete catalogs/operations for `agents.copy`
   and `issues.search`; update `runtimes.delete`, `autopilots.trigger`, and error
   evidence/rationale.
4. Record bindings, signatures, presence, validators, response adapters, and
   canonical vectors for each newly governed operation. Handwritten dual-shape
   search decoding remains an explicit adapter policy, not generated evidence.
5. Run `validate --source-checkout`, render the tracked runtime module and
   ignored transient projections, then run `check`. Review the generated diff.

Only `contracts/sdk-contract.json` may drive
`src/multica_py/_generated/approved_sdk.py`; collected evidence and candidate
command listings remain review-only. The tracked target becomes `0.4.20` and
generation derives the exclusive next patch `0.4.21`.

Alternative considered: update generated constants and a few fixtures without
reconciling all source references. Rejected because it would advertise a tested
baseline whose approved operation evidence still points at `v0.4.9`.

### Decision 2: Add direct presence-aware agent-copy methods, not a copy request model

Add matching methods on `AgentResource`:

```python
copy_command(
    source_agent_id: str,
    *,
    name: str | UnsetType = Unset,
    runtime_id: str | UnsetType = Unset,
    description: str | UnsetType = Unset,
    instructions: str | UnsetType = Unset,
    model: str | UnsetType = Unset,
    thinking_level: str | UnsetType = Unset,
    service_tier: str | UnsetType = Unset,
    custom_args: tuple[str, ...] | UnsetType = Unset,
    max_concurrent_tasks: int | UnsetType = Unset,
    permission_mode: str | UnsetType = Unset,
    public_to_workspace: bool | UnsetType = Unset,
    public_to_member_ids: tuple[str, ...] | UnsetType = Unset,
    copy_skills: bool = True,
) -> Command[Agent]
```

`copy()` has the identical arguments and delegates to `copy_command().run()`.
This keeps the basic `copy(source_id)` call natural and avoids a new public type
used by only one operation. `Unset` is required because an empty description,
instructions, model, thinking level, or service tier is different from an
omitted flag in upstream `Flags().Changed(...)` branches.

Build argv in the signature order. Validate source ID, present name, present
member IDs, `1 <= max_concurrent_tasks <= 50`, and that `custom_args` is a
string-only `tuple[str, ...]`; reject a present empty `public_to_member_ids`
tuple because Cobra cannot
represent “changed but empty” without producing an empty member target. Encode
the present string tuple `custom_args` with deterministic compact JSON. A present
`public_to_workspace=False` is emitted as `--public-to-workspace=false` so
Cobra records the flag as changed; `True` uses the ordinary boolean flag.
Repeat `--public-to-member` in tuple order. `copy_skills=False` emits
`--no-skills`; the default emits no skill flag.

When `runtime_id` is present and `model is Unset`, append `--model ""`.
Upstream requires a changed model flag for a cross-runtime fork, and empty means
the target runtime default. This is the sole automatic runtime-specific default:
when `runtime_id` is present, omitted `thinking_level` and `service_tier` remain
absent. This makes the issue's advertised
`copy(source_id, runtime_id=target)` form succeed without an extra discovery
call. When runtime is omitted, omit `model`, `thinking_level`, and
`service_tier` unless the caller supplied each one, so the CLI can preserve
same-runtime state.

The operation deliberately has no `custom_env`, `mcp_config`, or
`runtime_config` parameters. Their absence, combined with upstream copy's
never-copy rule, makes the security boundary structurally testable and avoids
putting secret JSON in process argv or preview. `custom_args` remains included
because it is portable CLI configuration and is explicitly copied upstream.

Alternative considered: GET the source agent in an SDK composite plan to decide
whether an explicit runtime ID is actually different. Rejected because the CLI
already performs that read, it would duplicate authorization/race behavior,
and it would turn one inspectable upstream operation into two SDK subprocesses.

Alternative considered: expose all upstream secret input flags and extend
redaction. Rejected for this change because direct JSON flags remain visible to
local process inspection, while using both stdin-based secret inputs is
ambiguous in one CLI process. A future secret-safe API can design those channels
without weakening copy defaults.

### Decision 3: Use one local dual-shape search adapter and keep tuple results

Add optional `match_source: str | None = None` to both `IssueSummary` and
`_IssueSummaryWire`, transferring it in `issue_summary_from_wire`. The open
string accepts the documented values (`title`, `description`, `comment`) and
future values without a new SDK release.

Add a private `_IssueSearchResultWire` for the `v0.4.20` object envelope. The
search command uses a resource-local decoder that inspects the JSON top-level
shape:

- object: decode `_IssueSearchResultWire`, then adapt its `issues`;
- array: decode `list[_IssueSummaryWire]` for legacy compatibility;
- any other/malformed shape: raise the existing typed decode/shape error.

Both branches use `issue_summary_from_wire`; they do not decode directly into
`IssueSummary`, which would lose the existing `parent_issue_id` rename and
labels/metadata projections. Envelope `total` can be decoded privately for
shape tolerance but is not returned, because changing search from tuple to a
new page/result model would violate the compatibility acceptance criterion.

Alternative considered: add `IssueSearchResult`. Rejected because the existing
SDK contract returns a tuple and this change needs only row metadata, not a
public pagination redesign.

Alternative considered: modify the generic list decoder to accept envelopes.
Rejected because envelope keys differ across resources and broadening a shared
primitive could silently accept wrong shapes elsewhere.

### Decision 4: Classify pinned CLI messages and construct exception strings from redacted detail

Extend transport classification in this order:

1. Existing semantic process exit codes remain authoritative.
2. A raw recognized HTTP status maps to its typed class: `409` to
   `ConflictError` while retaining the actual process exit code; `400`/`422`
   to `ValidationError` with semantic reported code `5`; existing auth/not-found
   behavior remains unchanged.
3. Case-sensitive pinned formatter markers classify normal non-debug output.
   Conflict markers cover English/Chinese actionable prefixes and generic
   fallbacks from `v0.4.20`; validation markers cover the corresponding
   localized prefixes/fallbacks.
4. The exact reviewed local concurrency marker
   `--max-concurrent-tasks must be between 1 and 50` maps to
   `ValidationError`. No broad “invalid” substring heuristic is added.
5. Existing network markers and generic fallback run last.

Import and use the existing `ConflictError`; do not invent a new exit code or
exception class. In `_raise_command_error`, redact stdout/stderr first, then
choose `stderr.strip()`, otherwise `stdout.strip()`, otherwise the existing
generic message. This selected safe detail becomes the exception message, so
`str(exc)` is actionable. The full redacted streams and redacted argv remain on
the exception; the actual argv is supplied only to the executed subprocess and
is never retained in exception diagnostics or previews. Command execution,
compatibility preflight, timeout, semaphore, and `Command[T]` execution paths
do not change.

Alternative considered: parse server JSON in the SDK. Rejected because this SDK
is CLI-only and ordinary CLI output has already been localized/formatted; JSON
is only available in debug/raw variants. Exact pinned prefixes plus raw status
support cover both modes without creating an HTTP coupling.

Alternative considered: use stderr only as an attribute and retain the generic
exception string. Rejected because issue #30 explicitly requires useful detail
from `str(exc)`, which is also the common logging path.

### Decision 5: Preserve open upstream strings through audit and focused tests

Do not add enums for runtime provider, model, thinking level, service tier, or
match source. Retain `RuntimeUsage.provider/model` as strings and use string
overrides in copy. Review generated contract enum candidates before promotion;
none of these runtime-owned vocabularies becomes a strict SDK validator.

The SDK still validates structural invariants it owns (nonblank identifiers,
concurrency range, tuple item types). Runtime/model compatibility remains an
upstream decision whose returned validation reason is preserved by Decision 4.

Alternative considered: snapshot all currently known provider/model values in
`StrEnum`s. Rejected because runtime discovery makes those sets explicitly
open and a closed decoder would turn a valid new upstream integration into an
SDK protocol failure.

### Decision 6: Treat autopilot trigger as a baseline revalidation, not new API work

Keep `AutopilotResource.trigger`, its command method, binding descriptor,
canonical vector, migration documentation, and generated mapping. Update their
source references to `v0.4.20` and add a negative source-contract assertion that
`autopilot run` cannot reappear. Do not add aliases: two public spellings would
weaken canonical discovery and revive the migration ambiguity already resolved
on `main`.

### Decision 7: Extend existing table-driven verification and documentation

Add canonical/variant rows to `tests/cases/operations.py` for copy and update
the search fixture from a bare array to the `v0.4.20` envelope. Put repeated
decode variants into frozen case tables in the existing issue-model/resource
test modules. Extend `tests/unit/test_transport.py` with a frozen failure-case
matrix for statuses, localized prefixes, local validation, detail selection,
and redaction. Keep runtime argv coverage in the existing resource case tables
and assert preservation semantics in docs/contract tests, since the SDK cannot
observe server persistence through an offline fake CLI.

Update `docs/api.md`, `docs/compatibility.md`, `docs/migration.md`,
`docs/service-usage.md` where relevant, generated approved SDK documentation,
and provenance/compatibility fixtures. Historical archived OpenSpec artifacts
may continue mentioning their original baseline; current docs/specs and active
contract expectations must not.

## Risks / Trade-offs

- **[Risk] Contract-wide source-reference churn hides a stale operation.** →
  Re-resolve refs individually against the exact tag, require
  `validate --source-checkout`, and review deterministic generated diffs before
  `check`.
- **[Risk] Localized CLI wording changes in a later release.** → Pin exact
  `v0.4.20` markers with tests, keep raw-status classification, and require a
  new reviewed baseline before accepting later wording.
- **[Risk] Automatically adding `--model ""` for an explicit runtime can reset
  a model even when the caller supplies the same runtime ID.** → Document that
  an explicit runtime selects the target-runtime model default only when model
  is omitted; omitted thinking-level and service-tier flags remain absent, and
  callers wanting unchanged same-runtime behavior omit `runtime_id`.
- **[Risk] Supporting two search wire shapes increases adapter complexity.** →
  Keep the branch private and local to search, reuse one row converter, and
  reject every top-level shape other than object/array.
- **[Risk] Actionable stderr may contain secrets or noisy debug content.** →
  Select detail only after existing redaction, retain redacted attributes, and
  keep the empty-detail generic fallback.
- **[Risk] Excluding secret copy overrides limits one-call cloning.** → This is
  intentional: portable cloning works now, while secret/machine-local setup is
  explicit and cannot leak into preview/process argv by surprise.
- **[Risk] GitHub issue #30's autopilot description is stale relative to
  `main`.** → Treat current `trigger` behavior as the required end state and add
  regression evidence instead of applying a redundant rename.

## Migration Plan

1. Collect ignored `v0.4.20` source/binary evidence and reconcile the approved
   contract, source refs, operation catalogs, target metadata, and generated
   runtime compatibility projection.
2. Add agent-copy API/contract mappings, dual-shape issue-search adaptation,
   open `match_source`, and transport error classification/detail selection.
3. Update table-driven tests, source-validation mutations, compatibility and
   provenance fixtures, and public/maintainer documentation.
4. Run focused tests while iterating, then `validate --source-checkout`, two
   deterministic renders with a clean diff comparison, `check`, Ruff, both
   mypy targets, package validation, offline collection exclusion, and the full
   `pytest -m "not live"` gate.
5. Deliver as one feature branch/PR. No data migration or server rollout is
   required; the SDK remains CLI-only.

Rollback is a normal Git revert of the SDK/contract change. It restores the
`v0.4.9` compatibility claim and removes the new public copy/match-source
surface; it does not mutate Multica server data. Do not partially roll back
only generated constants while leaving the approved contract or docs at
`v0.4.20`.

## Open Questions

None. The tagged source resolves command flags, presence semantics, response
shape, cascade behavior, error prefixes, and the autopilot spelling. Secret
copy inputs and a public paged search result are explicit non-goals for this
change rather than deferred implementation choices.
