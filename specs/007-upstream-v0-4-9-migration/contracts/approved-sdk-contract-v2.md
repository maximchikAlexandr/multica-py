# Contract: Approved SDK Contract Schema v2

## Authority

`contracts/sdk-contract.json` is the sole reviewed decision input for public
generation. Evidence packages, source delta, candidate semantic contracts,
manifest suggestions, upgrade bundles, and help output cannot satisfy this
contract or modify it.

## Closed Top-Level Shape

```json
{
  "schema_version": 2,
  "target": {},
  "catalogs": {},
  "source_refs": [],
  "test_refs": [],
  "scope": {},
  "operations": [],
  "traceability": []
}
```

No other top-level key is accepted. All nested objects are also closed.

`catalogs` has exactly `types`, `signatures`, `bindings`,
`binding_source_refs`, `presence`, `mapping_presence`, `responses`, `decoders`,
`validators`, and `validator_evidence`.
Each is an ID-keyed closed object. IDs are unique across their own catalog.
The seed is the literal catalog authority; an implementation may not add a
catalog member. `types` maps IDs to exact rendered Python annotations.
`signatures` map IDs to exact canonical public signature strings from the
seed. They are never evaluated as Python and validation requires exact seed
membership. `bindings` are `BindingProfile`; `responses` are
`ResponseContract`. Operations and
entrypoints reference catalog IDs rather than carrying free-form code strings.

## Required Object Shapes

All tuples below are JSON arrays. All object keys are required unless their
type explicitly includes `null`.

`target`:

| Key | Type / exact value |
| --- | --- |
| `version` | string, `0.4.9` |
| `tag` | string, `v0.4.9` |
| `commit` | string, `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18` |
| `release_id` | string, `358605496` |
| `release_provenance_ref` | string, `.devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9/release-provenance.json` |

`scope`:

| Key | Type |
| --- | --- |
| `operation_ids` | ordered array of the 16 strings in `operation-decisions.md` |
| `ungoverned_policy` | literal string `existing_unrelated_operations_unchanged` |
| `family_dispositions` | ordered array of exactly 11 `FamilyDisposition` objects |
| `source_authority_ref` | literal `specs/007-upstream-v0-4-9-migration/contracts/source-authority.json` |
| `family_disposition_ref` | literal string `specs/007-upstream-v0-4-9-migration/contracts/upstream-family-disposition.md` |

`FamilyDisposition`:

| Key | Type |
| --- | --- |
| `family` | one exact family name from `upstream-family-disposition.md` |
| `disposition` | `required_compatibility`, `required_subset_plus_extension_candidates`, `required_subset_plus_cli_only`, `required_subset_plus_deferred_extension`, `separate_extension_candidate`, `deferred_owner_decision`, or `cli_only_plus_deferred_extension` |
| `required_operation_ids` | sorted array containing only governed operation IDs; empty for families with no required migration subset |
| `rationale` | non-empty string matching the selected boundary |
| `source_ref_ids` | non-empty sorted IDs resolved against `source-authority.md` |

The 11 family names occur exactly once. The union of
`required_operation_ids` is a subset of `scope.operation_ids`; family entries
never create operation IDs.

Each operation requires:

- `operation_id: str`;
- `compatibility: CompatibilityOutcome`;
- `rationale: str` (non-empty);
- `entrypoints: tuple[ApprovedEntrypoint, ...]` (non-empty);
- `source_ref_ids: tuple[str, ...]` (non-empty);
- `test_ref_ids: tuple[str, ...]` (non-empty).

Each entrypoint requires:

- `entrypoint_id: str`;
- `public_symbol: str`;
- `signature_id: str`;
- `binding_id: str`;
- `response_id: str`;
- `errors`: literal `standard`, selecting the exact `ErrorContract` below.

`BindingProfile` contains exactly `command`, `output`, `mappings`, and
`constraints`. `catalogs.binding_source_refs` contains one non-empty
source-ref array for every binding ID and proves every mapping in that profile.
A mapping is the exact tuple `[python_path, cli_binding,
destination]`. `cli_binding` is `pos:N`, a literal flag, `repeat:<command>`,
or `description-selector`; destination is `<closed-kind>:<name>`. Constraints
are IDs from `catalogs.validators`.

`catalogs.presence` stores the closed five-state profiles.
`catalogs.mapping_presence` has one array per binding ID, with exactly one
presence-profile ID for each mapping at the same ordinal. No presence behavior
is inferred from a Python type or CLI token.

`catalogs.validator_evidence` has exactly one object for every validator ID:
`{"positive_case_id": "<validator-id>-valid", "negative_case_id":
"<validator-id>-invalid"}`. Both resolve through the single generated node
template `tests/unit/resources/test_operations.py::test_generated_constraint[<case-id>]`.
The two IDs must differ and collect exactly once after T021.

`catalogs.decoders` maps every `ResponseContract.decoder_id` to one exact
fully-qualified callable. Null is forbidden; no decoder name is inferred.

The seed intentionally uses normalized catalogs instead of an expanded
signature/constraint mini-language:

- signatures are exact immutable strings copied to stubs and checked against
  public inspection;
- a mapping is an ordered three-string tuple and has one presence profile at
  the same ordinal;
- every constraint is a validator ID with an exact callable and exact
  positive/negative generated case IDs;
- enums are generated only from the literal `IssueSort` and `SortDirection`
  shapes in `generated-output-formats.json`; status enums reuse existing
  public enums;
- multi-step `issues.create` is the sole sequence described below.

Therefore no `condition`, predicate expression, arbitrary default string,
arbitrary annotation, arbitrary decoder symbol, or inline validator symbol is
accepted in schema-v2 JSON.

`ResponseContract`:

| Key | Type |
| --- | --- |
| `public_type_id` | ID from `catalogs.types` |
| `wire_type_id` | ID from `catalogs.types`, or null when output mode is `none` |
| `decoder_id` | one of `decode_none`, `decode_issue`, `decode_issue_summaries`, `decode_comment`, `decode_comments`, `decode_comment_page`, `decode_comment_thread_page`, `decode_labels`, `decode_project`, `decode_project_resources`, or `decode_project_resource` |
| `success_exit_codes` | exact unique integer array; use `[0]` for all feature-007 operations |
| `malformed_output` | literal `raise_output_shape_or_decode_error` |

`ErrorContract`:

| Key | Exact value |
| --- | --- |
| `exit_2` | `NetworkError` |
| `exit_3` | `AuthenticationError` |
| `exit_4` | `NotFoundError` |
| `exit_5` | `ValidationError` |
| `other_nonzero` | `CommandExecutionError` |
| `sdk_timeout` | `CommandTimeoutError` |

`SourceRef`:

| Key | Type |
| --- | --- |
| `source_ref_id` | contract-wide unique stable string |
| `repository` | literal `multica-ai/multica` |
| `commit` | exact target full commit |
| `path` | repository-relative source path |
| `symbol` | non-empty Go symbol |
| `line_start` / `line_end` | positive integers, start <= end |

`TestRef`:

| Key | Type |
| --- | --- |
| `test_ref_id` | contract-wide unique stable string |
| `path` | existing repository-relative test file |
| `node_id` | exact collected suffix or null |

JSON always stores `{path, node_id}`; `node_id` never contains `::`.
`path::node_id` is display notation only. Runtime validation checks path and
syntax; contract tests additionally run `pytest --collect-only`.

`RequirementTrace`:

| Key | Type |
| --- | --- |
| `requirement_id` | one exact ID from FR-001..FR-040, BC-001..BC-006, SC-001..SC-012, or ET-001..ET-007 |
| `authority_ref` | `target`, `scope`, `generation`, `coherence`, `live`, or `operation:<operation_id>` |
| `test_ref_ids` | non-empty array resolving against top-level `test_refs` |

`traceability` contains exactly 65 unique objects: all 40 FR IDs, all 6 BC IDs,
all 12 SC IDs, and ET-001..ET-007, with no other ID.

Do not use raw dictionaries for any object above. Implement every object as a
frozen `msgspec.Struct` with `kw_only=True` and
`forbid_unknown_fields=True`.

Each source ref requires repository, exact commit, source file, symbol, and
inclusive line start/end. Each test ref must resolve to a repository file and,
when supplied, exact collectable node ID.

## Closed Values

- compatibility: `compatible`, `intentionally_changed`,
  `explicitly_unsupported`;
- output: `json`, `text`, `bytes`, `none`;
- destination: `path`, `query`, `json_body`, `header`, `multipart`,
  `local_control`;
- presence outcome: `not_applicable`, `omit`, `emit`, `reject`, `value`;
- enum policy: `none`, `strict`, `open`;
- constraints: `requires`, `conflicts_with`, `exactly_one`, `at_least_one`,
  `required_together`, `conditional_enum`, `conditional_range`,
  `custom_validator`.

## Required Validation Invariants

1. Target is exactly `v0.4.9` / `0.4.9` /
   `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`.
2. Scope and operations contain exactly the same 16 unique operation IDs.
3. Operation and entrypoint IDs are unique; command-step order is total and
   consecutive.
4. Every signature input is mapped or explicitly local-only; every mapping
   source and command step exists.
5. Every mapping states outcomes for omitted, null, empty, zero, and false.
6. Every mapping contains all five presence keys. Non-update mappings use
   `not_applicable` for states the Python type cannot represent. Project update
   name/description encode omitted as `omit`, empty as `emit`, and the
   operation rejects the all-omitted request.
7. Strict enums are non-empty; aliases/deprecations are explicit; open enums do
   not generate a closed public enum.
8. Every constraint has positive and negative test evidence.
9. Every source ref uses the target full commit and a valid line range.
10. `validate_approved()` resolves every test file and validates node-ID syntax
    without importing pytest; the offline traceability contract test runs
    pytest collect-only and proves every non-null node ID resolves exactly.
11. The 16 operations yield 15 `compatible`, one `intentionally_changed`
    (`issues.comments.list`), and zero `explicitly_unsupported`.
12. Unknown fields, unknown enum tokens, dangling refs, duplicate IDs, missing
    presence states, or unresolved review markers are fatal.
13. Traceability contains the exact 65-ID requirement set and every test ref
    resolves.
14. Scope contains exactly the 11 selected family dispositions and no family
    entry promotes an operation outside the 16-ID scope.
15. Every operation and binding profile has non-empty top-level source-ref IDs.
    Every family source-ref ID resolves against `source-authority.md`.
16. Catalog references resolve exactly; arbitrary annotation, decoder,
    validator, condition, default, response, or binding strings are rejected.

## Multi-Step Operations

`issues.create` records:

1. `issue create`;
2. zero or more ordered `issue label add` calls for ordered `label_ids`;
3. one `issue get` refresh when labels were supplied.

The contract explicitly marks the sequence non-atomic. Generation must not turn
it into an invented transaction or generate full resource implementations.

## Semantic Hash

Decode and validate first. Hash the canonical semantic representation with
sorted object keys, stable list order, UTF-8, compact separators, and a single
trailing newline. File formatting, evidence bundle paths, and timestamps are
not semantic inputs.
