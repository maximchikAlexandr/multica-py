# Data Model: Upstream v0.4.9 Migration

## Model Boundary

This document defines planning-level entities. The approved JSON shape is
closed and specified in
[contracts/approved-sdk-contract-v2.md](./contracts/approved-sdk-contract-v2.md).
No evidence or candidate entity may mutate an approved entity implicitly.

## Approved Contract Aggregate

### ApprovedSdkContract

Fields:

- `schema_version`: literal `2`.
- `target`: `ApprovedTarget`.
- `catalogs`: exact types/signatures/bindings/binding-source/response/validator catalogs from the seed.
- `source_refs`: operation binding source records.
- `test_refs`: repository test authorities.
- `scope`: `ApprovedScope`.
- `operations`: ordered tuple of exactly 16 `ApprovedOperation` values.
- `traceability`: ordered tuple of exactly 65 `RequirementTrace` values.

Validation:

- unknown fields fail decoding;
- `scope.operation_ids` is the sorted unique set of `operations.operation_id`;
- semantic hashing uses canonical UTF-8 JSON with sorted object keys and one
  trailing newline;
- only this aggregate is a decision input to generation.

### RequirementTrace

Fields: exact requirement ID, one authority reference (`target`, `scope`,
`generation`, `coherence`, `live`, or `operation:<operation_id>`), and non-empty
resolving test refs. The set is exactly FR-001..FR-040, BC-001..BC-006,
SC-001..SC-012, and ET-001..ET-007.

### ApprovedTarget

Fields:

- `version`: `0.4.9`;
- `tag`: `v0.4.9`;
- `commit`: `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`;
- `release_id`: `358605496`;
- `release_provenance_ref`: literal
  `.devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9/release-provenance.json`;
- `approved_contract_hash`: absent while authoring, materialized in generated
  projections from the canonical aggregate.

Validation: full 40-hex commit; exact target tuple; provenance ref resolves and
matches tag, commit, release, archive/executable checksums, and backend digests.

### ApprovedScope

Fields:

- `operation_ids`: ordered tuple of the 16 governed IDs;
- `ungoverned_policy`: literal stating that other existing raw/process
  operations remain unchanged and are not schema-v2 approved;
- `family_dispositions`: ordered tuple of exactly 11 `FamilyDisposition`
  values, each containing the exact family name, closed disposition,
  governed required-operation subset, and rationale;
- `family_disposition_ref`: repository-relative path to the feature contract.

Validation: exactly 16 unique IDs and 11 unique families; every family-required
operation belongs to the 16-ID set; no target addition outside that set.

### ApprovedOperation

Fields:

- `operation_id`: stable dotted ID;
- `compatibility`: `compatible`, `intentionally_changed`, or
  `explicitly_unsupported`;
- `rationale`: non-empty reviewed explanation;
- `entrypoints`: non-empty ordered tuple;
- `source_ref_ids`: non-empty tuple resolving through the top-level catalog;
- `test_ref_ids`: non-empty tuple resolving through the top-level catalog.

Relationships: belongs to one contract and owns entrypoints and evidence refs.

Validation: unique ID; exactly one compatibility outcome; unsupported
operations would require an explicit deliberate public failure entrypoint.
Feature 007 has 15 compatible operations, one intentionally changed operation,
and no unsupported operation.

### ApprovedEntrypoint

Fields:

- `entrypoint_id`: operation-local stable ID;
- `public_symbol`: fully-qualified public Python symbol;
- `signature_id`: reference to the closed signature catalog;
- `binding_id`: reference to the closed binding catalog;
- `response_id`: reference to the closed response catalog;
- `errors`: standard closed `ErrorContract`.

Validation: unique within operation; signature names unique; every mapping
references a signature source and existing command step; every required
argument and flag is mapped; steps use consecutive ordinals.

### ParameterMapping and PresenceContract

Input mapping is the exact seed tuple `[python_path, cli_binding,
destination]`. Its binding profile resolves one source-ref array, and
`mapping_presence[binding_id]` supplies one presence-profile ID at the same
ordinal.

Presence fields record an explicit outcome for each of `omitted`, `null`,
`empty`, `zero`, and `false`: `not_applicable`, `omit`, `emit`, `reject`, or
`value`, with a non-empty detail when the outcome is `emit` or `value`.

Validation: exactly one destination; all five states present even when not
applicable; update fields cannot collapse omitted and explicit clear; enum
policy is `none`, `strict`, or `open`, with aliases/deprecations explicit.

### Constraint

Input constraints are validator IDs only. Each resolves to one exact callable
and one exact positive/negative generated case pair in the seed catalogs.
Free-form predicates and validator symbols are not accepted.

### SourceRef and TestRef

Each `SourceRef` has a unique `source_ref_id`. Every `ParameterMapping` and
`FamilyDisposition` contains a non-empty tuple of proving source-ref IDs.
Response and error contracts belong to `ApprovedEntrypoint`, not the operation.

`SourceRef` contains repository identity, exact 40-hex commit, source path,
symbol, and inclusive positive line range. The target commit must equal the
contract target.

`TestRef` is always `{path, node_id}` and `node_id` excludes `::`.
File-only refs name an existing file;
node-specific refs use `::node_id`. Production validation checks containment,
existence, and syntax without importing pytest; the offline traceability
contract test must collect each node exactly.

## Public Compatibility Models

### CommentCursor

- `before: str`;
- `before_id: str`.

Both are non-empty. The two fields are atomic: neither may be emitted alone.

### CommentPage and CommentThreadPage

- `items`: immutable tuple of decoded comments or threads;
- `next_cursor`: `CommentCursor | None`.

A partial or malformed cursor line is an output-shape error. Flat mode always
returns `next_cursor=None`.

### IssueListFilter additions

- `sort: IssueSort | None`;
- `direction: SortDirection | None`.

`IssueSort` is strict:
`position`, `title`, `created_at`, `start_date`, `due_date`, `priority`.
`SortDirection` is strict: `asc`, `desc`. Direction requires sort and conflicts
with `position`.

### Presence-sensitive project values

`Unset` means omitted. Empty string means explicit clear for project update
name/description. `description=None` is invalid. Both fields `Unset` is an
invalid empty update. Project create empty description is omitted.

## Pipeline and Provenance Models

### CandidateState

Fields: canonical candidate ref, kind, target tuple, semantic hash, created
metadata, evidence trust `help-degraded`, and staged trust
`approved-contract-bound`. It never claims `verified` and never transitions
directly to supported. A convenience output path is not stored.

### PromotionDecision

Fields: candidate semantic hash, approved contract hash, exact target tuple,
release provenance ref/hash, previous supported identity, reviewer decision.

Validation: every identity matches current canonical artifacts; dry-check is
non-writing.

### SupportedState

Fields: canonical supported ref, semantic hash, target tuple, approved contract
hash, provenance identity. Candidate becomes null only after the successful
rollback-capable promotion transaction.

State transitions:

```text
no candidate
  -> canonical candidate collected
  -> candidate reviewed + approved contract generated/check-green
  -> promotion dry-check green + coherence green
  -> supported transaction committed, candidate cleared
```

Any identity mismatch transitions the workflow to invalid artifact, not a
warning or implicit repair.

## Live Acceptance Models

### TargetFingerprint

Exact tag, version, source commit, CLI archive/executable checksums, backend
manifest/platform digests, and approved contract hash.

### LiveOutcome

Fields:

- category: `passed`, `product_failure`, `environment_unready`,
  `authentication_limited`, or `invalid_run`;
- stage;
- pytest exit code;
- collected/started/completed/failed counts;
- optional target node;
- optional exception type;
- normalized redacted message;
- target fingerprint;
- JUnit/report/diagnostic paths;
- cleanup result and managed leftovers.

Product regression requires `product_failure`, operation reachability, and no
matching baseline/control category-stage-exception fingerprint.

### MutationCase

Fields: case ID, source path, original hash, exact node, mutation anchor,
mutation, expected failure fingerprint, clean JUnit, mutated JUnit.

Outcomes: killed, survived, invalid. Exit `0` means all validly killed; `1`
means a survivor; `2` means the gate was invalid.

### StabilityRun

Fields: ordinal 1..10, run ID, target fingerprint, categorized outcome,
artifact paths, cleanup audit, elapsed time. Ten completed passed runs and zero
leftovers are required; first non-pass stops the sequence.
