# Contract: Live Acceptance

## Typed Result Authority

`tools/live_support/outcomes.py` owns closed result models, JUnit parsing,
normalized redacted fingerprints, and count validation. Both
`scripts/run_live_tests.py` and `scripts/live_compatibility_report.py` use it.

Categories are exactly:

- `passed`;
- `product_failure`;
- `environment_unready`;
- `authentication_limited`;
- `invalid_run`.

Every result records stage, pytest exit, collected/started/completed/failed
counts, optional exact node, exception, normalized redacted message, target
fingerprint, artifact refs, cleanup status, and leftovers.

The closed JSON object has exactly `schema_version` (integer `2`), `category`,
`stage`, nullable integer `pytest_exit`, `counts`, nullable `node_id`, nullable
`exception`, `message`, `target_fingerprint`, `artifact_refs`, `cleanup`,
`leftovers`, and `operations_reached`. `counts` has exactly non-negative
integer `collected`, `started`, `completed`, and `failed`, satisfying
`failed <= completed <= started <= collected`. Arrays are sorted unique
strings. `cleanup` is `passed`, `failed`, or `not_run`.

Stages are exactly `preflight`, `backend_readiness`, `runtime_readiness`,
`authentication_rate_limit`, `collection`, `setup`, `operation`, `cleanup`,
`mutation_control`, `mutation_applied`, and `stability`.

Normalize messages in this order: redact configured secrets longest-first;
replace UUIDs with `<uuid>`; repository/temp absolute paths with `<path>`; ISO
timestamps with `<timestamp>`; collapse ASCII whitespace; strip; lowercase.
The fingerprint is `category|stage|exception-or-empty|normalized-message`.

## Reachability and Comparison

A candidate regression is emitted only if:

1. category is `product_failure`;
2. the intended operation was reached;
3. baseline/control does not share the normalized category, stage, and
   exception fingerprint.

Environment, auth, and invalid outcomes are inconclusive. Matching failure
shape alone never proves target regression.

## Readiness Stages

- `backend_readiness`: backend compose/probe did not become ready.
- `runtime_readiness`: exactly one online/ready/active `opencode` runtime for
  the selected daemon was not found.
- `authentication_rate_limit`: auth bootstrap exhausted its 429 retry policy.
- operation stage: the test reached governed behavior.

Other online providers are not counted for opencode readiness and appear only
in redacted diagnostics. Required offline cases: four providers with one
opencode succeeds; zero or two matching opencode runtimes are categorized
environment failures.

## Mutation Protocol

For every mutation case:

1. verify pytest import in the exact interpreter;
2. hash source;
3. run the unmodified exact node with unique JUnit;
4. require exactly that node collected, started, completed, and passed;
5. apply one mutation;
6. rerun that exact node with distinct JUnit;
7. require it started and failed for the expected public exception/assertion
   fingerprint;
8. reject missing/unparseable JUnit, pytest exits 2/3/4/5, setup errors, zero
   collection, wrong node/failure, and missing dependencies as invalid;
9. restore source and verify original hash.

Exit codes: `0` all mutations validly killed; `1` survivor; `2` invalid gate.

| ID | Source | Original | Replacement | Node | Required fingerprint |
| --- | --- | --- | --- | --- | --- |
| `project-update-title` | `src/multica_py/resources/projects.py` | `            args.extend(["--title", request.name])` | `            args.extend(["--name", request.name])` | `tests/unit/resources/test_operations.py::test_operation_argv[projects.update]` | `AssertionError\|--title` |
| `label-get-decoder` | `src/multica_py/resources/labels.py` | `        return self._run_json_decode(("label", "get", label_id), Label)` | `        raise AssertionError("forced label decoder failure")` | `tests/unit/resources/test_operations.py::test_operation_argv[labels.get]` | `AssertionError\|forced label decoder failure` |
| `exit-four-map` | `src/multica_py/_internal/transport.py` | `    4: NotFoundError,` | `    4: CommandExecutionError,` | `tests/unit/test_transport.py::test_exit_code_maps_to_exception[exit-4-notfound]` | `AssertionError\|NotFoundError` |

The command requires `--mutation-results
.test-artifacts/upstream-v0.4.9/mutation/mutation-results.json`. The closed
root is `schema_version`, `target`, `cases`, and `summary`; summary must be
`{"killed":3,"survived":0,"invalid":0}`. Each case stores table ID,
original/restored SHA-256, clean/mutated JUnit refs, fingerprint, and result
`killed`, `survived`, or `invalid`.

These are offline nodes. Mutation mode does not call live environment
validation, resolve a CLI release, or require credentials.

## Smoke and Extended

Smoke and extended reports must identify the exact target fingerprint. For
migration acceptance both categories are `passed`, governed behavior is
reached, secret scan and cleanup are green, and no managed leftovers remain.

## Stability

Repeat accepts exactly `--repeat 10`, the exact `--stability-report` output,
and a readable prerequisite smoke report
whose category is passed and fingerprint is identical. Each repetition runs
the full `live_smoke` selection under `tests/live`, writes unique structured
artifacts, audits cleanup, and stops at first non-pass. Acceptance is exactly
10/10 passed with zero leftovers.

The sole aggregation command is `uv run python
scripts/live_compatibility_report.py aggregate --smoke SMOKE --extended
EXTENDED --mutation MUTATION --stability STABILITY --output
ACCEPTANCE_SUMMARY`. The closed summary root has `schema_version`,
`target_fingerprint`, `inputs`, `categories`, `operations_reached`, `cleanup`,
`secret_scan`, and `accepted`. `accepted` is true only for passed
smoke/extended, mutation 3/0/0, stability 10/10, all 16 reached operations,
passed cleanup, and passed secret scan.
