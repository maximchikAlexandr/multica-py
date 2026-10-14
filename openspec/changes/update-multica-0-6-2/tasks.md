## 1. Approved 0.6.2 contract

- [x] 1.1 Update target, release, archive, executable, version-output, compatibility-interval, and rollback provenance in `contracts/sdk-contract.json` for exact `v0.6.2` commit `7ab92d7622ecd81d179a8d83ae2dea74835a5069`, retaining existing lower operation and field gates.
- [x] 1.2 Reconcile all 209 target CLI nodes with arity, aliases, visibility, flags, defaults, inherited flags, input destinations, five-state presence, imperative constraints, enum policy, secrets/local-control classification, coverage decisions, full-SHA sources, and test references; preserve reviewed handling of dynamic `checkin` and hidden `probe-runtimes`.
- [x] 1.3 Reconcile all 196 supported response entrypoints with changed/unchanged manifest rows covering envelopes, fields, types, nullability, omission, nested collections, pagination/cursors, enums, timestamps/numbers, and all reviewed error classes.
- [x] 1.4 Record all three daemon-autostart nodes as deferred inventory entries with no public symbol, binding, model, operation case, or documentation example.
- [x] 1.5 Extend contract schema/loader validation and mutation cases for the new property values, response fields, compatibility metadata, source references, deferred-node invariants, and complete inventory/registry reconciliation.
- [x] 1.6 Run approved-contract validation against the pinned `0.6.2` source, render the single committed runtime projection, run check mode, and prove a second render is byte-identical and consumes no review-only evidence.

## 2. Multi-value properties

- [x] 2.1 Extend property definition policy for open `multi_text` and `multi_url` strings, reject nonempty options for them, and add table rows for definition get/list/create behavior.
- [x] 2.2 Add a property-only immutable list value type without widening `MetadataValue`; decode `multi_text` and `multi_url` rows by property type and reject scalar/object/null/non-string collection payloads with the existing typed output error.
- [x] 2.3 Add the same keyword-only `property_type: Literal["multi_text", "multi_url"] | None` discriminator to direct issue-property set and create-time `IssuePropertyAssignment`; preserve undiscriminated scalar-string compatibility and reject sequences, unsupported types, conflicting scalar values, and null before I/O.
- [x] 2.4 Route both public inputs through one shared normalizer that parses discriminated comma/JSON strings or string sequences, emits compact JSON, stably de-duplicates, and enforces nonempty/max-20 plus type-specific text length and HTTP(S) URL scheme/length rules before command construction.
- [x] 2.5 Add exact-element list-property filter encoding and literal display-value decoding that never resolves member-shaped text; cover raw issue projections and authoritative resolved relations.
- [x] 2.6 Extend existing frozen unit/contract/component case tables for discriminator presence/conflict, both public boundaries, JSON-array/comma input, comma/bracket ambiguity, empty/over-limit/duplicate items, text/URL bounds, HTTP(S), null versus unset, filtering, display values, malformed response rows, and zero transport calls on every invalid case.

## 3. Target response models and retained operations

- [x] 3.1 Add optional `DaemonStatus.cli_commit` and fixtures for full SHA, explicit empty string, legacy omission, and the prohibition on `cli_version` fallback across eager and command paths.
- [x] 3.2 Add nullable `IssueWakeup.last_error` to the shared create/get/list/update/disable decoder; cover the three reviewed recoverable pull-request diagnostics, pending round trips, and clearing after recovery without stale client caching.
- [x] 3.3 Map interrupted attachment response-body reads to `NetworkError` without a partial success model, preserving existing redaction and exception chaining contracts.
- [x] 3.4 Add retained-operation regressions for digit-prefixed/cancelled issue search, project `Unset` versus explicit-null updates with revision conflicts, and redacted HTTP 500 payloads without asserting backend raw text.
- [x] 3.5 Run focused model, decoder, resource, transport, generated-contract, public-surface, and fake-CLI component tests for groups 2 and 3, plus mypy for source and tests.

## 4. Documentation and compatibility

- [x] 4.1 Update API, service-usage, compatibility, CLI-coverage, migration, changelog, contributing, and release documentation for direct `0.6.1→0.6.2`, the `0.6.3` exclusive ceiling, list-property semantics, daemon commit, wakeup diagnostics, error changes, and explicit autostart deferral.
- [x] 4.2 Extend documentation/public-export contract tests so examples, signatures, immutable value types, compatibility claims, source links, and absence of daemon-autostart SDK methods stay synchronized with the approved contract.
- [x] 4.3 Run the full-SHA source-link audit and confirm Git excludes `.devlocal`, binaries, collector/audit/response-review JSON, transient renders, and generated suggestions.

## 5. Final verification and release readiness

- [x] 5.1 Run all focused tests, `uv run pytest -m "not live"`, and `uv run pytest -m "not live" --collect-only`; confirm every expected offline layer is collected and no `tests/live/*` node is collected.
- [x] 5.2 Run `uv run ruff check`, `uv run ruff format --check`, `uv run mypy src`, `uv run mypy tests`, approved-contract validate/render/check and freshness checks, and strict OpenSpec validation.
- [x] 5.3 Build wheel and sdist, run packaging tests against both artifacts, and verify compatibility metadata, public model fields/value types, generated projection, and `py.typed` import before any CLI invocation.
- [ ] 5.4 Run the existing credential-gated live smoke only in its separate approved environment, record its result without weakening offline gates, and complete the release/migration checklist.
