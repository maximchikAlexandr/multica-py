## Context

The repository is a synchronous typed Python wrapper over an installed Multica
CLI. Public operations are expressed as eager resource methods and lazy
`Command` builders; JSON is decoded with msgspec, presence-sensitive inputs use
`Unset`, errors pass through a sanitized CLI boundary, and public coverage is
generated only from the reviewed `contracts/sdk-contract.json`.

The approved code base is exact SDK commit
`b268e3bec0436fe51727fda50583344f57663284`. Its contract targets CLI `0.7.1`
at upstream commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` and supports the
existing floor beginning at CLI `0.6.2`. The target is stable CLI `0.8.0` at
upstream commit `9b1ab4f9eed9153a94719596eb8a728d2770f065`. The verified
range contains new workflow and runtime operations, a public rerun replacement,
steering/force-stop inputs, additive response fields, and several validation,
diagnostic, and filesystem-semantics changes.

The issue's release/source/binary/help/response audit is review evidence. It
must be reproduced by implementation, but no extractor output can approve an
enum, method name, model, error, or compatibility claim. The planning-only
`0.7.2` work may inform intermediate facts but is neither the branch base nor a
generation input.

## Goals / Non-Goals

**Goals:**

- advance one reviewed direct compatibility contract from `0.7.1` to `0.8.0`;
- add the approved CLI-backed workflow, project-workflow, runtime-concurrency,
  rerun-task, steering, and force-stop surface with stable typed behavior;
- preserve omission/null/empty/zero distinctions, open upstream vocabularies,
  sanitized errors, and exact argv semantics;
- keep generation deterministic, case coverage complete, verification layered,
  and release evidence tied to one exact candidate revision.

**Non-Goals:**

- a direct HTTP client or bypass around the CLI;
- automatic public API generation from help, source heuristics, release notes,
  or response audit files;
- quick-create assignee-picker, hidden/root commands, UI/desktop/provider-only
  behavior, or server operations lacking a reviewed public CLI surface;
- a second validator, subprocess abstraction, workflow engine, model registry,
  E2E framework, evidence store, or background service;
- implementation, test execution, package publication, or issue topology
  mutation during planning.

## Decisions

### Decision 1: Keep one reviewed contract and generator pipeline

Implementation SHALL update the existing contract schema/records and render the
existing generated projection. It SHALL reproduce the target collector and
response review into ignored paths, compare those facts with the approved
contract, and then edit only reviewed contract input. Source-link, closure,
mutation, and deterministic-regeneration assertions SHALL fail closed on gaps.

Alternative: generate methods directly from the verified CLI tree. Rejected
because help does not prove destinations, presence, response envelopes,
privacy, or stable public names.

### Decision 2: Extend existing resources instead of adding architecture

Add one `WorkflowResource` following existing resource/eager/lazy conventions,
bind it on `MulticaClient`, add workflow get/set to `ProjectResource`, runtime
concurrency to `RuntimeResource`, rerun-task to `IssueResource`, steering to
the existing issue-comment add pair, and force to the daemon stop pair. Reuse
`Command`, `BaseResource`, argv helpers, msgspec models, `Unset`, process result,
and sanitized exceptions.

Alternative: create a generic dynamic endpoint client. Rejected because it
would weaken typed discovery and introduce a second transport contract.

### Decision 3: Treat workflows as typed structures with open vocabularies

Workflow, step, handoff, mapping, and conflict payloads SHALL be dedicated
immutable models, but server-owned status keys, actor/handler kinds, transition
labels, and future variants SHALL remain strings unless the target CLI itself
enforces a closed set. File inputs remain paths; secret or instruction content
must not enter previews, errors, or generated fixtures.

Alternative: closed Python enums for all observed values. Rejected because
workspaces can define statuses and future servers can add handler variants.

### Decision 4: Make rerun replacement explicitly breaking

Remove `rerun`/`rerun_command` and their generated `issue rerun` row. Add
`rerun_task`/`rerun_task_command` for the public target command and canonical
task-run result. Migration documentation names the changed identity, flags,
result, and required CLI version. No legacy alias calls the new command.

Alternative: retain `rerun()` and change its return type. Rejected because that
would silently alter command identity and output for existing callers.

### Decision 5: Put presence and safety at existing boundaries

Runtime concurrency uses `int | None`, validates exact integers in `1..50`,
and maps `None` to `none`. Task credits remain exact optional integers.
Attachment sequences emit repeated literal argv pairs. Steering reuses existing
content-source validation and adds an attachment conflict. Force-stop adds one
boolean flag and leaves PID/profile/child safety entirely to the CLI. Warnings
remain stderr/process metadata; JSON remains stdout.

Alternative: SDK-side process killing, CSV attachment serialization, warning
parsing, or implicit coercion. Rejected because each would diverge from target
CLI semantics or cross a safety boundary.

### Decision 6: Extend shared tables and CI gates

Use the existing `ArgvCase`, `DecodeCase`, `CommandCase`, contract mutation,
public-discovery, compatibility, live-smoke, packaging, and documentation
checks. Add rows for workflow variants, limits, null/omission, malformed data,
rerun migration, steering receipts/races, force-stop failures, literal paths,
warning separation, privacy, and target error boundaries. Update contract and
live-smoke source/version pins to the exact target revision. Do not add a new
test framework.

Alternative: one new test module per command. Rejected because repository rules
require row-oriented reuse and one completeness inventory.

### Decision 7: Ponytail full gate

No new product subsystem is necessary. The only new top-level public component
is the required workflow resource; its existing alternative is raw CLI use,
which would leave an approved public family untyped, so it remains. New
workflow models are necessary to preserve structured results; a generic JSON
dictionary alternative would weaken the SDK contract, so the minimal dedicated
models remain. One stdlib E2E orchestration helper is necessary because the
provided stand has fixed shared ports/profile state and force-stop evidence
must prove exact child ownership; its alternative is an undocumented sequence
of manual mutations, which cannot enforce a stand lease or reliable failure
cleanup, so the narrow helper remains. Its daemon mode is an explicit
human-local gate: it preserves task identity, refuses daemon-managed execution,
and uses a recorded dedicated foreground child plus POSIX `SIGSTOP` to make the
graceful path deterministically time out before observing the target CLI's
forced-termination/unconfirmed-cleanup result. Agent-safe fixtures cover argv,
human-local refusal, mismatch refusal, and error propagation; they never
impersonate a human or signal a daemon. A direct HTTP client, second generator,
second validator, custom process manager, background runner, parallel E2E
framework, and evidence database are unnecessary and removed from the plan.
All other work extends existing modules and tables.

## Risks / Trade-offs

- **Workflow payload details can drift** → pin every model and operation to
  exact source URLs and malformed/unknown-value fixtures; keep owned vocabularies
  open.
- **Removing rerun breaks existing callers** → make the removal explicit,
  document the replacement, and test that no stale export or inventory row
  remains.
- **Force-stop can be destructive** → expose only the reviewed CLI flag and
  prove the SDK never performs local discovery, signaling, or cleanup.
- **Warnings can corrupt JSON decoding** → keep stdout/stderr separated and add
  successful-warning fixtures around repository checkout.
- **Large inventory edits can create false coverage** → require exact closure,
  source-link, mutation, deterministic generation, and public-discovery gates.
- **Live environment may not yet provide CLI `0.8.0`** → treat missing exact
  target readiness as a verification blocker; never relabel a lower-version run
  as target evidence.

## Migration Plan

1. Reproduce target provenance, command inventory, response review, and exact
   source references in ignored evidence locations.
2. Update the reviewed contract/schema and deterministic generated projection;
   prove closure before editing public resources.
3. Add workflow models/resource, project bindings, runtime concurrency and
   response fields, rerun-task migration, steering, force-stop, and adapted
   validation/diagnostic behavior through existing layers.
4. Extend shared unit/component/contract/compatibility/package/documentation
   tables and update exact target pins.
5. Run focused gates, then the permitted complete offline/CI gates at one clean
   revision; independent Tester evidence uses the isolated project stand and
   exact candidate without changing source.
6. Publish normal commits and preserve the candidate branch/PR. Roll back with
   an ordinary revert that restores contract, generated output, resources,
   models, tests, pins, and docs atomically.

## Open Questions

None. All public-surface, migration, enum-openness, and exclusion decisions are
fixed by this design; implementation SHALL not substitute alternative behavior.
