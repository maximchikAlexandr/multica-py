# Review Fixes: spec 002-upstream-coverage-checks

Three reviewers ran in parallel; their findings have been aggregated and
conflict-resolved by the orchestrator. The orchestrator priority is
**code-review > thermo-nuclear > ponytail-review**, so when a more senior
reviewer says "this is required by the spec" we keep the code; when a
junior reviewer says "delete this" and the senior doesn't object, we
delete it.

This file is the **only** input for the fixer agent. Apply items in the
order listed (CRITICAL first). Do not touch LOW items unless forced by
a CRITICAL/MEDIUM fix.

## CRITICAL (HIGH) — Spec violations, must fix

### C1 — `affected_operations` never populated
**Files:** `src/multica_py/_internal/upstream_contract/diff.py`,
`suggestions.py`, `upgrade.py`, `impact.py`.

`DiffEntry.affected_operations` is always `()` (default). That makes
`suggestions.apply_manifest_suggestions` always insert
`CoverageDecision(operation_id="unresolved", coverage_level="incomplete")`,
losing the actual SDK binding. Same path through
`upgrade._manifest_suggestions`. FR-005/SC-011 require the cross-reference.

**Fix:** in `diff.py`, when building a `DiffEntry`, populate
`affected_operations` from `coverage._build_bindings_index` (or
`impact._index` — pick one and use it everywhere). The mapping for a
given `command_path` is `(operation_id,)` or `("unresolved",)` if no
binding exists. The coverage module already builds the index; share it.

### C2 — `observer.merge_observation` has three bugs
**File:** `src/multica_py/_internal/upstream_contract/observer.py`
(plus `scripts/upstream_contract.py:407-425` for exit codes).

- line 36: `published_at=observation.release_id` — should be a timestamp.
- lines 39-45: marks the *new* observation `superseded` when an older
  candidate exists; the spec says the *older candidate* is marked
  `superseded-candidate`. Use the `superseded_candidate_state` helper
  at lines 80-99.
- `cmd_observe` returns `EXIT_CLEAN` (0) for every input, including
  invalid `release_id`. Per the maintainer-commands table, observe
  failures are exits 3/4/5/64. Catch the relevant exceptions and map
  to the right exit.

### C3 — `cmd_promote` returns the wrong exit code
**File:** `scripts/upstream_contract.py:431-435`.

When `state.candidate` is missing, returns
`EXIT_UNRESOLVED_BREAKING` (6). Per the maintainer-commands table, this
is `EXIT_INVALID_ARTIFACT` (3). The function only catches
`ValueError`; missing candidate is not a ValueError, so it falls
through to exit 6. Fix the early-return path.

### C4 — `diff.py:165-174` real bug: deprecation misnamed
**File:** `src/multica_py/_internal/upstream_contract/diff.py:165-174`.

```python
"deprecation_added" if after.deprecated else "deprecation_added",
```

Both branches return the same string. Should be
`"deprecation_removed"` in the `else` branch. Add a test that the diff
produces `deprecation_removed` when before.deprecated is set and
after.deprecated is None.

### C5 — `supported.tag` not surfaced in report/human output
**Files:** `src/multica_py/_internal/upstream_contract/coverage.py:42-49`,
`reporting.py` (or wherever the `Supported: version=… commit=…` line
is rendered), `scripts/upstream_contract.py:106-109`.

`report.supported["tag"]` is never set; the human output therefore
omits `tag=` even though the contracts/implementation-oracles.md
mandate it (`Supported: version=… tag=… commit=… semantic_hash=…`).
Add the tag to the `Supported` summary struct, populate it from
`state.supported.tag` in `build_coverage_report`, and include it in
the human renderer's first line.

### C6 — `verify_checksum` only called for `release-asset` path
**File:** `src/multica_py/_internal/upstream_contract/collectors/binary.py`.

`collect_from_binary` (binary-exporter path) and the go-helper path
accept `--sha256` from the CLI but never call `verify_checksum`
before executing. The `release-asset` path does. FR-023 says checksum
mismatch must never be executed. Either call `verify_checksum` for
all three paths, or document why binary-exporter and go-helper are
exempt (and remove the `--sha256` argument from those CLI
subcommands). The simpler fix is to call `verify_checksum` for all
three when a digest is provided.

### C7 — `CoverageDecision.raw_argv_policy` not enforced
**File:** `src/multica_py/_internal/upstream_contract/coverage.py:148-149`.

The model declares `raw_argv_policy`, but `_decision_is_complete`
requires only `is not None` — it never validates the policy is
non-empty, never checks for shell interpolation, and there is no
positive/negative test fixture. FR-031: raw coverage accepts only
argument sequences, never shell-interpolated strings. Add a
validator (reject empty / reject "shell" tokens) and at least one
positive + one negative fixture under
`tests/fixtures/upstream_contract/golden/coverage-manifest-v2.json`
(or a new `coverage-raw.json`).

### C8 — `compatibility.py` is policy-only, missing client/cache/warning
**File:** `src/multica_py/_internal/upstream_contract/compatibility.py`
(28 LOC), `src/multica_py/compatibility.py` (modified per
`git status`).

FR-033 requires CLI version/build metadata read once per client
instance and an at-most-once warning for newer untested versions.
The current module is just `default_policy`/`supported_range_text` —
no client class, no cache, no warning path. Add a `Client` (or
similar) that:
- reads CLI version on first call and caches it;
- compares against the supported range;
- emits a warning at most once for "newer untested";
- exposes the same range text in diagnostics.

Plus at least one test that proves the warning fires once and is
suppressed on the second call.

### C9 — `generator/contract.py` YAML parser is a placeholder raise
**File:** `src/multica_py/_internal/upstream_contract/generator/contract.py:71-91`.

`_load_yaml` and `_YamlMinimal` exist only to raise "YAML parsing
not supported". The spec mandates
`contracts/sdk-contract.yaml` as the maintainer-approved contract.
Add a real minimal YAML parser (no new dependency — write a tiny
one that handles the 5–6 keys this file uses: `operation_id`,
`presence_semantics`, `enum_policy`, `constraints`,
`review_status`, `generator_input`). The current YAML is mostly
comments, so a fixture that exercises a small approved contract
is required.

## MEDIUM (MEDIUM) — Cleanup/quality, must fix this pass

### M1 — `source_evidence/extract.py` command_stack dead + unknown helper set incomplete
**File:** `src/multica_py/_internal/upstream_contract/source_evidence/extract.py`.

- Lines 36-37: `command_stack = []` is reserved-but-discarded
  (`_ = command_stack` on line 37). Delete the local.
- Lines 193-216: `_unknown_helper` builds a `known` set on every
  call; promote to a module-level frozenset. Also add the missing
  Cobra patterns: `Args`, `ValidArgs`, `PreRun`, `PersistentPreRun`,
  `SilenceUsage`, `MarkFlagsRequiredTogether`. FR-027.

### M2 — `_commands_from_help` returns `OutputContract(mode="none")` vs exporter `mode="text"`
**File:** `src/multica_py/_internal/upstream_contract/collectors/binary.py:308-337`.

The help-parser fallback and the binary exporter produce different
`OutputContract.mode` for the same command, so their semantic
hashes aren't comparable. Pick a single canonical form (e.g. always
`text` when output shape is unknown) and document the
`field_change_policy` override for commands that need `none`.

### M3 — `reporting.replace_state` does JSON round-trip
**File:** `src/multica_py/_internal/upstream_contract/reporting.py:22-26`.

```python
state = {**msgspec.to_builtins(struct)}
state.update(changes)
return msgspec.convert(state, type=type(struct))
```

Replace with `msgspec.structs.replace(struct, **changes)`. The
package already uses `msgspec.structs.replace` 9 times elsewhere.
Update the 4 callers in `coverage.py`.

### M4 — semantic_hash pattern repeated 3x in binary.py
**File:** `src/multica_py/_internal/upstream_contract/collectors/binary.py:128-130, 198-201, 250-253`.

Same `msgspec.structs.replace(contract, artifact=msgspec.structs.replace(contract.artifact, semantic_hash=...))`
shape three times. Extract a `_with_hash(contract, hash)` helper.

### M5 — manual JSON Schema generation
**File:** `src/multica_py/_internal/upstream_contract/schema.py:175-235`.

`msgspec` ships `msgspec.json.schema(SemanticCLIContract)` and
`msgspec.json.schema(CoverageReport)`. Replace the 60-line
`_build_schema_for` visitor with the stdlib call.

### M6 — unused `encode_*` one-liners
**File:** `src/multica_py/_internal/upstream_contract/schema.py:238-275`.

9 `encode_*` functions, 7 with zero callers (`encode_state`,
`encode_diff`, `encode_impact`, `encode_bundle`, `encode_promotion`,
`encode_evidence`, `encode_compatibility`, `encode_observer`).
Delete them. Keep the two actually used (or inline them where they
are used).

### M7 — unused `state.load_*` accessors
**File:** `src/multica_py/_internal/upstream_contract/state.py:34-43`.

`load_supported`/`load_observed`/`load_candidate` have zero callers
outside `state.py` itself. Production uses
`load_state(...).supported`. Delete.

### M8 — `state.set_candidate`/`clear_candidate` only in tests
**File:** `src/multica_py/_internal/upstream_contract/state.py:69-79`.

Production goes through `replace_supported`/promotion. Inline at
test sites or delete (tests can use `msgspec.structs.replace`).

### M9 — `observer.py` 4 functions only in tests
**File:** `src/multica_py/_internal/upstream_contract/observer.py:49-99`.

`tracking_identity`, `record_failed_write`,
`mark_recovery_required`, `superseded_candidate_state` are
test-only. Note: C2 needs `superseded_candidate_state` to be
**called** from production — keep that one, but ensure it is wired
in. Delete the other three.

### M10 — `provenance.py` 4 functions only in tests
**File:** `src/multica_py/_internal/upstream_contract/provenance.py:25-52`.

`assert_full_commit`, `validate_binary_ref`, `validate_source_ref`,
`validate_compatibility`. Production `BinaryRef` is constructed
with non-empty fields by code. Delete the 3 validators; keep
`assert_full_commit` because C1/C2 use it.

### M11 — `files.read_bytes` is `path.read_bytes()`
**File:** `src/multica_py/_internal/upstream_contract/files.py:11-12`.

Zero callers. Delete.

### M12 — `files.P = ParamSpec("P")` unused
**File:** `src/multica_py/_internal/upstream_contract/files.py:8`.

Delete.

### M13 — `_now_iso` duplicated
**File:** `src/multica_py/_internal/upstream_contract/collectors/binary.py:270-273`
and `scripts/upstream_contract.py:483-486`.

One `now_iso` in `provenance.py` (the right place) is enough.
Inline both call sites.

### M14 — `is_safe_output_size` is a one-liner wrapper
**File:** `src/multica_py/_internal/upstream_contract/collectors/security.py:79-80`.

Only tests use it. Inline `if n > limit:` at the 2 call sites in
binary.py.

### M15 — `sanitized_environment` re-implements stdlib redaction
**File:** `src/multica_py/_internal/upstream_contract/collectors/security.py:31-58`.

`{k: v for k, v in os.environ.items() if k in SAFE_ENV_KEYS and not any(...)}`
is the same idea. Either inline a 4-line dict comprehension at the
call sites or keep the helper but make it obvious. The current
inner `if/continue` cascade silently drops unknown keys — invert
the condition to `else: continue` or make it explicit.

### M16 — `_strip_volatile_state` is a no-op
**File:** `src/multica_py/_internal/upstream_contract/normalize.py:60-62`.

`msgspec.to_builtins(state); return result`. Delete; if needed,
have callers call `to_builtins` directly.

### M17 — `write_canonical`/`parse_canonical`/`command_path_key` 0 callers
**File:** `src/multica_py/_internal/upstream_contract/normalize.py:65-75`.

Delete.

### M18 — `*_SCHEMA_VERSION` constants in 8 modules
**Files:** `state.py`, `observer.py`, `compatibility.py`,
`schema.py`, `normalize.py`, `promotion.py`,
`source_evidence/extract.py`, `upgrade.py`.

Each module declares `*_SCHEMA_VERSION = 1` (or 2) that is only
read once to populate the struct's `schema_version` field. Inline
the literal.

### M19 — `BUNDLE_LAYOUT` declared but never read
**File:** `src/multica_py/_internal/upstream_contract/upgrade.py:18-28`.

`write_bundle` writes files by literal name. Delete the tuple.

### M20 — `_coerce_str_list` exists only to satisfy a type hint
**File:** `src/multica_py/_internal/upstream_contract/upgrade.py:196-199`.

`bundle.test_suggestions` already satisfies the type. Delete and
access directly.

### M21 — `_ =` dead-sentinel markers
**Files:** `upgrade.py:81`, `suggestions.py:105`,
`source_evidence/extract.py:37`.

These are deliberate "we have a bug we know about" sentinels. C1
fixes the underlying issue; once that's done, the sentinels can
go. Delete all three.

## LOW (LOW) — Defer to a later iteration

The following are judgement calls / structural concerns. Do NOT
address in this pass unless forced by a CRITICAL/MEDIUM fix:

- L1: `diff.py` 8 `_diff_*` helpers — table-driven refactor.
- L2: `coverage.py:138-156` `_decision_is_complete` 6-branch chain.
- L3: `coverage.py:159-163` `_lookup` O(n²).
- L4: `impact.py:47-54` `_index` rebuilds bindings dict.
- L5: `DiffEntry.before/after: object` — typed shape.
- L6: `scripts/upstream_contract.py:18-20` `ROOT`/`sys.path` hack.
- L7: `scripts/upstream_contract.py:280-294` `_emit` 4x copy-paste.
- L8: `scripts/upstream_contract.py:407-471` 3 cmds duplicate state-write.
- L9: `compatibility.py:7-25` data-clump in policy defaults.
- L10: `_legacy_contract_from_manifest` in `scripts/upstream_contract.py`.
- L11: 3 empty `__init__.py` (collectors, source_evidence, generator).
- L12: `binary.py:392-394` `field_change_policy` default_factory.
- L13: `binary.py:60` `generator_commit: str = "0" * 40` placeholder default.
- L14: `DiffEntry.before/after: object = msgspec.UNSET` (typed shape).

## KEEP (per spec, do NOT remove)

- `contracts/sdk-contract.yaml` — required by spec.
- `models.py` `OperationBinding.since/until`,
  `SemanticCLIContract.json_schema_ref`,
  `ObservationMeta.run_metadata`,
  `CoverageDecision.shares_implementation_with`,
  `ImpactEntry.candidate_method`,
  `ReleaseObservation.tracking_issue_id/tracking_pr_id` — these are
  required by data-model.md. Ponytail flagged them as unused, but the
  data-model says they are part of the typed contract.
- `_legacy_contract_from_manifest` in `scripts/upstream_contract.py`
  is the compat shim the spec requires.

## Gate to re-run after fixes

1. `uv run pytest` — must stay at 361+ passing.
2. `uv run ruff format --check . && uv run ruff check .` — clean.
3. `uv run mypy --namespace-packages --explicit-package-bases -p multica_py` — clean.
4. `uv run python scripts/upstream_contract.py check --format human` — exit 0, real semantic hash.
5. `grep -rn "0bf2e9ce" .github/ tests/` — empty.
6. `grep -rn "0000000000000000000000000000000000000000000000000000000000000000" src/ tests/fixtures/` — empty.

---

# Round 3 — Typing Clean-up

User feedback: "типизация должна быть явной. any, object — это не явная типизация".

Three reviewers ran in parallel. The aggregated, conflict-resolved list:

## CRITICAL (HIGH)

### T1 — `DiffEntry.before/after: object = msgspec.UNSET` is a type escape hatch
**File:** `src/multica_py/_internal/upstream_contract/models.py:189-190`.

`before` and `after` are typed as `object` so anything can be stuffed
in. FR-005/SC-011 require typed cross-references. Define a
`DiffValue` tagged union (or one typed per kind via a discriminated
union) so the JSON contract is fully typed. The diff builders in
`diff.py` currently pass `dict`, `list`, `str`, `bool`, `None` into
the same field — collapse to one tagged shape.

### T2 — `collectors/binary.py` helpers accept `payload: object`
**File:** `src/multica_py/_internal/upstream_contract/collectors/binary.py:272, 336, 348, 366, 378, 393`.

`_commands_from_exporter`, `_argument`, `_flag`, `_execution`,
`_output`, `_source` all accept `object` and then do `if not
isinstance(payload, dict): raise ...`. Replace with a typed
`RawCommand` (or `dict[str, Any]`-with-strict-validate-then-narrow)
msgspec `Struct` that decodes the exporter payload once, then
thread the typed object through. The intermediate dict
representations (`RawCommandPayload` etc.) live next to
`models.py`.

### T3 — `normalize.py` `obj: object` parameters
**File:** `src/multica_py/_internal/upstream_contract/normalize.py:15, 25, 33, 34`.

`canonical_bytes(obj: object)`, `_default(value: object) -> object`,
`semantic_hash(obj: object)`, `payload: object`. Replace
`obj: object` with `obj: msgspec.Struct | dict[str, object] | list[object]`
— the actual input types — and `_default` should return
`str | int | float | bool | None | list[object] | dict[str, object]`,
no `object`.

### T4 — `upgrade.py:26, 132` `candidate_contract: object`
**File:** `src/multica_py/_internal/upstream_contract/upgrade.py`.

Type as `SemanticCLIContract` (the only thing ever passed).

### T5 — `upgrade.py:155, 160` `cast("list[object]", ...)` is a workaround
**File:** `src/multica_py/_internal/upstream_contract/upgrade.py:155, 160`.

`bundle.test_suggestions.get("argv_targets", [])` returns
`object | list[object]` because `test_suggestions` is `dict[str,
object]`. Type the bundle fields properly. `UpgradeBundle`
should have explicit `argv_targets: list[str]`,
`output_fixture_targets: list[str]`, etc. — not `dict[str, object]`.

### T6 — `reporting.py:22` `**changes: object`
**File:** `src/multica_py/_internal/upstream_contract/reporting.py:22`.

`replace_state(struct: CoverageReport, **changes: object)`. Each
`changes[k]` is typed `object`. Make `replace_state` a typed method
on `CoverageReport` (or remove it — `msgspec.structs.replace` is
already in use elsewhere).

### T7 — `schema.py:62, 178, 182, 210, 219` `object` in JSON Schema builder
**File:** `src/multica_py/_internal/upstream_contract/schema.py`.

`_expect_int(obj: object, field: str)`, `add(t: object)`,
`visit(t: object) -> object`, `_t.Any` checks. The builder
internal API can be typed as `type` (the type, not an instance).
`visit(t: type) -> dict[str, object]` is fine because the JSON
output is a `dict[str, object]` (a real JSON object) — but the
*inputs* should be `type` not `object`.

### T8 — `generator/contract.py:168` `container: object` in YAML visitor
**File:** `src/multica_py/_internal/upstream_contract/generator/contract.py:168`.

`def __init__(self, indent: int, container: object, ...)`. The
container is a `dict[str, object] | list[object]`. Type explicitly.

### T9 — `normalize.py:45` `_t.Any` return
**File:** `src/multica_py/_internal/upstream_contract/normalize.py:45`.

`-> dict[str, _t.Any]`. Replace with `dict[str, object]` (the
output of `msgspec.to_builtins`).

## MEDIUM (MEDIUM)

### M22 — `models.py` `ImpactEntry.candidate_method`, `OperationBinding.since/until`, etc.
NOTE: these were "KEEP" in round 2 per data-model. Reaffirm: keep
them, but make sure they have explicit types (not `object`).

### M23 — `scripts/upstream_contract.py:18-20` `ROOT`/`sys.path` hack
The script does `sys.path.insert(0, ...)` to import the package.
Replace with `python -m multica_py._internal.upstream_contract_cli`
or restructure as a proper module. (Already L7 from round 2; user
raised the bar — promote to MEDIUM and address.)

### M24 — `normalize.py:25` `_default(value: object) -> object`
**File:** `src/multica_py/_internal/upstream_contract/normalize.py:25`.

The function returns the input unchanged if it is JSON-serializable.
Type the return as
`str | int | float | bool | None | list[object] | dict[str, object]`.
Type the input as a `Union` of those same types.

## KEEP

- `models.py` field declarations required by data-model.md.
- `contracts/sdk-contract.yaml` as the approved contract.

## Gate to re-run

Same as round 2: pytest ≥ 359, ruff clean, mypy clean, `check` exit 0.

---

# Round 3 (cont.) — Aggregated Typing Findings

Three reviewers converged. The orchestrator's priority is
**code-review > thermo-nuclear > ponytail**, but the user-level rule
("явная типизация") wins over any junior reviewer's deletion if the
fix is to keep the function. Conflict resolution already happened in
the per-reviewer call. Below is the canonical, deduplicated list.

## CRITICAL (HIGH) — typing violations

### T1 — `DiffEntry.before/after: object = msgspec.UNSET` (T1 code-review, T1 thermo, T1 ponytail)
**File:** `models.py:189-190`.

Replace with a `DiffValue` type alias:
```python
DiffValue = str | int | float | bool | None | tuple[str, ...] | dict[str, object] | list[object]
```
or, for stricter typing, a tagged union via `kind` discriminator.
**Fix:** introduce `DiffValue` alias and use it. Add tests that the
JSON contract is fully typed (e.g. `mypy --strict` on a tiny
example).

### T2 — `collectors/binary.py` six helpers take `object` (T2 code-review, T2 thermo, T2 ponytail)
**File:** `collectors/binary.py:272, 336, 348, 366, 378, 393`.

Define a small set of `RawCommand`, `RawFlag`, `RawArgument`,
`RawExecution`, `RawOutput`, `RawSource` `msgspec.Struct`s
(live next to `models.py` or in a new
`collectors/_raw_payloads.py`). Decode the exporter payload once
via `msgspec.convert(payload, type=RawExporterPayload, strict=False)`.
The 6 helpers then take a typed `RawCommand`-shaped object. Drop
the 6 `if not isinstance(payload, dict): raise` runtime guards.

### T3 — `UpgradeBundle.test_suggestions: dict[str, object]` (T3 code-review, T3 thermo, T3 ponytail)
**File:** `models.py:250`, `upgrade.py:155, 160`.

Replace with `TestSuggestions(msgspec.Struct, frozen=True)` with
explicit fields: `argv_targets: tuple[str, ...] = ()`,
`output_fixture_targets: tuple[str, ...] = ()`. Both `cast`
calls disappear.

### T4 — `UpgradeBundle.manifest_suggestions: tuple[dict[str, object], ...]` (T4 code-review)
**File:** `models.py:248`.

Replace with `ManifestSuggestion(msgspec.Struct)` (`operation_id`,
`command_path`, `change_kind`, `severity`, `coverage_level`,
`reason`).

### T5 — `CoverageReport.supported/observed/candidate: dict[str, object]` (T5 code-review, T7 thermo)
**File:** `models.py:218-220`.

Replace with `SupportedSummary`, `ObservedSummary`,
`CandidateSummary` `msgspec.Struct`s. The `build_coverage_report`
in `coverage.py` already builds these dicts from typed locals;
promote the locals to the structs. The human renderer in
`scripts/upstream_contract.py:105-118` then uses attribute access.

### T6 — `normalize.py` `obj: object` (T6 code-review, T5 thermo, T1 ponytail)
**File:** `normalize.py:15, 25, 33, 34, 45`.

- `canonical_bytes(obj: object)` → input is
  `msgspec.Struct | dict[str, object] | list[object] | str | int | float | bool | None`.
- `_default(value: object) -> object` → input and output both the
  union minus `msgspec.Struct`.
- `semantic_hash(obj: object)` → same union.
- `-> dict[str, _t.Any]` → `-> dict[str, object]` (actual
  `msgspec.to_builtins` return).

### T7 — `upgrade.py:26, 132` `candidate_contract: object` (T4 code-review, T2 thermo)
**File:** `upgrade.py:26, 132`.

`build_bundle` (line 26) — `candidate_contract` is in the signature
but unused inside. Delete the parameter.
`write_bundle` (line 132) — type as `SemanticCLIContract`.

### T8 — `upgrade.py:172` `_argv_patch(targets: list[object])` (T2 thermo)
**File:** `upgrade.py:172`.

The function only formats the list as strings. Type as
`list[str]`. The 2 cast call sites disappear once `test_suggestions`
is typed (T3).

### T9 — `reporting.replace_state(struct, **changes: object)` (T7 code-review, T6 thermo)
**File:** `reporting.py:22`.

Delete `replace_state`. Callers (5 in `coverage.py` and one in
`scripts/upstream_contract.py`) use `msgspec.structs.replace`
directly with named kwargs.

### T10 — `schema.py:62, 178, 182, 210, 219` `object` in JSON Schema builder (T8 code-review, T7 thermo)
**File:** `schema.py:62-235`.

Delete the 60-line `_build_schema_for` / `visit` / `_build_struct_schema`
visitor. Replace with `msgspec.json.schema(SemanticCLIContract)` and
`msgspec.json.schema(CoverageReport)`. All 5 `object` / `_t.Any`
sites in this file go away. (Round-2 M5 said this is partial because
of `dict[str, object]`; round-3 fixes the underlying model so
`msgspec.json.schema()` works.)

### T11 — `generator/contract.py:168` `container: object` (T9 code-review, T8 thermo, T8 ponytail)
**File:** `generator/contract.py:168`.

Type as `dict[str, object] | list[object]` (the only two shapes
the visitor handles). All 4 `isinstance(parent.container, ...)`
branches in `_parse_seq_item` / `_parse_mapping_entry` become
exhaustive over a closed union.

### T12 — `scripts/upstream_contract.py:18-20` `sys.path.insert` hack (T11 code-review, T9 thermo, T2 ponytail)
**File:** `scripts/upstream_contract.py:18-20`.

Replace with proper module entry: add `__main__.py` to
`src/multica_py/_internal/upstream_contract/` (or
`src/multica_py/_internal/upstream_contract_cli.py`) and invoke
`python -m`. The 13-line import block collapses to a single
package import.

### T13 — `pyproject.toml:111-128` mypy `disallow_any_expr = false` override (T-ponytail)
**File:** `pyproject.toml`.

The override nullifies `strict = true` for the upstream-contract
package and the script. Delete both overrides. With all T1-T12
done, the override is no longer needed; without the override, mypy
will enforce the typed shapes.

## MEDIUM (MEDIUM)

### M22 — `generator/contract.py:113-132` `_coerce_scalar` re-implements `json.loads`
**File:** `generator/contract.py:113-132`.

`json.loads(value)` handles the same cases. Collapse to one line.
Return type becomes `_YamlScalar = str | int | float | bool | None`.

### M23 — `generator/contract.py:55` `ApprovedOperation.constraints: tuple[dict[str, str], ...]`
**File:** `generator/contract.py:55`.

Replace with `Constraint(msgspec.Struct)` (`category` plus typed
optional fields). The validator at `contract.py:286-291` then
doesn't need `dict.get("category", "")`.

### M24 — `generator/contract.py:142, 150` `decode_observer / _read_json -> dict[str, object]`
**File:** `generator/contract.py:142, 150`.

`decode_observer` should return an `ObserverState` struct.
`_read_json` accepts `JsonScalar` shapes.

### M25 — `schema.py:68, 76, 84, 92, 100, 108, 116, 124, 132` `decode_*(data, dict[str, object])`
**File:** `schema.py`.

Replace `dict[str, object]` input with
`dict[str, JsonScalar] | bytes | str | pathlib.Path` — msgspec
handles all four natively.

## LOW (LOW) — Defer

- L1-L14 from round 2 still open (judgement calls).
- L15 (new): `_coerce_str_list` style helpers — already deleted in round 2.
- L16 (new): `TestSuggestions` extension fields (e.g. `golden_fixtures`) — add only when a second consumer appears.

## KEEP (per spec, do NOT remove)

- All `models.py` field declarations required by data-model.md.
- `contracts/sdk-contract.yaml` as the approved contract location.

## Gate to re-run

Same as round 2 + mypy without the override. After T13, `uv run mypy -p multica_py` must be clean with `disallow_any_expr` not relaxed for the upstream-contract package.

---

# Round 4 — Final cleanup

Three reviewers converged again. Round 4 priorities:

## CRITICAL (HIGH)

### F1 — `cli.py` `*_obj: object = args.X; str(...)` ritual
**File:** `src/multica_py/_internal/upstream_contract/cli.py`.

The `object` annotation + `str()` cast dance (10+ sites) is
**ceremony**, not typing. `argparse` hands you `str | None` directly.
Delete the `*_obj` locals, use `args.X` directly. The original
`object` violation is gone; the new ritual is just as dishonest as
`cast(...)` was.

### F2 — `suggestions.py` ignores the new `ManifestSuggestion` Struct
**File:** `src/multica_py/_internal/upstream_contract/suggestions.py:13, 15, 82`.

`generate_manifest_suggestions` returns `tuple[dict[str, object], ...]`
and `apply_manifest_suggestions` accepts the same. The new
`ManifestSuggestion` Struct in `models.py:274` exists but is
**never used** in this path. Migrate both to the Struct.

### F3 — `cli.py` emit/format pattern repeated 6×
**File:** `src/multica_py/_internal/upstream_contract/cli.py`.

`cmd_check`, `cmd_diff`, `cmd_prepare_upgrade`, `cmd_apply_manifest_suggestions`,
`cmd_observe`, `cmd_promote`, `cmd_reject` each end with the same
"if format=='json': to_builtins + dumps + optional file write; else:
human + optional file write" pair. One `_emit(args, payload, *, human_fn)`
helper. ~50 LOC.

### F4 — `cli.py:148-205` and `208-251` two near-duplicate legacy loaders
**File:** `src/multica_py/_internal/upstream_contract/cli.py`.

`_legacy_contract_from_manifest` and `_load_coverage_manifest` are
the same JSON-dict-load + per-key coercion. One helper.

### F5 — `cli.py:583` `_add_common` is dead
**File:** `src/multica_py/_internal/upstream_contract/cli.py:583`.

`--repo-root` is already on the parent parser at line 580. argparse
subparsers inherit parent flags. Delete `_add_common` and the 7 calls.

### F6 — `schema.py:69-152` 10 copy-paste `decode_*` functions
**File:** `src/multica_py/_internal/upstream_contract/schema.py`.

The 10 `decode_*` functions differ only in `(version_constant, target_struct)`.
Replace with a single `_decode(version, target, data)` + dispatch
table. ~60 LOC.

## MEDIUM (MEDIUM)

### M26 — `cli.py:315-320` `_emit` is dead
**File:** `src/multica_py/_internal/upstream_contract/cli.py:315-320`.

`_emit(args, report, *, writing_ok)` is unused (the only call site
in cmd_apply_manifest_suggestions doesn't exist). Delete.

### M27 — `upgrade.py:140-164` 7 to_builtins + canonical_bytes triplets
**File:** `src/multica_py/_internal/upstream_contract/upgrade.py`.

One `write_canonical_json(path, struct)` helper.

### M28 — `schema.py:9-40` re-export block is dead
**File:** `src/multica_py/_internal/upstream_contract/schema.py:9-40`.

`from .models import (... 30+ models ...)` — no caller imports
`schema.X` (only `schema.decode_*`). Delete.

### M29 — `decode_compatibility` and `decode_observer` are dead
**File:** `src/multica_py/_internal/upstream_contract/schema.py:135, 145`.

No src caller, no test caller. Delete.

### M30 — `coverage.py:199-202` `_build_bindings_index` dead alias
**File:** `src/multica_py/_internal/upstream_contract/coverage.py:199-202`.

3-line private alias for `build_bindings_index`. One caller
(line 85). Inline.

### M31 — `collectors/binary.py` 11-keyword-arg `collect_from_binary`
**File:** `src/multica_py/_internal/upstream_contract/collectors/binary.py:55-72`.

5 of the 11 args (`asset_name`, `sha256`, `os`, `arch`, `version_output`)
are 1:1 with `BinaryRef`. Pass `BinaryRef` instead.

### M32 — `files.py:29-31` `ensure_no_write` is dead
**File:** `src/multica_py/_internal/upstream_contract/files.py:29-31`.

Only used by its own test. Delete both (or keep with a note that
the feature is intentional for the no-write path).

### M33 — `normalize.py` `JsonValue`/`CanonicalInput` aliases are renamed `object`
**File:** `src/multica_py/_internal/upstream_contract/normalize.py:9, 19-20`.

`JsonValue = JsonScalar | list[object] | dict[str, object]` and
`CanonicalInput = msgspec.Struct | dict[str, object] | list[object] | JsonScalar`
both widen to `object` once you add the container cases. The aliases
overpromise and silently widen. Either name them precisely (recursive
type) or delete.

## KEEP

- `decode_*` functions that are actually called (decode_state, decode_contract, decode_diff, decode_coverage, decode_impact, decode_bundle, decode_promotion, decode_evidence).
- `SupportedSummary`/`ObservedSummary`/`CandidateSummary` as 3 separate Structs — the spec distinguishes them.
- `Raw*` Structs in `_raw_payloads.py` — real typed boundaries.

## Gate to re-run

Same as round 3:
1. `uv run pytest -q` — 359+ pass.
2. `uv run ruff check .` — clean.
3. `uv run ruff format --check .` — clean.
4. `uv run mypy --namespace-packages --explicit-package-bases -p multica_py` — clean.
5. `uv run python scripts/upstream_contract.py check --format human` — exit 0, real `semantic_hash`.
