# Data Model: Reduced Non-Production System

## ApprovedContract

The existing closed `contracts/sdk-contract.json` schema remains the sole
reviewed authority.

**Identity**: `(schema_version, target.version, target.commit)`.

**Required relationships**:

- owns approved operations, entrypoints, bindings, mappings, presence
  profiles, validators, responses, source refs, and test refs;
- is the only input to `GeneratedRuntimeProjection`;
- is informed by `EvidenceBundle` through human review and is never modified by it.

**Validation**:

- unknown fields and references fail;
- every mapping has explicit destination and five-state presence semantics;
- every enum and constraint has reviewed policy/evidence;
- source refs use the pinned full commit;
- unresolved review markers fail.

## EvidenceBundle

A transient directory produced by `collect`.

| Field | Type | Rule |
| --- | --- | --- |
| `target` | release identity | tag, version, full commit, release ID |
| `binary` | verified identity | asset, OS, architecture, SHA-256, version output |
| `facts` | ordered tuple | declarative Cobra facts with source provenance |
| `review_items` | ordered tuple | every unknown/dynamic/imperative pattern |

**State**: `collected` only. There is no candidate, supported, promoted, or
rejected state.

**Write boundary**: caller-supplied ignored directory only.

## GeneratedRuntimeProjection

The single committed file
`src/multica_py/_generated/approved_sdk.py`.

| Section | Contents |
| --- | --- |
| compatibility | target, minimum, and exclusive maximum CLI versions |
| enums | reviewed closed public choices |
| bindings | immutable command/mapping descriptors |
| validators | deterministic validator functions |

**Identity**: SHA-256 of the exact bytes rendered from `ApprovedContract`.

**Validation**:

- stable section and symbol order;
- no timestamp, local path, evidence path, or nondeterministic value;
- compiles as Python;
- exactly matches rerendered bytes;
- is importable from a built wheel.

## TransientProjectionSet

The transient render set has exactly three paths: `docs/approved-sdk.md`,
`reports/compatibility.json`, and `reports/provenance.json`. Operation cases
are never materialized: `generated_operation_cases(catalog)` creates them
in-memory only. Evidence/review output belongs to `collect`, not `render`.

**Identity**: ordered `(relative_path, SHA-256)` pairs.

**Validation**: two renders from the same approved contract have identical
paths and bytes; Python compiles, JSON decodes, Markdown is non-empty and uses
the approved operation IDs.

## OperationCase

The frozen row type in `tests/cases/operations.py`.

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | stable and unique across variants |
| `sdk_method` | dotted string | resolves to one public resource method |
| `args` | tuple | exact positional inputs |
| `kwargs` | tuple of pairs | exact keyword inputs |
| `transport_method` | `run_bytes`, `run_text`, or `spawn` | exact |
| `expected_argv` | tuple of strings | complete, ordered argv |
| `stdin` | bytes or null | compared exactly |
| `timeout` | float or null | compared exactly |
| `stdout` | bytes | fake successful output |
| `assert_result` | typed callable or null | required for a distinct decoded shape |
| `is_canonical` | bool | exactly one true row per `sdk_method` |
| `contract_operation_id` | string or null | approved operation ID for governed rows |
| `source_ref` | `SourceRef` or null | exact manual provenance for ungoverned rows |

**Relationships**:

- every supported public method has at least one row;
- variants share `sdk_method` and have unique `id`;
- every one of the 111 discovered methods has exactly one `is_canonical=True`
  row; the registry is exactly 135 rows: 111 canonical and 24 noncanonical
  argv variants, preserving every current argv row;
- generated rows contain exactly 19 entrypoint-base vectors and 11
  entrypoint-variant vectors; `entrypoint-base` is an ID category, not the
  public-method `is_canonical` field;
- generated rows contribute 16 canonical public-method rows and 14
  noncanonical public-method rows.  Manual rows contribute 95 canonical
  public-method rows and 10 noncanonical public-method rows.  The total is
  therefore 111 canonical and 24 noncanonical rows;
- one generic unit executor consumes every row;
- it has no live policy, owner, dimension set, or component duplicate.
- exactly one of `contract_operation_id` and `source_ref` is non-null;
- the loader rejects a row violating that XOR rule, an unknown contract ID, or a
  source ref with an empty repository, non-40-hex commit, empty path/symbol, or
  invalid inclusive line range.

## ProcessCase

The frozen row type local to
`tests/component/test_process_contract.py`.

**Closed IDs**:

- `bytes-env`;
- `text-stdin`;
- `timeout-tree-cleanup`.

Each ID has a fixed fixture mode and exact outcome defined in
`contracts/verification.md`.

## PreparedLiveTarget

Fixture inputs supplied by the self-hosted environment.

| Environment name | Type | Validation |
| --- | --- | --- |
| `MULTICA_LIVE_CLI` | absolute path | file is executable |
| `MULTICA_LIVE_EXPECTED_VERSION` | semantic version | exact version probe match |
| `MULTICA_LIVE_SERVER_URL` | URL | HTTPS or loopback HTTP |
| `MULTICA_LIVE_WORKSPACE_ID` | nonblank string | passed to client |
| `MULTICA_LIVE_PROFILE` | nonblank string | already authenticated |

No token is passed to pytest. Missing/invalid input is a setup error, not a
skip, when live selection is explicitly requested.

## LiveResourceScope

One `contextlib.ExitStack` owned by each live test.

**State transitions**:

`empty -> project/issue created -> cleanup registered -> assertions -> cleanup`

Every creation registers its public-SDK delete callback immediately. Cleanup
continues through all callbacks; a failed assertion remains primary and
cleanup failures are attached as notes.

## BaselineRequirement

One requirement in an OpenSpec-compatible baseline.

| Field | Rule |
| --- | --- |
| capability path | one of four fixed paths |
| name | unique within capability |
| statement | contains normative `MUST` or `SHALL` |
| scenarios | at least one named scenario |
| scenario steps | at least one `WHEN` and one `THEN` |
| source refs | one or more historical feature/requirement IDs in the migration table |

Baseline requirements have no lifecycle state in this feature. The later
OpenSpec migration adopts them without reinterpreting their meaning.

## Removed State Models

The following have no replacement entity: candidate baseline, supported
baseline, observed release, promotion decision, promotion transaction,
promotion journal, upgrade bundle, rename suggestion, behavioral coverage
ledger, duplicate-removal entry, quality baseline, live backend session, direct
API oracle, sandbox session, and live policy for every public operation.
