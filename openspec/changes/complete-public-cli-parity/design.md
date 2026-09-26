## Context

The implementation base is `d1b5f0e154c5587eca4cebd8bd2a6d39ae3d4d06`.
The approved contract already pins Multica `v0.5.3` at
`ff8b285497809e084915016c40c2bc5e5991ffbc`, but its 164 operations and 167
response review rows describe the historically approved SDK subset, not the
full public CLI. The pinned collector identifies 196 command-registration
edges, 895 declarative flag registrations, dynamic wakeup construction, aliased
daemon flags, and review-only source patterns that require human resolution.
Recursive source/help review found existing typed operations with invalid argv
or incompatible output shapes, public leaves without typed APIs, omitted
behavioral inputs, and public records whose nested fields are discarded.

The current architecture is a sound foundation: immutable public models,
resource classes, `Command[T]` plans, one controlled `CliTransport`, explicit
execution modes, frozen table-driven operation cases, and an approved contract
that alone may drive deterministic generation. The design extends those
mechanisms. It does not make extractor output authoritative.

## Goals / Non-Goals

**Goals:**

- Close every public CLI capability, input, transport, output, nested-field,
  acknowledgement, pagination, and error gap at the pinned target.
- Make the inventory mechanically closed: no public partial, unknown, deferred,
  or unreviewed item can pass strict validation.
- Correct false advertised contracts before expanding the surface.
- Reuse existing resources, models, command plans, transport modes, generated
  approved bindings, and test tables.
- Preserve presence, redaction, secret opt-in, process lifecycle, and version
  compatibility semantics explicitly.
- Keep evidence regeneration reproducible while excluding binaries, source
  checkouts, and transient reports from Git and distributions.

**Non-Goals:**

- No server-only fields or hidden/internal commands.
- No duplicate SDK methods for aliases, help parents, table-only formatting, or
  an already proven equivalent operation.
- No automatic generation from unreviewed source/help evidence.
- No Go interpreter, workflow engine, universal resource abstraction, second
  runtime registry, checkout-registry clone, or new runtime dependency.
- No destructive live daemon/auth actions on a developer machine.
- No async SDK redesign; streaming and interactive coverage stays within the
  existing managed-process/executor model.

## Decisions

### Decision 1: Extend the approved contract with one closed parity inventory

`contracts/sdk-contract.json` remains the sole production authority. Its schema
gains a versioned public-CLI inventory whose stable identity is command path plus
input/output facet. Each row stores pinned source/help references, public/hidden
state, positional and effective flag facts, mapping or transport, response
contract, disposition, compatibility, and test references. Contract validation
checks uniqueness, complete public coverage, allowed disposition evidence, and
references to existing approved operations or explicit transport entries.

The collector remains a declarative landing zone. A small reconciliation layer
resolves known command variables, `AddCommand` edges, wakeup factories, inherited
and aliased flags, and the concrete output path. Anything else becomes a
blocking review item. The renderer consumes only reviewed inventory and
operation data.

Alternative: keep a separate parity spreadsheet/report. Rejected because it
would drift from the production contract and could not close generated and
handwritten discovery in CI.

### Decision 2: Implement in contract-first vertical slices

The first implementation slice freezes the complete inventory and removes all
unknowns. The second corrects A1–A10 and provides native regression fixtures so
subsequent work builds on truthful transports and models. Remaining slices add
typed operations, missing inputs, response fields, and final closure gates by
resource family. Each slice updates the approved contract, public code,
table-driven tests, and documentation together; no operation is declared
covered before all four agree.

Alternative: add missing methods first and reconcile later. Rejected because
the issue explicitly requires inventory-first work and current passing tests can
encode SDK-invented shapes rather than CLI behavior.

### Decision 3: Reuse resource boundaries and add only three new families

Existing resources receive operations and inputs in their natural domain:
repository checkout on repositories; env and additive skills under agents;
workspace, squad, issue timeline, autopilot rotation, attachment, daemon, auth,
project, skill, comment, and user changes in their current modules. New
`chats`, `issue_wakeups`, and `runtime_profiles` resources/models are introduced
because those are coherent public CLI families with their own identity and
lifecycle. Client wiring and package exports follow existing resource patterns.

No one-method interfaces, service factories, or generic CRUD resource layer are
introduced. Shared behavior is extracted only for repeated concrete needs:
safe content materialization, daemon launch configuration, and inventory
validation.

Alternative: generate every public resource method from the inventory.
Rejected because current repository rules require reviewed operations to drive
generation and retain handwritten adapters for transport and wire normalization.

### Decision 4: Model semantic inputs, not CLI spelling variants

Public signatures expose domain values and explicit presence. File/stdin/inline
spelling variants share one safe content input that can represent text, bytes,
a path, or a caller-owned binary stream as required by the concrete leaf. It
materializes or streams only during command execution, participates in secret
redaction, and produces the exact reviewed argv/stdin channel. Daemon start and
restart share one frozen launch-options model for global and leaf lifecycle
controls. `Unset` remains the omitted-state mechanism whenever `None`, empty,
zero, or false have distinct semantics.

Alternative: mirror every Cobra flag with a separate Python method or overload.
Rejected because that duplicates transport spellings and obscures atomic and
presence behavior.

### Decision 5: Transport and result types must be truthful

Each operation declares one existing plan execution mode: decoded bytes,
decoded text, raw bytes, spawn/managed process, or a terminal-capable process
extension when interactive input is required. `--output json` is permitted only
where effective help/source proves it. Text, path, and lifecycle operations do
not receive fabricated JSON models.

Attachment download decodes the emitted metadata object; path mode returns the
typed record and byte mode reads its path after successful decode. Daemon
stop/restart and auth status/logout use their real lifecycle/text behavior.
Repository checkout delegates all checkout and registration work to the CLI.
Interactive setup and token prompting use the executor/process boundary, not a
domain JSON abstraction.

Alternative: enhance upstream CLI with JSON first. Rejected because this change
must represent the pinned public CLI and cannot make an upstream enhancement a
hidden prerequisite.

### Decision 6: Separate wire variants from immutable public projections

Wire models represent each actual CLI envelope/variant and preserve field
presence. Finalizers convert them to immutable public models without dropping
reviewed data. Open upstream string domains remain strings; closed values use
existing enums only when source validates closure. Secret-bearing trigger or
environment values are absent/redacted by default and available only through
explicit audited operations or opt-in flags. Model defaults cannot turn a
missing state into a false state, as happened with daemon status.

Compatibility aliases may remain for access paths that can faithfully project
the corrected result. An alias is not retained when it would require fabricated
fields, silently discard data, or continue invalid argv.

Alternative: add optional fields directly to current public models without wire
variants. Rejected because several commands emit structurally distinct healthy,
starting, stopped, aggregate, list, detail, and mutation shapes.

### Decision 7: Use one table-driven proof chain

The approved inventory, `OperationCase`, native response fixtures, component
fake CLI, public discovery, docs, and package exports form one closed proof
chain. Existing frozen case dataclasses are extended instead of creating a new
test framework. Exact argv cases cover positional/flag contracts and five-state
presence; decoder cases use source-linked native payloads; component cases prove
public routing and transport mode; negative cases prove exclusions, redaction,
and failure-before-I/O.

Destructive stop/restart/logout behavior is tested through isolated child
process fixtures and source-linked outputs. Prepared live smoke is optional and
reported separately; it cannot replace or weaken offline acceptance.

Alternative: infer coverage from method counts or line coverage. Rejected
because neither proves mapping, response completeness, dynamic registrations,
or semantic equivalence.

### Decision 8: Deliver breaking corrections atomically

Contract schema, generated projection, public models/resources, tests, and
documentation land in one implementation delivery. Migration documentation
lists corrected argv, return-type, model-field, and process-lifecycle changes.
Compatibility remains `[0.4.42,0.5.4)` only for operations whose reviewed
source contract is actually valid throughout that interval; newly promoted
target-only behavior receives its evidence-backed minimum. Rollback is a Git
revert of the atomic implementation commit/PR, not dual runtime behavior.

Alternative: ship compatibility shims that preserve known false results.
Rejected because false JSON flags, rejected argv, and data loss cannot be made
safe by deprecation warnings.

## Risks / Trade-offs

- **Inventory breadth can hide an unresolved helper** → validation rejects every
  unresolved relevant review item, and dynamic factories/aliases have named
  reconciliation tests.
- **A wide public-model correction creates migration cost** → source-linked
  native fixtures, explicit migration tables, and compatibility aliases are
  retained only where truthful.
- **Secret-bearing env and webhook operations can leak values** → default reads
  stay redacted, secret access is explicit, and preview/error/repr tests use
  exact sentinel values.
- **Interactive process support can exceed current executor guarantees** → add
  the smallest terminal-capable extension to the existing executor contract and
  keep buffered/spawn behavior unchanged.
- **Parallel changes touch shared client/contract/test registries** → shared
  contract schema, common models, client wiring, operation cases, exports, and
  documentation are owned by a foundation/final-integration package; sibling
  packages own disjoint resource families.
- **Historic 0.5.3 “unchanged” claims conflict with newly found defects** → new
  requirements explicitly distinguish version delta from absolute CLI-to-SDK
  parity and replace only the conflicting completion claims.

## Migration Plan

1. Capture a clean baseline and generate read-only pinned source/help evidence
   outside tracked paths.
2. Extend and validate the approved contract schema and checked inventory;
   resolve every public unknown before public SDK edits.
3. Correct A1–A10 transports and models with native regression fixtures.
4. Implement the missing operation families and existing-input gaps through
   reviewed contract-first vertical slices.
5. Complete the response-field/variant audit and public model migration.
6. Close generated, handwritten, docs, package, and negative-scope inventories;
   run focused checks after each slice and the full offline/package gate once at
   the exact delivery SHA.
7. Publish migration and coverage documentation. Roll back by reverting the
   atomic implementation delivery if a release gate fails.

## Open Questions

None. Any newly encountered unresolved public mapping or output shape is a
blocking contract-review finding that requires an OpenSpec planning revision;
implementers do not choose a fallback disposition.
