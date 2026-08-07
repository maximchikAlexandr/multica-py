## Why

The SDK currently exposes 124 canonical CLI-backed operations, but equivalent
operations still differ in how callers supply typed inputs, express field
presence, consume collections, and interpret mutation results. GitHub issue
#32 requires one predictable public contract that can be learned once and
applied across every resource, while preserving the already-delivered command
preview invariant.

## What Changes

- Extend the request-object/direct-keyword convention to every public method
  that accepts a typed request or filter, including list filters, comment and
  metadata requests, and autopilot trigger requests. Eager and `*_command()`
  forms expose identical overloads; mixing the two input styles is rejected
  before I/O.
- Make every update surface presence-aware: omitted fields use `Unset` and are
  not sent, explicit `None` clears only fields whose public contract is
  nullable, and falsey non-null values remain present. A request containing no
  changes is a valid no-op read that returns the current entity.
- **BREAKING**: normalize public collection reads on an immutable, directly
  iterable `Page[T]` contract with `.items` and common optional pagination
  metadata. Existing `IssueListPage`, `AutopilotListPage`,
  `AutopilotRunListPage`, comment-page, and metadata-page types remain as
  compatibility types, and their resource-named item properties remain
  deprecated read-only aliases.
- **BREAKING**: normalize action-style operations that do not naturally return
  an entity, scalar read value, or running process on `ActionResult[T]`.
  Delete/remove/toggle operations return `ActionResult[None]`; actions with
  useful payloads retain them as the typed `value`.
- Keep retrieval, creation, and entity-update operations returning the relevant
  entity; keep long-running operations returning `ManagedProcess`; keep normal
  eager execution exactly equivalent to `*_command(...).run()`.
- Add a checked operation-category and response-convention matrix for every
  canonical public method so new resources cannot reintroduce resource-specific
  conventions.
- Update API and migration documentation to present these as SDK-wide rules and
  identify the return-type and `None`-semantics migrations.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdk-surface`: Replace the finite dual-input exception list with an
  all-request/filter rule; define presence-aware updates, operation-category
  return conventions, the shared page interface, and the universal eager/
  command equivalence contract.
- `verification-and-release`: Require a complete category/return matrix,
  structural overload parity, presence-vector tests, page protocol tests,
  action-result tests, and documentation/migration gates across the canonical
  operation inventory.

## Impact

- Public models and exports in `src/multica_py/models/`, `sentinels.py`, and
  `multica_py.__init__` gain the canonical generic `Page[T]` and
  `ActionResult[T]` contracts and presence-aware update models.
- Resource signatures and command builders in `src/multica_py/resources/`
  adopt complete dual-input overloads, no-op update reads, consistent clear
  mappings, page finalizers, and action-result adapters.
- `contracts/sdk-contract.json`, its schema/tooling, and the canonical
  operation table record and verify each method's operation category and public
  response convention; this change does not infer behavior from unapproved
  upstream evidence.
- Unit, contract, component, packaging, and documentation tests are updated
  table-first. No dependency, transport, wire protocol, subprocess execution,
  or persistence change is intended.
